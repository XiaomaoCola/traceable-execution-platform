from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.ticket import Ticket, TicketStatus
from backend.app.models.asset import Asset


@tool
async def search_tickets(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 10,
) -> str:
    """搜索工单列表。

    Args:
        status: 状态过滤，可选值 draft / submitted / approved / running / done / failed / closed
        keyword: 在标题和描述中搜索的关键字
        limit: 返回数量上限，默认 10
    """
    async with AsyncSessionLocal() as db:
        query = select(Ticket)

        if status:
            try:
                query = query.where(Ticket.status == TicketStatus(status))
            except ValueError:
                valid = " / ".join(s.value for s in TicketStatus)
                return f"无效状态「{status}」，可用值：{valid}"

        if keyword:
            query = query.where(
                or_(
                    Ticket.title.ilike(f"%{keyword}%"),
                    Ticket.description.ilike(f"%{keyword}%"),
                )
            )

        result = await db.execute(query.order_by(Ticket.created_at.desc()).limit(limit))
        # 上面 query = select(Ticket) 和 两个 query.where 都是在 动态拼 SQL语句， 直到这里才真正发请求到数据库。
        # order_by(Ticket.created_at.desc()) 相当于 ORDER BY created_at DESC ， 按创建时间倒序（最新的在前） 。
        # .limit(limit) 相当于 LIMIT 10 ， 限制返回条数为10条。
        tickets = result.scalars().all()

        if not tickets:
            return "没有找到符合条件的工单"

        lines = [f"共 {len(tickets)} 张工单："]
        for t in tickets:
            lines.append(
                f"  #{t.id} {t.title} "
                f"[{t.status.value}] "
                f"{t.created_at.strftime('%Y-%m-%d')}"
            )
        return "\n".join(lines)


@tool
async def get_ticket_detail(ticket_id: int) -> str:
    """查询某张工单的详细信息，包含关联的设备信息。

    Args:
        ticket_id: 工单 ID（整数）
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Ticket)
            .options(selectinload(Ticket.asset))
            .where(Ticket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            return f"工单 #{ticket_id} 不存在"

        lines = [
            f"工单 #{ticket.id}：{ticket.title}",
            f"状态：{ticket.status.value}",
            f"描述：{ticket.description or '（无）'}",
            f"创建：{ticket.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"更新：{ticket.updated_at.strftime('%Y-%m-%d %H:%M')}",
        ]

        if ticket.asset:
            a = ticket.asset
            lines.append(f"设备：{a.name}（{a.asset_type}）")
            if a.serial_number:
                lines.append(f"  序列号：{a.serial_number}")
            if a.location:
                lines.append(f"  位置：{a.location}")
        else:
            lines.append("设备：未关联")

        return "\n".join(lines)


@tool
async def get_tickets_by_asset(asset_name: str) -> str:
    """查询某台设备的所有工单历史。

    Args:
        asset_name: 设备名称，支持模糊匹配
    """
    async with AsyncSessionLocal() as db:
        asset_result = await db.execute(
            select(Asset).where(Asset.name.ilike(f"%{asset_name}%"))
        )
        assets = asset_result.scalars().all()

        if not assets:
            return f"没有找到名称包含「{asset_name}」的设备"

        lines = []
        for asset in assets:
            ticket_result = await db.execute(
                select(Ticket)
                .where(Ticket.asset_id == asset.id)
                .order_by(Ticket.created_at.desc())
            )
            tickets = ticket_result.scalars().all()
            lines.append(
                f"设备「{asset.name}」({asset.asset_type}"
                + (f"，{asset.location}" if asset.location else "")
                + f") 共 {len(tickets)} 张工单："
            )
            if tickets:
                for t in tickets:
                    lines.append(
                        f"  #{t.id} {t.title} [{t.status.value}] {t.created_at.strftime('%Y-%m-%d')}"
                    )
            else:
                lines.append("  暂无工单记录")

        return "\n".join(lines)
