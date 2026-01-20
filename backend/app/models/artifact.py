"""Artifact model for evidence files."""

from sqlalchemy import Column, String, Integer, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship

from backend.app.db.base import Base, IDMixin, TimestampMixin


class Artifact(Base, IDMixin, TimestampMixin):
    """
    Artifact represents evidence files (configs, logs, screenshots, etc.).

    Key features:
    - Immutable: Once uploaded, cannot be modified
    - Hash-verified: SHA-256 hash stored for integrity verification
    - Traceable: Linked to specific run and uploader
    """

    __tablename__ = "artifacts"

    # File metadata
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)  # MIME type
    size_bytes = Column(BigInteger, nullable=False)

    # Integrity verification
    sha256_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hex digest

    # Storage location
    storage_path = Column(String(500), nullable=False)  # Path in storage backend

    # Classification
    artifact_type = Column(String(50), nullable=True)  # e.g., "config", "log", "screenshot"
    description = Column(String(500), nullable=True)

    # Related run
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)

    # Uploader
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Soft delete (for audit trail, never physically delete)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    run = relationship("Run", back_populates="artifacts")
    uploader = relationship("User", foreign_keys=[uploaded_by_id])

    def __repr__(self):
        return (
            f"<Artifact(id={self.id}, filename='{self.filename}', "
            f"hash='{self.sha256_hash[:8]}...', run_id={self.run_id})>"
        )
