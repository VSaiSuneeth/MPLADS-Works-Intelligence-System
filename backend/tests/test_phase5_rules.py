import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.seed import seed_database
from app.models import Work
from app.services.rule_engine import RuleEngine

@pytest.fixture(scope="module", autouse=True)
def setup_seed():
    Base.metadata.drop_all(bind=engine)
    seed_database()

def test_rule_fin_pay_mismatch():
    db = SessionLocal()
    try:
        # W-1001 has 15% progress and 13.5 Lakh disbursement on 15 Lakh sanction (90% payment)
        w1001 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1001 is not None

        results = RuleEngine.evaluate_work(w1001, db)
        rule_codes = [r.rule_code for r in results]
        
        assert "FIN-PAY-001" in rule_codes
        fin_pay_rule = next(r for r in results if r.rule_code == "FIN-PAY-001")
        assert fin_pay_rule.severity == "CRITICAL"
        assert fin_pay_rule.contribution == 35.0
        assert "15.0%" in fin_pay_rule.what_happened
    finally:
        db.close()

def test_rule_dq_date_chronology():
    db = SessionLocal()
    try:
        # W-1004 has completion date 2023-02-10 before sanction date 2023-04-05
        w1004 = db.query(Work).filter(Work.external_id == "W-1004").first()
        assert w1004 is not None

        results = RuleEngine.evaluate_work(w1004, db)
        rule_codes = [r.rule_code for r in results]
        
        assert "DQ-DATE-001" in rule_codes
        dq_date_rule = next(r for r in results if r.rule_code == "DQ-DATE-001")
        assert dq_date_rule.severity == "HIGH"
        assert dq_date_rule.contribution == 25.0
    finally:
        db.close()

def test_rule_comp_evid_lacking():
    db = SessionLocal()
    try:
        # W-1012 is COMPLETED but has no evidence records uploaded
        w1012 = db.query(Work).filter(Work.external_id == "W-1012").first()
        assert w1012 is not None

        results = RuleEngine.evaluate_work(w1012, db)
        rule_codes = [r.rule_code for r in results]
        
        assert "COMP-EVID-001" in rule_codes
        comp_rule = next(r for r in results if r.rule_code == "COMP-EVID-001")
        assert comp_rule.severity == "HIGH"
    finally:
        db.close()

def test_rule_fin_amount_exceeded():
    db = SessionLocal()
    try:
        # W-1006 has expenditure 1.02 Crore on 85 Lakh sanction
        w1006 = db.query(Work).filter(Work.external_id == "W-1006").first()
        assert w1006 is not None

        results = RuleEngine.evaluate_work(w1006, db)
        rule_codes = [r.rule_code for r in results]
        
        assert "FIN-AMOUNT-001" in rule_codes
        fin_amt_rule = next(r for r in results if r.rule_code == "FIN-AMOUNT-001")
        assert fin_amt_rule.severity == "HIGH"
        assert fin_amt_rule.contribution == 30.0
    finally:
        db.close()
