from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.session import get_db
from app.auth.dependencies import get_current_token_payload, TokenPayload
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard Summary"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    jurisdictionId: Optional[str] = Query(None),
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]
    summary = DashboardService.get_summary(db, authorized_jurisdictions, jurisdictionId)
    return DashboardSummaryResponse(**summary)
