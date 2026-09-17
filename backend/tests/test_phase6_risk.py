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
from app.models import Work
from app.services.risk_service import RiskService

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_seed():
    close_all_sessions()
    Base.metadata.drop_all(bind=engine)
    seed_database()

def get_auth_header(username: str = "district.officer", password: str = "demo-password"):
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}

def test_risk_queue_authenticated():
    headers = get_auth_header("district.officer")
    res = client.get("/api/v1/risk/queue", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0

    # Verify items are sorted by score descending
    scores = [item["score"] for item in data["items"]]
    assert scores == sorted(scores, reverse=True)

def test_risk_queue_category_filter_accepts_encoded_ampersand_category():
    headers = get_auth_header("district.officer")
    res = client.get(
        "/api/v1/risk/queue",
        params={"category": "Water Supply & Sanitation"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert all(item["category"] == "Water Supply & Sanitation" for item in data["items"])

def test_work_risk_detail_explanation():
    db = SessionLocal()
    try:
        w1001 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1001 is not None
        work_id = w1001.id
    finally:
        db.close()

    headers = get_auth_header("district.officer")
    res = client.get(f"/api/v1/risk/works/{work_id}", headers=headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["workId"] == work_id
    assert detail["score"] >= 30.0
    assert "signals" in detail
    
    signal_codes = [s["code"] for s in detail["signals"]]
    assert "FIN-PAY-001" in signal_codes

def test_statistical_cost_anomaly():
    db = SessionLocal()
    try:
        w1005 = db.query(Work).filter(Work.external_id == "W-1005").first()
        assert w1005 is not None
        work_id = w1005.id
    finally:
        db.close()

    headers = get_auth_header("district.officer")
    res = client.get(f"/api/v1/risk/works/{work_id}", headers=headers)
    assert res.status_code == 200
    detail = res.json()
    
    signal_codes = [s["code"] for s in detail["signals"]]
    assert "STAT-COST-001" in signal_codes
