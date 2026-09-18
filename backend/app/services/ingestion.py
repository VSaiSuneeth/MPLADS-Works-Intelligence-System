import csv
import hashlib
import io
from datetime import datetime, date, timezone
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.orm import Session

from app.models.jurisdiction import Jurisdiction
from app.models.agency import Agency
from app.models.work import Work, WorkLifecycleEvent, Payment, ProgressRecord, Evidence
from app.models.ingestion import DataSource, IngestionRun, DataQualityFinding

def parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str or not date_str.strip():
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            pass
    return None

def parse_float(val: Optional[str]) -> Optional[float]:
    if not val or not str(val).strip():
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except ValueError:
        return None

def compute_row_hash(row: Dict[str, str]) -> str:
    serialized = "|".join(f"{k}:{row[k]}" for k in sorted(row.keys()) if row[k] is not None)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

class IngestionService:
    @staticmethod
    def process_csv_content(csv_content: str, source_name: str, db: Session) -> IngestionRun:
        # 1. Ensure DataSource exists
        data_source = db.query(DataSource).filter(DataSource.name == source_name).first()
        if not data_source:
            data_source = DataSource(
                name=source_name,
                source_type="CONTROLLED_PROTOTYPE",
                authority_label="Prototype Import Authority",
                is_official=False
            )
            db.add(data_source)
            db.commit()
            db.refresh(data_source)

        # 2. Create IngestionRun
        ingestion_run = IngestionRun(
            source_id=data_source.id,
            file_name=source_name,
            status="PROCESSING",
            started_at=datetime.now(timezone.utc),
            transformation_version="v1.0.0"
        )
        db.add(ingestion_run)
        db.commit()
        db.refresh(ingestion_run)

        # 3. Read CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        accepted = 0
        rejected = 0
        errors = []

        for row_idx, row in enumerate(reader, start=2): # header is row 1
            try:
                ext_id = row.get("external_id", "").strip()
                title = row.get("title", "").strip()
                dist_code = row.get("district_code", "").strip()
                dist_name = row.get("district_name", "Demo District").strip()
                state_name = row.get("state_name", "Demo State").strip()

                if not ext_id or not title or not dist_code:
                    rejected += 1
                    errors.append({
                        "row": row_idx,
                        "error": "Missing mandatory identifier: external_id, title, or district_code"
                    })
                    continue

                # Ensure Jurisdiction
                jurisdiction = db.query(Jurisdiction).filter(Jurisdiction.district_code == dist_code).first()
                if not jurisdiction:
                    jurisdiction = Jurisdiction(
                        state_name=state_name,
                        district_name=dist_name,
                        district_code=dist_code
                    )
                    db.add(jurisdiction)
                    db.commit()
                    db.refresh(jurisdiction)

                # Ensure Agency
                agency_name = row.get("agency_name", "").strip()
                agency = None
                if agency_name:
                    agency = db.query(Agency).filter(Agency.name == agency_name, Agency.jurisdiction_id == jurisdiction.id).first()
                    if not agency:
                        agency = Agency(
                            name=agency_name,
                            agency_type=row.get("agency_type", "Government Agency").strip(),
                            jurisdiction_id=jurisdiction.id
                        )
                        db.add(agency)
                        db.commit()
                        db.refresh(agency)

                # Parse dates & numbers
                rec_date = parse_date(row.get("recommendation_date"))
                sanc_date = parse_date(row.get("sanction_date"))
                comp_date = parse_date(row.get("completion_date"))
                est_cost = parse_float(row.get("estimated_cost"))
                sanc_amt = parse_float(row.get("sanction_amount"))
                exp_amt = parse_float(row.get("expenditure_amount"))
                lat = parse_float(row.get("latitude"))
                lon = parse_float(row.get("longitude"))
                status = row.get("current_status", "EXECUTION").strip()
                row_hash = compute_row_hash(row)

                # Create or Update Work
                work = db.query(Work).filter(Work.external_id == ext_id, Work.jurisdiction_id == jurisdiction.id).first()
                if not work:
                    work = Work(
                        external_id=ext_id,
                        jurisdiction_id=jurisdiction.id,
                        title=title,
                        description=row.get("description", "").strip(),
                        category=row.get("category", "General").strip(),
                        location_text=row.get("location_text", "").strip(),
                        latitude=lat,
                        longitude=lon,
                        estimated_cost=est_cost,
                        sanction_amount=sanc_amt,
                        expenditure_amount=exp_amt,
                        current_status=status,
                        recommendation_date=rec_date,
                        sanction_date=sanc_date,
                        completion_date=comp_date,
                        agency_id=agency.id if agency else None
                    )
                    db.add(work)
                    db.commit()
                    db.refresh(work)
                else:
                    # Update fields
                    work.title = title
                    work.description = row.get("description", "").strip()
                    work.category = row.get("category", work.category)
                    work.location_text = row.get("location_text", work.location_text)
                    if lat is not None:
                        work.latitude = lat
                    if lon is not None:
                        work.longitude = lon
                    work.estimated_cost = est_cost or work.estimated_cost
                    work.sanction_amount = sanc_amt or work.sanction_amount
                    work.expenditure_amount = exp_amt or work.expenditure_amount
                    work.current_status = status
                    db.commit()

                # Add Progress record if present
                prog_val = parse_float(row.get("reported_progress"))
                if prog_val is not None:
                    db.add(ProgressRecord(
                        work_id=work.id,
                        progress_percent=prog_val,
                        # The source feed has no progress-report date. Do not
                        # fabricate one from sanction/completion dates.
                        reported_date=None,
                        status_text=f"Reported progress {prog_val}%",
                        source_id=data_source.id
                    ))

                # Add Payment record if present
                if exp_amt and exp_amt > 0:
                    db.add(Payment(
                        work_id=work.id,
                        payment_reference=f"PAY-{ext_id}-01",
                        # The source feed has no payment date. Keep this
                        # unrecorded rather than representing it as the
                        # sanction date in the lifecycle timeline.
                        payment_date=None,
                        amount=exp_amt,
                        payee_name=agency_name or "Executing Agency",
                        source_id=data_source.id
                    ))

                # Add Evidence record if present
                ev_file = row.get("evidence_file_name", "").strip()
                if ev_file:
                    has_cert = row.get("has_completion_certificate", "false").strip().lower() == "true"
                    db.add(Evidence(
                        work_id=work.id,
                        evidence_type=row.get("evidence_type", "PHOTOGRAPH").strip(),
                        file_name=ev_file,
                        storage_key=None,
                        source_url=None,
                        metadata_json={"hasCompletionCertificate": has_cert},
                        availability_status="METADATA_ONLY"
                    ))

                # DQ Check 1: Missing Mandatory Agency
                if not agency:
                    db.add(DataQualityFinding(
                        work_id=work.id,
                        ingestion_run_id=ingestion_run.id,
                        field_name="agency_name",
                        finding_type="DQ_MISSING_AGENCY",
                        severity="MEDIUM",
                        message="Implementing agency field is missing from import record.",
                        evidence_json={"external_id": ext_id}
                    ))

                # DQ Check 2: Invalid Date Order
                if sanc_date and comp_date and comp_date < sanc_date:
                    db.add(DataQualityFinding(
                        work_id=work.id,
                        ingestion_run_id=ingestion_run.id,
                        field_name="completion_date",
                        finding_type="DQ_DATE_ORDER_INVALID",
                        severity="HIGH",
                        message=f"Completion date ({comp_date}) precedes sanction date ({sanc_date}).",
                        evidence_json={"sanction_date": str(sanc_date), "completion_date": str(comp_date)}
                    ))

                accepted += 1
                db.commit()
            except Exception as e:
                db.rollback()
                rejected += 1
                print(f"Row {row_idx} error: {e}")
                errors.append({"row": row_idx, "error": str(e)})

        ingestion_run.total_rows = accepted + rejected
        ingestion_run.accepted_rows = accepted
        ingestion_run.rejected_rows = rejected
        ingestion_run.status = "COMPLETED" if rejected == 0 else "PARTIAL_SUCCESS"
        ingestion_run.completed_at = datetime.now(timezone.utc)
        ingestion_run.error_summary = {"errors": errors}
        db.commit()
        db.refresh(ingestion_run)

        return ingestion_run
