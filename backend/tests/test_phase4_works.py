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

def test_list_works_authenticated():
    headers = get_auth_header("district.officer")
    res = client.get("/api/v1/works", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0

def test_list_works_stage_filter():
    headers = get_auth_header("district.officer")
    res = client.get("/api/v1/works?stage=EXECUTION", headers=headers)
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["stage"] == "EXECUTION"

def test_list_works_search_query():
    headers = get_auth_header("district.officer")
    res = client.get("/api/v1/works?search=Borewell", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) > 0
    assert "Borewell" in data["items"][0]["title"]

def test_work_detail_and_timeline():
    db = SessionLocal()
    try:
        w = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w is not None
        work_id = w.id
    finally:
        db.close()

    headers = get_auth_header("district.officer")
    
    # Detail
    res = client.get(f"/api/v1/works/{work_id}", headers=headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["externalId"] == "W-1001"
    assert detail["title"] == "Construction of High Capacity Borewell and Tank"
    
    # Timeline
    t_res = client.get(f"/api/v1/works/{work_id}/timeline", headers=headers)
    assert t_res.status_code == 200
    timeline = t_res.json()
    assert len(timeline) > 0
    assert any(t["eventType"] == "RECOMMENDATION" for t in timeline)
    assert any(t["eventType"] == "SANCTION" for t in timeline)

def test_seeded_evidence_is_served_from_backend_and_timeline_does_not_invent_dates():
    db = SessionLocal()
    try:
        w = db.query(Work).filter(Work.external_id == "W-1005").first()
        assert w is not None
        work_id = w.id
    finally:
        db.close()

    headers = get_auth_header("district.officer")
    evidence_response = client.get(f"/api/v1/works/{work_id}/evidence", headers=headers)
    assert evidence_response.status_code == 200
    evidence = next(item for item in evidence_response.json() if item["fileName"] == "light_poles.jpg")
    assert evidence["availabilityStatus"] == "AVAILABLE"
    assert evidence["sourceUrl"].startswith(f"/api/v1/works/{work_id}/evidence/")

    file_response = client.get(evidence["sourceUrl"])
    assert file_response.status_code == 200
    assert file_response.headers["content-type"].startswith("image/jpeg")
    assert file_response.content

    timeline_response = client.get(f"/api/v1/works/{work_id}/timeline", headers=headers)
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()
    payment = next(item for item in timeline if item["eventType"] == "PAYMENT_DISBURSED")
    progress = next(item for item in timeline if item["eventType"] == "PROGRESS_UPDATE")
    assert payment["eventDate"] is None and payment["isMissing"] is True
    assert progress["eventDate"] is None and progress["isMissing"] is True

def test_jurisdiction_scope_isolation():
    # Delhi officer tries to query Lucknow works directly by ID
    db = SessionLocal()
    try:
        w_lucknow = db.query(Work).filter(Work.external_id == "W-1009").first()
        assert w_lucknow is not None
        lucknow_work_id = w_lucknow.id
    finally:
        db.close()

    delhi_headers = get_auth_header("district.officer")
    res = client.get(f"/api/v1/works/{lucknow_work_id}", headers=delhi_headers)
    # Should return 404 NOT_FOUND because access is restricted outside officer jurisdiction
    assert res.status_code == 404
