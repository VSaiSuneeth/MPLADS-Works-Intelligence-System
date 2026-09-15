import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, Integer, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Memory(Base):
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(20), nullable=False, index=True) # photo, note, voice
    title = Column(String(255), nullable=True)
    file_path = Column(String(512), nullable=True)
    raw_text = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_captured_at_estimated = Column(Boolean, default=False, nullable=False)
    
    # Geolocation
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    location_name = Column(String(255), nullable=True, index=True)
    
    # Media metadata
    duration_seconds = Column(Float, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True) # SHA-256
    phash = Column(String(64), nullable=True, index=True) # Perceptual hash
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # User curation
    is_important = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    embeddings = relationship("Embedding", back_populates="memory", cascade="all, delete-orphan")
    tags = relationship("MemoryTag", back_populates="memory", cascade="all, delete-orphan")
    entities = relationship("MemoryEntity", back_populates="memory", cascade="all, delete-orphan")
    event_memberships = relationship("EventMemory", back_populates="memory", cascade="all, delete-orphan")
    duplicate_memberships = relationship("DuplicateMember", back_populates="memory", cascade="all, delete-orphan")

    def to_dict(self, include_details: bool = True):
        data = {
            "id": self.id,
            "type": self.type,
            "title": self.title or ("Note" if self.type == "note" else "Voice Memo" if self.type == "voice" else "Photo"),
            "file_path": self.file_path,
            "raw_text": self.raw_text,
            "transcript": self.transcript,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "is_captured_at_estimated": self.is_captured_at_estimated,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "duration_seconds": self.duration_seconds,
            "file_hash": self.file_hash,
            "phash": self.phash,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "is_important": self.is_important,
        }
        if include_details:
            data["tags"] = [t.tag.name for t in self.tags if t.tag]
            data["entities"] = [{"name": e.entity.name, "type": e.entity.type, "confidence": e.confidence} for e in self.entities if e.entity]
            data["events"] = [{"id": em.event.id, "title": em.event.title} for em in self.event_memberships if em.event]
        return data
