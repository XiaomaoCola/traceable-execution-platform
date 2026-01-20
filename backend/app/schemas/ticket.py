"""Ticket schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict

from backend.app.models.ticket import TicketStatus


class TicketBase(BaseModel):
    """Base ticket schema."""
    title: str
    description: str | None = None
    asset_id: int | None = None


class TicketCreate(TicketBase):
    """Schema for creating a new ticket."""
    pass


class TicketUpdate(BaseModel):
    """Schema for updating an existing ticket."""
    title: str | None = None
    description: str | None = None
    status: TicketStatus | None = None
    asset_id: int | None = None


class TicketResponse(TicketBase):
    """Schema for ticket response."""
    id: int
    status: TicketStatus
    created_by_id: int
    approved_by_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketApprove(BaseModel):
    """Schema for approving a ticket."""
    approved: bool = True
