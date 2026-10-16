"""Evaluasi pemahaman (FR-21..FR-25). Status berubah hanya jika AI sukses (NFR-05) dan atomik (NFR-13)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import guardrails as G
from ..ai.client import AIClient, get_ai_client
from ..ai.prompts import build_eval_grade_prompt, build_eval_question_prompt
from ..config import settings
from ..core import learning as L
from ..core import state_machine as sm
from ..core.state_machine import InvalidTransition, Status, Trigger
from ..database import get_db
from ..deps import rate_limit_ai, require_learner
from ..models import EvaluationAttempt, ReadingPoint, User, utcnow
from ..schemas import AIGrade, AIQuestion, AnswerIn, EvaluationOut

router = APIRouter(tags=["5. Evaluasi"])


@router.post("/reading-points/{rid}/evaluation", summary="Minta pertanyaan evaluasi (FR-21)")
def request_evaluation(
    rid: int,
    db: Session = Depends(get_db),
    user: User = Depends(rate_limit_ai),
    ai: AIClient = Depends(get_ai_client),
):
    ctx = L.get_point_ctx(db, user.id, rid)
    lp = ctx.lp
    if lp.status == Status.ASSESSMENT.value:  # lanjutkan evaluasi yang tertunda
        pending = db.scalar(
            select(EvaluationAttempt)
            .where(EvaluationAttempt.user_id == user.id, EvaluationAttempt.reading_point_id == rid, EvaluationAttempt.status == "pending")
            .order_by(EvaluationAttempt.id.desc())
        )
        if pending:
            return EvaluationOut.model_validate(pending)
    elif lp.status == Status.DISCUSSING.value:
        n = L.count_learner_interactions(db, user.id, rid)
        if n < settings.min_mentor_interactions:
            raise HTTPException(
                409,
                {"code": "NEED_DISCUSSION", "message": f"Ajukan minimal {settings.min_mentor_interactions} pertanyaan ke mentor sebelum evaluasi.", "interactions": n},
            )
    else:
        try:
            L.apply_transition(db, lp, Trigger.REQUEST_EVALUATION)  # tidak valid -> dicatat & ditolak (FR-15)
        except InvalidTransition as e:
            raise L.invalid_transition_http(e) from None

    previous = [a.question for a in db.scalars(select(EvaluationAttempt).where(EvaluationAttempt.user_id == user.id, EvaluationAttempt.reading_point_id == rid))]
    system, messages = build_eval_question_prompt(L.active_prompt(db).content, ctx.rp, previous)
    q = ai.complete_structured(db, kind="eval_question", system=system, messages=messages, schema=AIQuestion, user_id=user.id)

    if lp.status == Status.DISCUSSING.value:
        L.apply_transition(db, lp, Trigger.REQUEST_EVALUATION)
    attempt = EvaluationAttempt(user_id=user.id, reading_point_id=rid, question=q.question)
    db.add(attempt)
    db.commit()
    return EvaluationOut.model_validate(attempt)


@router.post("/evaluations/{eid}/answer", summary="Kirim jawaban evaluasi (FR-22..FR-24)")
def answer_evaluation(
    eid: int,
    body: AnswerIn,
    db: Session = Depends(get_db),
    user: User = Depends(rate_limit_ai),
    ai: AIClient = Depends(get_ai_client),
):
    att = db.get(EvaluationAttempt, eid)
    if not att or att.user_id != user.id:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Evaluasi tidak ditemukan."})
    if att.status != "pending":
        raise HTTPException(409, {"code": "ALREADY_GRADED", "message": "Evaluasi ini sudah dinilai."})
    ctx = L.get_point_ctx(db, user.id, att.reading_point_id)
    lp = ctx.lp
    if lp.status != Status.ASSESSMENT.value:
        try:
            sm.transition(lp.status, Trigger.PASS_)
        except InvalidTransition as e:
            L._log_invalid(db, lp, Trigger.PASS_)
            raise L.invalid_transition_http(e) from None

    answer = G.sanitize_user_text(body.answer, max_chars=4000)
    if not answer:
        raise HTTPException(422, {"code": "EMPTY", "message": "Jawaban tidak boleh kosong."})
    system, messages = build_eval_grade_prompt(L.active_prompt(db).content, ctx.rp, att.question, answer)
    grade = ai.complete_structured(db, kind="eval_grade", system=system, messages=messages, schema=AIGrade, user_id=user.id)

    threshold = L.pass_threshold(db)
    trigger, _ = sm.next_status_after_score(grade.score, threshold)  # FR-24
    # ---- satu transaksi: skor + status + pembukaan poin berikutnya (NFR-13) ----
    att.answer, att.score, att.feedback = answer, float(grade.score), grade.feedback
    att.passed = trigger == Trigger.PASS_
    att.status, att.graded_at = "graded", utcnow()
    L.apply_transition(db, lp, trigger, f"skor {grade.score} (batas {threshold})")
    lp.best_score = max(lp.best_score or 0, float(grade.score))
    next_id = None
    if att.passed:
        L.unlock_next(db, user.id, ctx.rp, ctx.curriculum.id)
        pts = L.ordered_points(db, ctx.curriculum.id)
        idx = next(i for i, p in enumerate(pts) if p.id == ctx.rp.id)
        next_id = pts[idx + 1].id if idx + 1 < len(pts) else None
    db.commit()
    return {
        "evaluation": EvaluationOut.model_validate(att),
        "status": lp.status,
        "passed": att.passed,
        "threshold": threshold,
        "missed_points": grade.missed_points,
        "next_point_id": next_id,
    }


@router.get("/reading-points/{rid}/evaluations", summary="Riwayat evaluasi poin bacaan (FR-32)")
def evaluation_history(rid: int, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    L.get_point_ctx(db, user.id, rid)
    rows = db.scalars(
        select(EvaluationAttempt)
        .where(EvaluationAttempt.user_id == user.id, EvaluationAttempt.reading_point_id == rid)
        .order_by(EvaluationAttempt.id.desc())
    )
    return [EvaluationOut.model_validate(r) for r in rows]
