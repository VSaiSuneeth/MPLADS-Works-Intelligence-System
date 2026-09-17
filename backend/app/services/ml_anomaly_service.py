import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest

from app.models.work import Work, Payment, ProgressRecord

class MLAnomalyService:
    """
    Explainable Machine Learning Anomaly Detection Service using Isolation Forest.
    Engineers multidimensional feature vectors across financial, physical progress,
    and timeline metrics to detect multivariate operational anomalies for human review.
    """

    @staticmethod
    def extract_features(work: Work, db: Session) -> Dict[str, float]:
        """Extracts engineered numerical features for a single work."""
        sanction_amount = float(work.sanction_amount) if work.sanction_amount else 0.0

        # Financial disbursement ratio
        payments = db.query(Payment).filter(Payment.work_id == work.id).all()
        total_disbursed = sum(float(p.amount) for p in payments) if payments else 0.0
        disbursement_ratio = (total_disbursed / sanction_amount) if sanction_amount > 0 else 0.0

        # Physical progress percentage
        latest_progress = (
            db.query(ProgressRecord)
            .filter(ProgressRecord.work_id == work.id)
            .order_by(ProgressRecord.reported_date.desc())
            .first()
        )
        progress_pct = float(latest_progress.progress_percent) if latest_progress else (
            100.0 if work.current_status == "COMPLETED" else 25.0
        )

        # Timeline duration & delay days
        sanction_date = work.sanction_date or datetime.now(timezone.utc).date()
        target_comp = work.completion_date or sanction_date
        
        duration_days = max(1.0, float((target_comp - sanction_date).days))
        
        # Calculate delay
        today = datetime.now(timezone.utc).date()
        if work.current_status != "COMPLETED" and today > target_comp:
            delay_days = max(0.0, float((today - target_comp).days))
        else:
            delay_days = 0.0

        # Progress vs Time Elapsed ratio
        days_elapsed = max(1.0, float((today - sanction_date).days))
        expected_progress = min(100.0, (days_elapsed / duration_days) * 100.0)
        progress_lag = max(0.0, expected_progress - progress_pct)

        return {
            "sanction_amount": sanction_amount,
            "disbursement_ratio": round(disbursement_ratio, 4),
            "progress_pct": round(progress_pct, 2),
            "delay_days": round(delay_days, 1),
            "duration_days": round(duration_days, 1),
            "progress_lag": round(progress_lag, 2)
        }

    @classmethod
    def evaluate_all_works(cls, db: Session, works: Optional[List[Work]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Trains an Isolation Forest model over all active works in DB and returns
        standardized anomaly predictions for each work.
        """
        if works is None:
            works = db.query(Work).all()

        if not works:
            return {}

        feature_dicts = [cls.extract_features(w, db) for w in works]
        feature_matrix = np.array([
            [
                f["sanction_amount"],
                f["disbursement_ratio"],
                f["progress_pct"],
                f["delay_days"],
                f["duration_days"],
                f["progress_lag"]
            ]
            for f in feature_dicts
        ])

        # If sample size is very small, fit with reduced contamination
        contamination = min(0.20, max(0.05, 2.0 / len(works))) if len(works) > 1 else 0.1

        clf = IsolationForest(
            n_estimators=50,
            contamination=contamination,
            random_state=42
        )
        
        # Fit model and compute decision function scores
        clf.fit(feature_matrix)
        predictions = clf.predict(feature_matrix)  # -1 for anomaly, 1 for normal
        raw_scores = clf.decision_function(feature_matrix)  # lower values = more anomalous

        # Normalize raw decision score to 0–100 risk scale
        # decision_function yields values in roughly [-0.5, 0.5]
        min_s, max_s = np.min(raw_scores), np.max(raw_scores)
        score_range = (max_s - min_s) if (max_s - min_s) > 1e-5 else 1.0

        results = {}
        for idx, w in enumerate(works):
            pred = predictions[idx]
            is_anomaly = (pred == -1)
            raw = raw_scores[idx]
            
            # Scale so anomalous items (lower raw score) get higher ML anomaly score (0-100)
            norm_score = ((max_s - raw) / score_range) * 100.0
            
            feats = feature_dicts[idx]
            results[w.id] = {
                "workId": w.id,
                "externalId": w.external_id,
                "is_anomaly": is_anomaly,
                "ml_score": round(float(norm_score), 1),
                "raw_decision_score": round(float(raw), 4),
                "features": feats,
                "model_name": "IsolationForest (scikit-learn)",
                "governance_disclaimer": "ML anomaly signal is an operational indicator for human review, NOT proof of wrongdoing."
            }

        return results

    @classmethod
    def get_ml_signal_for_work(cls, work: Work, db: Session, ml_predictions: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Computes or retrieves ML anomaly signal dictionary for a single work to include in RiskScore signals.
        """
        if ml_predictions is None or work.id not in ml_predictions:
            all_preds = cls.evaluate_all_works(db, works=[work])
            pred_data = all_preds.get(work.id)
        else:
            pred_data = ml_predictions.get(work.id)

        if not pred_data or not pred_data.get("is_anomaly"):
            return None

        ml_score = pred_data["ml_score"]
        feats = pred_data["features"]
        
        # Contribution to composite risk score (up to 20 pts)
        contrib = min(20.0, max(5.0, ml_score * 0.20))

        explanation = (
            f"Isolation Forest ML model flagged multivariate feature anomaly (ML Score: {ml_score:.1f}/100) "
            f"across sanction amount (₹{feats['sanction_amount']:,.0f}), disbursement ratio ({feats['disbursement_ratio']:.0%}), "
            f"progress ({feats['progress_pct']}%), and delay ({feats['delay_days']} days)."
        )

        return {
            "code": "ML-ANOMALY-001",
            "type": "ML_ANOMALY",
            "severity": "HIGH" if ml_score >= 70.0 else "MEDIUM",
            "contribution": round(contrib, 1),
            "confidence_impact": 5.0,
            "whatHappened": explanation,
            "whyUnusual": "Multivariate non-linear feature pattern deviates significantly from baseline operational clusters.",
            "evidence": {
                "ml_score": ml_score,
                "is_anomaly": True,
                "model": "IsolationForest (scikit-learn)",
                "features": feats,
                "notice": "ML anomaly signal is an indicator for human review, NOT proof of wrongdoing."
            },
            "recommendedAction": "Conduct holistic review of financial progress milestones and physical site inspection logs."
        }
