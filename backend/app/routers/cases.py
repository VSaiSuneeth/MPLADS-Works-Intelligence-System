from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.auth.dependencies import get_current_token_payload, TokenPayload
from app.services.case_service import CaseService
from app.schemas.case import CaseCreate, CaseActionCreate, CaseOut, CaseListResponse

router = APIRouter(prefix="/cases", tags=["Case Review Workflow"])

@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    body: CaseCreate,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    try:
        case_data = CaseService.create_case(
            db=db,
            creator_id=payload.sub,
            work_id=body.workId,
            summary=body.summary,
            priority=body.priority,
            initial_notes=body.initialNotes
        )
        return CaseOut(**case_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=CaseListResponse)
def list_cases(
    status: Optional[str] = Query("ALL"),
    priority: Optional[str] = Query("ALL"),
    jurisdictionId: Optional[str] = Query(None),
    workId: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]
    result = CaseService.list_cases(
        db=db,
        authorized_jurisdiction_ids=authorized_jurisdictions,
        status_filter=status,
        priority_filter=priority,
        jurisdiction_id=jurisdictionId,
        work_id=workId,
        page=page,
        page_size=pageSize
    )
    return CaseListResponse(
        items=[CaseOut(**c) for c in result["items"]],
        page=result["page"],
        pageSize=result["pageSize"],
        total=result["total"]
    )

@router.get("/{id}", response_model=CaseOut)
def get_case_detail(
    id: str,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    try:
        case_data = CaseService.get_case_detail(db, id)
        return CaseOut(**case_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{id}/actions", response_model=CaseOut)
def add_case_action(
    id: str,
    body: CaseActionCreate,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    try:
        updated_case = CaseService.add_case_action(
            db=db,
            actor_id=payload.sub,
            case_id=id,
            action_type=body.actionType,
            notes=body.notes,
            new_status=body.newStatus,
            assigned_to_id=body.assignedToId
        )
        return CaseOut(**updated_case)
    except ValueError as e:
        err_str = str(e)
        if "Invalid state transition" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "INVALID_STATE_TRANSITION",
                        "message": err_str,
                        "details": []
                    }
                }
            )
        raise HTTPException(status_code=400, detail=str(e))

