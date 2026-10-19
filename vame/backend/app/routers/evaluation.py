"""Evaluasi & assessment 2-langkah (FR-25..FR-29, FR-32).

Langkah 1 — POST /reading-points/{rid}/evaluation:
  AI generate soal, buat EvaluationAttempt pending, transisi DISCUSSING→ASSESSMENT.
Langkah 2 — POST /evaluations/{eid}/answer {"answer": "..."}:
  AI grade jawaban, transisi ASSESSMENT→PASSED atau NEEDS_REVIEW.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.client import AIClient, get_ai_client
from ..ai.prompts import build_eval_grade_prompt, build_eval_question_prompt
from ..config import settings
from ..core import learning as L
from ..core import state_machine as sm
from ..deps import get_db, rate_limit_ai, require_learner
from ..models import EvaluationAttempt, Question, User, utcnow
from ..schemas import AIGrade, AIQuestion

router = APIRouter(tags=["5. Evaluation"])


class _AnswerIn(BaseModel):
    answer: str = Field(min_length=1)


# ---------- soal admin (FR-11) ----------
@router.get("/reading-points/{rid}/evaluation", summary="Daftar soal evaluasi untuk poin bacaan")
def list_questions(rid: int, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    ctx = L.get_point_ctx(db, user.id, rid)
    questions = db.scalars(select(Question).where(Question.reading_point_id == rid).order_by(Question.id)).all()
    return {
        "reading_point_id": rid,
        "title": ctx.rp.title,
        "questions": [
            {"id": q.id, "text": q.question_text, "type": q.question_type, "weight": q.weight}
            for q in questions
        ],
    }


# ---------- langkah 1: generate soal + mulai evaluasi ----------
@router.post("/reading-points/{rid}/evaluation", summary="Mulai evaluasi: AI generate soal (FR-25)")
def request_evaluation(
    rid: int,
    db: Session = Depends(get_db),
    user: User = Depends(rate_limit_ai),
    ai: AIClient = Depends(get_ai_client),
):
    """Buat soal evaluasi via AI. Wajib ≥1 interaksi mentoring normal (FR-27).
    Transisi DISCUSSING→ASSESSMENT setelah sukses; bila AI gagal status tetap (NFR-05)."""
    ctx = L.get_point_ctx(db, user.id, rid)

    # FR-27: minimal interaksi mentoring sebelum minta evaluasi
    n = L.count_learner_interactions(db, user.id, rid)
    if n < settings.min_mentor_interactions:
        raise HTTPException(409, {
            "code": "NEED_INTERACTION",
            "message": f"Minimal {settings.min_mentor_interactions} interaksi mentoring diperlukan sebelum evaluasi.",
            "current_status": ctx.lp.status,
            "interactions": n,
        })

    # idempoten: kembalikan pending yang sudah ada
    pending = db.scalar(
        select(EvaluationAttempt).where(
            EvaluationAttempt.user_id == user.id,
            EvaluationAttempt.reading_point_id == rid,
            EvaluationAttempt.status == "pending",
        )
    )
    if pending:
        return _attempt_out(pending)

    # transisi valid dari DISCUSSING, atau retry saat masih ASSESSMENT
    if ctx.lp.status == "DISCUSSING":
        L.apply_transition(db, ctx.lp, sm.Trigger.REQUEST_EVALUATION, "permintaan evaluasi")
    elif ctx.lp.status != "ASSESSMENT":
        raise L.invalid_transition_http(sm.InvalidTransition(
            sm.Status(ctx.lp.status), sm.Trigger.REQUEST_EVALUATION
        ))

    # riwayat pertanyaan agar tidak mengulang
    prev = db.scalars(
        select(EvaluationAttempt.question).where(
            EvaluationAttempt.user_id == user.id,
            EvaluationAttempt.reading_point_id == rid,
            EvaluationAttempt.status != "pending",
        ).order_by(EvaluationAttempt.created_at.desc()).limit(5)
    ).all()

    system_prompt = L.active_prompt(db).content
    system, messages = build_eval_question_prompt(system_prompt, ctx.rp, prev)
    q = ai.complete_structured(db, kind="eval_question", system=system, messages=messages, schema=AIQuestion, user_id=user.id)

    attempt = EvaluationAttempt(user_id=user.id, reading_point_id=rid, question=q.question, status="pending")
    db.add(attempt)
    db.commit()
    return _attempt_out(attempt)


# ---------- langkah 2: kirim jawaban & dinilai AI ----------
@router.post("/evaluations/{eid}/answer", summary="Kirim jawaban untuk dinilai AI (FR-29)")
def submit_answer(
    eid: int,
    body: _AnswerIn,
    db: Session = Depends(get_db),
    user: User = Depends(rate_limit_ai),
    ai: AIClient = Depends(get_ai_client),
):
    """Grade jawaban via AI. Hasil menentukan PASSED (buka poin berikut) atau NEEDS_REVIEW."""
    attempt = db.get(EvaluationAttempt, eid)
    if not attempt or attempt.user_id != user.id:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Evaluasi tidak ditemukan."})
    if attempt.status != "pending":
        raise HTTPException(409, {"code": "ALREADY_GRADED", "message": "Evaluasi ini sudah dinilai."})

    ctx = L.get_point_ctx(db, user.id, attempt.reading_point_id)

    system_prompt = L.active_prompt(db).content
    system, messages = build_eval_grade_prompt(system_prompt, ctx.rp, attempt.question, body.answer)
    grade = ai.complete_structured(db, kind="eval_grade", system=system, messages=messages, schema=AIGrade, user_id=user.id)

    threshold = L.pass_threshold(db)
    score = float(grade.score)
    trigger, next_st = sm.next_status_after_score(score, threshold)

    # simpan hasil
    attempt.answer = body.answer
    attempt.status = "graded"
    attempt.score = score
    attempt.passed = trigger.value == "pass"
    attempt.feedback = grade.feedback
    attempt.graded_at = utcnow()

    # transisi status belajar
    L.apply_transition(db, ctx.lp, trigger, f"penilaian skor={score} (batas={threshold})")
    next_point_id = None
    if trigger.value == "pass":
        ctx.lp.best_score = max(ctx.lp.best_score or 0, score)
        next_point_id = L.unlock_next(db, user.id, ctx.rp, ctx.curriculum.id)

    db.commit()
    from ..services.analytics import record_event
    record_event(db, event_type="evaluation_submit", user_id=user.id, reading_point_id=attempt.reading_point_id, meta={"score": score, "passed": attempt.passed})
    return {
        "id": attempt.id,
        "passed": attempt.passed,
        "status": next_st.value,
        "score": score,
        "threshold": threshold,
        "feedback": grade.feedback,
        "next_point_id": next_point_id,
        "missed_points": [],
        "evaluation": {
            "id": attempt.id,
            "score": score,
            "feedback": grade.feedback,
            "passed": attempt.passed,
            "status": "graded",
            "graded_at": attempt.graded_at.isoformat() if attempt.graded_at else None,
        },
    }


# ---------- riwayat evaluasi ----------
@router.get("/reading-points/{rid}/evaluations", summary="Riwayat evaluasi poin bacaan (FR-28)")
def evaluation_history(rid: int, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    L.get_point_ctx(db, user.id, rid)  # validasi akses
    attempts = db.scalars(
        select(EvaluationAttempt).where(
            EvaluationAttempt.user_id == user.id,
            EvaluationAttempt.reading_point_id == rid,
        ).order_by(EvaluationAttempt.created_at.desc())
    ).all()
    return [
        {
            "id": a.id, "question": a.question, "answer": a.answer,
            "score": a.score, "passed": a.passed, "status": a.status,
            "feedback": a.feedback, "created_at": a.created_at.isoformat(),
            "graded_at": a.graded_at.isoformat() if a.graded_at else None,
        }
        for a in attempts
    ]


# ---------- detail satu hasil ----------
@router.get("/evaluations/{eid}/result", summary="Lihat hasil ujian (FR-28)")
def get_evaluation_result(eid: int, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    attempt = db.get(EvaluationAttempt, eid)
    if not attempt or attempt.user_id != user.id:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Hasil evaluasi tidak ditemukan."})
    return {
        "attempt_id": attempt.id,
        "reading_point_id": attempt.reading_point_id,
        "status": attempt.status,
        "score": attempt.score,
        "passed": attempt.passed,
        "question": attempt.question,
        "answer": attempt.answer,
        "feedback": attempt.feedback or "",
        "graded_at": attempt.graded_at,
    }


def _attempt_out(a: EvaluationAttempt) -> dict:
    return {"id": a.id, "status": a.status, "reading_point_id": a.reading_point_id, "question": a.question}

