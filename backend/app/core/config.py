import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", case_sensitive=False)

    PROJECT_NAME: str = "Digital Memory Vault"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'data' / 'memory_vault.db'}"
    )
    SQLITE_FALLBACK_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'memory_vault.db'}"
    
    # Redis & RQ
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # File Storage
    UPLOAD_DIR: str = DEFAULT_UPLOAD_DIR
    MAX_UPLOAD_SIZE_MB: int = 100
    
    # ML Models
    CLIP_MODEL_NAME: str = os.getenv("CLIP_MODEL_NAME", "clip-ViT-B-32")
    TEXT_MODEL_NAME: str = os.getenv("TEXT_MODEL_NAME", "all-MiniLM-L6-v2")
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    
    # Deduplication thresholds
    PHASH_HAMMING_THRESHOLD: int = 6
    EMBEDDING_SIMILARITY_THRESHOLD: float = 0.93

    # Evidence Photo Fraud Thresholds
    EVIDENCE_PHASH_THRESHOLD: int = 8
    EVIDENCE_GPS_MATCH_METERS: float = 5.0
    EVIDENCE_TIMESTAMP_MATCH_SECONDS: int = 60
    EVIDENCE_LOCATION_MISMATCH_METERS: float = 500.0
    
    # Clustering thresholds
    CLUSTER_TIME_WINDOW_DAYS: int = 4
    CLUSTER_GEO_DISTANCE_KM: float = 50.0
    CLUSTER_SIMILARITY_THRESHOLD: float = 0.70

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

settings = Settings()

# Ensure upload directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(Path(settings.UPLOAD_DIR) / "photos", exist_ok=True)
os.makedirs(Path(settings.UPLOAD_DIR) / "voice", exist_ok=True)
os.makedirs(Path(settings.UPLOAD_DIR) / "notes", exist_ok=True)
os.makedirs(BASE_DIR / "data", exist_ok=True)
