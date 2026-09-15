import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    external_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agency_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    jurisdiction_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("jurisdictions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    jurisdiction: Mapped[Optional["Jurisdiction"]] = relationship("Jurisdiction")
    works: Mapped[List["Work"]] = relationship("Work", back_populates="agency")
