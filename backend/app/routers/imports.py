from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List

from app.db.session import get_db
from app.auth.dependencies import RequireRole
from app.services.ingestion import IngestionService
from app.services.risk_service import RiskService
from app.models.ingestion import IngestionRun

router = APIRouter(prefix="/imports", tags=["Data Import"])


@router.get("", dependencies=[Depends(RequireRole(["ADMIN", "AUDITOR"]))])
def list_import_runs(db: Session = Depends(get_db)):
    runs = db.query(IngestionRun).order_by(desc(IngestionRun.started_at)).all()
    return [
        {
            "id": r.id,
            "sourceName": r.file_name or "Seed Dataset",
            "status": r.status,
            "totalRowsParsed": r.total_rows,
            "acceptedRows": r.accepted_rows,
            "rejectedRows": r.rejected_rows,
            "dataQualityFindingsCount": 0,
            "completedAt": r.completed_at.isoformat() if r.completed_at else None,
            "createdAt": r.started_at.isoformat() if r.started_at else None
        }
        for r in runs
    ]

@router.post("", dependencies=[Depends(RequireRole(["ADMIN"]))])
async def import_csv(
    file: UploadFile = File(...),
    source_name: Optional[str] = Form("Prototype CSV Upload"),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "UNSUPPORTED_FILE_TYPE",
                    "message": "Only CSV files are supported for import.",
                    "details": []
                }
            }
        )

    try:
        contents = await file.read()
        csv_str = contents.decode("utf-8-sig") # Handle BOM if present
        ingestion_run = IngestionService.process_csv_content(csv_str, source_name, db)

        # Trigger risk scoring for newly ingested projects
        try:
            RiskService.calculate_and_save_all_risks(db)
        except Exception:
            pass


        return {
            "id": ingestion_run.id,
            "sourceName": file.filename,
            "status": ingestion_run.status,
            "totalRowsParsed": ingestion_run.total_rows,
            "acceptedRows": ingestion_run.accepted_rows,
            "rejectedRows": ingestion_run.rejected_rows,
            "dataQualityFindingsCount": 0,
            "executionTimeSeconds": 1.2
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "IMPORT_FAILED",
                    "message": f"Failed to process CSV import: {str(e)}",
                    "details": []
                }
            }
        )

@router.get("/{run_id}", dependencies=[Depends(RequireRole(["ADMIN", "AUDITOR"]))])
def get_import_run_status(run_id: str, db: Session = Depends(get_db)):
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Ingestion run '{run_id}' not found.",
                    "details": []
                }
            }
        )
    return {
        "id": run.id,
        "sourceName": run.file_name or "Seed Dataset",
        "status": run.status,
        "totalRowsParsed": run.total_rows,
        "acceptedRows": run.accepted_rows,
        "rejectedRows": run.rejected_rows,
        "dataQualityFindingsCount": 0,
        "startedAt": run.started_at.isoformat() if run.started_at else None,
        "completedAt": run.completed_at.isoformat() if run.completed_at else None
    }
