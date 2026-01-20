"""
Initialize database with sample data.

Creates an admin user and some sample assets.
"""

import asyncio
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal, engine
from backend.app.db.base import Base
from backend.app.models import User, Asset
from backend.app.core.security import get_password_hash


def create_admin_user(db: Session) -> User:
    """Create default admin user."""
    admin = db.query(User).filter(User.username == "admin").first()

    if admin:
        print("Admin user already exists")
        return admin

    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="System Administrator",
        is_admin=True,
        is_active=True
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    print(f"✅ Created admin user: {admin.username}")
    return admin


def create_sample_employee(db: Session) -> User:
    """Create a sample employee user."""
    employee = db.query(User).filter(User.username == "employee").first()

    if employee:
        print("Employee user already exists")
        return employee

    employee = User(
        username="employee",
        email="employee@example.com",
        hashed_password=get_password_hash("employee123"),
        full_name="Test Employee",
        is_admin=False,
        is_active=True
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    print(f"✅ Created employee user: {employee.username}")
    return employee


def create_sample_assets(db: Session, creator: User) -> list[Asset]:
    """Create sample assets."""
    assets_data = [
        {
            "name": "Main Office Switch",
            "asset_type": "switch",
            "serial_number": "SW-001-2024",
            "location": "Main Office - Floor 1",
            "description": "Cisco Catalyst 2960 - Main office network switch"
        },
        {
            "name": "Server Room Router",
            "asset_type": "router",
            "serial_number": "RT-001-2024",
            "location": "Server Room - Rack 1",
            "description": "Cisco ISR 4000 Series Router"
        },
        {
            "name": "Factory Gateway",
            "asset_type": "switch",
            "serial_number": "SW-FAC-001",
            "location": "Factory A - Control Room",
            "description": "Industrial Ethernet Switch for factory network"
        }
    ]

    assets = []
    for asset_data in assets_data:
        # Check if already exists
        existing = db.query(Asset).filter(
            Asset.serial_number == asset_data["serial_number"]
        ).first()

        if existing:
            print(f"Asset {asset_data['name']} already exists")
            assets.append(existing)
            continue

        asset = Asset(
            **asset_data,
            created_by_id=creator.id
        )

        db.add(asset)
        assets.append(asset)

    db.commit()

    for asset in assets:
        db.refresh(asset)
        print(f"✅ Created asset: {asset.name}")

    return assets


def init_database():
    """Initialize database with sample data."""
    print("🔧 Initializing database...")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

    # Create session
    db = SessionLocal()

    try:
        # Create users
        admin = create_admin_user(db)
        employee = create_sample_employee(db)

        # Create sample assets
        assets = create_sample_assets(db, admin)

        print("\n✅ Database initialization complete!")
        print("\n📝 Login credentials:")
        print("   Admin:    username=admin    password=admin123")
        print("   Employee: username=employee password=employee123")
        print(f"\n📦 Created {len(assets)} sample assets")

    finally:
        db.close()


if __name__ == "__main__":
    init_database()
