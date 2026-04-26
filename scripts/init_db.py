"""
Initialize database with sample data.

Creates an admin user and some sample assets.
Run after: alembic upgrade head
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import AsyncSessionLocal
from backend.app.models import User, Asset
from backend.app.core.security import get_password_hash


async def create_admin_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()

    if admin:
        print("Admin user already exists")
        return admin

    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="System Administrator",
        is_admin=True,
        is_active=True,
    )

    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    print(f"✅ Created admin user: {admin.username}")
    return admin


async def create_sample_employee(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == "employee"))
    employee = result.scalar_one_or_none()

    if employee:
        print("Employee user already exists")
        return employee

    employee = User(
        username="employee",
        email="employee@example.com",
        hashed_password=get_password_hash("employee123"),
        full_name="Test Employee",
        is_admin=False,
        is_active=True,
    )

    db.add(employee)
    await db.commit()
    await db.refresh(employee)

    print(f"✅ Created employee user: {employee.username}")
    return employee


async def create_sample_assets(db: AsyncSession, creator: User) -> list[Asset]:
    assets_data = [
        {
            "name": "Main Office Switch",
            "asset_type": "switch",
            "serial_number": "SW-001-2024",
            "location": "Main Office - Floor 1",
            "description": "Cisco Catalyst 2960 - Main office network switch",
        },
        {
            "name": "Server Room Router",
            "asset_type": "router",
            "serial_number": "RT-001-2024",
            "location": "Server Room - Rack 1",
            "description": "Cisco ISR 4000 Series Router",
        },
        {
            "name": "Factory Gateway",
            "asset_type": "switch",
            "serial_number": "SW-FAC-001",
            "location": "Factory A - Control Room",
            "description": "Industrial Ethernet Switch for factory network",
        },
    ]

    assets = []
    for asset_data in assets_data:
        result = await db.execute(
            select(Asset).where(Asset.serial_number == asset_data["serial_number"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Asset {asset_data['name']} already exists")
            assets.append(existing)
            continue

        asset = Asset(**asset_data, created_by_id=creator.id)
        db.add(asset)
        assets.append(asset)

    await db.commit()

    for asset in assets:
        await db.refresh(asset)
        print(f"✅ Created asset: {asset.name}")

    return assets


async def init_database():
    print("🔧 Initializing database...")
    print("⚠️  请先确保已执行 alembic upgrade head")

    async with AsyncSessionLocal() as db:
        admin = await create_admin_user(db)
        await create_sample_employee(db)
        assets = await create_sample_assets(db, admin)

        print("\n✅ Database initialization complete!")
        print("\n📝 Login credentials:")
        print("   Admin:    username=admin    password=admin123")
        print("   Employee: username=employee password=employee123")
        print(f"\n📦 Created {len(assets)} sample assets")


if __name__ == "__main__":
    asyncio.run(init_database())
