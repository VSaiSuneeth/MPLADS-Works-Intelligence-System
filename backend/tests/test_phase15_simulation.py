import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.work import Work
from app.services.simulation_service import SimulationService
from app.schemas.simulation import SimulationRequest

client = TestClient(app)

def get_auth_token(username: str = "district.officer") -> str:
    res = client.post("/api/v1/auth/login", json={"username": username, "password": "demo-password"})
    assert res.status_code == 200
    return res.json()["accessToken"]

def test_simulation_service_existing_project():
    db: Session = SessionLocal()
    try:
        work = db.query(Work).first()
        assert work is not None

        req = SimulationRequest(
            work_id=work.id,
            project_cost=float(work.sanction_amount or 1000000.0),
            expenditure_amount=1200000.0,  # Simulate expenditure increase
            completion_pct=20.0,
            sanction_date="2023-01-01",
            expected_completion_date="2023-12-31"
        )

        res = SimulationService.simulate(db, req)
        assert res.workId == work.id
        assert res.currentScenario is not None
        assert res.simulatedScenario is not None
        assert res.impactDelta is not None
        assert isinstance(res.impactDelta.overallScoreDelta, float)
        assert res.simulatedScenario.financialRiskScore >= 0.0
    finally:
        db.close()

def test_simulation_service_synthetic_project():
    db: Session = SessionLocal()
    try:
        req = SimulationRequest(
            title="Proposed Community Center",
            category="Community Facilities",
            project_cost=2500000.0,
            expenditure_amount=500000.0,
            completion_pct=10.0,
            sanction_date="2024-01-01",
            expected_completion_date="2025-06-30"
        )

        res = SimulationService.simulate(db, req)
        assert res.workId is None
        assert res.workTitle == "Proposed Community Center"
        assert res.simulatedScenario.completionPct == 10.0
        assert res.simulatedScenario.expenditureRatioPct == 20.0
    finally:
        db.close()

def test_simulation_edge_cases():
    db: Session = SessionLocal()
    try:
        # Edge case 1: 100% completion, zero cost overrun
        req_completed = SimulationRequest(
            title="Completed Library Project",
            category="Education Infrastructure",
            project_cost=1000000.0,
            expenditure_amount=950000.0,
            completion_pct=100.0,
            sanction_date="2023-01-01",
            expected_completion_date="2023-12-31",
            current_status="COMPLETED"
        )
        res_comp = SimulationService.simulate(db, req_completed)
        assert res_comp.simulatedScenario.completionPct == 100.0
        assert res_comp.simulatedScenario.delayRiskScore == 0.0

        # Edge case 2: Cost reduced below expenditure (150% expenditure ratio)
        req_overrun = SimulationRequest(
            title="Severe Overrun Proposal",
            category="Roads & Bridges",
            project_cost=1000000.0,
            expenditure_amount=1500000.0,
            completion_pct=30.0,
            sanction_date="2023-01-01",
            expected_completion_date="2023-12-31"
        )
        res_overrun = SimulationService.simulate(db, req_overrun)
        assert res_overrun.simulatedScenario.costOverrunPct == 50.0
        assert res_overrun.simulatedScenario.financialRiskScore >= 50.0
    finally:
        db.close()

def test_simulation_api_endpoints():
    token = get_auth_token("district.officer")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test projects list for dropdown
    p_res = client.get("/api/v1/simulation/projects", headers=headers)
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert "items" in p_data
    assert p_data["total"] > 0

    first_work_id = p_data["items"][0]["workId"]

    # 2. Test base project fetch
    b_res = client.get(f"/api/v1/simulation/base-project/{first_work_id}", headers=headers)
    assert b_res.status_code == 200
    b_data = b_res.json()
    assert b_data["workId"] == first_work_id
    assert "projectCost" in b_data

    # 3. Test run simulation endpoint
    sim_payload = {
        "workId": first_work_id,
        "projectCost": b_data["projectCost"] * 1.2,
        "expenditureAmount": b_data["expenditureAmount"] + 100000.0,
        "completionPct": max(5.0, b_data["completionPct"]),
        "expectedCompletionDate": "2026-12-31"
    }
    run_res = client.post("/api/v1/simulation/run", json=sim_payload, headers=headers)
    assert run_res.status_code == 200
    r_data = run_res.json()
    assert r_data["workId"] == first_work_id
    assert "currentScenario" in r_data
    assert "simulatedScenario" in r_data
    assert "impactDelta" in r_data
