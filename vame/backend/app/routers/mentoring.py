"""Mentoring interaktif (FR-16..FR-20) + guardrail (FR-26..FR-30)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import guardrails as G
from ..ai.client import AIClient, get_ai_client
from ..ai.prompts import build_mentor_prompt
from ..config import settings
from ..core import learning as L
from ..core import state_machine as sm
from ..database import get_db
from ..deps import rate_limit_ai, require_learner
from ..models import ChatSession, Message, User
from ..schemas import FlagIn, MessageIn, MessageOut

router = APIRouter(tags=["4. Mentoring"])


def _session_payload(ctx: L.PointCtx, s: ChatSession) -> dict:
    rp = ctx.rp
    return {
        "id": s.id,
        "reading_point": {
            "id": rp.id, "title": rp.title, "objective": rp.objective, "keywords": rp.keywords,
            "status": ctx.lp.status, "module_title": ctx.module.title, "curriculum_id": ctx.curriculum.id,
        },
        "messages": [MessageOut.model_validate(m) for m in s.messages],
        "ai_provider": settings.ai_provider,
        "min_interactions": settings.min_mentor_interactions,
    }


@router.post("/reading-points/{rid}/sessions", summary="Mulai/lanjutkan sesi mentoring pada poin bacaan")
def open_session(rid: int, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    from ..models import Enrollment
    ctx = L.get_point_ctx(db, user.id, rid)
    if not sm.can_open_mentoring(ctx.lp.status):  # BR-01, FR-12
        raise HTTPException(
            409,
            {
                "code": "READ_FIRST",
                "message": "Bacaan wajib harus dibaca dan ditandai selesai sebelum sesi mentoring dimulai.",
                "current_status": ctx.lp.status,
            },
        )
    enr = db.scalar(select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.curriculum_id == ctx.curriculum.id))
    s = db.scalar(select(ChatSession).where(ChatSession.enrollment_id == enr.id, ChatSession.reading_point_id == rid).order_by(ChatSession.id.desc()))
    if not s:
        s = ChatSession(enrollment_id=enr.id, reading_point_id=rid)
        db.add(s)
        db.commit()
    payload = _session_payload(ctx, s)
    payload["interactions"] = L.count_learner_interactions(db, user.id, rid)
    return payload


@router.get("/sessions/{sid}", summary="Riwayat percakapan sesi (FR-20)")
def get_session(sid: int, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    from ..models import Enrollment
    s = db.get(ChatSession, sid)
    if not s:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Sesi tidak ditemukan."})
    enr = db.get(Enrollment, s.enrollment_id)
    if not enr or enr.user_id != user.id:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Sesi tidak ditemukan."})
    ctx = L.get_point_ctx(db, user.id, s.reading_point_id)
    payload = _session_payload(ctx, s)
    payload["interactions"] = L.count_learner_interactions(db, user.id, s.reading_point_id)
    return payload


@router.post("/sessions/{sid}/messages", summary="Kirim pesan ke mentor AI (FR-16)")
def send_message(
    sid: int,
    body: MessageIn,
    db: Session = Depends(get_db),
    user: User = Depends(rate_limit_ai),
    ai: AIClient = Depends(get_ai_client),
):
    from ..models import Enrollment
    s = db.get(ChatSession, sid)
    if not s:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Sesi tidak ditemukan."})
    enr = db.get(Enrollment, s.enrollment_id)
    if not enr or enr.user_id != user.id:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Sesi tidak ditemukan."})
    ctx = L.get_point_ctx(db, user.id, s.reading_point_id)
    if not sm.can_open_mentoring(ctx.lp.status):
        raise HTTPException(409, {"code": "NOT_DISCUSSING", "message": "Sesi mentoring hanya aktif pada tahap diskusi.", "current_status": ctx.lp.status})

    text = G.sanitize_user_text(body.content)
    if not text:
        raise HTTPException(422, {"code": "EMPTY", "message": "Pesan tidak boleh kosong."})

    if G.detect_injection(text):  # FR-28: tidak diteruskan ke AI
        um = Message(session_id=s.id, role="user", content=text, kind="blocked")
        mm = Message(session_id=s.id, role="mentor", content=G.REFUSAL_INJECTION, kind="blocked")
        db.add_all([um, mm])
        db.commit()
        return {"user_message": MessageOut.model_validate(um), "mentor_message": MessageOut.model_validate(mm)}

    history = [{"role": m.role, "content": m.content} for m in s.messages if m.kind != "blocked"]
    system_prompt = L.active_prompt(db).content
    system, messages = build_mentor_prompt(system_prompt, ctx.rp, history, text)  # FR-17
    result = ai.complete(db, kind="mentor", system=system, messages=messages, user_id=user.id)  # galat => 503, tidak ada yg tersimpan (NFR-05)
    reply, kind = G.postprocess_mentor(result.text, system_prompt)

    um = Message(session_id=s.id, role="user", content=text, kind="normal" if kind == "normal" else kind)
    mm = Message(session_id=s.id, role="mentor", content=reply, kind=kind)
    db.add_all([um, mm])
    db.commit()
    from ..services.analytics import record_event
    record_event(db, event_type="message_send", user_id=user.id, reading_point_id=s.reading_point_id, session_id=s.id, meta={"kind": kind})
    return {
        "user_message": MessageOut.model_validate(um),
        "mentor_message": MessageOut.model_validate(mm),
        "interactions": L.count_learner_interactions(db, user.id, s.reading_point_id),
    }


@router.post("/messages/{mid}/flag", summary="Tandai jawaban AI tidak sesuai materi (FR-30)")
def flag_message(mid: int, body: FlagIn, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    from ..models import Enrollment
    m = db.get(Message, mid)
    s = db.get(ChatSession, m.session_id) if m else None
    if not m or not s or m.role != "mentor":
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Pesan mentor tidak ditemukan."})
    enr = db.get(Enrollment, s.enrollment_id) if s else None
    if not enr or enr.user_id != user.id:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Pesan mentor tidak ditemukan."})
    m.flagged = True
    m.flag_reason = body.reason.strip()
    db.commit()
    return {"flagged": True}
