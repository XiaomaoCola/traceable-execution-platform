"""Asset management endpoints."""

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func

from backend.app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse, PaginatedAssetResponse
from backend.app.core.dependencies import DatabaseSession, CurrentUser
from backend.app.services.asset_service import create_asset, update_asset
from backend.app.models.asset import Asset
from backend.app.core.pagination import apply_pagination_and_sort, build_paginated_response

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

#修改
@router.get("", response_model=PaginatedAssetResponse)
async def list_assets(
    db: DatabaseSession,
    current_user: CurrentUser,
    asset_type: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    order_by: str = Query(default="created_at"),  # 【新增】
    order: str = Query(default="desc")            # 【新增】
):
    """List assets with pagination."""
    query = select(Asset)

    if asset_type:
        query = query.where(Asset.asset_type == asset_type)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    result = await db.execute(
        apply_pagination_and_sort(query, Asset, page, page_size, order_by, order)
    )
    assets = result.scalars().all()

    return build_paginated_response(assets, AssetResponse, total, page, page_size)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get asset by ID."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

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
