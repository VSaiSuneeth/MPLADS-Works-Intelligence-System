import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.ingestion import DataSource, IngestionRun
from app.services.ingestion import IngestionService

class EsakshiAdapter:
    """
    Data Mapping Adapter for MoSPI eSAKSHI Public Export CSV Format.
    Transforms raw eSAKSHI column headers into standard MPLADS schema definitions
    while tracking provenance metadata (OFFICIAL_PUBLIC vs SYNTHETIC_DEMO).
    """

    # Official eSAKSHI to MPLADS Standard Schema Column Mapping
    COLUMN_MAP = {
        "work_id": "external_id",
        "work id": "external_id",
        "work_description": "title",
        "work description": "title",
        "work_title": "title",
        "district_code": "district_code",
        "district code": "district_code",
        "district_name": "district_name",
        "district name": "district_name",
        "state_name": "state_name",
        "state name": "state_name",
        "category": "category",
        "work_category": "category",
        "sanction_amount": "sanction_amount",
        "sanction amount (rs)": "sanction_amount",
        "sanction amount": "sanction_amount",
        "expenditure_amount": "expenditure_amount",
        "expenditure amount (rs)": "expenditure_amount",
        "agency_name": "agency_name",
        "implementing_agency": "agency_name",
        "implementing agency": "agency_name",
        "sanction_date": "sanction_date",
        "sanction date": "sanction_date",
        "completion_date": "completion_date",
        "target completion date": "completion_date",
        "status": "status",
        "current_status": "status",
        "latitude": "latitude",
        "longitude": "longitude",
        "location": "location_text",
        "location_text": "location_text"
    }

    @classmethod
    def normalize_csv_content(cls, raw_csv_content: str) -> str:
        """
        Normalizes eSAKSHI CSV headers and data types to standard MPLADS CSV layout.
        """
        reader = csv.DictReader(io.StringIO(raw_csv_content))
        if not reader.fieldnames:
            return raw_csv_content

        # Build header mapping
        normalized_headers = []
        header_map = {}
        for original in reader.fieldnames:
            key_clean = original.strip().lower()
            target = cls.COLUMN_MAP.get(key_clean, key_clean.replace(" ", "_"))
            header_map[original] = target
            if target not in normalized_headers:
                normalized_headers.append(target)

        # Output normalized CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=normalized_headers)
        writer.writeheader()

        for row in reader:
            norm_row = {}
            for orig_k, orig_v in row.items():
                target_k = header_map.get(orig_k, orig_k)
                norm_row[target_k] = orig_v.strip() if orig_v else ""
            writer.writerow(norm_row)

        return output.getvalue()

    @classmethod
    def process_esakshi_ingestion(
        cls,
        raw_csv_content: str,
        source_name: str,
        db: Session,
        is_official: bool = True
    ) -> IngestionRun:
        """
        Ingests eSAKSHI CSV export with full provenance metadata recording.
        """
        # 1. Ensure DataSource with OFFICIAL_PUBLIC provenance metadata
        data_source = db.query(DataSource).filter(DataSource.name == source_name).first()
        if not data_source:
            data_source = DataSource(
                name=source_name,
                source_type="OFFICIAL_PUBLIC" if is_official else "CONTROLLED_PROTOTYPE",
                authority_label="MoSPI eSAKSHI Official Portal" if is_official else "Controlled Prototype Feed",
                is_official=is_official
            )
            db.add(data_source)
            db.commit()
            db.refresh(data_source)

        # 2. Normalize eSAKSHI CSV
        normalized_csv = cls.normalize_csv_content(raw_csv_content)

        # 3. Delegate to IngestionService
        return IngestionService.process_csv_content(normalized_csv, source_name, db)
