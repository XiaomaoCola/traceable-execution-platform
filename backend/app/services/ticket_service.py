"""Ticket service for managing work orders."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.ticket import Ticket, TicketStatus
from backend.app.models.user import User
from backend.app.schemas.ticket import TicketCreate, TicketUpdate
from backend.app.audit.events import AuditEvent, AuditEventType
from backend.app.audit.audit_logger import audit_logger


async def create_ticket(
    db: Session,
    ticket_in: TicketCreate,
    creator: User
) -> Ticket:
    """
    Create a new ticket.

    Args:
        db: Database session
        ticket_in: Ticket creation data
        creator: User creating the ticket

    Returns:
        Created ticket object
    """
    # Create ticket
    ticket = Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        asset_id=ticket_in.asset_id,
        created_by_id=creator.id,
        status=TicketStatus.SUBMITTED
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Log ticket creation
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.TICKET_CREATED,
        actor_id=creator.id,
        actor_username=creator.username,
        resource_type="ticket",
        resource_id=ticket.id,
        action=f"Created ticket: {ticket.title}",
        details={
            "asset_id": ticket.asset_id
        }
    ))

    return ticket


async def approve_ticket(
    db: Session,
    ticket_id: int,
    approver: User
) -> Ticket:
    """
    Approve a ticket (required for action runs).

    Args:
        db: Database session
        ticket_id: Ticket ID
        approver: User approving the ticket (must be admin)

    Returns:
        Approved ticket object

    Raises:
        HTTPException: If ticket not found or user not authorized
    """
    if not approver.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve tickets"
        )

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    if ticket.status != TicketStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticket must be in SUBMITTED status to be approved (current: {ticket.status.value})"
        )

    # Approve ticket
    ticket.status = TicketStatus.APPROVED
    ticket.approved_by_id = approver.id

    db.commit()
    db.refresh(ticket)

    # Log approval
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.TICKET_APPROVED,
        actor_id=approver.id,
        actor_username=approver.username,
        resource_type="ticket",
        resource_id=ticket.id,
        action=f"Approved ticket: {ticket.title}",
        details={
            "created_by_id": ticket.created_by_id
        }
    ))

    return ticket


async def update_ticket(
    db: Session,
    ticket_id: int,
    ticket_in: TicketUpdate,
    user: User
) -> Ticket:
    """
    Update a ticket.

    Args:
        db: Database session
        ticket_id: Ticket ID
        ticket_in: Update data
        user: User updating the ticket

    Returns:
        Updated ticket object

    Raises:
        HTTPException: If ticket not found or user not authorized
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Only creator or admin can update
    if ticket.created_by_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this ticket"
        )

    # Update fields
    update_data = ticket_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)

    # Log update
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.TICKET_UPDATED,
        actor_id=user.id,
        actor_username=user.username,
        resource_type="ticket",
        resource_id=ticket.id,
        action=f"Updated ticket: {ticket.title}",
        details={"updated_fields": list(update_data.keys())}
    ))

    return ticket
