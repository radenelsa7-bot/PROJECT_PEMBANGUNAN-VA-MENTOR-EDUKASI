"""Pencatatan event alur inti untuk analytics (Issue #10)."""
import json

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import AnalyticsEvent


def record_event(
    db: Session,
    *,
    event_type: str,
    user_id: int | None = None,
    reading_point_id: int | None = None,
    session_id: int | None = None,
    meta: dict | None = None,
) -> None:
    """Catat event analytics dalam sesi terpisah agar tetap tersimpan walau transaksi utama dibatalkan."""
    try:
        with Session(bind=db.get_bind()) as s:
            s.add(
                AnalyticsEvent(
                    user_id=user_id,
                    event_type=event_type,
                    reading_point_id=reading_point_id,
                    session_id=session_id,
                    meta_json=json.dumps(meta or {}, ensure_ascii=False),
                )
            )
            s.commit()
    except Exception:  # analytics tidak boleh menggagalkan alur utama
        pass
