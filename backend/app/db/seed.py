import os
import sys
import io
import piexif
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import SessionLocal, engine, ensure_db_schema
from app.db.base import Base
from app.models import *
from app.core.security import get_password_hash
from app.core.storage import storage_backend
from app.services.ingestion import IngestionService
from app.services.evidence_fraud_service import EvidenceFraudService

def seed_demo_evidence(db):
    print("Seeding Demo Evidence Photos & Cross-Work Fraud Flags...")
    w1001 = db.query(Work).filter(Work.external_id == "W-1001").first()
    w1009 = db.query(Work).filter(Work.external_id == "W-1009").first()
    w1002 = db.query(Work).filter(Work.external_id == "W-1002").first()

    if not w1001 or not w1009:
        print("Works W-1001 / W-1009 not found for evidence fraud seeding.")
        return

    def make_exif_jpeg(lat=None, lon=None, date_str="2024:05:15 10:30:00", camera="iPhone 15 Pro", color=(120, 180, 220)):
        img = Image.new("RGB", (400, 300), color=color)
        buf = io.BytesIO()
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make] = "Apple"
        exif_dict["0th"][piexif.ImageIFD.Model] = camera
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_str.encode("utf-8")
        if lat is not None and lon is not None:
            def deg_to_dms(val):
                abs_val = abs(val)
                d = int(abs_val)
                m = int((abs_val - d) * 60)
                s = int(((abs_val - d) * 60 - m) * 60 * 100)
                return ((d, 1), (m, 1), (s, 100))
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = "N" if lat >= 0 else "S"
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = deg_to_dms(lat)
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = "E" if lon >= 0 else "W"
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = deg_to_dms(lon)
        exif_bytes = piexif.dump(exif_dict)
        img.save(buf, format="JPEG", exif=exif_bytes)
        return buf.getvalue()

    # 1. Delhi Borewell Original Photo (W-1001)
    delhi_jpeg = make_exif_jpeg(lat=28.8521, lon=77.0934, date_str="2024:05:15 10:30:00", camera="iPhone 15 Pro", color=(120, 180, 220))
    rel_path_1 = storage_backend.save_file(io.BytesIO(delhi_jpeg), "w1001_delhi_borewell.jpg", subfolder="evidence")
    
    ev1 = db.query(Evidence).filter(Evidence.work_id == w1001.id, Evidence.file_name == "w1001_delhi_borewell.jpg").first()
    if not ev1:
        ev1 = Evidence(
            work_id=w1001.id,
            file_name="w1001_delhi_borewell.jpg",
            storage_key=rel_path_1,
            evidence_type="PHOTOGRAPH"
        )
        db.add(ev1)
        db.commit()
        db.refresh(ev1)
    EvidenceFraudService.process_uploaded_evidence(ev1, storage_backend.get_full_path(ev1.storage_key), db)

    # 2. Fraudulent Re-upload of same Delhi photo to Lucknow Anganwadi work (W-1009)
    rel_path_2 = storage_backend.save_file(io.BytesIO(delhi_jpeg), "w1009_fraudulent_reused_photo.jpg", subfolder="evidence")
    ev2 = db.query(Evidence).filter(Evidence.work_id == w1009.id, Evidence.file_name == "w1009_fraudulent_reused_photo.jpg").first()
    if not ev2:
        ev2 = Evidence(
            work_id=w1009.id,
            file_name="w1009_fraudulent_reused_photo.jpg",
            storage_key=rel_path_2,
            evidence_type="PHOTOGRAPH"
        )
        db.add(ev2)
        db.commit()
        db.refresh(ev2)
    EvidenceFraudService.process_uploaded_evidence(ev2, storage_backend.get_full_path(ev2.storage_key), db)

    # Run cross-work fraud check on both
    EvidenceFraudService.run_fraud_check(ev1, db)
    EvidenceFraudService.run_fraud_check(ev2, db)

    # 3. Location Mismatch Evidence on W-1002 (EXIF GPS in Mumbai, 1100km away from Delhi)
    if w1002:
        mumbai_jpeg = make_exif_jpeg(lat=19.0760, lon=72.8777, date_str="2024:05:16 11:00:00", camera="Samsung S23", color=(200, 100, 100))
        rel_path_3 = storage_backend.save_file(io.BytesIO(mumbai_jpeg), "w1002_mumbai_mismatch.jpg", subfolder="evidence")
        ev3 = db.query(Evidence).filter(Evidence.work_id == w1002.id, Evidence.file_name == "w1002_mumbai_mismatch.jpg").first()
        if not ev3:
            ev3 = Evidence(
                work_id=w1002.id,
                file_name="w1002_mumbai_mismatch.jpg",
                storage_key=rel_path_3,
                evidence_type="PHOTOGRAPH"
            )
            db.add(ev3)
            db.commit()
            db.refresh(ev3)
        EvidenceFraudService.process_uploaded_evidence(ev3, storage_backend.get_full_path(ev3.storage_key), db)
        EvidenceFraudService.run_fraud_check(ev3, db)

