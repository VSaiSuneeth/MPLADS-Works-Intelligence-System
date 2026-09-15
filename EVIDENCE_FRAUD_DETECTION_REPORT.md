# AI Evidence Photo Fraud & Cross-Work Duplicate Detection Engine
## Complete Technical Architecture, Algorithm Reference & QA Test Report
**System:** MPLADS Works Intelligence & Review System (SIH 2026)  
**Verification Status:** 42 / 42 Pytest Tests Passed (100%) | Frontend Build: 0 Errors | 10-Step E2E QA Matrix: 100% Passed

---

## 1. Executive Summary & Response to Judge's Question

### The Hackathon Judge Question:
> *"If I take a photo on my mobile phone with a geotag, upload it as evidence for my project, and another contractor takes that same photo off my phone and uploads it as evidence for their project — how would your system detect that as fraud? What algorithm are you using?"*

### Our System's Answer:
Our system implements a **multi-signal, explainable AI Evidence Fraud & Cross-Work Duplicate Engine**. When a photo is uploaded as work evidence, the system instantly computes its **SHA-256 byte hash**, **Perceptual Image Hash (pHash)**, and extracts **EXIF GPS coordinates, capture timestamp, and camera metadata**. It then cross-checks these signals against all existing evidence files in the database across all jurisdictions.

If contractor B uploads contractor A's photo to a different work, our system instantly flags the photo with **100% confidence** using three redundant signals:
1. **EXACT_HASH_REUSE (SHA-256)**: Detects identical byte content across works (CRITICAL severity, 100% confidence).
2. **NEAR_DUPLICATE_PHASH (Perceptual Hash)**: Detects re-compressed, cropped, or resized copies of the photo (CRITICAL/HIGH severity, $\le 8$ Hamming distance).
3. **GPS_TIMESTAMP_MATCH (EXIF Metadata)**: Detects matching EXIF GPS coordinates (within 5m) and capture timestamps (within 60s) pointing back to contractor A's project site.

---

## 2. 5 Multi-Layer Fraud Detection Signals

| Signal Code | Detection Method | Threshold / Rule | Severity | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `EXACT_HASH_REUSE` | SHA-256 hex digest comparison | Byte-for-byte identical file hash across different `work_id`s | **CRITICAL** | 100.0% |
| `NEAR_DUPLICATE_PHASH` | Perceptual Hash (pHash 64-bit DCT) | Hamming distance $d \le 8$ ($d \le 4 \rightarrow \text{CRITICAL}$, $d \le 8 \rightarrow \text{HIGH}$) | **CRITICAL / HIGH** | $100 \times (1 - \frac{d}{64})\%$ |
| `GPS_TIMESTAMP_MATCH` | EXIF Geotag + Timestamp | GPS distance $\le 5.0\text{m}$ AND capture time difference $\le 60\text{s}$ across works | **HIGH** | 90.0% |
| `LOCATION_MISMATCH` | EXIF Geotag vs Declared Site | Photo EXIF GPS distance $> 500\text{m}$ from work's declared site lat/lon | **MEDIUM** | 80.0% |
| `EXIF_STRIPPED_UNVERIFIABLE` | Provenance Audit | Missing EXIF header or stripped GPS metadata | **LOW** | 50.0% |

> [!NOTE]
> **False-Positive Guard:** Uploading a photo multiple times to the *same* work (`other.work_id == evidence.work_id`) is treated as a routine re-upload or revision and does **not** trigger a cross-work fraud alert.

---

## 3. Database Schema & Data Models

### Extended `evidence` Table:
- `file_hash`: `VARCHAR(64)` — SHA-256 hex digest of raw file bytes.
- `phash`: `VARCHAR(64)` — 64-bit perceptual hash (DCT-based).
- `exif_latitude`, `exif_longitude`: `NUMERIC(10, 6)` — Extracted EXIF GPS coordinates.
- `exif_captured_at`: `TIMESTAMP` — Hardware camera capture timestamp.
- `camera_model`: `VARCHAR(255)` — Device make and model (e.g. "Apple iPhone 15 Pro").
- `exif_present`, `gps_present`: `BOOLEAN` — Provenance indicators.
- `file_size_bytes`: `INTEGER` — File size in bytes.
- `uploaded_by_user_id`: `VARCHAR(36)` — User ID of uploading officer.

