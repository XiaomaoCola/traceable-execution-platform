"""通用分页和排序工具函数"""

from sqlalchemy import asc, desc
from sqlalchemy.sql import Select


def apply_pagination_and_sort(
    query: Select,
    model,
    page: int,
    page_size: int,
    order_by: str = "created_at",
    order: str = "desc"
) -> Select:
    """
    对查询应用排序和分页。

    Args:
        query: 已构建好过滤条件的 select 查询
        model: SQLAlchemy 模型类，用于获取排序字段
        page: 当前页码
        page_size: 每页条数
        order_by: 排序字段名
        order: 排序方向 asc 或 desc

    Returns:
        应用了排序和分页的查询
    """
    sort_column = getattr(model, order_by, model.created_at)
    sort_func = desc(sort_column) if order == "desc" else asc(sort_column)

    return (
        query.order_by(sort_func)
             .offset((page - 1) * page_size)
             .limit(page_size)
    )


def build_paginated_response(items, response_schema, total: int, page: int, page_size: int) -> dict:
    """
    构建统一的分页响应结构。

    Args:
        items: 查询结果列表
        response_schema: Pydantic schema 类，用于序列化
        total: 总条数
        page: 当前页码
        page_size: 每页条数

    Returns:
        标准分页响应字典
    """
    return {
        "data": [response_schema.model_validate(item).model_dump(mode="json") for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }