from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.work import Work
from app.models.agency import Agency
from app.models.jurisdiction import Jurisdiction
from app.models.risk import RiskScore

class AgencyConcentrationService:
    """
    Lightweight Analytical Service for Implementing Agency & Contractor Allocation Concentration.
    Surfaces operational concentration patterns across sanctioned works, total allocation amounts,
    district span, and risk priority distributions for human review.
    """

    @classmethod
    def get_agency_concentration_analysis(
        cls,
        db: Session,
        authorized_jurisdiction_ids: List[str],
        jurisdiction_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        
        query = db.query(Work).options(
            joinedload(Work.agency),
            joinedload(Work.jurisdiction)
        )

        if jurisdiction_id:
            if jurisdiction_id not in authorized_jurisdiction_ids and "ALL" not in authorized_jurisdiction_ids:
                query = query.filter(Work.id == "none")
            else:
                query = query.filter(Work.jurisdiction_id == jurisdiction_id)
        elif "ALL" not in authorized_jurisdiction_ids:
            query = query.filter(Work.jurisdiction_id.in_(authorized_jurisdiction_ids))

        works = query.all()

        # Group works by agency
        agency_groups: Dict[str, List[Work]] = {}
        for w in works:
            agency_name = w.agency.name if w.agency else "Unassigned / Direct Department"
            agency_groups.setdefault(agency_name, []).append(w)

        results = []
        total_scoped_works = max(1, len(works))

        for agency_name, a_works in agency_groups.items():
            tot_works = len(a_works)
            tot_sanction = sum(float(w.sanction_amount) for w in a_works if w.sanction_amount)
            
            districts = set(w.jurisdiction.district_name for w in a_works if w.jurisdiction)
            categories = set(w.category for w in a_works if w.category)

            # Get Risk Scores for these works
            w_ids = [w.id for w in a_works]
            risk_scores = db.query(RiskScore).filter(RiskScore.work_id.in_(w_ids)).all()
            
            critical_cnt = sum(1 for r in risk_scores if r.priority == "CRITICAL")
            high_cnt = sum(1 for r in risk_scores if r.priority == "HIGH")
            medium_cnt = sum(1 for r in risk_scores if r.priority == "MEDIUM")
            low_cnt = sum(1 for r in risk_scores if r.priority == "LOW")

            work_share_pct = (tot_works / total_scoped_works) * 100.0

            # Concentration indicator flag (3+ works or multi-district or high share)
            concentration_flag = (tot_works >= 3 or len(districts) >= 2 or work_share_pct >= 25.0)

            results.append({
                "agencyName": agency_name,
                "totalWorks": tot_works,
                "workSharePercent": round(work_share_pct, 1),
                "totalSanctionAmount": round(tot_sanction, 2),
                "districtSpanCount": len(districts),
                "districts": list(districts),
                "categories": list(categories),
                "riskBreakdown": {
                    "critical": critical_cnt,
                    "high": high_cnt,
                    "medium": medium_cnt,
                    "low": low_cnt
                },
                "concentrationFlag": concentration_flag,
                "governanceNote": "Concentration indicator flagged for human review. Multi-project allocation reflects operational capacity, NOT proof of impropriety."
            })

        # Sort agencies by total works descending
        results.sort(key=lambda x: x["totalWorks"], reverse=True)
        return results
