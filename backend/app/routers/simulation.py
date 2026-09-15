from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.auth.dependencies import get_current_token_payload, TokenPayload
from app.models.work import Work
from app.services.simulation_service import SimulationService
from app.schemas.simulation import SimulationRequest, SimulationResponse

router = APIRouter(prefix="/simulation", tags=["What-If Impact Simulator"])

@router.post("/run", response_model=SimulationResponse)
def run_simulation(
    request: SimulationRequest,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    """Runs What-If Impact Simulation comparing current baseline vs simulated scenario parameters."""
    if request.work_id:
        work = db.query(Work).filter(Work.id == request.work_id).first()
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "WORK_NOT_FOUND",
                        "message": f"Work '{request.work_id}' not found.",
                        "details": []
                    }
                }
            )
        # Check jurisdiction scope
        if "ADMIN" not in payload.roles and work.jurisdiction_id not in payload.jurisdictions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "JURISDICTION_DENIED",
                        "message": "User not authorized for work jurisdiction.",
                        "details": []
                    }
                }
            )

    return SimulationService.simulate(db, request)

@router.get("/base-project/{work_id}")
def get_base_project_params(
    work_id: str,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    """Returns baseline project parameters for pre-filling the What-If simulation form."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "WORK_NOT_FOUND",
                    "message": f"Work '{work_id}' not found.",
                    "details": []
                }
            }
        )
    if "ADMIN" not in payload.roles and work.jurisdiction_id not in payload.jurisdictions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "JURISDICTION_DENIED",
                    "message": "User not authorized for work jurisdiction.",
                    "details": []
                }
            }
        )

    latest_prog = 0.0
    if work.progress_records:
        sorted_p = sorted(work.progress_records, key=lambda x: x.created_at, reverse=True)
        latest_prog = float(sorted_p[0].progress_percent)

    return {
        "workId": work.id,
        "externalId": work.external_id,
        "title": work.title,
        "category": work.category or "Water Supply & Sanitation",
        "projectCost": float(work.sanction_amount or 0.0),
        "expenditureAmount": float(work.expenditure_amount or 0.0),
        "completionPct": latest_prog,
        "sanctionDate": str(work.sanction_date) if work.sanction_date else None,
        "expectedCompletionDate": str(work.completion_date) if work.completion_date else None,
        "currentStatus": work.current_status
    }

@router.get("/projects")
def list_simulation_projects(
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    """Returns list of authorized works for dropdown selection in the What-If Simulator."""
    query = db.query(Work)
    if "ADMIN" not in payload.roles:
        query = query.filter(Work.jurisdiction_id.in_(payload.jurisdictions))

    works = query.order_by(Work.title).all()

    result = []
    for w in works:
        latest_prog = 0.0
        if w.progress_records:
            sorted_p = sorted(w.progress_records, key=lambda x: x.created_at, reverse=True)
            latest_prog = float(sorted_p[0].progress_percent)

        result.append({
            "workId": w.id,
            "externalId": w.external_id,
            "title": w.title,
            "category": w.category or "Water Supply & Sanitation",
            "projectCost": float(w.sanction_amount or 0.0),
            "expenditureAmount": float(w.expenditure_amount or 0.0),
            "completionPct": latest_prog,
            "sanctionDate": str(w.sanction_date) if w.sanction_date else None,
            "expectedCompletionDate": str(w.completion_date) if w.completion_date else None,
            "currentStatus": w.current_status
        })

    return {"items": result, "total": len(result)}
