from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, asc

from app.models.work import Work, WorkLifecycleEvent, Payment, ProgressRecord, Evidence
from app.models.ingestion import DataQualityFinding
from app.models.jurisdiction import Jurisdiction
from app.models.agency import Agency
from app.schemas.work import WorkListItem, WorkDetailOut, PaginatedWorkResponse, AgencyOut, JurisdictionOut, DataQualityFindingOut, LifecycleEventOut, PaymentOut, EvidenceOut

class WorkService:
    @staticmethod
    def get_works(
        db: Session,
        authorized_jurisdiction_ids: List[str],
        jurisdiction_id: Optional[str] = None,
        search: Optional[str] = None,
        stage: Optional[str] = None,
        category: Optional[str] = None,
        agency_id: Optional[str] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        page: int = 1,
        page_size: int = 25,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        
        query = db.query(Work).options(
            joinedload(Work.jurisdiction),
            joinedload(Work.agency),
            joinedload(Work.progress_records)
        )

        # Apply Jurisdiction boundary restrictions
        if jurisdiction_id:
            if jurisdiction_id not in authorized_jurisdiction_ids and "ALL" not in authorized_jurisdiction_ids:
                return [], 0
            query = query.filter(Work.jurisdiction_id == jurisdiction_id)
        elif "ALL" not in authorized_jurisdiction_ids:
            query = query.filter(Work.jurisdiction_id.in_(authorized_jurisdiction_ids))

        # Apply Search filter
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Work.title.ilike(term),
                    Work.external_id.ilike(term),
                    Work.location_text.ilike(term)
                )
            )

        # Apply Category, Stage, Agency, Cost filters
        if stage and stage.strip():
            query = query.filter(Work.current_status == stage.strip())
        if category and category.strip():
            query = query.filter(Work.category == category.strip())
        if agency_id and agency_id.strip():
            query = query.filter(Work.agency_id == agency_id.strip())
        if min_cost is not None:
            query = query.filter(Work.sanction_amount >= min_cost)
        if max_cost is not None:
            query = query.filter(Work.sanction_amount <= max_cost)

        total_count = query.count()

        # Apply Sorting
        sort_col = getattr(Work, sort_by, Work.created_at)
        if sort_dir.lower() == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        # Apply Pagination
        offset = (page - 1) * page_size
        works = query.offset(offset).limit(page_size).all()

        items = []
        for w in works:
            latest_prog = None
            if w.progress_records:
                sorted_progs = sorted(w.progress_records, key=lambda x: x.created_at, reverse=True)
                latest_prog = float(sorted_progs[0].progress_percent)

            dq_count = db.query(DataQualityFinding).filter(DataQualityFinding.work_id == w.id).count()

            items.append({
                "id": w.id,
                "externalId": w.external_id,
                "title": w.title,
                "category": w.category,
                "locationText": w.location_text,
                "stage": w.current_status,
                "sanctionAmount": float(w.sanction_amount) if w.sanction_amount else None,
                "expenditureAmount": float(w.expenditure_amount) if w.expenditure_amount else None,
                "latestProgressPercent": latest_prog,
                "recommendationDate": w.recommendation_date,
                "sanctionDate": w.sanction_date,
                "completionDate": w.completion_date,
                "agency": AgencyOut.model_validate(w.agency) if w.agency else None,
                "jurisdiction": JurisdictionOut.model_validate(w.jurisdiction),
                "dataQualityFlagsCount": dq_count
            })

        return items, total_count

    @staticmethod
    def get_work_by_id(db: Session, work_id: str, authorized_jurisdiction_ids: List[str]) -> Optional[Dict[str, Any]]:
        w = db.query(Work).options(
            joinedload(Work.jurisdiction),
            joinedload(Work.agency),
            joinedload(Work.progress_records),
            joinedload(Work.payments),
            joinedload(Work.evidence)
        ).filter(Work.id == work_id).first()

        if not w:
            return None

        if "ALL" not in authorized_jurisdiction_ids and w.jurisdiction_id not in authorized_jurisdiction_ids:
            return None

        latest_prog = None
        if w.progress_records:
            sorted_progs = sorted(w.progress_records, key=lambda x: x.created_at, reverse=True)
            latest_prog = float(sorted_progs[0].progress_percent)

        payments_total = sum(float(p.amount) for p in w.payments) if w.payments else 0.0

        dq_findings = db.query(DataQualityFinding).filter(DataQualityFinding.work_id == w.id).all()
        dq_out = [DataQualityFindingOut.model_validate(dq) for dq in dq_findings]

        return {
            "id": w.id,
            "externalId": w.external_id,
            "title": w.title,
            "description": w.description,
            "category": w.category,
            "locationText": w.location_text,
            "latitude": float(w.latitude) if w.latitude else None,
            "longitude": float(w.longitude) if w.longitude else None,
            "estimatedCost": float(w.estimated_cost) if w.estimated_cost else None,
            "sanctionAmount": float(w.sanction_amount) if w.sanction_amount else None,
            "expenditureAmount": float(w.expenditure_amount) if w.expenditure_amount else None,
            "stage": w.current_status,
            "recommendationDate": w.recommendation_date,
            "sanctionDate": w.sanction_date,
            "completionDate": w.completion_date,
            "sourceRecordHash": getattr(w, 'source_record_hash', None),
            "agency": AgencyOut.model_validate(w.agency) if w.agency else None,
            "jurisdiction": JurisdictionOut.model_validate(w.jurisdiction),
            "latestProgressPercent": latest_prog,
            "paymentsTotal": payments_total,
            "evidenceCount": len(w.evidence),
            "dataQualityFindings": dq_out
        }

    @staticmethod
    def get_work_timeline(db: Session, work_id: str) -> List[Dict[str, Any]]:
        w = db.query(Work).options(
            joinedload(Work.progress_records),
            joinedload(Work.payments),
            joinedload(Work.evidence)
        ).filter(Work.id == work_id).first()

        if not w:
            return []

        timeline = []

        # 1. Recommendation Event
        if w.recommendation_date:
            timeline.append({
                "id": f"rec-{w.id}",
                "event_type": "RECOMMENDATION",
                "event_date": w.recommendation_date,
                "status": "APPROVED",
                "description": "MP Recommendation submitted to District Authority.",
                "is_missing": False
            })
        else:
            timeline.append({
                "id": f"rec-missing-{w.id}",
                "event_type": "RECOMMENDATION",
                "event_date": None,
                "status": "UNRECORDED",
                "description": "Recommendation date not available in source system.",
                "is_missing": True
            })

        # 2. Sanction Event
        if w.sanction_date:
            timeline.append({
                "id": f"sanc-{w.id}",
                "event_type": "SANCTION",
                "event_date": w.sanction_date,
                "status": "SANCTIONED",
                "amount": float(w.sanction_amount) if w.sanction_amount else None,
                "description": f"District Sanction issued for amount ₹{w.sanction_amount:,.2f}" if w.sanction_amount else "District Sanction issued.",
                "is_missing": False
            })
        else:
            timeline.append({
                "id": f"sanc-missing-{w.id}",
                "event_type": "SANCTION",
                "event_date": None,
                "status": "UNRECORDED",
                "description": "Sanction date not available in source system.",
                "is_missing": True
            })

        # 3. Agency Assignment Event
        if w.agency:
            timeline.append({
                "id": f"agency-{w.id}",
                "event_type": "AGENCY_ASSIGNMENT",
                "event_date": w.sanction_date,
                "status": "ASSIGNED",
                "description": f"Executing Agency assigned: {w.agency.name}",
                "is_missing": False
            })

        # 4. Progress Update Events
        for prg in w.progress_records:
            timeline.append({
                "id": f"prg-{prg.id}",
                "event_type": "PROGRESS_UPDATE",
                "event_date": prg.reported_date,
                "status": f"{prg.progress_percent}% Physical Progress",
                "description": prg.status_text or f"Physical progress reported at {prg.progress_percent}%.",
                "is_missing": False
            })

        # 5. Payment Events
        for pay in w.payments:
            timeline.append({
                "id": f"pay-{pay.id}",
                "event_type": "PAYMENT_DISBURSED",
                "event_date": pay.payment_date,
                "status": getattr(pay, 'payment_status', 'DISBURSED'),
                "amount": float(pay.amount),
                "description": f"Disbursement of ₹{pay.amount:,.2f} recorded (Ref: {pay.payment_reference}).",
                "is_missing": False
            })

        # 6. Completion Event
        if w.current_status == "COMPLETED" or w.completion_date:
            if w.completion_date:
                timeline.append({
                    "id": f"comp-{w.id}",
                    "event_type": "COMPLETION",
                    "event_date": w.completion_date,
                    "status": "COMPLETED",
                    "description": "Work marked completed by District Authority.",
                    "is_missing": False
                })
            else:
                timeline.append({
                    "id": f"comp-missing-date-{w.id}",
                    "event_type": "COMPLETION",
                    "event_date": None,
                    "status": "COMPLETED_WITHOUT_DATE",
                    "description": "Work marked completed, but completion date missing in source record.",
                    "is_missing": True
                })

        # Sort timeline by event_date (treating None as early or missing)
        timeline.sort(key=lambda x: x["event_date"] or date(1970, 1, 1))

        return timeline
