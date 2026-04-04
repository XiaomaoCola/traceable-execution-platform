"""Run execution endpoints."""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from backend.app.core.pagination import apply_pagination_and_sort, build_paginated_response
from backend.app.schemas.run import RunCreate, RunResponse, RunDetailResponse, PaginatedRunResponse
from backend.app.core.dependencies import DatabaseSession, CurrentUser
from backend.app.services.run_service import create_run
from backend.app.services.runner import run_executor
from backend.app.models.run import Run


# 新增
from fastapi import Query
from sqlalchemy import select, func
from backend.app.models.ticket import Ticket


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


# 修改
@router.get("", response_model=PaginatedRunResponse)
async def list_runs(
    db: DatabaseSession,
    current_user: CurrentUser,
    ticket_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    order_by: str = Query(default="created_at"),  # 【新增】
    order: str = Query(default="desc")            # 【新增】
):
    """
    List runs with pagination.

    Optionally filter by ticket_id.
    """
    query = select(Run)

    if ticket_id:
        query = query.where(Run.ticket_id == ticket_id)

    if not current_user.is_admin:
        query = query.join(Ticket).where(Ticket.created_by_id == current_user.id)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    result = await db.execute(
        apply_pagination_and_sort(query, Run, page, page_size, order_by, order)
    )
    runs = result.scalars().all()
    return build_paginated_response(runs, RunResponse, total, page, page_size)



@router.get("/{run_id}", response_model=RunDetailResponse)
async def get_run(
    run_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Get run details including logs.
    """
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )

    # Check permissions
    if not current_user.is_admin:
        from backend.app.models.ticket import Ticket
        ticket_result = await db.execute(select(Ticket).where(Ticket.id == run.ticket_id))
        ticket = ticket_result.scalar_one_or_none()
        if ticket.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this run"
            )

    return run
