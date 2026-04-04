"""Run service for managing execution records."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.models.run import Run, RunType, RunStatus
from backend.app.models.ticket import Ticket, TicketStatus
from backend.app.models.user import User
from backend.app.schemas.run import RunCreate
from backend.app.audit.events import AuditEvent, AuditEventType
from backend.app.audit.audit_logger import audit_logger


async def create_run(
    db: AsyncSession,
    run_in: RunCreate,
    executor: User
) -> Run:
    
    # TODO（权限与状态校验待完善）:
    # 当前仅对 ACTION 类型的 run 做了权限与状态限制，
    # 其他 run 类型（如 proof / precheck 等）几乎没有授权校验。
    #
    # 存在的问题：
    # - 任意已登录用户只要知道 ticket_id，就可能为不属于自己的工单创建 run
    # - 非 ACTION 的 run 仍会修改 ticket.status（如改为 RUNNING），
    #   可能导致工单流程被越权或异常推进
    #
    # 后续需要补充：
    # - 明确哪些用户可以对某个 ticket 创建 run（owner / assignee / admin / 同租户等）
    # - 按 run_type 定义不同的创建权限和 ticket 状态前置条件
    # - 明确哪些 run 类型允许/不允许修改 ticket 的主状态
    #
    # 目标：
    # 防止越权创建 run（IDOR），并避免非执行类 run 干扰工单主流程

    # Verify ticket exists
    result = await db.execute(select(Ticket).where(Ticket.id == run_in.ticket_id))
    ticket = result.scalar_one_or_none()
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

    await db.commit()
    await db.refresh(run)

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
    db: AsyncSession,
    run_id: int,
    new_status: RunStatus,
    result_summary: str | None = None,
    stdout_log: str | None = None,
    stderr_log: str | None = None,
    exit_code: int | None = None
) -> Run:
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )

    # Update run
    run.status = new_status
    if result_summary is not None:
        run.result_summary = result_summary
    if stdout_log is not None:
        run.stdout_log = stdout_log
    if stderr_log is not None:
        run.stderr_log = stderr_log
    if exit_code is not None:
        run.exit_code = exit_code

    # Update related ticket status
    ticket_result = await db.execute(select(Ticket).where(Ticket.id == run.ticket_id))
    ticket = ticket_result.scalar_one_or_none()
    if new_status == RunStatus.SUCCESS:
        ticket.status = TicketStatus.DONE
        event_type = AuditEventType.RUN_COMPLETED
    elif new_status == RunStatus.FAILED:
        ticket.status = TicketStatus.FAILED
        event_type = AuditEventType.RUN_FAILED
    elif new_status == RunStatus.TIMEOUT:
        ticket.status = TicketStatus.FAILED
        event_type = AuditEventType.RUN_TIMEOUT
    elif new_status == RunStatus.RUNNING:
        event_type = AuditEventType.RUN_STARTED
    else:
        event_type = AuditEventType.RUN_COMPLETED

    await db.commit()
    await db.refresh(run)

    # Log status update
    executor_result = await db.execute(select(User).where(User.id == run.executed_by_id))
    executor = executor_result.scalar_one_or_none()
    await audit_logger.log(AuditEvent(
        event_type=event_type,
        actor_id=run.executed_by_id,
        actor_username=executor.username if executor else "unknown",
        resource_type="run",
        resource_id=run.id,
        action=f"Run status updated to {new_status.value}",
        details={
            "ticket_id": ticket.id,
            "exit_code": exit_code,
            "success": new_status == RunStatus.SUCCESS
        },
        success=new_status == RunStatus.SUCCESS
    ))

    return run
