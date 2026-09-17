import os
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.seed import seed_database
from app.services.esakshi_adapter import EsakshiAdapter
from app.models.work import Work
from app.models.ingestion import DataSource

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_esakshi_header_normalization():
    raw_csv = (
        "Work ID,Work Description,Category,Sanction Amount (Rs),District Name,District Code\n"
        "TEST-E-001,Test Community Project,Water Supply,500000.00,Indore District,DIST-002\n"
    )
    norm = EsakshiAdapter.normalize_csv_content(raw_csv)
    assert "external_id" in norm
    assert "title" in norm
    assert "sanction_amount" in norm
    assert "district_code" in norm
    assert "TEST-E-001" in norm

def test_esakshi_ingestion_process(db_session: Session):
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "esakshi_sample_export.csv")
    assert os.path.exists(fixture_path), "eSAKSHI sample CSV fixture must exist"
    
    with open(fixture_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    run = EsakshiAdapter.process_esakshi_ingestion(
        raw_csv_content=raw_content,
        source_name="eSAKSHI Official Public Export 2024",
        db=db_session,
        is_official=True
    )

    assert run.status == "COMPLETED"
    assert run.accepted_rows == 3
    assert run.rejected_rows == 0

    # Verify provenance data source
    ds = db_session.query(DataSource).filter(DataSource.id == run.source_id).first()
    assert ds is not None
    assert ds.source_type == "OFFICIAL_PUBLIC"
    assert ds.is_official is True

    # Verify ingested work record
    work = db_session.query(Work).filter(Work.external_id == "ESAKSHI-IND-2024-001").first()
    assert work is not None
    assert work.title == "Construction of Community Drinking Water Facility in Ward 12"
    assert float(work.sanction_amount) == 750000.00
    assert float(work.latitude) == 22.7196
