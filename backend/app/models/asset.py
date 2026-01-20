"""Asset model for devices and resources."""

from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship

from backend.app.db.base import Base, IDMixin, TimestampMixin


class Asset(Base, IDMixin, TimestampMixin):
    """
    Asset model representing physical/virtual devices or resources.

    Examples: switches, routers, servers, etc.
    """

    __tablename__ = "assets"

    name = Column(String(100), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)  # e.g., "switch", "router", "server"
    serial_number = Column(String(100), unique=True, nullable=True, index=True)
    location = Column(String(255), nullable=True)  # Physical location or site
    description = Column(Text, nullable=True)

    # Metadata (JSON-like flexible field can be added if needed)
    # metadata = Column(JSON, nullable=True)

    # Who created/manages this asset
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by_id])
    tickets = relationship("Ticket", back_populates="asset")

    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.asset_type}')>"
