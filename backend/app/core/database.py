import os
import logging
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Determine database connection
DB_URL = settings.DATABASE_URL
IS_POSTGRES = DB_URL.startswith("postgresql")

try:
    if IS_POSTGRES:
        engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("Connected to PostgreSQL with pgvector extension enabled.")
    else:
        engine = create_engine(settings.SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})
        IS_POSTGRES = False
        logger.info(f"Using SQLite database at {settings.SQLITE_FALLBACK_URL}")
except Exception as e:
    logger.warning(f"Could not connect to primary DB ({DB_URL}): {e}. Falling back to SQLite.")
    engine = create_engine(settings.SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})
    IS_POSTGRES = False

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables in the database."""
    # Ensure all models are imported before calling create_all
    import app.models # noqa
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
