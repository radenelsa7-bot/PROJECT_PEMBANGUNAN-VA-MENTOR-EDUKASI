"""Pelacakan progres (FR-31..FR-33)."""
import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core import learning as L
from ..database import get_db
from ..deps import require_learner
from ..models import Curriculum, Enrollment, EvaluationAttempt, Module, ReadingPoint, StudyActivity, User
from ..schemas import HeartbeatIn

router = APIRouter(tags=["6. Progres"])


def _history(db: Session, user_id: int, limit: int = 50) -> list[dict]:
    rows = db.execute(
        select(EvaluationAttempt, ReadingPoint.title, Module.title, Curriculum.short_name)
        .join(ReadingPoint, EvaluationAttempt.reading_point_id == ReadingPoint.id)
        .join(Module, ReadingPoint.module_id == Module.id)
        .join(Curriculum, Module.curriculum_id == Curriculum.id)
        .where(EvaluationAttempt.user_id == user_id, EvaluationAttempt.status == "graded")
        .order_by(EvaluationAttempt.graded_at.desc())
        .limit(limit)
    ).all()
    return [
        {"id": a.id, "reading_point_id": a.reading_point_id, "point": pt, "module": mt, "curriculum": cn,
         "question": a.question, "score": a.score, "passed": a.passed, "feedback": a.feedback, "graded_at": a.graded_at}
        for a, pt, mt, cn in rows
    ]


@router.get("/progress", summary="Ringkasan progres belajar (FR-31, FR-33)")
def progress(db: Session = Depends(get_db), user: User = Depends(require_learner)):
    curricula = []
    for e in db.scalars(select(Enrollment).where(Enrollment.user_id == user.id).order_by(Enrollment.started_at)):
        c = db.get(Curriculum, e.curriculum_id)
        if not c or not c.is_active:
            continue
        p = L.build_learning_path(db, user.id, user.name, c)
        curricula.append(
            {
                "curriculum_id": c.id, "title": c.title, "short_name": c.short_name or c.title,
                "summary": p["summary"], "current": p["current"], "recommendation": p["recommendation"],
                "modules": [{k: m[k] for k in ("id", "title", "status", "passed", "total", "percent", "final_score")} for m in p["modules"]],
            }
        )
    hist = _history(db, user.id)
    scores = [h["score"] for h in hist if h["score"] is not None]
    return {
        "overall": {
            "avg_score": round(sum(scores) / len(scores), 1) if scores else None,
            "attempts": len(hist),
            "passed_attempts": sum(1 for h in hist if h["passed"]),
        },
        "curricula": curricula,
        "history": hist,
    }


@router.post("/progress/heartbeat", summary="Catat durasi belajar harian")
def heartbeat(body: HeartbeatIn, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    today = date.today()
    row = db.scalar(select(StudyActivity).where(StudyActivity.user_id == user.id, StudyActivity.day == today))
    if row:
        row.seconds += body.seconds
    else:
        db.add(StudyActivity(user_id=user.id, day=today, seconds=body.seconds))
    db.commit()
    return {"ok": True}


@router.get("/progress/export", summary="Ekspor laporan progres CSV (opsional)")
def export_csv(db: Session = Depends(get_db), user: User = Depends(require_learner)):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["tanggal", "kurikulum", "modul", "poin_bacaan", "skor", "lulus", "umpan_balik"])
    for h in _history(db, user.id, limit=1000):
        w.writerow([h["graded_at"], h["curriculum"], h["module"], h["point"], h["score"], "ya" if h["passed"] else "tidak", h["feedback"]])
    return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=laporan-progres.csv"})
