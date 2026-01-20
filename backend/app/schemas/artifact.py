"""Artifact schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ArtifactBase(BaseModel):
    """Base artifact schema."""
    filename: str
    artifact_type: str | None = None
    description: str | None = None


class ArtifactCreate(ArtifactBase):
    """Schema for creating artifact metadata (file upload handled separately)."""
    run_id: int


class ArtifactResponse(ArtifactBase):
    """Schema for artifact response."""
    id: int
    content_type: str | None = None
    size_bytes: int
    sha256_hash: str
    run_id: int
    uploaded_by_id: int
    is_deleted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArtifactUploadResponse(BaseModel):
    """Schema for artifact upload response."""
    artifact: ArtifactResponse
    message: str = "Artifact uploaded successfully"
