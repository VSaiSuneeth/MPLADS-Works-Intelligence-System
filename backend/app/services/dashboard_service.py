from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from sqlalchemy import desc, func

from app.models.work import Work
from app.models.risk import RiskScore
from app.models.case import Case
from app.models.ingestion import IngestionRun
from app.models.jurisdiction import Jurisdiction
from app.config import settings
from app.services.risk_service import RiskService

class DashboardService:
    @staticmethod
    def get_summary(
        db: Session,
        authorized_jurisdiction_ids: List[str],
        jurisdiction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        
        # Ensure risk scores exist
        if db.query(RiskScore).count() == 0:
            RiskService.calculate_and_save_all_risks(db)

        # Base Works Query
        work_query = db.query(Work)
        if jurisdiction_id:
            if jurisdiction_id not in authorized_jurisdiction_ids and "ALL" not in authorized_jurisdiction_ids:
                work_query = work_query.filter(Work.id == "none")
            else:
                work_query = work_query.filter(Work.jurisdiction_id == jurisdiction_id)
        elif "ALL" not in authorized_jurisdiction_ids:
            work_query = work_query.filter(Work.jurisdiction_id.in_(authorized_jurisdiction_ids))

        total_works = work_query.count()
        completed_works = work_query.filter(Work.current_status == "COMPLETED").count()
        execution_works = work_query.filter(Work.current_status == "EXECUTION").count()

        # Open Cases Query
        case_query = db.query(Case).join(Work)
        if jurisdiction_id:
            if jurisdiction_id in authorized_jurisdiction_ids or "ALL" in authorized_jurisdiction_ids:
                case_query = case_query.filter(Work.jurisdiction_id == jurisdiction_id)
        elif "ALL" not in authorized_jurisdiction_ids:
            case_query = case_query.filter(Work.jurisdiction_id.in_(authorized_jurisdiction_ids))

        open_cases = case_query.filter(Case.status.in_(["DETECTED", "TRIAGED", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED"])).count()

        # Risk Distribution Query
        risk_query = db.query(RiskScore).join(Work)
        if jurisdiction_id:
            if jurisdiction_id in authorized_jurisdiction_ids or "ALL" in authorized_jurisdiction_ids:
                risk_query = risk_query.filter(Work.jurisdiction_id == jurisdiction_id)
        elif "ALL" not in authorized_jurisdiction_ids:
            risk_query = risk_query.filter(Work.jurisdiction_id.in_(authorized_jurisdiction_ids))

        risk_dist = {
            "critical": risk_query.filter(RiskScore.priority == "CRITICAL").count(),
            "high": risk_query.filter(RiskScore.priority == "HIGH").count(),
            "medium": risk_query.filter(RiskScore.priority == "MEDIUM").count(),
            "low": risk_query.filter(RiskScore.priority == "LOW").count(),
        }

        # Top 5 Critical Risk Works
        top_risks = risk_query.options(
            joinedload(RiskScore.work).joinedload(Work.jurisdiction),
            joinedload(RiskScore.signals)
        ).order_by(desc(RiskScore.score)).limit(5).all()

        top_risk_items = []
        for r in top_risks:
            w = r.work
            top_signal = sorted(r.signals, key=lambda s: s.contribution, reverse=True)[0] if r.signals else None
            signal_label = top_signal.explanation_json.get("whatHappened", top_signal.signal_code) if top_signal else "High Priority Anomaly"
            
            top_risk_items.append({
                "workId": w.id,
                "externalId": w.external_id,
                "title": w.title,
                "category": w.category,
                "stage": w.current_status,
                "sanctionAmount": float(w.sanction_amount) if w.sanction_amount else None,
                "score": float(r.score),
                "priority": r.priority,
                "confidence": float(r.confidence),
                "topSignalLabel": signal_label,
                "districtName": w.jurisdiction.district_name
            })

        # Data Freshness Metadata
        latest_run = db.query(IngestionRun).order_by(desc(IngestionRun.completed_at)).first()
        last_ingested_str = latest_run.completed_at.isoformat() if (latest_run and latest_run.completed_at) else datetime.now(timezone.utc).isoformat()

        # Target District Name if specified
        target_district_name = None
        if jurisdiction_id:
            jur = db.query(Jurisdiction).filter(Jurisdiction.id == jurisdiction_id).first()
            if jur:
                target_district_name = jur.district_name

        return {
            "jurisdictionId": jurisdiction_id,
            "districtName": target_district_name or "All Authorized Districts",
            "dataFreshness": {
                "last_ingestion_at": last_ingested_str,
                "source_label": "Controlled Prototype Seed Data",
                "dataset_label": settings.DATASET_LABEL,
                "is_official_data": settings.IS_OFFICIAL_DATA
            },
            "totals": {
                "totalWorks": total_works,
                "openCases": open_cases,
                "completedWorks": completed_works,
                "executionWorks": execution_works
            },
            "riskDistribution": risk_dist,
            "topRiskWorks": top_risk_items
        }
