from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Engine configuration (handles SQLite and PostgreSQL)
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_db_schema():
    """Idempotently adds missing evidence columns to existing SQLite table if needed."""
    try:
        inspector = inspect(engine)
        if "evidence" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("evidence")]
            new_cols = [
                ("file_hash", "VARCHAR(64)"),
                ("phash", "VARCHAR(64)"),
                ("exif_latitude", "NUMERIC(10, 6)"),
                ("exif_longitude", "NUMERIC(10, 6)"),
                ("exif_captured_at", "TIMESTAMP"),
                ("camera_model", "VARCHAR(255)"),
                ("exif_present", "BOOLEAN DEFAULT 0"),
                ("gps_present", "BOOLEAN DEFAULT 0"),
                ("file_size_bytes", "INTEGER"),
                ("uploaded_by_user_id", "VARCHAR(36)")
            ]
            with engine.begin() as conn:
                for col_name, col_type in new_cols:
                    if col_name not in columns:
                        try:
                            conn.execute(text(f"ALTER TABLE evidence ADD COLUMN {col_name} {col_type}"))
                        except Exception:
                            pass
    except Exception:
        pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
