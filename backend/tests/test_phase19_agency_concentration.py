import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.seed import seed_database

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_seed():
    seed_database()

def get_auth_header(username: str = "admin.demo", password: str = "demo-password"):
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}

def test_agency_concentration_analytics_endpoint():
    headers = get_auth_header("admin.demo")
    res = client.get("/api/v1/works/analytics/agencies", headers=headers)
    assert res.status_code == 200
    
    agencies = res.json()
    assert isinstance(agencies, list)
    assert len(agencies) > 0

    first_agency = agencies[0]
    assert "agencyName" in first_agency
    assert "totalWorks" in first_agency
    assert "workSharePercent" in first_agency
    assert "totalSanctionAmount" in first_agency
    assert "riskBreakdown" in first_agency
    assert "concentrationFlag" in first_agency
    assert "governanceNote" in first_agency
    assert "human review" in first_agency["governanceNote"].lower()
