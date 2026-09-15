import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class SimilarityCandidate(Base):
    __tablename__ = "similarity_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("works.id", ondelete="CASCADE"), index=True, nullable=False)
    candidate_work_id: Mapped[str] = mapped_column(String(36), ForeignKey("works.id", ondelete="CASCADE"), index=True, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    candidate_label: Mapped[str] = mapped_column(String(40), nullable=False)
    feature_breakdown_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(80), default="sim-v1.0", nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    work: Mapped["Work"] = relationship("Work", foreign_keys=[work_id])
    candidate_work: Mapped["Work"] = relationship("Work", foreign_keys=[candidate_work_id])
