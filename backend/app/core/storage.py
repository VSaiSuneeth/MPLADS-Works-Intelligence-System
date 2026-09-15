import os
import shutil
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
import mimetypes

from app.core.config import settings

class BaseStorage(ABC):
    @abstractmethod
    def save_file(self, file_obj: BinaryIO, filename: str, subfolder: str = "general") -> str:
        """Save a file and return its relative storage path."""
        pass

    @abstractmethod
    def get_full_path(self, relative_path: str) -> str:
        """Return the absolute path on disk (or cloud URL)."""
        pass

    @abstractmethod
    def read_file(self, relative_path: str) -> bytes:
        """Read and return the raw file bytes."""
        pass

    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """Delete the file from storage."""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check if file exists in storage."""
        pass

class LocalStorageBackend(BaseStorage):
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.UPLOAD_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_obj: BinaryIO, filename: str, subfolder: str = "general") -> str:
        target_dir = self.base_dir / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Avoid filename collisions by prefixing or keeping safe path
        safe_filename = filename.replace("/", "_").replace("\\", "_")
        target_path = target_dir / safe_filename
        
        # If target file exists, generate a unique filename
        if target_path.exists():
            stem = target_path.stem
            suffix = target_path.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        file_obj.seek(0)
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
        
        # Return relative path from base_dir with forward slashes
        rel_path = target_path.relative_to(self.base_dir).as_posix()
        return rel_path

    def get_full_path(self, relative_path: str) -> str:
        return str((self.base_dir / relative_path).resolve())

    def read_file(self, relative_path: str) -> bytes:
        full_path = self.get_full_path(relative_path)
        with open(full_path, "rb") as f:
            return f.read()

    def delete_file(self, relative_path: str) -> bool:
        full_path = Path(self.get_full_path(relative_path))
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def exists(self, relative_path: str) -> bool:
        return Path(self.get_full_path(relative_path)).exists()

# Singleton storage instance
storage_backend = LocalStorageBackend()
