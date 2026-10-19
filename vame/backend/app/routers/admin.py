"""Administrasi & monitoring (FR-38..FR-41)."""
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..core import learning as L
from ..database import get_db
from ..deps import require_admin
from ..models import (
    AIUsageLog, AppSetting, ChatSession, Enrollment, EvaluationAttempt, LearningProgress, Message,
    PromptConfig, ReadingPoint, StateTransitionLog, User,
)
from ..schemas import AIProviderConfigIn, PromptConfigIn, QuestionIn, SettingsIn

router = APIRouter(prefix="/admin", tags=["7. Admin"])


@router.get("/overview", summary="Ringkasan sistem")
def overview(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    c = lambda q: db.scalar(q) or 0  # noqa: E731
    return {
        "learners": c(select(func.count(User.id)).where(User.role == "learner")),
        "sessions": c(select(func.count(ChatSession.id))),
        "flagged_messages": c(select(func.count(Message.id)).where(Message.flagged.is_(True))),
        "ai_calls": c(select(func.count(AIUsageLog.id))),
        "ai_failures": c(select(func.count(AIUsageLog.id)).where(AIUsageLog.success.is_(False))),
        "pass_threshold": L.pass_threshold(db),
    }


@router.get("/users", summary="Daftar pengguna & progres agregat (FR-39)")
def users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    out = []
    for u in db.scalars(select(User).order_by(User.id)):
        total = c = 0
        if u.role == "learner":
            rows = db.scalars(select(LearningProgress).where(LearningProgress.user_id == u.id)).all()
            total, c = len(rows), sum(r.status == "PASSED" for r in rows)
        scores = db.scalars(select(EvaluationAttempt.score).where(EvaluationAttempt.user_id == u.id, EvaluationAttempt.status == "graded")).all()
        out.append({
            "id": u.id, "name": u.name, "email": u.email, "role": u.role, "created_at": u.created_at,
            "enrollments": db.scalar(select(func.count(Enrollment.id)).where(Enrollment.user_id == u.id)) or 0,
            "points_passed": c, "points_total": total, "percent": round(100 * c / total) if total else 0,
            "avg_score": round(sum(scores) / len(scores), 1) if scores else None,
        })
    return out


@router.get("/sessions", summary="Log sesi mentoring, termasuk yang ditandai (FR-40)")
def sessions(
    flagged: bool = False, limit: int = Query(50, le=200), offset: int = 0,
    db: Session = Depends(get_db), _: User = Depends(require_admin),
):
    flag_sum = func.sum(case((Message.flagged.is_(True), 1), else_=0))
    q = (
        select(ChatSession, User.name, ReadingPoint.title,
               func.count(Message.id), flag_sum)
        .join(Enrollment, ChatSession.enrollment_id == Enrollment.id)
        .join(User, Enrollment.user_id == User.id)
        .join(ReadingPoint, ChatSession.reading_point_id == ReadingPoint.id)
        .join(Message, Message.session_id == ChatSession.id, isouter=True)
        .group_by(ChatSession.id, User.name, ReadingPoint.title)
        .order_by(ChatSession.id.desc())
        .limit(limit).offset(offset)
    )
    if flagged:
        q = q.having(flag_sum > 0)
    return [
        {"id": s.id, "learner": name, "reading_point": title, "started_at": s.started_at, "messages": n or 0, "flagged": int(f or 0)}
        for s, name, title, n, f in db.execute(q)
    ]


@router.get("/sessions/{sid}", summary="Detail percakapan sesi (FR-40)")
def session_detail(sid: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    s = db.get(ChatSession, sid)
    if not s:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Sesi tidak ditemukan."})
    enr = db.get(Enrollment, s.enrollment_id)
    learner_name = db.get(User, enr.user_id).name if enr else "?"
    return {
        "id": s.id, "learner": learner_name, "reading_point": db.get(ReadingPoint, s.reading_point_id).title,
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content, "kind": m.kind, "flagged": m.flagged, "flag_reason": m.flag_reason, "created_at": m.created_at}
            for m in s.messages
        ],
    }


