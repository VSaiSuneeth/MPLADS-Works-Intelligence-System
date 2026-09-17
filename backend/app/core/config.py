import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", case_sensitive=False)

    PROJECT_NAME: str = "MPLADS Works Intelligence and Review System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'mplads_intelligence.db'}")
    
    # File Storage
    UPLOAD_DIR: str = DEFAULT_UPLOAD_DIR
    MAX_UPLOAD_SIZE_MB: int = 100
    
    # Evidence Photo Fraud Thresholds
    EVIDENCE_PHASH_THRESHOLD: int = 8
    EVIDENCE_GPS_MATCH_METERS: float = 5.0
    EVIDENCE_TIMESTAMP_MATCH_SECONDS: int = 60
    EVIDENCE_LOCATION_MISMATCH_METERS: float = 500.0

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(BASE_DIR / "data", exist_ok=True)
