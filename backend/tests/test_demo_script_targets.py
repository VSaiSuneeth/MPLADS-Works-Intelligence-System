import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import close_all_sessions

from app.main import app
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.seed import seed_database
from app.models.work import Work, Evidence
from app.services.risk_service import RiskService
from app.services.ml_anomaly_service import MLAnomalyService
from app.services.similarity_service import SimilarityService
from app.services.simulation_service import SimulationService
from app.schemas.simulation import SimulationRequest

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_seed():
    close_all_sessions()
    Base.metadata.drop_all(bind=engine)
    seed_database()

def test_demo_script_w1001_risk_target():
    """Verifies W-1001 risk score = 85.0, priority = CRITICAL, and active signals count = 3."""
    db = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1 is not None

        peer_stats = RiskService.calculate_peer_cost_anomalies(db)
        works = db.query(Work).all()
        ml_preds = MLAnomalyService.evaluate_all_works(db, works)

        score, confidence, priority, signals = RiskService.compute_work_risk(w1, db, peer_stats, ml_preds)

        assert score == 85.0
        assert priority == "CRITICAL"
        assert len(signals) == 3

        signal_codes = [s["code"] for s in signals]
        assert "FIN-PAY-001" in signal_codes
        assert "STAT-COST-001" in signal_codes
        assert "ML-ANOMALY-001" in signal_codes
    finally:
        db.close()

def test_demo_script_w1002_similarity_target():
    """Verifies Candidate W-1002 similarity score = 84.0%."""
    db = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1 is not None

        sim_list = SimilarityService.get_similar_works(db, w1.id)
        w2_cand = next((c for c in sim_list if c["externalId"] == "W-1002"), None)

        assert w2_cand is not None
        assert w2_cand["similarityScore"] == 84.0
    finally:
        db.close()

def test_demo_script_w1001_evidence_metadata():
    """Verifies W-1001 evidence filename and EXIF metadata."""
    db = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1 is not None

        ev = db.query(Evidence).filter(Evidence.work_id == w1.id, Evidence.file_name == "site_inspection_01.jpg").first()
        assert ev is not None
        assert ev.file_name == "site_inspection_01.jpg"
        assert float(ev.exif_latitude) == 28.6139
        assert float(ev.exif_longitude) == 77.2090
    finally:
        db.close()

def test_demo_script_simulator_premature_spend_spike():
    """Verifies What-If Simulator premature spend spike yields 90.0 / 100 CRITICAL."""
    db = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1 is not None

        sim_req = SimulationRequest(
            work_id=w1.id,
            project_cost=4500000.0,
            expenditure_amount=4275000.0,
            completion_pct=15.0,
            sanction_date="2025-10-15"
        )
        sim_res = SimulationService.simulate(db, sim_req)
        assert sim_res.simulatedScenario.overallScore == 90.0
        assert sim_res.simulatedScenario.priorityBand == "CRITICAL"
    finally:
        db.close()
