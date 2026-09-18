import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import close_all_sessions
from app.main import app
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.seed import seed_database
from app.models import Work, Jurisdiction, Agency, DataQualityFinding, Payment, Evidence, ProgressRecord

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_seed():
    close_all_sessions()
    Base.metadata.drop_all(bind=engine)
    seed_database()

def test_seed_works_populated():
    db = SessionLocal()
    try:
        works = db.query(Work).all()
        assert len(works) >= 15
        
        # Verify specific work record
        w1001 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1001 is not None
        assert w1001.title == "Construction of High Capacity Borewell and Tank"
        assert w1001.category == "Water Supply & Sanitation"
        assert float(w1001.sanction_amount) == 4500000.00
    finally:
        db.close()

def test_seed_data_quality_findings():
    db = SessionLocal()
    try:
        # Check that invalid date order anomaly in W-1004 generated a DQ finding
        w1004 = db.query(Work).filter(Work.external_id == "W-1004").first()
        assert w1004 is not None
        
        dq_date = db.query(DataQualityFinding).filter(DataQualityFinding.work_id == w1004.id).first()
        assert dq_date is not None
        assert dq_date.finding_type == "DQ_DATE_ORDER_INVALID"
        assert dq_date.severity == "HIGH"
    finally:
        db.close()

def test_seed_evidence_records():
    db = SessionLocal()
    try:
        evidence = db.query(Evidence).all()
        assert len(evidence) > 0
        
        w1003 = db.query(Work).filter(Work.external_id == "W-1003").first()
        w1003_ev = db.query(Evidence).filter(Evidence.work_id == w1003.id).first()
        assert w1003_ev is not None
        assert w1003_ev.file_name == "road_completion.pdf"
        assert w1003_ev.metadata_json.get("hasCompletionCertificate") is True
    finally:
        db.close()
