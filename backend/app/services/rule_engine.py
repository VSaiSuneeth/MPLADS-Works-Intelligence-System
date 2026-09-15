from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.models.work import Work, WorkLifecycleEvent, Payment, ProgressRecord, Evidence
from app.models.rule import Rule, RuleVersion

class RuleResult(BaseModel):
    rule_code: str
    rule_type: str = "RULE"
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    contribution: float  # Score addition
    confidence_impact: float  # Impact on confidence score
    what_happened: str
    why_unusual: str
    supporting_fields: Dict[str, Any]
    recommended_action: str

class RuleEngine:
    @staticmethod
    def evaluate_work(work: Work, db: Session) -> List[RuleResult]:
        results: List[RuleResult] = []

        # Load related entities if not already loaded
        progress_records = work.progress_records or []
        payments = work.payments or []
        evidence_list = work.evidence or []

        latest_prog = 0.0
        if progress_records:
            sorted_progs = sorted(progress_records, key=lambda x: x.created_at, reverse=True)
            latest_prog = float(sorted_progs[0].progress_percent)

        sanction_amt = float(work.sanction_amount) if work.sanction_amount else 0.0
        expenditure_amt = float(work.expenditure_amount) if work.expenditure_amount else 0.0
        payments_total = sum(float(p.amount) for p in payments)

        # -------------------------------------------------------------
        # Rule 1: DQ-MISSING-001 — Missing Mandatory Fields
        # -------------------------------------------------------------
        missing_fields = []
        if not work.agency_id:
            missing_fields.append("agency_name")
        if not work.location_text:
            missing_fields.append("location_text")
        if not work.sanction_amount:
            missing_fields.append("sanction_amount")

        if missing_fields:
            results.append(RuleResult(
                rule_code="DQ-MISSING-001",
                severity="MEDIUM",
                contribution=15.0,
                confidence_impact=-10.0,
                what_happened=f"Mandatory metadata fields missing: {', '.join(missing_fields)}.",
                why_unusual="Incomplete work records impede district monitoring and audit traceability.",
                supporting_fields={"missing_fields": missing_fields, "external_id": work.external_id},
                recommended_action="Request executing agency or district clerk to update missing work metadata."
            ))

        # -------------------------------------------------------------
        # Rule 2: DQ-DATE-001 — Invalid Date Chronology
        # -------------------------------------------------------------
        if work.sanction_date and work.completion_date and work.completion_date < work.sanction_date:
            results.append(RuleResult(
                rule_code="DQ-DATE-001",
                severity="HIGH",
                contribution=25.0,
                confidence_impact=-15.0,
                what_happened=f"Completion date ({work.completion_date}) precedes sanction date ({work.sanction_date}).",
                why_unusual="Lifecycle milestones are chronologically inconsistent in source data.",
                supporting_fields={
                    "sanction_date": str(work.sanction_date),
                    "completion_date": str(work.completion_date)
                },
                recommended_action="Verify source sanction and completion certificates to correct date entry."
            ))

        # -------------------------------------------------------------
        # Rule 3: FIN-AMOUNT-001 — Expenditure Exceeds Sanction Amount
        # -------------------------------------------------------------
        if sanction_amt > 0 and (expenditure_amt > sanction_amt * 1.05 or payments_total > sanction_amt * 1.05):
            excess = max(expenditure_amt, payments_total) - sanction_amt
            results.append(RuleResult(
                rule_code="FIN-AMOUNT-001",
                severity="HIGH",
                contribution=30.0,
                confidence_impact=5.0,
                what_happened=f"Total expenditure/disbursements (₹{max(expenditure_amt, payments_total):,.2f}) exceeds approved sanction (₹{sanction_amt:,.2f}) by ₹{excess:,.2f}.",
                why_unusual="Disbursements beyond approved sanction amount violate financial limits without approved revised sanction.",
                supporting_fields={
                    "sanction_amount": sanction_amt,
                    "expenditure_amount": expenditure_amt,
                    "payments_total": payments_total,
                    "excess_amount": excess
                },
                recommended_action="Verify financial records and check for formal revised sanction approval."
            ))

        # -------------------------------------------------------------
        # Rule 4: FIN-PAY-001 — Payment / Progress Mismatch
        # -------------------------------------------------------------
        payment_ratio = (payments_total / sanction_amt) * 100.0 if sanction_amt > 0 else 0.0
        if payment_ratio >= 50.0 and latest_prog < 30.0 and work.current_status == "EXECUTION":
            results.append(RuleResult(
                rule_code="FIN-PAY-001",
                severity="CRITICAL",
                contribution=35.0,
                confidence_impact=10.0,
                what_happened=f"Disbursements reach {payment_ratio:.1f}% of sanction, but reported physical progress is only {latest_prog:.1f}%.",
                why_unusual="High financial disbursement combined with low physical progress indicates potential execution lag or premature payment release.",
                supporting_fields={
                    "payment_ratio_percent": round(payment_ratio, 1),
                    "latest_progress_percent": latest_prog,
                    "payments_total": payments_total,
                    "sanction_amount": sanction_amt
                },
                recommended_action="Conduct physical site inspection or request updated progress verification from implementing agency."
            ))

        # -------------------------------------------------------------
        # Rule 5: COMP-EVID-001 — Completion Lacks Verification Evidence
        # -------------------------------------------------------------
        if work.current_status == "COMPLETED":
            has_cert = any(e.metadata_json.get("hasCompletionCertificate") is True for e in evidence_list)
            has_doc = any(e.evidence_type == "DOCUMENT" for e in evidence_list)
            if not has_cert and not has_doc:
                results.append(RuleResult(
                    rule_code="COMP-EVID-001",
                    severity="HIGH",
                    contribution=25.0,
                    confidence_impact=-10.0,
                    what_happened="Work marked COMPLETED in system, but completion certificate or inspection document is missing.",
                    why_unusual="Official program guidelines require formal completion certificate prior to closing work status.",
                    supporting_fields={"current_status": work.current_status, "evidence_count": len(evidence_list)},
                    recommended_action="Upload signed completion certificate or physical inspection report."
                ))

        # -------------------------------------------------------------
        # Rule 6: TIME-DELAY-001 — Prolonged Execution Delay
        # -------------------------------------------------------------
        if work.current_status == "EXECUTION" and work.sanction_date:
            days_elapsed = (date.today() - work.sanction_date).days
            if days_elapsed > 365 and latest_prog < 50.0:
                results.append(RuleResult(
                    rule_code="TIME-DELAY-001",
                    severity="MEDIUM",
                    contribution=20.0,
                    confidence_impact=5.0,
                    what_happened=f"Work in EXECUTION stage for {days_elapsed} days (> 1 year) with only {latest_prog:.1f}% progress.",
                    why_unusual="Work progress significantly lags expected lifecycle completion timeline.",
                    supporting_fields={"days_elapsed": days_elapsed, "latest_progress_percent": latest_prog},
                    recommended_action="Issue formal progress query to executing agency and request revised timeline."
                ))

        return results
