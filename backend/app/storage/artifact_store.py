"""
Artifact storage abstraction layer.

Supports multiple backends: local filesystem, MinIO, S3.
"""

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

import aiofiles

from backend.app.core.config import settings


class ArtifactStore(ABC):
    """Abstract base class for artifact storage backends."""

    @abstractmethod
    async def save(self, file: BinaryIO, storage_path: str) -> tuple[str, int, str]:
        """
        Save a file to storage.

        Args:
            file: File-like object to save
            storage_path: Destination path in storage

        Returns:
            Tuple of (storage_path, size_bytes, sha256_hash)
        """
        pass

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """
        Read a file from storage.

        Args:
            storage_path: Path in storage

        Returns:
            File contents as bytes
        """
        pass

    @abstractmethod
    async def delete(self, storage_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            storage_path: Path in storage

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            storage_path: Path in storage

        Returns:
            True if file exists
        """
        pass


class LocalArtifactStore(ArtifactStore):
    """Local filesystem storage backend."""

    def __init__(self, base_path: str):
        """
        Initialize local storage.

        Args:
            base_path: Base directory for artifact storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, storage_path: str) -> Path:
        """Get full filesystem path from storage path."""
        full_path = self.base_path / storage_path
        # Ensure path is within base_path (security check)
        if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid storage path: directory traversal detected")
        return full_path

    async def save(self, file: BinaryIO, storage_path: str) -> tuple[str, int, str]:
        """Save file to local filesystem."""
        full_path = self._get_full_path(storage_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate hash and size while writing
        hasher = hashlib.sha256()
        size = 0

        async with aiofiles.open(full_path, 'wb') as f:
            while chunk := file.read(8192):
                await f.write(chunk)
                hasher.update(chunk)
                size += len(chunk)

        sha256_hash = hasher.hexdigest()
        return (storage_path, size, sha256_hash)

    async def read(self, storage_path: str) -> bytes:
        """Read file from local filesystem."""
        full_path = self._get_full_path(storage_path)

        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {storage_path}")

        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()

    async def delete(self, storage_path: str) -> bool:
        """Delete file from local filesystem."""
        full_path = self._get_full_path(storage_path)

        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def exists(self, storage_path: str) -> bool:
        """Check if file exists in local filesystem."""
        full_path = self._get_full_path(storage_path)
        return full_path.exists()


# Future: MinIOArtifactStore, S3ArtifactStore implementations

def get_artifact_store() -> ArtifactStore:
    """
    Get configured artifact storage backend.

    Returns:
        Configured artifact store instance
    """
    storage_type = settings.artifact_storage_type

    if storage_type == "local":
        return LocalArtifactStore(settings.artifact_storage_path)
    elif storage_type == "minio":
        # TODO: Implement MinIOArtifactStore
        raise NotImplementedError("MinIO storage not yet implemented")
    elif storage_type == "s3":
        # TODO: Implement S3ArtifactStore
        raise NotImplementedError("S3 storage not yet implemented")
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")


# Global artifact store instance
artifact_store = get_artifact_store()
