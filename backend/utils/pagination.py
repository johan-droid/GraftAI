"""
Standardized pagination utilities for API endpoints.
Provides consistent pagination across all list endpoints.
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from dataclasses import dataclass
from math import ceil

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar("T")


@dataclass
class PaginationParams:
    """Standard pagination parameters."""

    page: int = 1
    per_page: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "desc"

    @property
    def offset(self) -> int:
        """Calculate SQL offset from page and per_page."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Return per_page as SQL limit."""
        return self.per_page


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
) -> PaginationParams:
    """
    Dependency function for FastAPI to get pagination parameters.

    Usage:
        @app.get("/items")
        async def get_items(
            pagination: PaginationParams = Depends(get_pagination_params)
        ):
            ...
    """
    return PaginationParams(
        page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response structure.

    Example:
        {
            "data": [...],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": 100,
                "total_pages": 5,
                "has_next": True,
                "has_prev": False
            }
        }
    """

    data: List[T]
    pagination: Dict[str, Any]

    class Config:
        from_attributes = True


class PaginationHelper:
    """
    Helper class for creating paginated queries and responses.
    """

    @staticmethod
    async def paginate_query(
        db: AsyncSession, query, params: PaginationParams, model_class: type = None
    ) -> tuple[List, int]:
        """
        Execute a paginated query and return results with total count.

        Args:
            db: Database session
            query: SQLAlchemy select query
            params: Pagination parameters
            model_class: Optional model class for count query

        Returns:
            Tuple of (results, total_count)
        """
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        paginated_query = query.offset(params.offset).limit(params.limit)

        # Apply sorting if specified
        if params.sort_by and model_class:
            if hasattr(model_class, params.sort_by):
                sort_column = getattr(model_class, params.sort_by)
                if params.sort_order == "desc":
                    paginated_query = paginated_query.order_by(sort_column.desc())
                else:
                    paginated_query = paginated_query.order_by(sort_column.asc())

        result = await db.execute(paginated_query)
        items = result.scalars().all()

        return items, total

    @staticmethod
    def create_pagination_metadata(
        params: PaginationParams, total: int
    ) -> Dict[str, Any]:
        """
        Create pagination metadata for response.

        Args:
            params: Pagination parameters
            total: Total number of items

        Returns:
            Pagination metadata dictionary
        """
        total_pages = ceil(total / params.per_page) if total > 0 else 1

        return {
            "page": params.page,
            "per_page": params.per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": params.page < total_pages,
            "has_prev": params.page > 1,
            "next_page": params.page + 1 if params.page < total_pages else None,
            "prev_page": params.page - 1 if params.page > 1 else None,
        }

    @staticmethod
    def create_response(
        data: List[T], params: PaginationParams, total: int
    ) -> PaginatedResponse[T]:
        """
        Create a complete paginated response.

        Args:
            data: List of items for current page
            params: Pagination parameters
            total: Total number of items

        Returns:
            Paginated response object
        """
        pagination = PaginationHelper.create_pagination_metadata(params, total)

        return PaginatedResponse(data=data, pagination=pagination)

    @staticmethod
    def create_cursor_response(
        data: List[T],
        next_cursor: Optional[str] = None,
        prev_cursor: Optional[str] = None,
        has_more: bool = False,
    ) -> Dict[str, Any]:
        """
        Create cursor-based paginated response.

        Args:
            data: List of items
            next_cursor: Cursor for next page
            prev_cursor: Cursor for previous page
            has_more: Whether there are more items

        Returns:
            Cursor pagination response
        """
        return {
            "data": data,
            "pagination": {
                "type": "cursor",
                "next_cursor": next_cursor,
                "prev_cursor": prev_cursor,
                "has_more": has_more,
            },
        }


async def paginate(
    db: AsyncSession, query, params: PaginationParams, model_class: type = None
) -> tuple[List, Dict[str, Any]]:
    """
    Convenience function for pagination.

    Args:
        db: Database session
        query: SQLAlchemy select query
        params: Pagination parameters
        model_class: Optional model class for sorting

    Returns:
        Tuple of (items, pagination_metadata)
    """
    items, total = await PaginationHelper.paginate_query(db, query, params, model_class)
    pagination = PaginationHelper.create_pagination_metadata(params, total)
    return items, pagination


def add_pagination_headers(response, pagination: Dict[str, Any]) -> None:
    """
    Add pagination metadata to response headers.
    Useful for API consumers that prefer headers over body.

    Args:
        response: FastAPI response object
        pagination: Pagination metadata dictionary
    """
    response.headers["X-Page"] = str(pagination["page"])
    response.headers["X-Per-Page"] = str(pagination["per_page"])
    response.headers["X-Total"] = str(pagination["total"])
    response.headers["X-Total-Pages"] = str(pagination["total_pages"])

    if pagination.get("has_next"):
        response.headers["X-Has-Next"] = "true"
    if pagination.get("has_prev"):
        response.headers["X-Has-Prev"] = "true"


# Common pagination presets
class PaginationPresets:
    """Predefined pagination configurations."""

    SMALL = PaginationParams(page=1, per_page=10)
    DEFAULT = PaginationParams(page=1, per_page=20)
    LARGE = PaginationParams(page=1, per_page=50)
    MAX = PaginationParams(page=1, per_page=100)


# Example usage decorators
from functools import wraps


def paginated_endpoint(per_page_default: int = 20, per_page_max: int = 100):
    """
    Decorator to add standard pagination to an endpoint.

    Usage:
        @app.get("/items")
        @paginated_endpoint(per_page_default=20)
        async def get_items(
            pagination: PaginationParams = Depends(get_pagination_params),
            db: AsyncSession = Depends(get_db)
        ):
            # Your logic here
            pass
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, pagination: PaginationParams = None, **kwargs):
            if pagination and pagination.per_page > per_page_max:
                pagination.per_page = per_page_max
            return await func(*args, pagination=pagination, **kwargs)

        return wrapper

    return decorator
