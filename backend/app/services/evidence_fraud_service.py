import os
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from PIL import Image
import imagehash
from sqlalchemy.orm import Session

from app.models.work import Work, Evidence, EvidenceFraudFlag
from app.core.config import settings
from app.services.exif_extractor import extract_exif_metadata
from app.services.geo_utils import haversine_distance_meters

def compute_file_sha256(file_path: str) -> str:
    """Computes SHA-256 hex digest of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_phash(file_path: str) -> Optional[str]:
    """Computes perceptual hash (pHash) for an image file."""
    try:
        with Image.open(file_path) as img:
            return str(imagehash.phash(img))
    except Exception:
        return None

def compute_phash_distance(hash1_str: str, hash2_str: str) -> int:
    """Computes Hamming distance between two hex pHash strings."""
    try:
        h1 = imagehash.hex_to_hash(hash1_str)
        h2 = imagehash.hex_to_hash(hash2_str)
        return h1 - h2
    except Exception:
        return 999

class EvidenceFraudService:
    @staticmethod
    def process_uploaded_evidence(evidence: Evidence, file_path: str, db: Session) -> Evidence:
        """
        Populate file_hash, phash, file_size_bytes, and EXIF metadata for an uploaded evidence file.
        """
        if os.path.exists(file_path):
            evidence.file_size_bytes = os.path.getsize(file_path)
            evidence.file_hash = compute_file_sha256(file_path)

            ext = os.path.splitext(file_path)[1].lower()
            if ext in ('.jpg', '.jpeg', '.png', '.webp'):
                evidence.phash = compute_phash(file_path)

                exif = extract_exif_metadata(file_path)
                if exif:
                    if exif.get("latitude") is not None and exif.get("longitude") is not None:
                        evidence.exif_latitude = float(exif["latitude"])
                        evidence.exif_longitude = float(exif["longitude"])
                        evidence.gps_present = True
                    else:
                        evidence.gps_present = False

                    if exif.get("captured_at"):
                        captured_dt = exif["captured_at"]
                        if captured_dt.tzinfo is None:
                            captured_dt = captured_dt.replace(tzinfo=timezone.utc)
                        evidence.exif_captured_at = captured_dt
                        evidence.captured_at = captured_dt

                    if exif.get("camera_model"):
                        evidence.camera_model = str(exif["camera_model"])

                    evidence.exif_present = not exif.get("is_estimated", True)

            db.commit()
            db.refresh(evidence)

        return evidence

    @staticmethod
    def run_fraud_check(evidence: Evidence, db: Session) -> List[EvidenceFraudFlag]:
        """
        Compare target evidence against all other evidence items in the database
        and persist/return detected fraud flags.
        """
        # Delete old flags for this evidence item before re-checking
        db.query(EvidenceFraudFlag).filter(EvidenceFraudFlag.evidence_id == evidence.id).delete()
        db.commit()

        new_flags: List[EvidenceFraudFlag] = []
        target_work = db.query(Work).filter(Work.id == evidence.work_id).first()

        # Query all other evidence records in the database
        other_evidence_list = db.query(Evidence).filter(Evidence.id != evidence.id).all()

        for other in other_evidence_list:
            # FALSE-POSITIVE GUARD: Same work_id is a re-upload, not cross-work fraud!
            if other.work_id == evidence.work_id:
                continue

            other_work = db.query(Work).filter(Work.id == other.work_id).first()
            other_title = other_work.title if other_work else "Other Work"
            other_ext_id = other_work.external_id if other_work else "N/A"

            # 1. Exact SHA-256 Hash Reuse across different works
            if evidence.file_hash and other.file_hash and evidence.file_hash == other.file_hash:
                hash_short = evidence.file_hash[:12]
                flag = EvidenceFraudFlag(
                    evidence_id=evidence.id,
                    matched_evidence_id=other.id,
                    matched_work_id=other.work_id,
                    flag_type="EXACT_HASH_REUSE",
                    severity="CRITICAL",
                    confidence_score=100.0,
                    message=f"Identical image file (SHA-256: {hash_short}...) was reused as evidence for work '{other_title}' (ID: {other_ext_id})."
                )
                new_flags.append(flag)
                
                # Also create reciprocal flag on other evidence if not present
                existing_recip = db.query(EvidenceFraudFlag).filter(
                    EvidenceFraudFlag.evidence_id == other.id,
                    EvidenceFraudFlag.matched_evidence_id == evidence.id,
                    EvidenceFraudFlag.flag_type == "EXACT_HASH_REUSE"
                ).first()
                if not existing_recip:
                    db.add(EvidenceFraudFlag(
                        evidence_id=other.id,
                        matched_evidence_id=evidence.id,
                        matched_work_id=evidence.work_id,
                        flag_type="EXACT_HASH_REUSE",
                        severity="CRITICAL",
                        confidence_score=100.0,
                        message=f"Identical image file (SHA-256: {hash_short}...) was reused as evidence for work '{target_work.title if target_work else 'Work'}' (ID: {target_work.external_id if target_work else 'N/A'})."
                    ))

            # 2. Near-Duplicate Perceptual Hash (pHash) Match
            elif evidence.phash and other.phash:
                dist = compute_phash_distance(evidence.phash, other.phash)
                threshold = getattr(settings, 'EVIDENCE_PHASH_THRESHOLD', 8)
                if dist <= threshold:
                    severity = "CRITICAL" if dist <= 4 else "HIGH"
                    conf = round(100.0 * (1.0 - (dist / 64.0)), 1)
                    flag = EvidenceFraudFlag(
                        evidence_id=evidence.id,
                        matched_evidence_id=other.id,
                        matched_work_id=other.work_id,
                        flag_type="NEAR_DUPLICATE_PHASH",
                        severity=severity,
                        confidence_score=conf,
                        phash_distance=dist,
                        message=f"Perceptual image match (pHash distance: {dist}/64) indicates re-compressed or cropped duplicate photo reused from work '{other_title}' (ID: {other_ext_id})."
                    )
                    new_flags.append(flag)

            # 3. Same EXIF GPS + Capture Timestamp Match
            if (evidence.gps_present and other.gps_present and 
                evidence.exif_latitude is not None and evidence.exif_longitude is not None and
                other.exif_latitude is not None and other.exif_longitude is not None and
                evidence.exif_captured_at and other.exif_captured_at):
                
                d_m = haversine_distance_meters(
                    float(evidence.exif_latitude), float(evidence.exif_longitude),
                    float(other.exif_latitude), float(other.exif_longitude)
                )
                dt_s = abs((evidence.exif_captured_at - other.exif_captured_at).total_seconds())

                gps_thresh = getattr(settings, 'EVIDENCE_GPS_MATCH_METERS', 5.0)
                time_thresh = getattr(settings, 'EVIDENCE_TIMESTAMP_MATCH_SECONDS', 60)

                if d_m <= gps_thresh and dt_s <= time_thresh:
                    # Check if already covered by exact hash or phash
                    already_flagged = any(f.matched_evidence_id == other.id for f in new_flags)
                    if not already_flagged:
                        flag = EvidenceFraudFlag(
                            evidence_id=evidence.id,
                            matched_evidence_id=other.id,
                            matched_work_id=other.work_id,
                            flag_type="GPS_TIMESTAMP_MATCH",
                            severity="HIGH",
                            confidence_score=90.0,
                            distance_meters=round(d_m, 1),
                            message=f"Photo EXIF GPS ({evidence.exif_latitude:.4f}°, {evidence.exif_longitude:.4f}°) and timestamp ({evidence.exif_captured_at.strftime('%Y-%m-%d %H:%M:%S')}) match evidence from work '{other_title}' (ID: {other_ext_id}) within {d_m:.1f}m / {dt_s:.0f}s."
                        )
                        new_flags.append(flag)

        # 4. Declared Work Site vs EXIF Location Mismatch (Same Work Sanity Check)
        if (evidence.gps_present and evidence.exif_latitude is not None and evidence.exif_longitude is not None and
            target_work and target_work.latitude is not None and target_work.longitude is not None):

            d_m = haversine_distance_meters(
                float(evidence.exif_latitude), float(evidence.exif_longitude),
                float(target_work.latitude), float(target_work.longitude)
            )
            loc_thresh = getattr(settings, 'EVIDENCE_LOCATION_MISMATCH_METERS', 500.0)

            if d_m > loc_thresh:
                flag = EvidenceFraudFlag(
                    evidence_id=evidence.id,
                    matched_evidence_id=None,
                    matched_work_id=evidence.work_id,
                    flag_type="LOCATION_MISMATCH",
                    severity="MEDIUM",
                    confidence_score=80.0,
                    distance_meters=round(d_m, 1),
                    message=f"Embedded EXIF GPS location ({evidence.exif_latitude:.4f}°, {evidence.exif_longitude:.4f}°) is {d_m:.0f} meters away from declared work site ({target_work.latitude:.4f}°, {target_work.longitude:.4f}°)."
                )
                new_flags.append(flag)

        # 5. Missing / Stripped EXIF Metadata (Honest Uncertainty Signal)
        ext = os.path.splitext(evidence.file_name or "")[1].lower() if evidence.file_name else ""
        if ext in ('.jpg', '.jpeg', '.png', '.webp'):
            if not evidence.exif_present or not evidence.gps_present:
                flag = EvidenceFraudFlag(
                    evidence_id=evidence.id,
                    matched_evidence_id=None,
                    matched_work_id=evidence.work_id,
                    flag_type="EXIF_STRIPPED_UNVERIFIABLE",
                    severity="LOW",
                    confidence_score=50.0,
                    message="Photo metadata (EXIF/GPS) is absent or stripped (commonly caused by messaging app forwards or screenshots). Provenance cannot be automatically verified."
                )
                new_flags.append(flag)

        for f in new_flags:
            db.add(f)

        db.commit()
        return new_flags

    @staticmethod
    def get_fraud_flags_for_work(work_id: str, db: Session) -> List[Dict[str, Any]]:
        """Used by API/UI to return all evidence fraud flags associated with a work."""
        evidences = db.query(Evidence).filter(Evidence.work_id == work_id).all()
        evidence_ids = [e.id for e in evidences]

        if not evidence_ids:
            return []

        flags = db.query(EvidenceFraudFlag).filter(EvidenceFraudFlag.evidence_id.in_(evidence_ids)).all()

        result = []
        for f in flags:
            matched_work = db.query(Work).filter(Work.id == f.matched_work_id).first() if f.matched_work_id else None
            result.append({
                "id": f.id,
                "evidenceId": f.evidence_id,
                "matchedEvidenceId": f.matched_evidence_id,
                "matchedWorkId": f.matched_work_id,
                "matchedWorkTitle": matched_work.title if matched_work else None,
                "matchedWorkExternalId": matched_work.external_id if matched_work else None,
                "flagType": f.flag_type,
                "severity": f.severity,
                "confidenceScore": float(f.confidence_score),
                "distanceMeters": float(f.distance_meters) if f.distance_meters is not None else None,
                "phashDistance": f.phash_distance,
                "message": f.message,
                "createdAt": f.created_at.isoformat() if f.created_at else None
            })

        return result
