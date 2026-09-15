import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    state_name: Mapped[str] = mapped_column(String(150), nullable=False)
    district_name: Mapped[str] = mapped_column(String(150), nullable=False)
    district_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    works: Mapped[List["Work"]] = relationship("Work", back_populates="jurisdiction")
