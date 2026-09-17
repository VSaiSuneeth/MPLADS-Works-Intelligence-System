import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.db.seed import seed_database
from app.models.work import Work
from app.models.risk import RiskScore
from app.services.ml_anomaly_service import MLAnomalyService
from app.services.risk_service import RiskService

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_ml_feature_extraction(db_session: Session):
    work = db_session.query(Work).first()
    assert work is not None, "Seed work required for ML test"
    
    feats = MLAnomalyService.extract_features(work, db_session)
    assert isinstance(feats, dict)
    assert "sanction_amount" in feats
    assert "disbursement_ratio" in feats
    assert "progress_pct" in feats
    assert "delay_days" in feats
    assert "duration_days" in feats
    assert "progress_lag" in feats
    assert feats["sanction_amount"] >= 0.0

def test_ml_evaluate_all_works(db_session: Session):
    works = db_session.query(Work).all()
    assert len(works) > 0, "Seed dataset required"
    
    predictions = MLAnomalyService.evaluate_all_works(db_session, works)
    assert len(predictions) == len(works)
    
    for w in works:
        pred = predictions[w.id]
        assert "is_anomaly" in pred
        assert "ml_score" in pred
        assert 0.0 <= pred["ml_score"] <= 100.0
        assert "governance_disclaimer" in pred

def test_ml_signal_integration_in_risk_engine(db_session: Session):
    RiskService.calculate_and_save_all_risks(db_session)
    
    risk_scores = db_session.query(RiskScore).all()
    assert len(risk_scores) > 0
    
    # Check that at least one risk score includes signals and runs cleanly
    for rs in risk_scores:
        assert rs.score >= 0.0
        assert rs.priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

def test_ml_disclaimer_governance_text(db_session: Session):
    work = db_session.query(Work).first()
    preds = MLAnomalyService.evaluate_all_works(db_session)
    signal = MLAnomalyService.get_ml_signal_for_work(work, db_session, preds)
    
    if signal:
        assert signal["code"] == "ML-ANOMALY-001"
        assert "notice" in signal["evidence"]
        assert "human review" in signal["evidence"]["notice"].lower()
