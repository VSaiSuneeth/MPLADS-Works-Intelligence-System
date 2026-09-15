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

def test_dashboard_summary_authenticated():
    headers = get_auth_header("district.officer")
    res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "totals" in data
    assert "riskDistribution" in data
    assert "topRiskWorks" in data
    assert "dataFreshness" in data

    assert data["totals"]["totalWorks"] > 0
    assert data["riskDistribution"]["critical"] >= 0
    assert len(data["topRiskWorks"]) > 0

def test_dashboard_auditor_view():
    headers = get_auth_header("auditor.demo")
    res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # Senior Auditor has all jurisdictions scope
    assert data["totals"]["totalWorks"] >= 15
