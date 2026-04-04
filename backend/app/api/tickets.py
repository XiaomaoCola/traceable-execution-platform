"""Ticket management endpoints."""

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func, text
from datetime import datetime

from backend.app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketApprove, PaginatedTicketResponse
from backend.app.core.dependencies import DatabaseSession, CurrentUser, CurrentAdmin
from backend.app.services.ticket_service import create_ticket, approve_ticket, update_ticket
from backend.app.models.ticket import Ticket
from backend.app.core.pagination import apply_pagination_and_sort, build_paginated_response
import json
from backend.app.core.dependencies import DatabaseSession, CurrentUser, CurrentAdmin, RedisClient


router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketResponse)
async def create_new_ticket(
    ticket_in: TicketCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
    redis: RedisClient 
):
    """Create a new ticket."""
    ticket = await create_ticket(db, ticket_in, current_user)
    # 创建工单时清除该用户的工单列表缓存
    if redis:
        async for key in redis.scan_iter(f"tickets:{current_user.id}:*"):
            await redis.delete(key)
    return ticket


# 修改
@router.get("", response_model=PaginatedTicketResponse)
async def list_tickets(
    db: DatabaseSession,
    current_user: CurrentUser,
    redis: RedisClient,  
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
     # ↓ 新增四个筛选参数
    keyword: str | None = Query(default=None),           # 标题关键词
    status: str | None = Query(default=None),            # 状态筛选
    asset_id: int | None = Query(default=None),          # 资产筛选
    start_date: datetime | None = Query(default=None),   # 开始时间
    end_date: datetime | None = Query(default=None),     # 结束时间
    order_by: str = Query(default="created_at"),         # 【新增】
    order: str = Query(default="desc")                   # 【新增】
):
        # 【新增】缓存 key，包含所有查询参数
    cache_key = f"tickets:{current_user.id}:{page}:{page_size}:{keyword}:{status}:{asset_id}:{start_date}:{end_date}:{order_by}:{order}"

    # 【新增】有缓存直接返回
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
    query = select(Ticket)

    if not current_user.is_admin:
        query = query.where(Ticket.created_by_id == current_user.id)

    if keyword:
        query = query.where(Ticket.title.ilike(f"%{keyword}%"))
    if status:
        query = query.where(Ticket.status == status)
    if asset_id:
        query = query.where(Ticket.asset_id == asset_id)
    if start_date:
        query = query.where(Ticket.created_at >= start_date)
    if end_date:
        query = query.where(Ticket.created_at <= end_date) 

    # 总数
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    # 分页数据
    result = await db.execute(
        apply_pagination_and_sort(query, Ticket, page, page_size, order_by, order))
    tickets = result.scalars().all()

    response = build_paginated_response(tickets, TicketResponse, total, page, page_size)

    if redis:
        await redis.set(cache_key, json.dumps(response), ex=60)

    return response


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

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get ticket by ID."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    if not current_user.is_admin and ticket.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this ticket"
        )

    return ticket

@router.post("/{ticket_id}/approve", response_model=TicketResponse)
async def approve_ticket_endpoint(
    ticket_id: int,
    db: DatabaseSession,
    current_admin: CurrentAdmin,
    redis: RedisClient 
):
    """
    Approve a ticket (admin only).

    Required for action runs.
    """
    ticket = await approve_ticket(db, ticket_id, current_admin)
    # 审批工单时清除所有用户的工单列表缓存（审批影响所有人看到的状态）
    if redis:
        async for key in redis.scan_iter("tickets:*"):
            await redis.delete(key)
    return ticket

