import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("works.id", ondelete="CASCADE"), index=True, nullable=False)
    score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    priority: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    risk_version: Mapped[str] = mapped_column(String(80), default="risk-v1.0", nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    work: Mapped["Work"] = relationship("Work")
    signals: Mapped[List["RiskSignal"]] = relationship("RiskSignal", back_populates="risk_score", cascade="all, delete-orphan")

class RiskSignal(Base):
    __tablename__ = "risk_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("works.id", ondelete="CASCADE"), index=True, nullable=False)
    risk_score_id: Mapped[str] = mapped_column(String(36), ForeignKey("risk_scores.id", ondelete="CASCADE"), nullable=False)
    signal_code: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    signal_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    contribution: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    confidence_impact: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    explanation_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    risk_score: Mapped["RiskScore"] = relationship("RiskScore", back_populates="signals")
