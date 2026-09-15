import uuid
from datetime import datetime, date, timezone
from typing import List, Optional
from sqlalchemy import String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("works.id", ondelete="CASCADE"), index=True, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(40), index=True, default="DETECTED", nullable=False)
    priority: Mapped[str] = mapped_column(String(30), default="MEDIUM", nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    work: Mapped["Work"] = relationship("Work")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to])
    actions: Mapped[List["CaseAction"]] = relationship("CaseAction", back_populates="case", cascade="all, delete-orphan")

class CaseAction(Base):
    __tablename__ = "case_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(60), nullable=False)
    from_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    to_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    case: Mapped["Case"] = relationship("Case", back_populates="actions")
    actor: Mapped["User"] = relationship("User")
