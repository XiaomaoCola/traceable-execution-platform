"""Run service for managing execution records."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.run import Run, RunType, RunStatus
from backend.app.models.ticket import Ticket, TicketStatus
from backend.app.models.user import User
from backend.app.schemas.run import RunCreate
from backend.app.audit.events import AuditEvent, AuditEventType
from backend.app.audit.audit_logger import audit_logger


async def create_run(
    db: Session,
    run_in: RunCreate,
    executor: User
) -> Run:
    """
    Create a new run.

    Args:
        db: Database session
        run_in: Run creation data
        executor: User executing the run

    Returns:
        Created run object

    Raises:
        HTTPException: If ticket not found or validation fails
    """
    # Verify ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == run_in.ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Validate run creation based on type
    if run_in.run_type == RunType.ACTION:
        # Action runs require approval
        if ticket.status != TicketStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket must be approved before running action runs"
            )

        # Only admins can trigger action runs (optional policy)
        if not executor.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can trigger action runs"
            )

    # Create run
    run = Run(
        run_type=run_in.run_type,
        status=RunStatus.PENDING,
        ticket_id=run_in.ticket_id,
        executed_by_id=executor.id,
        script_id=run_in.script_id,
        execution_context=run_in.execution_context
    )

    db.add(run)

    # Update ticket status
    ticket.status = TicketStatus.RUNNING

    db.commit()
    db.refresh(run)

    # Log run creation
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.RUN_CREATED,
        actor_id=executor.id,
        actor_username=executor.username,
        resource_type="run",
        resource_id=run.id,
        action=f"Created {run_in.run_type.value} run for ticket {ticket.id}",
        details={
            "run_type": run_in.run_type.value,
            "ticket_id": ticket.id,
            "script_id": run_in.script_id
        }
    ))

    return run


async def update_run_status(
    db: Session,
    run_id: int,
    status: RunStatus,
    result_summary: str | None = None,
    stdout_log: str | None = None,
    stderr_log: str | None = None,
    exit_code: int | None = None
) -> Run:
    """
    Update run status and logs.

    Args:
        db: Database session
        run_id: Run ID
        status: New status
        result_summary: Result summary
        stdout_log: Standard output log
        stderr_log: Standard error log
        exit_code: Exit code

    Returns:
        Updated run object
    """
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )

    # Update run
    run.status = status
    if result_summary is not None:
        run.result_summary = result_summary
    if stdout_log is not None:
        run.stdout_log = stdout_log
    if stderr_log is not None:
        run.stderr_log = stderr_log
    if exit_code is not None:
        run.exit_code = exit_code

    # Update related ticket status
    ticket = run.ticket
    if status == RunStatus.SUCCESS:
        ticket.status = TicketStatus.DONE
        event_type = AuditEventType.RUN_COMPLETED
    elif status == RunStatus.FAILED:
        ticket.status = TicketStatus.FAILED
        event_type = AuditEventType.RUN_FAILED
    elif status == RunStatus.TIMEOUT:
        ticket.status = TicketStatus.FAILED
        event_type = AuditEventType.RUN_TIMEOUT
    elif status == RunStatus.RUNNING:
        event_type = AuditEventType.RUN_STARTED
    else:
        event_type = AuditEventType.RUN_COMPLETED

    db.commit()
    db.refresh(run)

    # Log status update
    await audit_logger.log(AuditEvent(
        event_type=event_type,
        actor_id=run.executed_by_id,
        actor_username=run.executor.username,
        resource_type="run",
        resource_id=run.id,
        action=f"Run status updated to {status.value}",
        details={
            "ticket_id": ticket.id,
            "exit_code": exit_code,
            "success": status == RunStatus.SUCCESS
        },
        success=status == RunStatus.SUCCESS
    ))

    return run
