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
    # 关于序列号的设计，因为路由器，防火墙，交换机这些设备通常都是有唯一序列号的，所以写了unique=True。
    # 但是不能作为主键，因为以后会有各种场景，
    # 同一台设备主板换了，SN 变了，厂商返修回来，SN 变了，供应商贴错标签，虚拟设备复制，SN 重复等等。
    # 但是目前这个阶段不用上这么复杂，以后再说。
    location = Column(String(255), nullable=True)  # Physical location or site
    description = Column(Text, nullable=True)

    # Metadata (JSON-like flexible field can be added if needed)
    # metadata = Column(JSON, nullable=True)

    # Who created/manages this asset
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # TODO:
    # created_by_id 当前用于追踪“资产记录的创建者”（录入责任人）以及权限控制（creator/admin 可更新）。
    # 若未来采用组织/租户/团队维度的资产归属与权限模型（tenant_id/team_id/managed_by_id），
    # 需要重新评估 created_by_id 的必要性与 update 权限策略，避免将“录入者”误当“资产归属者”。

    # Relationships
    creator = relationship("User", foreign_keys=[created_by_id])
    tickets = relationship("Ticket", back_populates="asset")

    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.asset_type}')>"
