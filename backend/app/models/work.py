import uuid
from datetime import datetime, date, timezone
from typing import List, Optional
from sqlalchemy import String, Numeric, Date, DateTime, ForeignKey, Text, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Work(Base):
    __tablename__ = "works"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    external_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    jurisdiction_id: Mapped[str] = mapped_column(String(36), ForeignKey("jurisdictions.id"), index=True, nullable=False)
    agency_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("agencies.id"), nullable=True)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    sanction_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    expenditure_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)

    recommendation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sanction_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    location_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)

    current_status: Mapped[str] = mapped_column(String(50), default="SANCTIONED", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    jurisdiction: Mapped["Jurisdiction"] = relationship("Jurisdiction", back_populates="works")
    agency: Mapped[Optional["Agency"]] = relationship("Agency", back_populates="works")
    lifecycle_events: Mapped[List["WorkLifecycleEvent"]] = relationship("WorkLifecycleEvent", back_populates="work", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="work", cascade="all, delete-orphan")
    progress_records: Mapped[List["ProgressRecord"]] = relationship("ProgressRecord", back_populates="work", cascade="all, delete-orphan")
    evidence: Mapped[List["Evidence"]] = relationship("Evidence", back_populates="work", cascade="all, delete-orphan")

class WorkLifecycleEvent(Base):
    __tablename__ = "work_lifecycle_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("data_sources.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    work: Mapped["Work"] = relationship("Work", back_populates="lifecycle_events")

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payee_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("data_sources.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    work: Mapped["Work"] = relationship("Work", back_populates="payments")

class ProgressRecord(Base):
    __tablename__ = "progress_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    progress_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    reported_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("data_sources.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    work: Mapped["Work"] = relationship("Work", back_populates="progress_records")

class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    availability_status: Mapped[str] = mapped_column(String(40), default="AVAILABLE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Fraud & Provenance Metadata Fields
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    phash: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    exif_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)
    exif_longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)
    exif_captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    camera_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    exif_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gps_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uploaded_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    work: Mapped["Work"] = relationship("Work", back_populates="evidence")
    fraud_flags: Mapped[List["EvidenceFraudFlag"]] = relationship(
        "EvidenceFraudFlag",
        foreign_keys="[EvidenceFraudFlag.evidence_id]",
        back_populates="evidence",
        cascade="all, delete-orphan"
    )

class EvidenceFraudFlag(Base):
    __tablename__ = "evidence_fraud_flags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    evidence_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence.id", ondelete="CASCADE"), index=True, nullable=False)
    matched_evidence_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True)
    matched_work_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    flag_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    distance_meters: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    phash_distance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    evidence: Mapped["Evidence"] = relationship("Evidence", foreign_keys=[evidence_id], back_populates="fraud_flags")
    matched_evidence: Mapped[Optional["Evidence"]] = relationship("Evidence", foreign_keys=[matched_evidence_id])
    matched_work: Mapped[Optional["Work"]] = relationship("Work", foreign_keys=[matched_work_id])
