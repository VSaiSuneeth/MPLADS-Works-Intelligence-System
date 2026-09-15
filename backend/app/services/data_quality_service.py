from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.ingestion import DataQualityFinding
from app.models.work import Work

class DataQualityService:
    @staticmethod
    def get_findings_for_work(db: Session, work_id: str) -> List[Dict[str, Any]]:
        findings = db.query(DataQualityFinding).filter(DataQualityFinding.work_id == work_id).all()
        result = []
        for f in findings:
            result.append({
                "id": f.id,
                "fieldName": f.field_name,
                "findingType": f.finding_type,
                "severity": f.severity,
                "message": f.message,
                "evidenceJson": f.evidence_json or {}
            })
        return result

    @staticmethod
    def get_quality_summary(db: Session, jurisdiction_ids: List[str]) -> Dict[str, Any]:
        query = db.query(DataQualityFinding).join(Work)
        if "ALL" not in jurisdiction_ids:
            query = query.filter(Work.jurisdiction_id.in_(jurisdiction_ids))

        total_findings = query.count()
        critical_findings = query.filter(DataQualityFinding.severity == "HIGH").count()
        missing_metadata = query.filter(DataQualityFinding.finding_type == "MISSING_FIELD").count()
        chronology_errors = query.filter(DataQualityFinding.finding_type == "CHRONOLOGY_INVALID").count()

        return {
            "totalFindings": total_findings,
            "criticalFindings": critical_findings,
            "missingMetadataCount": missing_metadata,
            "chronologyErrorsCount": chronology_errors
        }
