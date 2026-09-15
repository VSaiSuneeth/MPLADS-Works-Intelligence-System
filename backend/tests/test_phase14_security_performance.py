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
from app.models.work import Work
from app.models.jurisdiction import Jurisdiction
from app.services.data_quality_service import DataQualityService

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_seed():
    close_all_sessions()
    Base.metadata.drop_all(bind=engine)
    seed_database()

def get_auth_header(username: str, password: str = "demo-password"):
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}

def test_jurisdiction_isolation_security():
    # Lucknow Officer (DIST-002) attempting to access unassigned Delhi jurisdiction
    lucknow_headers = get_auth_header("lucknow.officer")
    
    db = SessionLocal()
    delhi_jur = db.query(Jurisdiction).filter(Jurisdiction.district_code == "DIST-001").first()
    db.close()
    assert delhi_jur is not None

    # Request dashboard summary for Delhi jurisdiction
    res = client.get(f"/api/v1/dashboard/summary?jurisdictionId={delhi_jur.id}", headers=lucknow_headers)
    assert res.status_code == 200
    data = res.json()
    # Isolation enforced: total works should be 0 because officer is not authorized for DIST-001
    assert data["totals"]["totalWorks"] == 0

def test_api_performance_response_headers():
    headers = get_auth_header("district.officer")
    res = client.get("/api/v1/works?pageSize=10", headers=headers)
    assert res.status_code == 200
    assert "X-Process-Time" in res.headers
    process_time = float(res.headers["X-Process-Time"])
    assert process_time < 1.0 # Response time within expected bounds

def test_data_quality_service_aggregation():
    db = SessionLocal()
    try:
        summary = DataQualityService.get_quality_summary(db, ["ALL"])
        assert "totalFindings" in summary
        assert summary["totalFindings"] >= 0
    finally:
        db.close()
