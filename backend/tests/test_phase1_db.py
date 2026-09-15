import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import inspect
from app.db.session import engine, SessionLocal

from app.db.base import Base
import app.models as models

def test_database_tables_created():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    expected_tables = [
        "users",
        "roles",
        "user_roles",
        "jurisdictions",
        "user_jurisdictions",
        "agencies",
        "works",
        "work_lifecycle_events",
        "payments",
        "progress_records",
        "evidence",
        "data_sources",
        "ingestion_runs",
        "data_quality_findings",
        "rules",
        "rule_versions",
        "risk_scores",
        "risk_signals",
        "similarity_candidates",
        "cases",
        "case_actions",
        "audit_logs",
    ]
    
    for table in expected_tables:
        assert table in table_names, f"Table '{table}' missing from database schema!"

def test_model_instantiation():
    db = SessionLocal()
    try:
        # Create test jurisdiction
        jurisdiction = models.Jurisdiction(
            state_name="Demo State",
            district_name="Demo District",
            district_code="DIST-999"
        )
        db.add(jurisdiction)
        db.commit()
        db.refresh(jurisdiction)
        
        assert jurisdiction.id is not None
        assert jurisdiction.district_code == "DIST-999"
        
        # Clean up test object
        db.delete(jurisdiction)
        db.commit()
    finally:
        db.close()

from sqlalchemy.exc import IntegrityError

def test_sqlite_foreign_key_enforcement():
    db = SessionLocal()
    try:
        invalid_work = models.Work(
            external_id="INVALID-FK-001",
            jurisdiction_id="NON_EXISTENT_JURISDICTION_ID_9999",
            title="Foreign Key Violation Work Test"
        )
        db.add(invalid_work)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_database_tables_created()
    test_model_instantiation()
    test_sqlite_foreign_key_enforcement()
    print("ALL PHASE 1 & PHASE 2 DB TESTS PASSED!")

