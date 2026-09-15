import io
import os
import pytest
import piexif
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal, ensure_db_schema
from app.models import Work, Evidence, EvidenceFraudFlag
from app.core.storage import storage_backend
from app.services.evidence_fraud_service import EvidenceFraudService

client = TestClient(app)

ensure_db_schema()

def get_auth_token(username: str = "district.officer") -> str:
    res = client.post("/api/v1/auth/login", json={"username": username, "password": "demo-password"})
    assert res.status_code == 200
    return res.json()["accessToken"]

from PIL import Image, ImageDraw

def make_test_jpeg(lat=None, lon=None, date_str="2024:05:15 10:30:00", camera="iPhone 15 Pro", color=(100, 150, 200), seed=0):
    img = Image.new("RGB", (300, 200), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10 + (seed % 50), 10 + (seed % 50), 100 + (seed % 50), 100 + (seed % 50)], fill=(255 - (seed * 5 % 255), (seed * 10) % 255, 128))
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

def test_exact_hash_reuse_across_works():
    db: Session = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1001").first()
        w2 = db.query(Work).filter(Work.external_id == "W-1003").first()
        assert w1 and w2

        jpeg_bytes = make_test_jpeg(28.8521, 77.0934, color=(50, 100, 150))
        
        path1 = storage_backend.save_file(io.BytesIO(jpeg_bytes), "test_exact_1.jpg", subfolder="test_evidence")
        ev1 = Evidence(work_id=w1.id, file_name="test_exact_1.jpg", storage_key=path1, evidence_type="PHOTOGRAPH")
        db.add(ev1)
        db.commit()
        db.refresh(ev1)
        EvidenceFraudService.process_uploaded_evidence(ev1, storage_backend.get_full_path(ev1.storage_key), db)

        path2 = storage_backend.save_file(io.BytesIO(jpeg_bytes), "test_exact_2.jpg", subfolder="test_evidence")
        ev2 = Evidence(work_id=w2.id, file_name="test_exact_2.jpg", storage_key=path2, evidence_type="PHOTOGRAPH")
        db.add(ev2)
        db.commit()
        db.refresh(ev2)
        EvidenceFraudService.process_uploaded_evidence(ev2, storage_backend.get_full_path(ev2.storage_key), db)

        flags = EvidenceFraudService.run_fraud_check(ev2, db)
        exact_flags = [f for f in flags if f.flag_type == "EXACT_HASH_REUSE"]
        assert len(exact_flags) > 0
        assert exact_flags[0].severity == "CRITICAL"
        assert float(exact_flags[0].confidence_score) == 100.0
    finally:
        db.close()

def test_same_work_reupload_false_positive_guard():
    db: Session = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1

        jpeg_bytes = make_test_jpeg(28.8521, 77.0934, date_str="2024:08:20 15:45:00", color=(80, 120, 160), seed=42)
        
        path1 = storage_backend.save_file(io.BytesIO(jpeg_bytes), "test_same_work_1.jpg", subfolder="test_evidence")
        ev1 = Evidence(work_id=w1.id, file_name="test_same_work_1.jpg", storage_key=path1, evidence_type="PHOTOGRAPH")
        db.add(ev1)
        db.commit()
        db.refresh(ev1)
        EvidenceFraudService.process_uploaded_evidence(ev1, storage_backend.get_full_path(ev1.storage_key), db)

        path2 = storage_backend.save_file(io.BytesIO(jpeg_bytes), "test_same_work_2.jpg", subfolder="test_evidence")
        ev2 = Evidence(work_id=w1.id, file_name="test_same_work_2.jpg", storage_key=path2, evidence_type="PHOTOGRAPH")
        db.add(ev2)
        db.commit()
        db.refresh(ev2)
        EvidenceFraudService.process_uploaded_evidence(ev2, storage_backend.get_full_path(ev2.storage_key), db)

        flags = EvidenceFraudService.run_fraud_check(ev2, db)
        cross_work_flags = [f for f in flags if f.flag_type in ("EXACT_HASH_REUSE", "NEAR_DUPLICATE_PHASH", "GPS_TIMESTAMP_MATCH")]
        assert len(cross_work_flags) == 0, "Re-upload to same work should NOT raise cross-work fraud flag"
    finally:
        db.close()

