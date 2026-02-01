"""Ticket model for work orders."""

from sqlalchemy import Column, String, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from backend.app.db.base import Base, IDMixin, TimestampMixin


class TicketStatus(str, enum.Enum):
    """Ticket status state machine."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"  # Required for action runs
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CLOSED = "closed"


class Ticket(Base, IDMixin, TimestampMixin):
    """
    Ticket represents a work order submitted by employees.

    Lifecycle:
    1. Employee creates ticket (DRAFT/SUBMITTED)
    2. For ProofRun: no approval needed, can run immediately
    3. For ActionRun: requires approval (APPROVED)
    4. Run executes (RUNNING)
    5. Completes (DONE/FAILED)
    6. Ticket closed (CLOSED)
    """

    __tablename__ = "tickets"

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.SUBMITTED, nullable=False, index=True)

    # Related asset (e.g., which switch/router this ticket is about)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    # ForeignKey 写在 Ticket，而不是 Asset的原因是：
    # 一对多，即，一个 Asset对应多个 Ticket。多的一方，持有外键。

    # Creator
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # ForeignKey("users.id") 的意思是：created_by_id 这个数字必须等于 users 表中某一行的 id，
    # 也就意味着 如果试图插入一个不存在的 id，数据库会直接拒绝。
    # "users.id"写成字符串的原因：
    # users 这个表本身可能“还没完全存在”，目前只是用 Python 描述未来的表结构，
    # 等所有表都加载完了之后，再去找一张叫 users 的表，再去找它的 id 列，
    # 这个叫做延迟绑定（lazy resolution）。

    # Approver (for action runs)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    asset = relationship("Asset", back_populates="tickets")
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="tickets")
    # 上面的ForeignKey是：数据库层，保证数据正确。这里的relationship是：Python 层。
    approver = relationship("User", foreign_keys=[approved_by_id])
    runs = relationship("Run", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket(id={self.id}, title='{self.title}', status={self.status.value})>"
