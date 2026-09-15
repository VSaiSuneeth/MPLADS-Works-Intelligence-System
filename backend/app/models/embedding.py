import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, TypeDecorator
from sqlalchemy.orm import relationship
from app.core.database import Base, IS_POSTGRES

class VectorType(TypeDecorator):
    """
    Custom SQLAlchemy TypeDecorator:
    - In PostgreSQL with pgvector: uses native Vector(512)
    - In SQLite fallback: transparently serializes list to JSON string
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 512, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if IS_POSTGRES and dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            if IS_POSTGRES and dialect.name == "postgresql":
                return value
            return json.dumps(list(value))
        elif hasattr(value, "tolist"):
            if IS_POSTGRES and dialect.name == "postgresql":
                return value.tolist()
            return json.dumps(value.tolist())
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                clean = value.strip("[]() ")
                if not clean:
                    return []
                return [float(x.strip()) for x in clean.split(",") if x.strip()]
        return value

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    vector = Column(VectorType(512), nullable=False)
    model_name = Column(String(100), default="clip-ViT-B-32", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    memory = relationship("Memory", back_populates="embeddings")

    def get_vector_list(self) -> list[float]:
        """Convert stored vector column to python list of floats."""
        if isinstance(self.vector, list):
            return self.vector
        if isinstance(self.vector, str):
            try:
                return json.loads(self.vector)
            except Exception:
                clean = self.vector.strip("[]() ")
                if not clean:
                    return []
                return [float(x.strip()) for x in clean.split(",") if x.strip()]
        if hasattr(self.vector, "tolist"):
            return self.vector.tolist()
        return list(self.vector) if self.vector else []