@router.get("/ai-usage", summary="Statistik penggunaan AI per rentang tanggal (FR-41)")
def ai_usage(date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    date_to = date_to or date.today()
    date_from = date_from or (date_to - timedelta(days=29))
    start, end = datetime.combine(date_from, time.min), datetime.combine(date_to + timedelta(days=1), time.min)
    rows = db.scalars(select(AIUsageLog).where(AIUsageLog.created_at >= start, AIUsageLog.created_at < end).order_by(AIUsageLog.id)).all()
    by_day: dict[str, dict] = {}
    by_kind: dict[str, int] = {}
    for r in rows:
        d = by_day.setdefault(r.created_at.date().isoformat(), {"day": r.created_at.date().isoformat(), "calls": 0, "tokens_in": 0, "tokens_out": 0})
        d["calls"] += 1
        d["tokens_in"] += r.tokens_in
        d["tokens_out"] += r.tokens_out
        by_kind[r.kind] = by_kind.get(r.kind, 0) + 1
    ok = [r for r in rows if r.success]
    return {
        "range": {"from": date_from, "to": date_to},
        "totals": {
            "calls": len(rows), "failures": len(rows) - len(ok),
            "tokens_in": sum(r.tokens_in for r in rows), "tokens_out": sum(r.tokens_out for r in rows),
            "avg_latency_ms": round(sum(r.latency_ms for r in ok) / len(ok)) if ok else 0,
        },
        "by_kind": by_kind,
        "by_day": list(by_day.values()),
        "recent": [
            {"id": r.id, "kind": r.kind, "provider": r.provider, "model": r.model, "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
             "latency_ms": r.latency_ms, "success": r.success, "error": r.error, "created_at": r.created_at}
            for r in reversed(rows[-20:])
        ],
    }


@router.get("/ai-usage/calls/{cid}", summary="Audit prompt & respons satu panggilan AI (NFR-04)")
def ai_call(cid: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    r = db.get(AIUsageLog, cid)
    if not r:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Log tidak ditemukan."})
    return {"id": r.id, "kind": r.kind, "prompt": r.prompt, "response": r.response, "error": r.error}


@router.get("/prompt-config", summary="System Prompt aktif & riwayat versi (FR-38)")
def get_prompt_config(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    active = L.active_prompt(db)
    versions = db.scalars(select(PromptConfig).order_by(PromptConfig.version.desc())).all()
    return {
        "active": {"version": active.version, "content": active.content},
        "versions": [{"version": v.version, "active": v.active, "created_at": v.created_at, "content": v.content} for v in versions],
    }


@router.put("/prompt-config", summary="Ubah System Prompt (versi baru) (FR-38)")
def put_prompt_config(body: PromptConfigIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    L.active_prompt(db)
    last = db.scalar(select(func.max(PromptConfig.version))) or 0
    for v in db.scalars(select(PromptConfig).where(PromptConfig.active.is_(True))):
        v.active = False
    new = PromptConfig(version=last + 1, content=body.content.strip(), active=True, created_by=admin.id)
    db.add(new)
    db.commit()
    return {"version": new.version, "active": True}


@router.get("/settings", summary="Pengaturan sistem")
def get_settings(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return {"pass_threshold": L.pass_threshold(db)}


@router.put("/settings", summary="Ubah batas kelulusan (BR-04)")
def put_settings(body: SettingsIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    db.merge(AppSetting(key="pass_threshold", value=str(body.pass_threshold)))
    db.commit()
    return {"pass_threshold": body.pass_threshold}


@router.get("/state-logs", summary="Jejak transisi status (audit, FR-15/NFR-04)")
def state_logs(invalid_only: bool = False, limit: int = Query(50, le=200), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    q = select(StateTransitionLog).order_by(StateTransitionLog.id.desc()).limit(limit)
    if invalid_only:
        q = q.where(StateTransitionLog.valid.is_(False))
    return [
        {"id": r.id, "user_id": r.user_id, "reading_point_id": r.reading_point_id, "from": r.from_status, "trigger": r.trigger,
         "to": r.to_status, "valid": r.valid, "note": r.note, "created_at": r.created_at}
        for r in db.scalars(q)
    ]


# ---------- Question Management (Admin) ----------
@router.post("/reading-points/{rid}/questions", summary="Tambah soal evaluasi (admin)")
def create_question(rid: int, body: QuestionIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import Question
    rp = db.get(ReadingPoint, rid)
    if not rp:
        raise HTTPException(404)
    q = Question(**body.model_dump(), reading_point_id=rid)
    db.add(q)
    db.commit()
    return {"id": q.id, "created": True}


@router.get("/questions/{qid}")
def get_question(qid: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import Question
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404)
    return q


@router.patch("/questions/{qid}")
def update_question(qid: int, body: QuestionIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import Question
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(q, k, v)
    db.commit()
    return {"updated": True}


@router.delete("/questions/{qid}")
def delete_question(qid: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import Question
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404)
    db.delete(q)
    db.commit()
    return {"deleted": True}


# ---------- AI Provider Config (Admin) ----------
@router.get("/ai-providers")
def list_providers(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import AIProviderConfig
    return db.scalars(select(AIProviderConfig).order_by(AIProviderConfig.id.desc())).all()


@router.post("/ai-providers")
def create_provider(body: AIProviderConfigIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import AIProviderConfig
    cfg = AIProviderConfig(**body.model_dump())
    db.add(cfg)
    db.commit()
    return {"id": cfg.id, "created": True}


@router.patch("/ai-providers/{pid}")
def update_provider(pid: int, body: AIProviderConfigIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import AIProviderConfig
    cfg = db.get(AIProviderConfig, pid)
    if not cfg:
        raise HTTPException(404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(cfg, k, v)
    db.commit()
    return {"updated": True}


@router.delete("/ai-providers/{pid}")
def delete_provider(pid: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import AIProviderConfig
    cfg = db.get(AIProviderConfig, pid)
    if not cfg:
        raise HTTPException(404)
    db.delete(cfg)
    db.commit()
    return {"deleted": True}
