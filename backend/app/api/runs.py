"""Run execution endpoints."""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from backend.app.schemas.run import RunCreate, RunResponse, RunDetailResponse
from backend.app.core.dependencies import DatabaseSession, CurrentUser
from backend.app.services.run_service import create_run
from backend.app.services.runner import run_executor
from backend.app.models.run import Run


router = APIRouter(prefix="/runs", tags=["Runs"])


@router.post("", response_model=RunResponse)
async def create_new_run(
    run_in: RunCreate,
    background_tasks: BackgroundTasks,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Create and execute a new run.

    The run will be executed in the background.
    """
    # Create run
    run = await create_run(db, run_in, current_user)

    # Execute run in background
    background_tasks.add_task(run_executor.execute_run, db, run)

    return run


@router.get("", response_model=list[RunResponse])
async def list_runs(
    db: DatabaseSession,
    current_user: CurrentUser,
    ticket_id: int | None = None,
    skip: int = 0,
    limit: int = 100
):
    """
    List runs.

    Optionally filter by ticket_id.
    """
    query = db.query(Run)

    if ticket_id:
        query = query.filter(Run.ticket_id == ticket_id)

    # Non-admins can only see runs from their own tickets
    if not current_user.is_admin:
        from backend.app.models.ticket import Ticket
        query = query.join(Ticket).filter(Ticket.created_by_id == current_user.id)

    runs = query.order_by(Run.created_at.desc()).offset(skip).limit(limit).all()
    return runs


@router.get("/{run_id}", response_model=RunDetailResponse)
async def get_run(
    run_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Get run details including logs.
    """
    run = db.query(Run).filter(Run.id == run_id).first()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )

    # Check permissions
    if not current_user.is_admin:
        if run.ticket.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this run"
            )

    return run