### `evidence_fraud_flags` Table:
- `id`: `VARCHAR(36)` — Primary key (UUID).
- `evidence_id`: `VARCHAR(36)` — Target evidence ID.
- `matched_evidence_id`: `VARCHAR(36)` — Matched evidence ID from another work.
- `matched_work_id`: `VARCHAR(36)` — Matched work ID from another project.
- `flag_type`: `VARCHAR(80)` — Fraud signal code.
- `severity`: `VARCHAR(30)` — `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`.
- `confidence_score`: `NUMERIC(5, 2)` — Confidence score percentage (0–100%).
- `distance_meters`: `NUMERIC(10, 2)` — Distance offset in meters (for location signals).
- `phash_distance`: `INTEGER` — Perceptual hash Hamming distance (0–64).
- `message`: `TEXT` — Human-readable explainable message.

---

## 4. API Endpoints

```http
POST /api/v1/works/{work_id}/evidence
Content-Type: multipart/form-data
Response: 201 Created (Returns EvidenceOut schema with embedded fraudFlags)

GET /api/v1/works/{work_id}/evidence
Response: 200 OK (List of Evidence items with fraudFlags and EXIF metadata)

GET /api/v1/works/{work_id}/evidence/{evidence_id}/file
Response: 200 OK (Serves raw image file bytes)

GET /api/v1/evidence/fraud-flags
Response: 200 OK (System-wide Audit Register of all evidence photo fraud flags)
```

---

## 5. Live Demonstration Scenario Seeded in Database

1. **Work W-1001 (Delhi Ward 4 Borewell Project)**:
   - Contains site photo `w1001_delhi_borewell.jpg` with EXIF GPS (`28.8521° N, 77.0934° E`) and capture date `2024-05-15 10:30:00`.
2. **Work W-1009 (Lucknow Anganwadi Project)**:
   - Contains fraudulent re-upload `w1009_fraudulent_reused_photo.jpg` using the exact same Delhi photo file.
   - **Triggered Signals:**
     - `EXACT_HASH_REUSE`: 100% confidence match to `W-1001`.
     - `NEAR_DUPLICATE_PHASH`: pHash distance 0/64 match to `W-1001`.
     - `GPS_TIMESTAMP_MATCH`: 0.0m GPS & 0s timestamp match to `W-1001`.
3. **Work W-1002 (Delhi Borewell Unit)**:
   - Contains evidence photo `w1002_mumbai_mismatch.jpg` with EXIF GPS in Mumbai (`19.0760° N, 72.8777° E`), 1,160 km away from Delhi.
   - **Triggered Signal:** `LOCATION_MISMATCH` (MEDIUM severity).

---

## 6. Verification & Test Matrix Results

### Automated Pytest Backend Test Suite: 42 / 42 PASSED (100%)
- `test_phase1_db.py` (2 passed)
- `test_phase2_auth.py` (4 passed)
- `test_phase3_ingestion.py` (3 passed)
- `test_phase4_works.py` (5 passed)
- `test_phase5_rules.py` (4 passed)
- `test_phase6_risk.py` (3 passed)
- `test_phase7_similarity.py` (2 passed)
- `test_phase8_dashboard.py` (2 passed)
- `test_phase12_cases_audit.py` (2 passed)
- `test_phase13_admin_import.py` (2 passed)
- `test_phase14_security_performance.py` (3 passed)
- `test_phase15_simulation.py` (4 passed)
- `test_phase16_evidence_fraud.py` (6 passed)

### Frontend Production Build: 1,607 Modules transformed in 3.08s (0 Errors)
### E2E Live Verification Script (`scratch/test_complete_button_flow.py`): 10 / 10 Steps Passed (100%)

---

## 7. Bug Fix Log Table

| Component | Root Cause | Resolution Applied | Status |
| :--- | :--- | :--- | :--- |
| `sqlite3.OperationalError` | Missing columns in pre-existing SQLite table | Added `ensure_db_schema()` to execute `ALTER TABLE evidence ADD COLUMN ...` idempotently | Fixed |
| `evidence_fraud_service.py` | Variable assignment typo inside SQLAlchemy `filter` | Changed to `EvidenceFraudFlag.evidence_id.in_(evidence_ids)` | Fixed |
| `ingestion.py` | Non-existent kwargs `source_id` & `source_record_hash` passed to `Work()` and `Payment()` | Cleaned keyword arguments in `IngestionService.process_csv_content` | Fixed |
| `schemas/work.py` | Pydantic `current_status` validation alias error in `WorkDetailOut` | Added `AliasChoices('stage', 'current_status')` and `populate_by_name=True` | Fixed |
| `schemas/work.py` | Raw bytes integer conversion error in `FraudFlagOut.phashDistance` | Added `@field_validator` with `int.from_bytes(v, "little")` support | Fixed |
