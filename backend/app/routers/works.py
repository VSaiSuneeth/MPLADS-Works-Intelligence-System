import os
import mimetypes
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.auth.dependencies import get_current_token_payload, TokenPayload, RequireRole
from app.services.work_service import WorkService
from app.services.evidence_fraud_service import EvidenceFraudService
from app.services.audit_service import AuditService
from app.services.agency_concentration_service import AgencyConcentrationService
from app.core.storage import storage_backend
from app.schemas.work import PaginatedWorkResponse, WorkDetailOut, LifecycleEventOut, EvidenceOut, DataQualityFindingOut, FraudFlagOut
from app.models.work import Work, Evidence, EvidenceFraudFlag
from app.models.ingestion import DataQualityFinding

router = APIRouter(prefix="/works", tags=["Works Management"])

@router.get("/analytics/agencies")
def get_agency_concentration_analytics(
    jurisdictionId: Optional[str] = Query(None),
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    """Returns lightweight agency and contractor allocation concentration analysis."""
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]
    return AgencyConcentrationService.get_agency_concentration_analysis(
        db=db,
        authorized_jurisdiction_ids=authorized_jurisdictions,
        jurisdiction_id=jurisdictionId
    )

@router.get("", response_model=PaginatedWorkResponse)
def list_works(
    jurisdictionId: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    agencyId: Optional[str] = Query(None),
    minCost: Optional[float] = Query(None),
    maxCost: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    sortBy: str = Query("created_at"),
    sortDir: str = Query("desc"),
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]

    items, total = WorkService.get_works(
        db=db,
        authorized_jurisdiction_ids=authorized_jurisdictions,
        jurisdiction_id=jurisdictionId,
        search=search,
        stage=stage,
        category=category,
        agency_id=agencyId,
        min_cost=minCost,
        max_cost=maxCost,
        page=page,
        page_size=pageSize,
        sort_by=sortBy,
        sort_dir=sortDir
    )

    return PaginatedWorkResponse(
        items=items,
        page=page,
        pageSize=pageSize,
        total=total
    )

@router.get("/{work_id}", response_model=WorkDetailOut)
def get_work_detail(
    work_id: str,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]
    work_detail = WorkService.get_work_by_id(db, work_id, authorized_jurisdictions)

    if not work_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "WORK_NOT_FOUND",
                    "message": f"Work '{work_id}' not found or access denied for authorized jurisdiction scope.",
                    "details": []
                }
            }
        )

    return WorkDetailOut(**work_detail)

@router.get("/{work_id}/timeline", response_model=List[LifecycleEventOut])
def get_work_timeline(
    work_id: str,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]
    work_detail = WorkService.get_work_by_id(db, work_id, authorized_jurisdictions)

    if not work_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work not found")

    timeline = WorkService.get_work_timeline(db, work_id)
    return [LifecycleEventOut(**t) for t in timeline]

@router.get("/{work_id}/evidence", response_model=List[EvidenceOut])
def get_work_evidence(
    work_id: str,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]
    work_detail = WorkService.get_work_by_id(db, work_id, authorized_jurisdictions)

    if not work_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work not found")

    evidence_records = db.query(Evidence).filter(Evidence.work_id == work_id).all()
    results = []
    for e in evidence_records:
        item = EvidenceOut.model_validate(e)
        # Populate matched work title and external ID on nested flags
        populated_flags = []
        for f in e.fraud_flags:
            f_out = FraudFlagOut.model_validate(f)
            if f.matched_work_id:
                w = db.query(Work).filter(Work.id == f.matched_work_id).first()
                if w:
                    f_out.matchedWorkTitle = w.title
                    f_out.matchedWorkExternalId = w.external_id
            populated_flags.append(f_out)
        item.fraudFlags = populated_flags
        results.append(item)

    return results

@router.post("/{work_id}/evidence", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def upload_work_evidence(
    work_id: str,
    file: UploadFile = File(...),
    evidenceType: str = Query("PHOTO_INSPECTION"),
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    """Uploads evidence artifact file for a work, extracts EXIF/pHash, and triggers real-time cross-work fraud check."""
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Work '{work_id}' not found.")

    if "ADMIN" not in payload.roles and work.jurisdiction_id not in payload.jurisdictions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized jurisdiction scope for this work.")

    # Save file using storage_backend
    subfolder = "evidence"
    rel_path = storage_backend.save_file(file.file, file.filename, subfolder=subfolder)
    full_path = storage_backend.get_full_path(rel_path)

    # Create Evidence model instance
    evidence = Evidence(
        work_id=work.id,
        evidence_type=evidenceType,
        file_name=file.filename,
        storage_key=rel_path,
        source_url=f"/api/v1/works/{work.id}/evidence/pending/file",
        captured_at=datetime.now(timezone.utc),
        metadata_json={"originalFilename": file.filename, "contentType": file.content_type},
        availability_status="AVAILABLE",
        uploaded_by_user_id=payload.sub
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    # Update source_url with actual evidence ID
    evidence.source_url = f"/api/v1/works/{work.id}/evidence/{evidence.id}/file"
    db.commit()

    # Process uploaded file (SHA-256, pHash, EXIF)
    EvidenceFraudService.process_uploaded_evidence(evidence, full_path, db)

    # Run real-time cross-work fraud check
    fraud_flags = EvidenceFraudService.run_fraud_check(evidence, db)

    # Audit log entry
    AuditService.log_action(
        db=db,
        action="EVIDENCE_UPLOADED",
        entity_type="Evidence",
        user_id=payload.sub,
        entity_id=evidence.id,
        details_json={
            "workId": work.id,
            "fileName": file.filename,
            "fileHash": evidence.file_hash,
            "phash": evidence.phash,
            "fraudFlagsCount": len(fraud_flags),
            "flagTypes": [f.flag_type for f in fraud_flags]
        }
    )

    db.refresh(evidence)
    res_out = EvidenceOut.model_validate(evidence)

    # Populate matched work title and external ID on nested flags
    populated_flags = []
    for f in evidence.fraud_flags:
        f_out = FraudFlagOut.model_validate(f)
        if f.matched_work_id:
            w = db.query(Work).filter(Work.id == f.matched_work_id).first()
            if w:
                f_out.matchedWorkTitle = w.title
                f_out.matchedWorkExternalId = w.external_id
        populated_flags.append(f_out)
    res_out.fraudFlags = populated_flags

    return res_out

@router.get("/{work_id}/evidence/{evidence_id}/file")
def get_evidence_file(
    work_id: str,
    evidence_id: str,
    db: Session = Depends(get_db)
):
    """Serves the raw evidence file bytes (with guessed content type) for UI image preview and lightbox."""
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id, Evidence.work_id == work_id).first()
    if not evidence or not evidence.storage_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence record not found.")

    full_path = storage_backend.get_full_path(evidence.storage_key)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found on disk.")

    media_type, _ = mimetypes.guess_type(full_path)
    return FileResponse(full_path, media_type=media_type or "application/octet-stream", filename=evidence.file_name)

@router.get("/{work_id}/data-quality", response_model=List[DataQualityFindingOut])
def get_work_data_quality(
    work_id: str,
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    authorized_jurisdictions = payload.jurisdictions if "ADMIN" not in payload.roles else ["ALL"]
    work_detail = WorkService.get_work_by_id(db, work_id, authorized_jurisdictions)

    if not work_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work not found")

    dq_findings = db.query(DataQualityFinding).filter(DataQualityFinding.work_id == work_id).all()
    return [DataQualityFindingOut.model_validate(dq) for dq in dq_findings]
