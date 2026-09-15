from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.auth.dependencies import get_current_token_payload, TokenPayload
from app.services.audit_service import AuditService
from app.schemas.audit import AuditLogOut, AuditLogListResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Trail System"])

@router.get("", response_model=AuditLogListResponse)
def get_audit_logs(
    action: Optional[str] = Query(None),
    entityType: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    result = AuditService.get_logs(
        db=db,
        page=page,
        page_size=pageSize,
        action_filter=action,
        entity_type_filter=entityType
    )
    return AuditLogListResponse(
        items=[AuditLogOut(**l) for l in result["items"]],
        page=result["page"],
        pageSize=result["pageSize"],
        total=result["total"]
    )
