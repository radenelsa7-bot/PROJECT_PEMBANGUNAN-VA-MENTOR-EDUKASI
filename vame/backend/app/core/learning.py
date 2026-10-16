"""Layanan Core Engine di atas DB: progres belajar, transisi, learning path, rekomendasi.
Perubahan status dilakukan oleh kode ini (bukan AI). Pemanggil melakukan db.commit() sekali
agar perubahan status + skor bersifat atomik (NFR-13)."""
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai.prompts import DEFAULT_SYSTEM_PROMPT
from ..config import settings
from ..models import (
    AppSetting,
    ChatSession,
    Curriculum,
    Enrollment,
    EvaluationAttempt,
    LearningProgress,
    Message,
    Module,
    PromptConfig,
    ReadingPoint,
    StateTransitionLog,
    StudyActivity,
    utcnow,
)
from . import state_machine as sm
from .state_machine import Status, Trigger

STATUS_ORDER = [s.value for s in Status]


# ---------------- pengaturan & prompt ----------------
def pass_threshold(db: Session) -> int:
    row = db.get(AppSetting, "pass_threshold")
    return int(row.value) if row else settings.pass_threshold


def active_prompt(db: Session) -> PromptConfig:
    row = db.scalar(select(PromptConfig).where(PromptConfig.active.is_(True)).order_by(PromptConfig.version.desc()))
    if not row:
        row = PromptConfig(version=1, content=DEFAULT_SYSTEM_PROMPT, active=True)
        db.add(row)
        db.commit()
    return row


# ---------------- struktur & progres ----------------
def ordered_points(db: Session, curriculum_id: int) -> list[ReadingPoint]:
    return list(
        db.scalars(
            select(ReadingPoint)
            .join(Module)
            .where(Module.curriculum_id == curriculum_id)
            .order_by(Module.order, ReadingPoint.order)
        )
    )


def ensure_progress(db: Session, user_id: int, curriculum_id: int) -> dict[int, LearningProgress]:
    """Pastikan setiap poin punya baris progres. Poin pertama otomatis AVAILABLE (B.1)."""
    points = ordered_points(db, curriculum_id)
    existing = {
        lp.reading_point_id: lp
        for lp in db.scalars(
            select(LearningProgress).where(
                LearningProgress.user_id == user_id,
                LearningProgress.reading_point_id.in_([p.id for p in points] or [0]),
            )
        )
    }
    prev_passed = True
    for pt in points:
        lp = existing.get(pt.id)
        if lp is None:
            lp = LearningProgress(
                user_id=user_id, reading_point_id=pt.id, status=(Status.AVAILABLE if prev_passed else Status.LOCKED).value
            )
            db.add(lp)
            existing[pt.id] = lp
        elif lp.status == Status.LOCKED.value and prev_passed:
            apply_transition(db, lp, Trigger.UNLOCK, "sinkronisasi")
        prev_passed = lp.status == Status.PASSED.value
    db.flush()
    return existing


def _log_invalid(db: Session, lp: LearningProgress, trigger: Trigger) -> None:
    # Session terpisah: percobaan tidak valid tetap tercatat walau request dibatalkan (FR-15).
    with Session(bind=db.get_bind()) as s:
        s.add(
            StateTransitionLog(
                user_id=lp.user_id,
                reading_point_id=lp.reading_point_id,
                from_status=lp.status,
                trigger=trigger.value,
                to_status=None,
                valid=False,
                note="transisi ditolak",
            )
        )
        s.commit()


def apply_transition(db: Session, lp: LearningProgress, trigger: Trigger, note: str = "") -> Status:
    try:
        new = sm.transition(lp.status, trigger)
    except sm.InvalidTransition:
        _log_invalid(db, lp, trigger)
        raise
    db.add(
        StateTransitionLog(
            user_id=lp.user_id,
            reading_point_id=lp.reading_point_id,
            from_status=lp.status,
            trigger=trigger.value,
            to_status=new.value,
            valid=True,
            note=note,
        )
    )
    lp.status = new.value
    lp.updated_at = utcnow()
    return new


def unlock_next(db: Session, user_id: int, rp: ReadingPoint, curriculum_id: int) -> None:
    """FR-14: buka poin berikutnya hanya setelah poin ini PASSED."""
    pts = ordered_points(db, curriculum_id)
    idx = next((i for i, p in enumerate(pts) if p.id == rp.id), None)
    if idx is None or idx + 1 >= len(pts):
        return
    lp = ensure_progress(db, user_id, curriculum_id)[pts[idx + 1].id]
    if lp.status == Status.LOCKED.value:
        apply_transition(db, lp, Trigger.UNLOCK, f"poin sebelumnya (#{rp.id}) PASSED")


