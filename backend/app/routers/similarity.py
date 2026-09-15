from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.auth.dependencies import get_current_token_payload, TokenPayload, RequireRole
from app.services.similarity_service import SimilarityService
from app.models.work import Work

router = APIRouter(tags=["Candidate Duplicate Engine"])

@router.get("/works/{work_id}/similar")
def get_similar_works(
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
                    "message": "User not authorized for requested work jurisdiction scope.",
                    "details": []
                }
            }
        )

    similar_items = SimilarityService.get_similar_works(db, work_id)
    return {
        "workId": work_id,
        "totalCandidates": len(similar_items),
        "candidates": similar_items
    }

@router.post("/works/{work_id}/similarity/recompute", dependencies=[Depends(RequireRole(["ADMIN", "AUDITOR"]))])
def recompute_similarities(work_id: str, db: Session = Depends(get_db)):
    w = db.query(Work).filter(Work.id == work_id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work not found")

    SimilarityService.recompute_all_similarities(db)
    similar_items = SimilarityService.get_similar_works(db, work_id)
    return {
        "message": "Successfully recomputed candidate duplicate matches.",
        "workId": work_id,
        "totalCandidates": len(similar_items),
        "candidates": similar_items
    }
