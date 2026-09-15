from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True) # person, place, event_type, topic
    canonical_id = Column(String(100), nullable=True, index=True)

    memory_entities = relationship("MemoryEntity", back_populates="entity", cascade="all, delete-orphan")

class MemoryEntity(Base):
    __tablename__ = "memory_entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Float, default=1.0, nullable=False)

    memory = relationship("Memory", back_populates="entities")
    entity = relationship("Entity", back_populates="memory_entities")

    __table_args__ = (
        UniqueConstraint("memory_id", "entity_id", name="uq_memory_entity"),
    )
