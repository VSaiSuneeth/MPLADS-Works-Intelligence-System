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

def test_case_creation_and_state_transition():
    headers = get_auth_header("district.officer")
    db = SessionLocal()
    try:
        work = db.query(Work).first()
        assert work is not None
        work_id = work.id
        work_ext_id = work.external_id
    finally:
        db.close()

    # 1. Create Case
    res_create = client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "workId": work_id,
            "priority": "HIGH",
            "summary": "Potential financial anomaly requiring physical verification",
            "initialNotes": "Initiated formal review case"
        }
    )
    assert res_create.status_code in [200, 201]
    case_data = res_create.json()
    resp_work_id = case_data.get("workId") or case_data.get("work_id")
    assert resp_work_id == work_id
    assert case_data["status"] == "DETECTED"

    case_id = case_data["id"]

    # 2. Add Action (Request Clarification)
    res_action = client.post(
        f"/api/v1/cases/{case_id}/actions",
        headers=headers,
        json={
            "actionType": "REQUEST_CLARIFICATION",
            "newStatus": "CLARIFICATION_REQUESTED",
            "notes": "Requesting official response from executing agency regarding physical completion certificate."
        }
    )
    assert res_action.status_code == 200
    updated_data = res_action.json()
    assert updated_data["status"] == "CLARIFICATION_REQUESTED"
    assert len(updated_data["actions"]) >= 2

def test_audit_logs_retrieval():
    headers = get_auth_header("auditor.demo")
    res = client.get("/api/v1/audit-logs", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] > 0
    case_logs = [l for l in data["items"] if (l.get("entityType") or l.get("entity_type")) == "Case"]
    assert len(case_logs) > 0

def test_case_invalid_state_transition_409():
    headers = get_auth_header("district.officer")
    db = SessionLocal()
    try:
        work = db.query(Work).first()
        work_id = work.id
    finally:
        db.close()

    res_create = client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "workId": work_id,
            "priority": "MEDIUM",
            "summary": "State machine transition conflict test",
            "initialNotes": "Opening test case for 409 check"
        }
    )
    case_data = res_create.json()
    case_id = case_data["id"]

    res_close = client.post(
        f"/api/v1/cases/{case_id}/actions",
        headers=headers,
        json={
            "actionType": "CLOSE_CASE",
            "newStatus": "CLOSED",
            "notes": "Closing case officially."
        }
    )
    assert res_close.status_code == 200
    assert res_close.json()["status"] == "CLOSED"

    res_invalid = client.post(
        f"/api/v1/cases/{case_id}/actions",
        headers=headers,
        json={
            "actionType": "REOPEN_ATTEMPT",
            "newStatus": "UNDER_REVIEW",
            "notes": "Attempting invalid transition on closed case."
        }
    )
    assert res_invalid.status_code == 409
    assert res_invalid.json()["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"

