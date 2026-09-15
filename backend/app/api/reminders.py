from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_, or_

from app.core.database import get_db
from app.models.memory import Memory
from app.models.event import Event

router = APIRouter()

@router.get("/flashbacks")
def get_flashbacks(db: Session = Depends(get_db)):
    """
    Resurfacing endpoint for Phase 6:
    - 'On This Day' memories from previous years
    - 'Important' pinned memories
    - Featured past events
    """
    now = datetime.utcnow()
    current_month = now.month
    current_day = now.day
    current_year = now.year

    # 1. On This Day memories (past years)
    on_this_day_exact = db.query(Memory).filter(
        extract('month', Memory.captured_at) == current_month,
        extract('day', Memory.captured_at) == current_day,
        extract('year', Memory.captured_at) < current_year
    ).all()

    # If no exact match today, broaden to current week in past years
    on_this_day_results = on_this_day_exact
    if not on_this_day_results:
        # Check window +/- 3 days
        window_memories = db.query(Memory).filter(
            extract('month', Memory.captured_at) == current_month,
            extract('day', Memory.captured_at).between(max(1, current_day - 3), min(28, current_day + 3)),
            extract('year', Memory.captured_at) < current_year
        ).limit(10).all()
        on_this_day_results = window_memories

    # 2. Important memories (starred by user)
    important_memories = db.query(Memory).filter(Memory.is_important == True).order_by(Memory.captured_at.desc()).limit(15).all()

    # 3. Featured events
    featured_events = db.query(Event).order_by(Event.start_date.desc()).limit(5).all()

    return {
        "today": now.strftime("%B %d, %Y"),
        "on_this_day": [
            {
                "years_ago": current_year - (m.captured_at.year if m.captured_at else current_year),
                "memory": m.to_dict()
            }
            for m in on_this_day_results
        ],
        "important_memories": [m.to_dict() for m in important_memories],
        "featured_events": [ev.to_dict(include_memories=True) for ev in featured_events]
    }
