"""Asset management endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse
from backend.app.core.dependencies import DatabaseSession, CurrentUser
from backend.app.services.asset_service import create_asset, update_asset
from backend.app.models.asset import Asset


router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post("", response_model=AssetResponse)
async def create_new_asset(
    asset_in: AssetCreate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Create a new asset."""
    asset = await create_asset(db, asset_in, current_user)
    return asset


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    db: DatabaseSession,
    current_user: CurrentUser,
    asset_type: str | None = None,
    skip: int = 0,
    limit: int = 100
):
    """List assets."""
    query = db.query(Asset)

    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)

    assets = query.offset(skip).limit(limit).all()
    return assets


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get asset by ID."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset_endpoint(
    asset_id: int,
    asset_in: AssetUpdate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Update an asset."""
    asset = await update_asset(db, asset_id, asset_in, current_user)
    return asset
