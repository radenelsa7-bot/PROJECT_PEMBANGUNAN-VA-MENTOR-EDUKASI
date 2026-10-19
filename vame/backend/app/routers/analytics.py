"""Analytics admin (Issue #10): query event alur inti."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import AnalyticsEvent, User

router = APIRouter(tags=["7. Analytics"], dependencies=[Depends(require_admin)])


@router.get("/analytics/events", summary="Query analytics events (admin)")
def list_events(
    user_id: int | None = None,
    event_type: str | None = None,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
):
    q = select(AnalyticsEvent).order_by(AnalyticsEvent.created_at.desc())
    if user_id:
        q = q.where(AnalyticsEvent.user_id == user_id)
    if event_type:
        q = q.where(AnalyticsEvent.event_type == event_type)
    events = db.scalars(q.limit(limit)).all()
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "event_type": e.event_type,
            "reading_point_id": e.reading_point_id,
            "session_id": e.session_id,
            "meta": e.meta_json,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]
