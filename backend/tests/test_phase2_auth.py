import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import close_all_sessions
from app.main import app
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models import User, Role, Jurisdiction
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    close_all_sessions()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Create test roles
        role_officer = Role(code="DISTRICT_OFFICER", name="District Monitoring Officer")
        role_admin = Role(code="ADMIN", name="System Administrator")
        db.add_all([role_officer, role_admin])

        # Create test jurisdictions
        dist_a = Jurisdiction(state_name="State A", district_name="District A", district_code="DIST-A")
        dist_b = Jurisdiction(state_name="State B", district_name="District B", district_code="DIST-B")
        db.add_all([dist_a, dist_b])
        db.commit()

        # Create test user
        user = User(
            username="test.officer",
            email="officer@district.gov.in",
            password_hash=get_password_hash("secure-password-123"),
            full_name="Test District Officer",
            is_active=True
        )
        user.roles.append(role_officer)
        user.jurisdictions.append(dist_a)
        
        db.add(user)
        db.commit()
    finally:
        db.close()

def test_login_success():
    response = client.post("/api/v1/auth/login", json={
        "username": "test.officer",
        "password": "secure-password-123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["user"]["username"] == "test.officer"
    assert "DISTRICT_OFFICER" in data["user"]["roles"]

def test_login_invalid_password():
    response = client.post("/api/v1/auth/login", json={
        "username": "test.officer",
        "password": "wrong-password"
    })
    assert response.status_code == 401

def test_get_me_authenticated():
    login_res = client.post("/api/v1/auth/login", json={
        "username": "test.officer",
        "password": "secure-password-123"
    })
    token = login_res.json()["accessToken"]

    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "test.officer"
    assert data["email"] == "officer@district.gov.in"

def test_get_me_unauthorized():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
