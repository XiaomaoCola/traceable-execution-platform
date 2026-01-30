"""Artifact service for managing evidence files."""

from typing import BinaryIO
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.artifact import Artifact
from backend.app.models.run import Run
from backend.app.models.user import User
from backend.app.storage.artifact_store import artifact_store
from backend.app.audit.events import AuditEvent, AuditEventType
from backend.app.audit.audit_logger import audit_logger
from backend.app.core.config import settings


async def upload_artifact(
    db: Session,
    file: BinaryIO,
    filename: str,
    run_id: int,
    uploader: User,
    content_type: str | None = None,
    artifact_type: str | None = None,
    description: str | None = None
) -> Artifact:
    """
    Upload an artifact file.

    Args:
        db: Database session
        file: File to upload
        filename: Original filename
        run_id: Associated run ID
        uploader: User uploading the artifact
        content_type: MIME type
        artifact_type: Classification (e.g., "config", "log")
        description: Optional description

    Returns:
        Created artifact object

    Raises:
        HTTPException: If validation fails
    """
    # Verify run exists
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )

    # Check file size limit
    file.seek(0, 2)
    # 这里的概念叫做文件指针（file pointer）。
    # 当打开一个文件时，不管是 Python、C、Java，系统都会偷偷做一件事，给这个文件创建一个“指针”，默认在 0。
    # file.seek(offset, whence)意思是：从 whence 指定的位置开始，往后移动 offset 个字节。
    # whence为0，表示从文件开头开始。whence为1，表示从当前位置。whence为2，表示从文件末尾。
    # file.seek(0, 2)表示：从文件末尾开始，移动 0 个字节。
    file_size = file.tell()
    # file.tell() 的意思是： 现在读到第几个字节。
    file.seek(0)
    # Reset to beginning

    max_size_bytes = settings.max_artifact_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_artifact_size_mb}MB"
        )

    # Generate storage path: runs/<run_id>/<filename>
    storage_path = f"runs/{run_id}/{filename}"

    # Save file and get hash
    storage_path, size_bytes, sha256_hash = await artifact_store.save(file, storage_path)

    # Create artifact record
    artifact = Artifact(
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256_hash=sha256_hash,
        storage_path=storage_path,
        artifact_type=artifact_type,
        description=description,
        run_id=run_id,
        uploaded_by_id=uploader.id
    )

    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    # Log artifact upload
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.ARTIFACT_UPLOADED,
        actor_id=uploader.id,
        actor_username=uploader.username,
        resource_type="artifact",
        resource_id=artifact.id,
        action=f"Uploaded artifact: {filename}",
        details={
            "run_id": run_id,
            "filename": filename,
            "size_bytes": size_bytes,
            "sha256_hash": sha256_hash,
            "artifact_type": artifact_type
        }
    ))

    return artifact


async def download_artifact(
    db: Session,
    artifact_id: int,
    user: User
) -> tuple[bytes, Artifact]:
    """
    Download an artifact file.

    Args:
        db: Database session
        artifact_id: Artifact ID
        user: User downloading the artifact

    Returns:
        Tuple of (file_content, artifact)

    Raises:
        HTTPException: If artifact not found or deleted
    """
    # Get artifact metadata
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )

    if artifact.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Artifact has been deleted"
        )

    # Read file from storage
    file_content = await artifact_store.read(artifact.storage_path)

    # Log artifact download
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.ARTIFACT_DOWNLOADED,
        actor_id=user.id,
        actor_username=user.username,
        resource_type="artifact",
        resource_id=artifact.id,
        action=f"Downloaded artifact: {artifact.filename}",
        details={
            "run_id": artifact.run_id,
            "filename": artifact.filename
        }
    ))

    return file_content, artifact


async def verify_artifact(
    db: Session,
    artifact_id: int
) -> bool:
    """
    Verify artifact integrity by checking hash.

    Args:
        db: Database session
        artifact_id: Artifact ID

    Returns:
        True if hash matches

    Raises:
        HTTPException: If artifact not found
    """
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )

    # Read file and compute hash
    from backend.app.utils.hashing import compute_sha256
    import io

    file_content = await artifact_store.read(artifact.storage_path)
    file_obj = io.BytesIO(file_content)
    computed_hash = compute_sha256(file_obj)

    verified = computed_hash == artifact.sha256_hash

    # Log verification
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.ARTIFACT_VERIFIED,
        resource_type="artifact",
        resource_id=artifact.id,
        action=f"Artifact verification: {'passed' if verified else 'failed'}",
        details={
            "expected_hash": artifact.sha256_hash,
            "computed_hash": computed_hash
        },
        success=verified
    ))

    return verified
