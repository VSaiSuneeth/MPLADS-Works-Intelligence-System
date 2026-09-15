from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.auth.dependencies import get_current_token_payload, TokenPayload
from app.models.work import EvidenceFraudFlag, Work, Evidence
from app.schemas.work import FraudFlagOut

router = APIRouter(prefix="/evidence", tags=["Evidence Fraud Detection"])

@router.get("/fraud-flags", response_model=List[FraudFlagOut])
def list_system_fraud_flags(
    severity: Optional[str] = Query(None),
    flagType: Optional[str] = Query(None),
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    """Returns evidence fraud flags filtered by authorized user jurisdiction for auditor compliance review."""
    query = db.query(EvidenceFraudFlag)
    if "ADMIN" not in payload.roles:
        query = query.join(Evidence, EvidenceFraudFlag.evidence_id == Evidence.id).join(Work, Evidence.work_id == Work.id).filter(Work.jurisdiction_id.in_(payload.jurisdictions))
    if severity:
        query = query.filter(EvidenceFraudFlag.severity == severity)
    if flagType:
        query = query.filter(EvidenceFraudFlag.flag_type == flagType)


    flags = query.order_by(EvidenceFraudFlag.created_at.desc()).all()

    result = []
    for f in flags:
        item = FraudFlagOut.model_validate(f)
        if f.matched_work_id:
            w = db.query(Work).filter(Work.id == f.matched_work_id).first()
            if w:
                item.matchedWorkTitle = w.title
                item.matchedWorkExternalId = w.external_id
        result.append(item)

    return result
