from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    memory_tags = relationship("MemoryTag", back_populates="tag", cascade="all, delete-orphan")

class MemoryTag(Base):
    __tablename__ = "memory_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    is_user_edited = Column(Boolean, default=False, nullable=False)

    memory = relationship("Memory", back_populates="tags")
    tag = relationship("Tag", back_populates="memory_tags")

    __table_args__ = (
        UniqueConstraint("memory_id", "tag_id", name="uq_memory_tag"),
    )
