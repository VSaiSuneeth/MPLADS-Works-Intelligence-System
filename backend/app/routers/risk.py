from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.auth.dependencies import get_current_token_payload, TokenPayload, RequireRole
from app.services.risk_service import RiskService
from app.models.work import Work
from app.models.risk import RiskScore

router = APIRouter(prefix="/risk", tags=["Risk Prioritization Engine"])

@router.get("/queue")
def get_risk_queue(
    jurisdictionId: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]

    # Ensure risk scores are calculated
    if db.query(RiskScore).count() == 0:
        RiskService.calculate_and_save_all_risks(db)

    items, total = RiskService.get_risk_queue(
        db=db,
        authorized_jurisdiction_ids=authorized_jurisdictions,
        jurisdiction_id=jurisdictionId,
        priority=priority,
        stage=stage,
        category=category,
        search=search,
        page=page,
        page_size=pageSize
    )

    return {
        "items": items,
        "page": page,
        "pageSize": pageSize,
        "total": total
    }

@router.get("/works/{work_id}")
def get_work_risk_detail(
    work_id: str,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    w = db.query(Work).filter(Work.id == work_id).first()
    if not w:
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

    # Check jurisdiction authorization
    if "ADMIN" not in payload.roles and w.jurisdiction_id not in payload.jurisdictions:
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

    risk_score = db.query(RiskScore).filter(RiskScore.work_id == work_id).first()
    if not risk_score:
        peer_stats = RiskService.calculate_peer_cost_anomalies(db)
        score, confidence, priority, signals = RiskService.compute_work_risk(w, db, peer_stats)
        return {
            "workId": w.id,
            "score": score,
            "priority": priority,
            "confidence": confidence,
            "riskVersion": "risk-v1.0",
            "calculatedAt": None,
            "signals": signals
        }

    signals = [s.explanation_json for s in risk_score.signals]
    return {
        "workId": w.id,
        "score": float(risk_score.score),
        "priority": risk_score.priority,
        "confidence": float(risk_score.confidence),
        "riskVersion": risk_score.risk_version,
        "calculatedAt": risk_score.calculated_at.isoformat(),
        "signals": signals
    }

@router.post("/recalculate", dependencies=[Depends(RequireRole(["ADMIN", "AUDITOR"]))])
def recalculate_risks(db: Session = Depends(get_db)):
    RiskService.calculate_and_save_all_risks(db)
    return {"message": "Successfully recalculated risk scores across all works."}
