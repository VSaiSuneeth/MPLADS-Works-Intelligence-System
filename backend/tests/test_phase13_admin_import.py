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

def get_auth_header(username: str = "admin.demo", password: str = "demo-password"):
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}

def test_imports_list_authenticated():
    headers = get_auth_header("admin.demo")
    res = client.get("/api/v1/imports", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_risk_recalculate_trigger():
    headers = get_auth_header("admin.demo")
    res = client.post("/api/v1/risk/recalculate", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "message" in data or "count" in data
