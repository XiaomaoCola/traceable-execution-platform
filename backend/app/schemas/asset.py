"""Asset schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AssetBase(BaseModel):
    """Base asset schema."""
    name: str
    asset_type: str
    serial_number: str | None = None
    location: str | None = None
    description: str | None = None


class AssetCreate(AssetBase):
    """Schema for creating a new asset."""
    pass


class AssetUpdate(BaseModel):
    """Schema for updating an existing asset."""
    name: str | None = None
    asset_type: str | None = None
    serial_number: str | None = None
    location: str | None = None
    description: str | None = None


class AssetResponse(AssetBase):
    """Schema for asset response."""
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
