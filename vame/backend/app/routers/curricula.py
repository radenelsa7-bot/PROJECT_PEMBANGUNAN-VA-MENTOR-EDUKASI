"""Manajemen kurikulum (FR-05..FR-09). Poin bacaan lengkap hanya terlihat oleh admin."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import Curriculum, Enrollment, Module, ReadingPoint, User
from ..schemas import (
    CurriculumImport,
    CurriculumIn,
    CurriculumUpdate,
    ModuleIn,
    ModuleUpdate,
    ReadingPointIn,
    ReadingPointUpdate,
)

router = APIRouter(tags=["2. Kurikulum"])


def _conflict(msg: str) -> HTTPException:
    return HTTPException(409, {"code": "CONFLICT", "message": msg})


def _not_found(what: str) -> HTTPException:
    return HTTPException(404, {"code": "NOT_FOUND", "message": f"{what} tidak ditemukan."})


def rp_admin(rp: ReadingPoint) -> dict:
    return {
        "id": rp.id, "title": rp.title, "content": rp.content, "objective": rp.objective,
        "keywords": rp.keywords, "references": rp.references, "order": rp.order,
    }


def curriculum_dict(c: Curriculum, db: Session, detail: bool = False, admin: bool = False, user_id: int | None = None) -> dict:
    n_mod = len(c.modules)
    n_pts = sum(len(m.reading_points) for m in c.modules)
    out = {
        "id": c.id, "code": c.code, "title": c.title, "short_name": c.short_name or c.title, "description": c.description,
        "level": c.level, "topic_label": c.topic_label, "est_hours": c.est_hours, "mentor_name": c.mentor_name,
        "is_active": c.is_active, "modules_count": n_mod, "points_count": n_pts,
    }
    if user_id is not None:
        out["enrolled"] = bool(
            db.scalar(select(func.count(Enrollment.id)).where(Enrollment.user_id == user_id, Enrollment.curriculum_id == c.id))
        )
    if detail:
        out["modules"] = [
            {
                "id": m.id, "title": m.title, "label": m.label, "order": m.order,
                "reading_points": [
                    rp_admin(rp) if admin else {"id": rp.id, "title": rp.title, "order": rp.order} for rp in m.reading_points
                ],
            }
            for m in c.modules
        ]
    return out


# -------------------- kurikulum --------------------
@router.get("/curricula", summary="Daftar kurikulum")
def list_curricula(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(Curriculum).order_by(Curriculum.id)
    if user.role != "admin":
        q = q.where(Curriculum.is_active.is_(True))
    return [curriculum_dict(c, db, user_id=user.id if user.role == "learner" else None) for c in db.scalars(q)]


@router.get("/curricula/{cid}", summary="Detail kurikulum")
def get_curriculum(cid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.get(Curriculum, cid)
    if not c or (not c.is_active and user.role != "admin"):
        raise _not_found("Kurikulum")
    return curriculum_dict(c, db, detail=True, admin=user.role == "admin")


@router.post("/curricula", status_code=201, summary="Buat kurikulum (FR-05)")
def create_curriculum(body: CurriculumIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.scalar(select(Curriculum).where(Curriculum.code == body.code)):
        raise _conflict("Kode kurikulum sudah dipakai.")
    c = Curriculum(**body.model_dump())
    db.add(c)
    db.commit()
    return curriculum_dict(c, db, detail=True, admin=True)


@router.put("/curricula/{cid}", summary="Ubah / nonaktifkan kurikulum (FR-05)")
def update_curriculum(cid: int, body: CurriculumUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    c = db.get(Curriculum, cid)
    if not c:
        raise _not_found("Kurikulum")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    return curriculum_dict(c, db, detail=True, admin=True)


# -------------------- modul --------------------
@router.post("/curricula/{cid}/modules", status_code=201, summary="Tambah modul (FR-06)")
def add_module(cid: int, body: ModuleIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if not db.get(Curriculum, cid):
        raise _not_found("Kurikulum")
    if db.scalar(select(Module).where(Module.curriculum_id == cid, Module.order == body.order)):
        raise _conflict(f"Urutan modul {body.order} sudah dipakai.")  # FR-08
    m = Module(curriculum_id=cid, **body.model_dump())
    db.add(m)
    db.commit()
    return {"id": m.id, "title": m.title, "label": m.label, "order": m.order}


@router.put("/modules/{mid}", summary="Ubah modul / urutan (FR-06)")
def update_module(mid: int, body: ModuleUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    m = db.get(Module, mid)
    if not m:
        raise _not_found("Modul")
    data = body.model_dump(exclude_unset=True)
    if "order" in data and data["order"] != m.order:
        if db.scalar(select(Module).where(Module.curriculum_id == m.curriculum_id, Module.order == data["order"])):
            raise _conflict(f"Urutan modul {data['order']} sudah dipakai.")
    for k, v in data.items():
        setattr(m, k, v)
    db.commit()
    return {"id": m.id, "title": m.title, "label": m.label, "order": m.order}


# -------------------- poin bacaan --------------------
@router.post("/modules/{mid}/reading-points", status_code=201, summary="Tambah poin bacaan wajib (FR-07)")
def add_reading_point(mid: int, body: ReadingPointIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if not db.get(Module, mid):
        raise _not_found("Modul")
    if db.scalar(select(ReadingPoint).where(ReadingPoint.module_id == mid, ReadingPoint.order == body.order)):
        raise _conflict(f"Urutan poin bacaan {body.order} sudah dipakai pada modul ini.")
    data = body.model_dump()
    rp = ReadingPoint(module_id=mid, **{k: v for k, v in data.items() if k != "keywords"})
    rp.keywords = data["keywords"]
    db.add(rp)
    db.commit()
    return rp_admin(rp)


@router.put("/reading-points/{rid}", summary="Ubah poin bacaan (FR-07)")
def update_reading_point(rid: int, body: ReadingPointUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rp = db.get(ReadingPoint, rid)
    if not rp:
        raise _not_found("Poin bacaan")
    data = body.model_dump(exclude_unset=True)
    if "order" in data and data["order"] != rp.order:
        if db.scalar(select(ReadingPoint).where(ReadingPoint.module_id == rp.module_id, ReadingPoint.order == data["order"])):
            raise _conflict(f"Urutan poin bacaan {data['order']} sudah dipakai.")
    if "keywords" in data and data["keywords"] is not None:
        rp.keywords = [k.strip() for k in data.pop("keywords") if k.strip()]
    for k, v in data.items():
        if v is not None:
            setattr(rp, k, v)
    db.commit()
    return rp_admin(rp)


# -------------------- impor --------------------
def import_curriculum(db: Session, body: CurriculumImport) -> Curriculum:
    """Impor kurikulum JSON lengkap (FR-09). Validasi unik urutan sebelum disimpan (FR-08)."""
    if db.scalar(select(Curriculum).where(Curriculum.code == body.code)):
        raise _conflict(f"Kode kurikulum {body.code} sudah ada.")
    orders = [m.order for m in body.modules]
    if len(set(orders)) != len(orders):
        raise HTTPException(422, {"code": "VALIDATION", "message": "Urutan modul harus unik."})
    c = Curriculum(**body.model_dump(exclude={"modules"}))
    for m in body.modules:
        pts_orders = [p.order for p in m.reading_points]
        if len(set(pts_orders)) != len(pts_orders):
            raise HTTPException(422, {"code": "VALIDATION", "message": f"Urutan poin bacaan pada modul '{m.title}' harus unik."})
        mod = Module(title=m.title, label=m.label, order=m.order)
        for p in m.reading_points:
            rp = ReadingPoint(title=p.title, content=p.content, objective=p.objective, references=p.references, order=p.order)
            rp.keywords = p.keywords
            mod.reading_points.append(rp)
        c.modules.append(mod)
    db.add(c)
    db.commit()
    return c


@router.post("/curricula/import", status_code=201, summary="Impor kurikulum dari JSON (FR-09)")
def import_json(body: CurriculumImport, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return curriculum_dict(import_curriculum(db, body), db, detail=True, admin=True)
