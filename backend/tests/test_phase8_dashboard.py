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
    assert "mapWorks" in data
    assert "dataFreshness" in data

    assert data["totals"]["totalWorks"] > 0
    assert data["riskDistribution"]["critical"] >= 0
    assert len(data["topRiskWorks"]) > 0
    assert len(data["mapWorks"]) == 10  # Scoped to DIST-001 (10 works)

def test_dashboard_auditor_view():
    headers = get_auth_header("auditor.demo")
    res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # Senior Auditor has all jurisdictions scope
    assert data["totals"]["totalWorks"] >= 15
    assert "mapWorks" in data
    assert len(data["mapWorks"]) == 17

def test_dashboard_gis_coordinates_and_rbac_isolation():
    # 1. Test District Officer (DIST-001 scope)
    headers_officer = get_auth_header("district.officer")
    res_officer = client.get("/api/v1/dashboard/summary", headers=headers_officer)
    assert res_officer.status_code == 200
    data_officer = res_officer.json()

    map_works_officer = data_officer["mapWorks"]
    assert len(map_works_officer) == 10
    for mw in map_works_officer:
        assert mw["latitude"] is not None
        assert mw["longitude"] is not None
        assert -90.0 <= mw["latitude"] <= 90.0
        assert -180.0 <= mw["longitude"] <= 180.0
        assert mw["districtName"] == "North Delhi District"

    # 2. Test Admin (All jurisdictions scope)
    headers_admin = get_auth_header("admin.demo")
    res_admin = client.get("/api/v1/dashboard/summary", headers=headers_admin)
    assert res_admin.status_code == 200
    data_admin = res_admin.json()

    map_works_admin = data_admin["mapWorks"]
    assert len(map_works_admin) == 17
    valid_coords_count = sum(
        1 for mw in map_works_admin
        if mw["latitude"] is not None and mw["longitude"] is not None
    )
    assert valid_coords_count == 17

