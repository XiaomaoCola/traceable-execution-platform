"""Ticket management endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketApprove
from backend.app.core.dependencies import DatabaseSession, CurrentUser, CurrentAdmin
from backend.app.services.ticket_service import create_ticket, approve_ticket, update_ticket
from backend.app.models.ticket import Ticket


router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketResponse)
async def create_new_ticket(
    ticket_in: TicketCreate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Create a new ticket."""
    ticket = await create_ticket(db, ticket_in, current_user)
    return ticket


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
):
    """
    List tickets.

    Admins can see all tickets, employees can only see their own.
    """
    query = db.query(Ticket)

    if not current_user.is_admin:
        query = query.filter(Ticket.created_by_id == current_user.id)

    tickets = query.offset(skip).limit(limit).all()
    return tickets


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get ticket by ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check permissions
    if not current_user.is_admin and ticket.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this ticket"
        )

    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket_endpoint(
    ticket_id: int,
    ticket_in: TicketUpdate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Update a ticket."""
    ticket = await update_ticket(db, ticket_id, ticket_in, current_user)
    return ticket


@router.post("/{ticket_id}/approve", response_model=TicketResponse)
async def approve_ticket_endpoint(
    ticket_id: int,
    db: DatabaseSession,
    current_admin: CurrentAdmin
):
    """
    Approve a ticket (admin only).

    Required for action runs.
    """
    ticket = await approve_ticket(db, ticket_id, current_admin)
    return ticket