class PointCtx:
    def __init__(self, rp: ReadingPoint, module: Module, curriculum: Curriculum, lp: LearningProgress):
        self.rp, self.module, self.curriculum, self.lp = rp, module, curriculum, lp


def get_point_ctx(db: Session, user_id: int, rp_id: int) -> PointCtx:
    rp = db.get(ReadingPoint, rp_id)
    if not rp:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Poin bacaan tidak ditemukan."})
    module = db.get(Module, rp.module_id)
    curriculum = db.get(Curriculum, module.curriculum_id)
    enrolled = db.scalar(
        select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.curriculum_id == curriculum.id)
    )
    if not enrolled:
        raise HTTPException(403, {"code": "NOT_ENROLLED", "message": "Kamu belum terdaftar pada kurikulum ini."})
    lp = ensure_progress(db, user_id, curriculum.id)[rp.id]
    return PointCtx(rp, module, curriculum, lp)


def invalid_transition_http(e: sm.InvalidTransition, hint: str = "") -> HTTPException:
    msg = {
        Status.LOCKED: "Poin ini masih terkunci. Selesaikan poin sebelumnya sampai lulus (PASSED).",
        Status.AVAILABLE: "Buka dan baca materi terlebih dahulu.",
        Status.READING: "Selesaikan bacaan wajib dan tandai selesai dahulu.",
        Status.DISCUSSING: "Mintalah evaluasi dari tahap diskusi.",
        Status.ASSESSMENT: "Poin ini sedang dalam evaluasi. Jawab pertanyaan evaluasi.",
        Status.PASSED: "Poin ini sudah lulus.",
        Status.NEEDS_REVIEW: "Tinjau ulang materi terlebih dahulu.",
    }[e.current]
    return HTTPException(
        409,
        {"code": "INVALID_TRANSITION", "message": hint or msg, "current_status": e.current.value, "trigger": e.trigger.value},
    )


def count_learner_interactions(db: Session, user_id: int, rp_id: int) -> int:
    return (
        db.scalar(
            select(func.count(Message.id))
            .join(ChatSession, Message.session_id == ChatSession.id)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.reading_point_id == rp_id,
                Message.role == "user",
                Message.kind == "normal",
            )
        )
        or 0
    )


# ---------------- ringkasan learning path ----------------
def _fmt_minutes(seconds: int) -> str:
    m = seconds // 60
    return f"{m // 60}j {m % 60}m" if m >= 60 else f"{m}m"


def build_learning_path(db: Session, user_id: int, user_name: str, curriculum: Curriculum) -> dict:
    lps = ensure_progress(db, user_id, curriculum.id)
    db.commit()
    modules_out, counts = [], {s: 0 for s in STATUS_ORDER}
    current = None
    total_pts = passed_pts = 0
    for m in curriculum.modules:
        pts = []
        for rp in m.reading_points:
            lp = lps[rp.id]
            counts[lp.status] += 1
            total_pts += 1
            passed_pts += lp.status == Status.PASSED.value
            item = {"id": rp.id, "title": rp.title, "order": rp.order, "status": lp.status, "score": lp.best_score}
            pts.append(item)
            if current is None and lp.status not in (Status.PASSED.value, Status.LOCKED.value):
                current = {**item, "module_id": m.id, "module_title": m.title}
        n_pass = sum(p["status"] == "PASSED" for p in pts)
        if pts and n_pass == len(pts):
            mstatus = "PASSED"
        elif all(p["status"] == "LOCKED" for p in pts):
            mstatus = "LOCKED"
        else:
            mstatus = "IN_PROGRESS"
        scores = [p["score"] for p in pts if p["score"] is not None]
        modules_out.append(
            {
                "id": m.id, "title": m.title, "label": m.label, "order": m.order, "status": mstatus,
                "passed": n_pass, "total": len(pts),
                "percent": round(100 * n_pass / len(pts)) if pts else 0,
                "final_score": round(sum(scores) / len(scores), 1) if mstatus == "PASSED" and scores else None,
                "reading_points": pts,
            }
        )
    summary = {
        "percent": round(100 * passed_pts / total_pts) if total_pts else 0,
        "points_passed": passed_pts,
        "points_total": total_pts,
        "modules_total": len(modules_out),
        "modules_done": sum(m["status"] == "PASSED" for m in modules_out),
        "modules_in_progress": sum(m["status"] == "IN_PROGRESS" for m in modules_out),
        "modules_locked": sum(m["status"] == "LOCKED" for m in modules_out),
        "status_counts": counts,
    }
    insight = latest_insight(db, user_id, curriculum.id)
    return {
        "curriculum": {
            "id": curriculum.id, "code": curriculum.code, "title": curriculum.title, "short_name": curriculum.short_name or curriculum.title,
            "description": curriculum.description, "level": curriculum.level, "topic_label": curriculum.topic_label,
            "est_hours": curriculum.est_hours, "mentor_name": curriculum.mentor_name,
        },
        "summary": summary,
        "modules": modules_out,
        "current": current and {**current, "action": _action_for(current["status"])},
        "activity": activity_today(db, user_id, curriculum.id),
        "insight": insight,
        "recommendation": recommend(current, insight, summary),
    }


