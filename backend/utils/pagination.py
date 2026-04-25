"""
Standardized pagination utilities for API endpoints.
Provides consistent pagination across all list endpoints.
"""

from typing import Generic, Optional, Sequence, TypeVar
from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "asc"


class PaginationMeta(BaseModel):
    total: int
    page: int
    size: int
    has_more: bool


class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    pagination: PaginationMeta


def get_pagination_params(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> PaginationParams:
    return PaginationParams(
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def paginate(items: Sequence[T], total: int, page: int, size: int) -> PaginatedResponse[T]:
    return PaginatedResponse(
        items=items,
        pagination=PaginationMeta(
            total=total,
            page=page,
            size=size,
            has_more=(page * size) < total,
        ),
    )


async def paginate_query(
    db: AsyncSession,
    stmt: Select,
    pagination: PaginationParams,
    model: type[T],
) -> tuple[list[T], PaginationMeta]:
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(
        stmt.offset((pagination.page - 1) * pagination.size).limit(pagination.size)
    )
    items = result.scalars().all()
    pagination_meta = PaginationMeta(
        total=total,
        page=pagination.page,
        size=pagination.size,
        has_more=(pagination.page * pagination.size) < total,
    )
    return items, pagination_meta
