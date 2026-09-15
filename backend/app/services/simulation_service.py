import math
from datetime import datetime, date, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.work import Work, ProgressRecord, Payment, Evidence
from app.services.risk_service import RiskService
from app.services.rule_engine import RuleEngine
from app.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    ScenarioMetrics,
    ImpactDelta,
)

class SimulationService:
    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[date]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    @staticmethod
    def compute_scenario(
        cost: float,
        expenditure: float,
        completion_pct: float,
        sanction_d: Optional[date],
        expected_comp_d: Optional[date],
        category: str,
        current_status: str,
        transient_work: Work,
        peer_stats: Dict[str, Any],
        db: Session
    ) -> ScenarioMetrics:
        today = date.today()
        
        # 1. Calculate Financial Risk
        expenditure_ratio = (expenditure / cost * 100.0) if cost > 0 else 0.0
        mismatch = expenditure_ratio - completion_pct
        cost_overrun_pct = ((expenditure - cost) / cost * 100.0) if (cost > 0 and expenditure > cost) else 0.0

        fin_score = 0.0
        fin_signals: List[Dict[str, Any]] = []

        if mismatch > 50.0:
            fin_score += 45.0
            fin_signals.append({
                "code": "SIM-FIN-001",
                "severity": "CRITICAL",
                "message": f"Severe premature disbursement mismatch: {expenditure_ratio:.1f}% disbursed vs {completion_pct:.1f}% physical progress."
            })
        elif mismatch > 30.0:
            fin_score += 30.0
            fin_signals.append({
                "code": "SIM-FIN-001",
                "severity": "HIGH",
                "message": f"High expenditure ratio ({expenditure_ratio:.1f}%) exceeds physical completion ({completion_pct:.1f}%)."
            })
        elif mismatch > 15.0:
            fin_score += 15.0
            fin_signals.append({
                "code": "SIM-FIN-001",
                "severity": "MEDIUM",
                "message": f"Moderate expenditure ahead of reported progress ({mismatch:.1f}% gap)."
            })

        if cost_overrun_pct > 0:
            overrun_contrib = min(40.0, 15.0 + cost_overrun_pct * 1.2)
            fin_score += overrun_contrib
            fin_signals.append({
                "code": "SIM-FIN-002",
                "severity": "HIGH" if cost_overrun_pct > 20 else "MEDIUM",
                "message": f"Expenditure exceeds sanctioned cost by ₹{expenditure - cost:,.2f} ({cost_overrun_pct:.1f}% overrun)."
            })

        # Category Peer Cost Anomaly Z-Score
        if category in peer_stats and cost > 0:
            stats = peer_stats[category]
            median = stats["median"]
            mad = stats["mad"]
            z_score = abs(cost - median) / (1.4826 * mad + 1e-5)
            if z_score > 3.0:
                stat_contrib = min(25.0, 10.0 + (z_score - 3.0) * 3.0)
                fin_score += stat_contrib
                fin_signals.append({
                    "code": "SIM-STAT-001",
                    "severity": "HIGH" if z_score > 5.0 else "MEDIUM",
                    "message": f"Sanction cost (₹{cost:,.2f}) deviates from category peer median (₹{median:,.2f}, z-score {z_score:.1f})."
                })

        final_fin_score = min(100.0, round(fin_score, 1))
        if final_fin_score >= 80.0:
            fin_severity = "CRITICAL"
        elif final_fin_score >= 60.0:
            fin_severity = "HIGH"
        elif final_fin_score >= 30.0:
            fin_severity = "MEDIUM"
        else:
            fin_severity = "LOW"

        # 2. Calculate Delay Risk
        s_date = sanction_d or today
        target_d = expected_comp_d or date(s_date.year + 1, s_date.month, s_date.day)

        days_elapsed = max(0, (today - s_date).days)
        days_planned = max(1, (target_d - s_date).days)
        days_overdue = max(0, (today - target_d).days) if (today > target_d and completion_pct < 100.0) else 0

        expected_prog = min(100.0, (days_elapsed / days_planned) * 100.0) if days_planned > 0 else 100.0
        slippage = max(0.0, expected_prog - completion_pct)

        delay_score = 0.0
        delay_signals: List[Dict[str, Any]] = []

        if slippage > 40.0:
            delay_score += 45.0
            delay_signals.append({
                "code": "SIM-DELAY-001",
                "severity": "CRITICAL",
                "message": f"Critical progress slippage: {slippage:.1f}% behind timeline schedule ({completion_pct:.1f}% actual vs {expected_prog:.1f}% target)."
            })
        elif slippage > 25.0:
            delay_score += 30.0
            delay_signals.append({
                "code": "SIM-DELAY-001",
                "severity": "HIGH",
                "message": f"Significant timeline delay ({slippage:.1f}% progress slippage)."
            })
        elif slippage > 10.0:
            delay_score += 15.0
            delay_signals.append({
                "code": "SIM-DELAY-001",
                "severity": "MEDIUM",
                "message": f"Moderate timeline slippage ({slippage:.1f}% behind expected schedule)."
            })

        if days_overdue > 0:
            overdue_contrib = min(40.0, 15.0 + (days_overdue / 30.0) * 5.0)
            delay_score += overdue_contrib
            delay_signals.append({
                "code": "SIM-DELAY-002",
                "severity": "HIGH" if days_overdue > 90 else "MEDIUM",
                "message": f"Project is {days_overdue} days past target completion date."
            })

        if days_elapsed > 180 and completion_pct < 15.0 and current_status == "EXECUTION":
            delay_score += 20.0
            delay_signals.append({
                "code": "SIM-DELAY-003",
                "severity": "MEDIUM",
                "message": f"Stagnant execution: Only {completion_pct:.1f}% progress recorded after {days_elapsed} days."
            })

        final_delay_score = min(100.0, round(delay_score, 1))
        if final_delay_score >= 80.0:
            delay_severity = "CRITICAL"
        elif final_delay_score >= 60.0:
            delay_severity = "HIGH"
        elif final_delay_score >= 30.0:
            delay_severity = "MEDIUM"
        else:
            delay_severity = "LOW"

        # 3. Rule Engine Extras & Overall Composite Score
        rule_results = RuleEngine.evaluate_work(transient_work, db)
        extra_rule_contrib = sum(r.contribution for r in rule_results if r.rule_code not in ("FIN-AMOUNT-001", "FIN-PAY-001", "TIME-DELAY-001"))

        raw_overall = (0.45 * final_fin_score) + (0.45 * final_delay_score) + (0.10 * min(100.0, extra_rule_contrib))
        final_overall_score = min(100.0, round(raw_overall, 1))

        if final_overall_score >= 80.0:
            priority_band = "CRITICAL"
        elif final_overall_score >= 60.0:
            priority_band = "HIGH"
        elif final_overall_score >= 30.0:
            priority_band = "MEDIUM"
        else:
            priority_band = "LOW"

        all_signals = fin_signals + delay_signals + [
            {"code": r.rule_code, "severity": r.severity, "message": r.what_happened}
            for r in rule_results
        ]

        return ScenarioMetrics(
            overallScore=final_overall_score,
            priorityBand=priority_band,
            financialRiskScore=final_fin_score,
            financialRiskSeverity=fin_severity,
            delayRiskScore=final_delay_score,
            delayRiskSeverity=delay_severity,
            expenditureRatioPct=round(expenditure_ratio, 1),
            completionPct=round(completion_pct, 1),
            costOverrunPct=round(cost_overrun_pct, 1),
            daysElapsed=days_elapsed,
            daysTotalPlanned=days_planned,
            daysOverdue=days_overdue,
            signals=all_signals
        )

    @staticmethod
    def simulate(db: Session, request: SimulationRequest) -> SimulationResponse:
        peer_stats = RiskService.calculate_peer_cost_anomalies(db)

        # 1. Determine baseline / current scenario values
        base_work: Optional[Work] = None
        if request.work_id:
            base_work = db.query(Work).filter(Work.id == request.work_id).first()

        if base_work:
            base_title = base_work.title
            base_category = base_work.category or request.category or "Water Supply & Sanitation"
            curr_cost = float(base_work.sanction_amount or request.project_cost)
            curr_expenditure = float(base_work.expenditure_amount or 0.0)
            
            # Fetch latest progress record if available
            latest_prog = 0.0
            if base_work.progress_records:
                sorted_p = sorted(base_work.progress_records, key=lambda x: x.created_at, reverse=True)
                latest_prog = float(sorted_p[0].progress_percent)
            curr_completion_pct = latest_prog
            
            curr_sanction_d = base_work.sanction_date
            curr_expected_comp_d = base_work.completion_date
            curr_status = base_work.current_status
            
            curr_transient = base_work
        else:
            base_title = request.title or "Simulated Work Proposal"
            base_category = request.category or "Water Supply & Sanitation"
            curr_cost = request.project_cost
            curr_expenditure = request.expenditure_amount
            curr_completion_pct = request.completion_pct
            curr_sanction_d = SimulationService.parse_date(request.sanction_date) or date.today()
            curr_expected_comp_d = SimulationService.parse_date(request.expected_completion_date)
            curr_status = request.current_status or "EXECUTION"

            curr_transient = Work(
                title=base_title,
                category=base_category,
                sanction_amount=curr_cost,
                expenditure_amount=curr_expenditure,
                sanction_date=curr_sanction_d,
                completion_date=curr_expected_comp_d,
                current_status=curr_status
            )

        # Calculate Current Scenario Metrics
        current_metrics = SimulationService.compute_scenario(
            cost=curr_cost,
            expenditure=curr_expenditure,
            completion_pct=curr_completion_pct,
            sanction_d=curr_sanction_d,
            expected_comp_d=curr_expected_comp_d,
            category=base_category,
            current_status=curr_status,
            transient_work=curr_transient,
            peer_stats=peer_stats,
            db=db
        )

        # 2. Simulated Scenario
        sim_cost = request.project_cost
        sim_expenditure = request.expenditure_amount
        sim_completion_pct = request.completion_pct
        sim_sanction_d = SimulationService.parse_date(request.sanction_date) or curr_sanction_d
        sim_expected_comp_d = SimulationService.parse_date(request.expected_completion_date) or curr_expected_comp_d
        sim_status = request.current_status or curr_status

        sim_transient = Work(
            id=base_work.id if base_work else None,
            title=base_title,
            category=base_category,
            sanction_amount=sim_cost,
            expenditure_amount=sim_expenditure,
            sanction_date=sim_sanction_d,
            completion_date=sim_expected_comp_d,
            current_status=sim_status
        )

        simulated_metrics = SimulationService.compute_scenario(
            cost=sim_cost,
            expenditure=sim_expenditure,
            completion_pct=sim_completion_pct,
            sanction_d=sim_sanction_d,
            expected_comp_d=sim_expected_comp_d,
            category=base_category,
            current_status=sim_status,
            transient_work=sim_transient,
            peer_stats=peer_stats,
            db=db
        )

        # 3. Calculate Impact Delta
        score_delta = round(simulated_metrics.overallScore - current_metrics.overallScore, 1)
        fin_delta = round(simulated_metrics.financialRiskScore - current_metrics.financialRiskScore, 1)
        delay_delta = round(simulated_metrics.delayRiskScore - current_metrics.delayRiskScore, 1)

        band_change = f"{current_metrics.priorityBand} → {simulated_metrics.priorityBand}" if current_metrics.priorityBand != simulated_metrics.priorityBand else f"UNCHANGED ({simulated_metrics.priorityBand})"
        is_increased = score_delta > 0

        key_drivers: List[str] = []

        if fin_delta > 5:
            key_drivers.append(f"Financial risk increased by +{fin_delta:.1f} pts due to higher disbursement ratio ({simulated_metrics.expenditureRatioPct}%) or cost overrun ({simulated_metrics.costOverrunPct}%).")
        elif fin_delta < -5:
            key_drivers.append(f"Financial risk reduced by {fin_delta:.1f} pts due to improved alignment between expenditure ({simulated_metrics.expenditureRatioPct}%) and physical progress ({simulated_metrics.completionPct}%).")

        if delay_delta > 5:
            key_drivers.append(f"Delay risk increased by +{delay_delta:.1f} pts due to progress slippage ({simulated_metrics.completionPct}% progress vs target timeline).")
        elif delay_delta < -5:
            key_drivers.append(f"Delay risk reduced by {delay_delta:.1f} pts due to accelerated physical completion ({simulated_metrics.completionPct}%).")

        if sim_cost != curr_cost:
            key_drivers.append(f"Project sanction cost adjusted from ₹{curr_cost:,.2f} to ₹{sim_cost:,.2f}.")

        if not key_drivers:
            key_drivers.append("Simulated scenario parameters remain closely aligned with baseline project metrics.")

        if simulated_metrics.priorityBand in ("CRITICAL", "HIGH"):
            recommended_action = "Recommend physical inspection, formal expenditure audit, and revised execution milestone targets before releasing further funds."
        elif simulated_metrics.priorityBand == "MEDIUM":
            recommended_action = "Issue formal progress clarification notice to executing agency and monitor upcoming milestone schedule."
        else:
            recommended_action = "Simulated scenario indicates low risk level. Maintain routine monthly progress reporting."

        impact_delta = ImpactDelta(
            overallScoreDelta=score_delta,
            financialRiskDelta=fin_delta,
            delayRiskDelta=delay_delta,
            priorityBandChange=band_change,
            isRiskIncreased=is_increased,
            keyDrivers=key_drivers,
            recommendedAction=recommended_action
        )

        return SimulationResponse(
            workId=request.work_id,
            workTitle=base_title,
            category=base_category,
            currentScenario=current_metrics,
            simulatedScenario=simulated_metrics,
            impactDelta=impact_delta
        )
