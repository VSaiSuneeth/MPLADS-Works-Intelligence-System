import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_

from app.models.work import Work
from app.models.risk import RiskScore, RiskSignal
from app.services.rule_engine import RuleEngine, RuleResult
from app.services.ml_anomaly_service import MLAnomalyService

class RiskService:
    @staticmethod
    def calculate_peer_cost_anomalies(db: Session) -> Dict[str, Dict[str, Any]]:
        """Calculates category peer cost distributions using robust median and median absolute deviation (MAD)."""
        works = db.query(Work).all()
        categories: Dict[str, List[float]] = {}
        for w in works:
            if w.category and w.sanction_amount and float(w.sanction_amount) > 0:
                categories.setdefault(w.category, []).append(float(w.sanction_amount))

        peer_stats = {}
        for cat, costs in categories.items():
            if len(costs) >= 2:
                sorted_costs = sorted(costs)
                n = len(sorted_costs)
                median = sorted_costs[n // 2] if n % 2 != 0 else (sorted_costs[n // 2 - 1] + sorted_costs[n // 2]) / 2.0
                devs = sorted([abs(c - median) for c in costs])
                mad = devs[n // 2] if n % 2 != 0 else (devs[n // 2 - 1] + devs[n // 2]) / 2.0
                peer_stats[cat] = {
                    "count": n,
                    "median": median,
                    "mad": mad if mad > 0 else median * 0.2
                }
        return peer_stats

    @staticmethod
    def compute_work_risk(
        work: Work,
        db: Session,
        peer_stats: Optional[Dict[str, Any]] = None,
        ml_predictions: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, float, str, List[Dict[str, Any]]]:
        # 1. Evaluate Deterministic Rules
        rule_results = RuleEngine.evaluate_work(work, db)
        signals: List[Dict[str, Any]] = []

        total_score = 0.0
        confidence_delta = 0.0

        for r in rule_results:
            total_score += r.contribution
            confidence_delta += r.confidence_impact
            signals.append({
                "code": r.rule_code,
                "type": r.rule_type,
                "severity": r.severity,
                "contribution": r.contribution,
                "confidence_impact": r.confidence_impact,
                "whatHappened": r.what_happened,
                "whyUnusual": r.why_unusual,
                "evidence": r.supporting_fields,
                "recommendedAction": r.recommended_action
            })

        # 2. Evaluate Statistical Cost Anomaly (STAT-COST-001)
        if peer_stats and work.category in peer_stats and work.sanction_amount:
            stats = peer_stats[work.category]
            cost = float(work.sanction_amount)
            median = stats["median"]
            mad = stats["mad"]
            
            # Robust z-score calculation
            z_score = abs(cost - median) / (1.4826 * mad + 1e-5)
            if z_score > 3.0:
                stat_contrib = min(30.0, 10.0 + (z_score - 3.0) * 3.0)
                total_score += stat_contrib
                signals.append({
                    "code": "STAT-COST-001",
                    "type": "STATISTICAL",
                    "severity": "HIGH" if z_score > 5.0 else "MEDIUM",
                    "contribution": round(stat_contrib, 1),
                    "confidence_impact": 5.0,
                    "whatHappened": f"Sanction cost (₹{cost:,.2f}) deviates significantly from peer median (₹{median:,.2f}) for category '{work.category}' (z-score: {z_score:.1f}).",
                    "whyUnusual": "Work cost is statistically higher than comparable peer works within the category distribution.",
                    "evidence": {
                        "category": work.category,
                        "work_cost": cost,
                        "peer_median": median,
                        "robust_z_score": round(z_score, 2),
                        "peer_count": stats["count"]
                    },
                    "recommendedAction": "Compare cost estimate breakdown against standard PWD rate schedule."
                })

        # 3. Evaluate ML Anomaly Signal (ML-ANOMALY-001)
        ml_signal = MLAnomalyService.get_ml_signal_for_work(work, db, ml_predictions)
        if ml_signal:
            total_score += ml_signal["contribution"]
            signals.append(ml_signal)

        # Cap score at 100
        final_score = min(100.0, round(total_score, 1))

        # Assign Priority Band
        if final_score >= 80.0:
            priority = "CRITICAL"
        elif final_score >= 60.0:
            priority = "HIGH"
        elif final_score >= 30.0:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Calculate Confidence Score (0 - 100)
        # Completeness (40%) + Reliability (30%) + Peer Quality (20%) + Freshness (10%)
        non_null_count = sum(1 for v in [work.agency_id, work.location_text, work.sanction_amount, work.sanction_date, work.completion_date] if v is not None)
        completeness = (non_null_count / 5.0) * 100.0
        reliability = 90.0  # High determinism for rule engine
        peer_count = peer_stats[work.category]["count"] if (peer_stats and work.category in peer_stats) else 1
        peer_quality = min(100.0, peer_count * 25.0)
        freshness = 100.0

        raw_confidence = (0.4 * completeness) + (0.3 * reliability) + (0.2 * peer_quality) + (0.1 * freshness)
        final_confidence = max(10.0, min(100.0, round(raw_confidence + confidence_delta, 1)))

        return final_score, final_confidence, priority, signals

    @staticmethod
    def calculate_and_save_all_risks(db: Session):
        peer_stats = RiskService.calculate_peer_cost_anomalies(db)
        works = db.query(Work).all()
        ml_predictions = MLAnomalyService.evaluate_all_works(db, works)

        for w in works:
            score, confidence, priority, signals = RiskService.compute_work_risk(w, db, peer_stats, ml_predictions)
            
            # Save or update RiskScore
            risk_score = db.query(RiskScore).filter(RiskScore.work_id == w.id).first()
            if not risk_score:
                risk_score = RiskScore(
                    work_id=w.id,
                    score=score,
                    priority=priority,
                    confidence=confidence,
                    risk_version="risk-v1.0"
                )
                db.add(risk_score)
                db.commit()
                db.refresh(risk_score)
            else:
                risk_score.score = score
                risk_score.priority = priority
                risk_score.confidence = confidence
                risk_score.calculated_at = datetime.now(timezone.utc)
                db.commit()

            # Delete old signals & insert updated signals
            db.query(RiskSignal).filter(RiskSignal.risk_score_id == risk_score.id).delete()
            for s in signals:
                db.add(RiskSignal(
                    work_id=w.id,
                    risk_score_id=risk_score.id,
                    signal_code=s["code"],
                    signal_type=s["type"],
                    severity=s["severity"],
                    contribution=s["contribution"],
                    confidence_impact=s["confidence_impact"],
                    explanation_json=s
                ))
            db.commit()

    @staticmethod
    def get_risk_queue(
        db: Session,
        authorized_jurisdiction_ids: List[str],
        jurisdiction_id: Optional[str] = None,
        priority: Optional[str] = None,
        stage: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 25
    ) -> Tuple[List[Dict[str, Any]], int]:
        
        query = db.query(RiskScore).join(Work).options(
            joinedload(RiskScore.work).joinedload(Work.jurisdiction),
            joinedload(RiskScore.work).joinedload(Work.agency),
            joinedload(RiskScore.signals)
        )

        # Apply Jurisdiction filter
        if jurisdiction_id:
            if jurisdiction_id not in authorized_jurisdiction_ids and "ALL" not in authorized_jurisdiction_ids:
                return [], 0
            query = query.filter(Work.jurisdiction_id == jurisdiction_id)
        elif "ALL" not in authorized_jurisdiction_ids:
            query = query.filter(Work.jurisdiction_id.in_(authorized_jurisdiction_ids))

        # Apply Priority filter
        if priority and priority.strip() and priority.strip().upper() != "ALL":
            query = query.filter(RiskScore.priority == priority.strip().upper())

        # Apply Stage filter
        if stage and stage.strip() and stage.strip().upper() != "ALL":
            query = query.filter(Work.current_status == stage.strip())

        # Apply Category filter
        if category and category.strip() and category.strip().upper() != "ALL":
            query = query.filter(Work.category == category.strip())

        # Apply Search filter across title, external_id, category, location
        if search and search.strip():
            s_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Work.title.ilike(s_pattern),
                    Work.external_id.ilike(s_pattern),
                    Work.category.ilike(s_pattern),
                    Work.location_text.ilike(s_pattern)
                )
            )

        total = query.count()

        # Sort by Risk Score descending (highest risk first)
        risk_scores = query.order_by(desc(RiskScore.score)).offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for rs in risk_scores:
            w = rs.work
            top_signals = [
                {
                    "code": s.signal_code,
                    "severity": s.severity,
                    "label": s.explanation_json.get("whatHappened", s.signal_code)
                }
                for s in sorted(rs.signals, key=lambda x: x.contribution, reverse=True)[:2]
            ]

            items.append({
                "workId": w.id,
                "externalId": w.external_id,
                "title": w.title,
                "category": w.category,
                "locationText": w.location_text,
                "stage": w.current_status,
                "sanctionAmount": float(w.sanction_amount) if w.sanction_amount else None,
                "latitude": float(w.latitude) if w.latitude is not None else None,
                "longitude": float(w.longitude) if w.longitude is not None else None,
                "score": float(rs.score),
                "priority": rs.priority,
                "confidence": float(rs.confidence),
                "topSignals": top_signals,
                "jurisdiction": {
                    "id": w.jurisdiction.id,
                    "stateName": w.jurisdiction.state_name,
                    "districtName": w.jurisdiction.district_name,
                    "districtCode": w.jurisdiction.district_code
                }
            })

        return items, total