def seed_database():
    print("Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)
    ensure_db_schema()
    db = SessionLocal()

    try:
        # 1. Seed Roles
        print("Seeding System Roles...")
        roles_def = [
            ("DISTRICT_OFFICER", "District Monitoring Officer"),
            ("AUDITOR", "State / Ministry Auditor"),
            ("STATE_MONITOR", "State Level Monitoring Officer"),
            ("ADMIN", "System Administrator"),
        ]
        role_map = {}
        for code, name in roles_def:
            role = db.query(Role).filter(Role.code == code).first()
            if not role:
                role = Role(code=code, name=name)
                db.add(role)
                db.commit()
                db.refresh(role)
            role_map[code] = role

        # 2. Seed Jurisdictions
        print("Seeding Jurisdictions...")
        jurisdictions_def = [
            ("Delhi", "North Delhi District", "DIST-001"),
            ("Uttar Pradesh", "Lucknow District", "DIST-002"),
            ("Karnataka", "Bengaluru Urban District", "DIST-003"),
        ]
        jurisdiction_map = {}
        for state, district, code in jurisdictions_def:
            jur = db.query(Jurisdiction).filter(Jurisdiction.district_code == code).first()
            if not jur:
                jur = Jurisdiction(state_name=state, district_name=district, district_code=code)
                db.add(jur)
                db.commit()
                db.refresh(jur)
            jurisdiction_map[code] = jur

        # 3. Seed Users
        print("Seeding User Accounts...")
        users_def = [
            ("district.officer", "officer.delhi@mplads.gov.in", "Delhi Nodal Officer", ["DISTRICT_OFFICER"], ["DIST-001"]),
            ("lucknow.officer", "officer.lucknow@mplads.gov.in", "Lucknow Nodal Officer", ["DISTRICT_OFFICER"], ["DIST-002"]),
            ("bengaluru.officer", "officer.blr@mplads.gov.in", "Bengaluru Nodal Officer", ["DISTRICT_OFFICER"], ["DIST-003"]),
            ("auditor.demo", "auditor@mplads.gov.in", "Senior Auditor", ["AUDITOR"], ["DIST-001", "DIST-002", "DIST-003"]),
            ("admin.demo", "admin@mplads.gov.in", "System Administrator", ["ADMIN"], ["DIST-001", "DIST-002", "DIST-003"]),
        ]

        for username, email, full_name, r_codes, j_codes in users_def:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                user = User(
                    username=username,
                    email=email,
                    password_hash=get_password_hash("demo-password"),
                    full_name=full_name,
                    is_active=True
                )
                for r_code in r_codes:
                    user.roles.append(role_map[r_code])
                for j_code in j_codes:
                    user.jurisdictions.append(jurisdiction_map[j_code])
                db.add(user)
                db.commit()

        # 4. Import Seed Works CSV
        seed_csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "seed_works.csv"))
        if os.path.exists(seed_csv_path):
            print(f"Importing Seed Works CSV from {seed_csv_path}...")
            with open(seed_csv_path, "r", encoding="utf-8") as f:
                csv_content = f.read()
            run = IngestionService.process_csv_content(csv_content, "Prototype Controlled Seed Dataset", db)
            print(f"Ingestion Completed: Accepted {run.accepted_rows} rows, Rejected {run.rejected_rows} rows.")
        else:
            print(f"Warning: Seed CSV path '{seed_csv_path}' not found!")

        # 5. Seed Demo Evidence Photos and Fraud Flags
        seed_demo_evidence(db)

        print("Database Seeding Completed Successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
