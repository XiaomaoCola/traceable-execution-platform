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
        """
        将文件保存到本地文件系统中（异步方式）。

        该方法会以“流式”的方式读取并写入文件：
        - 从输入文件对象中按固定大小（chunk）逐块读取数据
        - 每读取一块数据，就立即写入磁盘，避免一次性占用大量内存
        - 在写入文件的同时，逐步计算文件的 SHA-256 哈希值，用于完整性校验
        - 同时统计文件的实际字节大小

        这种实现方式适用于大文件上传场景，并且不会阻塞 FastAPI 的事件循环。

        参数：
            file (BinaryIO):
                已打开的二进制文件对象（例如 FastAPI UploadFile.file），
                需要从该对象中读取文件内容。
            storage_path (str):
                文件在存储系统中的逻辑路径（相对于 artifact 存储根目录），
                例如：runs/123/output.log。

        返回值：
            tuple[str, int, str]:
                - storage_path: 实际保存使用的逻辑存储路径
                - size_bytes: 文件的实际大小（字节数）
                - sha256_hash: 文件内容对应的 SHA-256 哈希值（十六进制字符串）

        异常：
            ValueError:
                当 storage_path 非法（例如目录穿越攻击）时抛出。
            OSError:
                当文件系统写入失败时抛出。
        """
        full_path = self._get_full_path(storage_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate hash and size while writing
        hasher = hashlib.sha256()
        # 创建一个“SHA-256 指纹计算器”。
        size = 0

        async with aiofiles.open(full_path, 'wb') as f:
        # 这句话意思是：在磁盘上打开一个文件，准备把内容写进去（wb = write binary）。
        # 异步写法是：async with aiofiles.open。  普通写法是：with open。
            while chunk := file.read(8192):
            # 这句话意思是：从文件里读取内容，最多 8192 个字节（8KB）。就是把文件切割成一个个chunk。
                await f.write(chunk)
                hasher.update(chunk)
                # 把当前的chunk给指纹计算器，算出hash。因为hash算法不依赖完整文件，可以一部分一部分的算。（但是依赖顺序，顺序错了，hash值肯定不同。）
                size += len(chunk)
                # size的意思是，已经写了多少字节了，最后可以算出文件总大小。

        sha256_hash = hasher.hexdigest()
        # 这里的意思是：把刚才算出来的指纹，转成一个人类可存储的字符串。
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
