import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class DuplicateGroup(Base):
    __tablename__ = "duplicate_groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String(50), default="pending", nullable=False, index=True) # pending, resolved, dismissed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    members = relationship("DuplicateMember", back_populates="group", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "members": [
                {
                    "memory_id": m.memory_id,
                    "similarity_score": m.similarity_score,
                    "duplicate_type": m.duplicate_type,
                    "is_primary": m.is_primary,
                    "memory": m.memory.to_dict() if m.memory else None
                }
                for m in self.members
            ]
        }

class DuplicateMember(Base):
    __tablename__ = "duplicate_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(36), ForeignKey("duplicate_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    similarity_score = Column(Float, default=1.0, nullable=False)
    duplicate_type = Column(String(50), default="exact", nullable=False) # exact_hash, phash_match, embedding_similarity
    is_primary = Column(Boolean, default=False, nullable=False)

    group = relationship("DuplicateGroup", back_populates="members")
    memory = relationship("Memory", back_populates="duplicate_memberships")

    __table_args__ = (
        UniqueConstraint("group_id", "memory_id", name="uq_duplicate_member"),
    )
