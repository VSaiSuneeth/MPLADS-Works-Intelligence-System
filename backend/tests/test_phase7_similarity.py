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
from app.services.similarity_service import SimilarityService

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

def test_seeded_duplicate_borewell_pair():
    db = SessionLocal()
    try:
        w1001 = db.query(Work).filter(Work.external_id == "W-1001").first()
        w1002 = db.query(Work).filter(Work.external_id == "W-1002").first()
        assert w1001 is not None and w1002 is not None
        w1001_id = w1001.id
        w1002_id = w1002.id
    finally:
        db.close()

    headers = get_auth_header("district.officer")
    res = client.get(f"/api/v1/works/{w1001_id}/similar", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "candidates" in data
    assert len(data["candidates"]) > 0

    candidate_ids = [c["candidateWorkId"] for c in data["candidates"]]
    assert w1002_id in candidate_ids

    match = next(c for c in data["candidates"] if c["candidateWorkId"] == w1002_id)
    assert match["similarityScore"] >= 70.0
    assert match["similarityScore"] <= 100.0
    assert match["workId"] == w1002_id
    assert "featureBreakdown" in match
    assert match["featureBreakdown"]["geoProximity"] >= 90.0

def test_seeded_duplicate_anganwadi_pair():
    db = SessionLocal()
    try:
        w1009 = db.query(Work).filter(Work.external_id == "W-1009").first()
        w1010 = db.query(Work).filter(Work.external_id == "W-1010").first()
        assert w1009 is not None and w1010 is not None
        w1009_id = w1009.id
        w1010_id = w1010.id
    finally:
        db.close()

    headers = get_auth_header("lucknow.officer")
    res = client.get(f"/api/v1/works/{w1009_id}/similar", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["candidates"]) > 0

    candidate_ids = [c["candidateWorkId"] for c in data["candidates"]]
    assert w1010_id in candidate_ids

    match = next(c for c in data["candidates"] if c["candidateWorkId"] == w1010_id)
    assert match["similarityScore"] >= 70.0