def _action_for(status: str) -> str:
    return {
        "AVAILABLE": "read", "READING": "read", "NEEDS_REVIEW": "review",
        "DISCUSSING": "mentoring", "ASSESSMENT": "evaluation",
    }.get(status, "read")


def activity_today(db: Session, user_id: int, curriculum_id: int) -> dict:
    today = date.today()
    sec = lambda d: db.scalar(select(StudyActivity.seconds).where(StudyActivity.user_id == user_id, StudyActivity.day == d)) or 0  # noqa: E731
    t, y = sec(today), sec(today - timedelta(days=1))
    day_start = datetime.combine(today, time.min)
    day_end = day_start + timedelta(days=1)
    sessions_today = (
        db.scalar(
            select(func.count(func.distinct(Message.session_id)))
            .join(ChatSession, Message.session_id == ChatSession.id)
            .where(ChatSession.user_id == user_id, Message.role == "user", Message.created_at >= day_start, Message.created_at < day_end)
        )
        or 0
    )
    enr = db.scalar(select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.curriculum_id == curriculum_id))
    diff = (t - y) // 60
    return {
        "study_seconds": t,
        "study_label": _fmt_minutes(t),
        "delta_label": f"{'+' if diff >= 0 else '-'}{abs(diff)}m vs kemarin",
        "delta_positive": diff >= 0,
        "discussion_sessions": sessions_today,
        "day_number": ((today - enr.started_at.date()).days + 1) if enr else 1,
    }


def latest_insight(db: Session, user_id: int, curriculum_id: int) -> dict | None:
    row = db.execute(
        select(EvaluationAttempt, ReadingPoint.title)
        .join(ReadingPoint, EvaluationAttempt.reading_point_id == ReadingPoint.id)
        .join(Module, ReadingPoint.module_id == Module.id)
        .where(
            EvaluationAttempt.user_id == user_id,
            EvaluationAttempt.status == "graded",
            Module.curriculum_id == curriculum_id,
        )
        .order_by(EvaluationAttempt.graded_at.desc())
        .limit(1)
    ).first()
    if not row:
        return None
    att, title = row
    return {"reading_point_id": att.reading_point_id, "title": title, "score": att.score, "feedback": att.feedback, "passed": att.passed}


def recommend(current: dict | None, insight: dict | None, summary: dict) -> str:
    """FR-33: rekomendasi langkah berikutnya berdasarkan status & skor."""
    if current is None:
        if summary["points_total"] and summary["points_passed"] == summary["points_total"]:
            return "Selamat! Semua poin bacaan pada kurikulum ini sudah lulus. Pilih kurikulum lain untuk melanjutkan."
        return "Belum ada poin yang terbuka. Hubungi admin kurikulum."
    t, st = current["title"], current["status"]
    if st == "AVAILABLE":
        return f"Mulai membaca “{t}”. Bacaan wajib harus selesai sebelum sesi mentoring."
    if st == "READING":
        return f"Selesaikan bacaan “{t}”, lalu tandai selesai untuk membuka sesi mentoring."
    if st == "DISCUSSING":
        return f"Diskusikan “{t}” dengan mentor AI (minimal 1 pertanyaan), lalu minta evaluasi."
    if st == "ASSESSMENT":
        return f"Jawab pertanyaan evaluasi “{t}” untuk membuka poin berikutnya."
    score = f" (skor terakhir {current['score']:.0f})" if current.get("score") is not None else ""
    return f"Tinjau ulang “{t}”{score}, fokus pada catatan mentor, lalu ulangi evaluasi."
