from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.search_service import search_memories

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    type_filter: Optional[str] = None
    tag_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 30

@router.post("/")
def search(
    req: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Multi-modal natural language search across photos, notes, and voice recordings.
    """
    dt_from = None
    dt_to = None
    if req.date_from:
        try:
            dt_from = datetime.fromisoformat(req.date_from.replace("Z", "+00:00"))
        except Exception:
            pass
    if req.date_to:
        try:
            dt_to = datetime.fromisoformat(req.date_to.replace("Z", "+00:00"))
        except Exception:
            pass

    results = search_memories(
        query=req.query,
        db=db,
        type_filter=req.type_filter,
        tag_filter=req.tag_filter,
        date_from=dt_from,
        date_to=dt_to,
        limit=req.limit
    )

    return {
        "query": req.query,
        "count": len(results),
        "results": results
    }
