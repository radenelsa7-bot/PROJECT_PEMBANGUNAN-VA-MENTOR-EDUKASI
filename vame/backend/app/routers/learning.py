"""Learning path & state machine (FR-10..FR-15)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..core import learning as L
from ..core.state_machine import InvalidTransition, Status, Trigger
from ..database import get_db
from ..deps import require_learner
from ..models import Curriculum, Enrollment, LearningProgress, Module, ReadingPoint, User
from ..schemas import EnrollmentIn

router = APIRouter(tags=["3. Learning Path"])


def _enrolled_curriculum(db: Session, user: User, cid: int) -> Curriculum:
    c = db.get(Curriculum, cid)
    if not c:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Kurikulum tidak ditemukan."})
    if not db.scalar(select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.curriculum_id == cid)):
        raise HTTPException(403, {"code": "NOT_ENROLLED", "message": "Kamu belum terdaftar pada kurikulum ini."})
    return c


@router.post("/enrollments", status_code=201, summary="Daftar kurikulum (FR-10)")
def enroll(body: EnrollmentIn, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    c = db.get(Curriculum, body.curriculum_id)
    if not c or not c.is_active:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Kurikulum tidak ditemukan atau nonaktif."})
    if not db.scalar(select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.curriculum_id == c.id)):
        db.add(Enrollment(user_id=user.id, curriculum_id=c.id))
        db.flush()
    L.ensure_progress(db, user.id, c.id)
    db.commit()
    from ..services.analytics import record_event
    record_event(db, event_type="enroll", user_id=user.id, meta={"curriculum_id": c.id, "curriculum_code": c.code})
    return {"enrolled": True, "curriculum_id": c.id}


@router.get("/enrollments", summary="Kurikulum yang saya ikuti")
def my_enrollments(db: Session = Depends(get_db), user: User = Depends(require_learner)):
    out = []
    for e in db.scalars(select(Enrollment).where(Enrollment.user_id == user.id).order_by(Enrollment.started_at)):
        c = db.get(Curriculum, e.curriculum_id)
        if not c or not c.is_active:
            continue
        path = L.build_learning_path(db, user.id, user.name, c)
        out.append({"curriculum_id": c.id, "code": c.code, "title": c.title, "short_name": c.short_name or c.title,
                    "percent": path["summary"]["percent"], "started_at": e.started_at})
    return out


@router.get("/learning-path/{curriculum_id}", summary="Peta learning path (FR-11)")
def learning_path(curriculum_id: int, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    c = _enrolled_curriculum(db, user, curriculum_id)
    return L.build_learning_path(db, user.id, user.name, c)


@router.get("/reading-points/{rid}", summary="Baca poin wajib (FR-12)")
def read_point(rid: int, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    ctx = L.get_point_ctx(db, user.id, rid)
    lp = ctx.lp
    if lp.status == Status.LOCKED.value:
        try:
            L.apply_transition(db, lp, Trigger.OPEN_READING)  # ditolak & dicatat (FR-15)
        except InvalidTransition as e:
            raise L.invalid_transition_http(e) from None
    elif lp.status == Status.AVAILABLE.value:
        L.apply_transition(db, lp, Trigger.OPEN_READING)
    elif lp.status == Status.NEEDS_REVIEW.value:
        L.apply_transition(db, lp, Trigger.REVIEW, "learner meninjau ulang materi")
    db.commit()
    rp = ctx.rp
    pts = L.ordered_points(db, ctx.curriculum.id)
    idx = next(i for i, p in enumerate(pts) if p.id == rp.id)
    return {
        "id": rp.id, "title": rp.title, "content": rp.content, "objective": rp.objective, "keywords": rp.keywords,
        "references": rp.references, "order": rp.order, "status": lp.status, "score": lp.best_score,
        "module": {"id": ctx.module.id, "title": ctx.module.title, "order": ctx.module.order},
        "curriculum": {"id": ctx.curriculum.id, "title": ctx.curriculum.title, "short_name": ctx.curriculum.short_name or ctx.curriculum.title},
        "position": {"index": idx + 1, "total": len(pts)},
    }


@router.post("/reading-points/{rid}/complete-reading", summary="Tandai selesai membaca (B.1)")
def complete_reading(rid: int, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    ctx = L.get_point_ctx(db, user.id, rid)
    try:
        L.apply_transition(db, ctx.lp, Trigger.COMPLETE_READING)
    except InvalidTransition as e:
        raise L.invalid_transition_http(e) from None
    db.commit()
    return {"status": ctx.lp.status}


@router.get("/search", summary="Cari topik pada kurikulum yang diikuti")
def search(q: str = Query(min_length=2, max_length=60), db: Session = Depends(get_db), user: User = Depends(require_learner)):
    like = f"%{q.lower()}%"
    rows = db.execute(
        select(ReadingPoint, Module, LearningProgress)
        .join(Module, ReadingPoint.module_id == Module.id)
        .join(Enrollment, (Enrollment.curriculum_id == Module.curriculum_id) & (Enrollment.user_id == user.id))
        .join(LearningProgress, (LearningProgress.reading_point_id == ReadingPoint.id) & (LearningProgress.user_id == user.id), isouter=True)
        .where(or_(ReadingPoint.title.ilike(like), ReadingPoint.keywords_json.ilike(like), Module.title.ilike(like)))
        .limit(8)
    ).all()
    # Isi materi tidak dibocorkan; hanya judul + status
    return [
        {"id": rp.id, "title": rp.title, "module": m.title, "status": lp.status if lp else "LOCKED"} for rp, m, lp in rows
    ]
