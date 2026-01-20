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

    # Creator
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Approver (for action runs)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    asset = relationship("Asset", back_populates="tickets")
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="tickets")
    approver = relationship("User", foreign_keys=[approved_by_id])
    runs = relationship("Run", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket(id={self.id}, title='{self.title}', status={self.status.value})>"