def test_location_mismatch():
    db: Session = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1

        bengaluru_jpeg = make_test_jpeg(12.9716, 77.5946, color=(160, 80, 80))
        path = storage_backend.save_file(io.BytesIO(bengaluru_jpeg), "test_mismatch.jpg", subfolder="test_evidence")
        ev = Evidence(work_id=w1.id, file_name="test_mismatch.jpg", storage_key=path, evidence_type="PHOTOGRAPH")
        db.add(ev)
        db.commit()
        db.refresh(ev)
        EvidenceFraudService.process_uploaded_evidence(ev, storage_backend.get_full_path(ev.storage_key), db)

        flags = EvidenceFraudService.run_fraud_check(ev, db)
        mismatch_flags = [f for f in flags if f.flag_type == "LOCATION_MISMATCH"]
        assert len(mismatch_flags) > 0
        assert mismatch_flags[0].severity == "MEDIUM"
        assert float(mismatch_flags[0].distance_meters) > 500.0
    finally:
        db.close()

def test_stripped_exif_unverifiable():
    db: Session = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1004").first()
        assert w1

        img = Image.new("RGB", (200, 200), color=(100, 200, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()

        path = storage_backend.save_file(io.BytesIO(jpeg_bytes), "test_stripped.jpg", subfolder="test_evidence")
        ev = Evidence(work_id=w1.id, file_name="test_stripped.jpg", storage_key=path, evidence_type="PHOTOGRAPH")
        db.add(ev)
        db.commit()
        db.refresh(ev)
        EvidenceFraudService.process_uploaded_evidence(ev, storage_backend.get_full_path(ev.storage_key), db)

        flags = EvidenceFraudService.run_fraud_check(ev, db)
        stripped_flags = [f for f in flags if f.flag_type == "EXIF_STRIPPED_UNVERIFIABLE"]
        assert len(stripped_flags) > 0
        assert stripped_flags[0].severity == "LOW"
    finally:
        db.close()

def test_non_image_pdf_handling():
    db: Session = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1003").first()
        assert w1

        pdf_bytes = b"%PDF-1.4 Fake PDF Content for Test"
        path = storage_backend.save_file(io.BytesIO(pdf_bytes), "test_doc.pdf", subfolder="test_evidence")
        ev = Evidence(work_id=w1.id, file_name="test_doc.pdf", storage_key=path, evidence_type="DOCUMENT")
        db.add(ev)
        db.commit()
        db.refresh(ev)

        ev_processed = EvidenceFraudService.process_uploaded_evidence(ev, storage_backend.get_full_path(ev.storage_key), db)
        assert ev_processed.file_hash is not None
        assert ev_processed.phash is None
        assert ev_processed.exif_present is False
    finally:
        db.close()

def test_api_evidence_upload_and_fraud_flags_endpoint():
    token = get_auth_token("district.officer")
    headers = {"Authorization": f"Bearer {token}"}

    db: Session = SessionLocal()
    try:
        w1 = db.query(Work).filter(Work.external_id == "W-1001").first()
        assert w1
        work_id = w1.id
    finally:
        db.close()

    test_jpeg = make_test_jpeg(28.8521, 77.0934, date_str="2024:09:01 14:00:00", color=(90, 140, 190), seed=99)
    files = {"file": ("upload_api_test.jpg", test_jpeg, "image/jpeg")}
    data = {"evidence_type": "PHOTOGRAPH"}

    res = client.post(f"/api/v1/works/{work_id}/evidence", headers=headers, files=files, data=data)
    assert res.status_code in (200, 201), f"Upload failed: {res.text}"
    json_data = res.json()
    assert json_data["id"] is not None
    assert json_data["fileName"] == "upload_api_test.jpg"

    flags_res = client.get("/api/v1/evidence/fraud-flags", headers=headers)
    assert flags_res.status_code == 200
    flags_json = flags_res.json()
    assert isinstance(flags_json, list)
