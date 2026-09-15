import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    location_name = Column(String(255), nullable=True, index=True)
    cover_memory_id = Column(String(36), nullable=True)
    is_auto_generated = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    event_memories = relationship("EventMemory", back_populates="event", cascade="all, delete-orphan")

    def to_dict(self, include_memories: bool = False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "location_name": self.location_name,
            "cover_memory_id": self.cover_memory_id,
            "is_auto_generated": self.is_auto_generated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "memory_count": len(self.event_memories) if self.event_memories else 0
        }
        if include_memories and self.event_memories:
            data["memories"] = [em.memory.to_dict(include_details=False) for em in sorted(self.event_memories, key=lambda x: x.order_index) if em.memory]
        return data

class EventMemory(Base):
    __tablename__ = "event_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)

    event = relationship("Event", back_populates="event_memories")
    memory = relationship("Memory", back_populates="event_memberships")

    __table_args__ = (
        UniqueConstraint("event_id", "memory_id", name="uq_event_memory"),
    )
