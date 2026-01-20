"""Asset service for managing devices and resources."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.asset import Asset
from backend.app.models.user import User
from backend.app.schemas.asset import AssetCreate, AssetUpdate
from backend.app.audit.events import AuditEvent, AuditEventType
from backend.app.audit.audit_logger import audit_logger


async def create_asset(
    db: Session,
    asset_in: AssetCreate,
    creator: User
) -> Asset:
    """
    Create a new asset.

    Args:
        db: Database session
        asset_in: Asset creation data
        creator: User creating the asset

    Returns:
        Created asset object
    """
    # Check if serial number already exists (if provided)
    if asset_in.serial_number:
        existing = db.query(Asset).filter(
            Asset.serial_number == asset_in.serial_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset with this serial number already exists"
            )

    # Create asset
    asset = Asset(
        name=asset_in.name,
        asset_type=asset_in.asset_type,
        serial_number=asset_in.serial_number,
        location=asset_in.location,
        description=asset_in.description,
        created_by_id=creator.id
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Log asset creation
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.ASSET_CREATED,
        actor_id=creator.id,
        actor_username=creator.username,
        resource_type="asset",
        resource_id=asset.id,
        action=f"Created asset: {asset.name}",
        details={
            "asset_type": asset.asset_type,
            "serial_number": asset.serial_number
        }
    ))

    return asset


async def update_asset(
    db: Session,
    asset_id: int,
    asset_in: AssetUpdate,
    user: User
) -> Asset:
    """
    Update an asset.

    Args:
        db: Database session
        asset_id: Asset ID
        asset_in: Update data
        user: User updating the asset

    Returns:
        Updated asset object

    Raises:
        HTTPException: If asset not found or user not authorized
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    # Only creator or admin can update
    if asset.created_by_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this asset"
        )

    # Update fields
    update_data = asset_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)

    # Log update
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.ASSET_UPDATED,
        actor_id=user.id,
        actor_username=user.username,
        resource_type="asset",
        resource_id=asset.id,
        action=f"Updated asset: {asset.name}",
        details={"updated_fields": list(update_data.keys())}
    ))

    return asset
