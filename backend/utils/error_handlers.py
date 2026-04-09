import logging
import os
import traceback
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.utils.errors import categorize_error, http_status_for_error

logger = logging.getLogger("backend.error_handler")


def _get_request_meta(request: Request) -> dict[str, Any]:
    user_id = None
    if hasattr(request.state, "user_id"):
        user_id = request.state.user_id
    elif hasattr(request.state, "user") and getattr(request.state.user, "id", None):
        user_id = request.state.user.id

    return {
        "path": request.url.path,
        "method": request.method,
        "user_id": user_id,
    }


def _get_user_message(category: str, error: Exception) -> str:
    if category == "conflict":
        return "This time slot is no longer available. Please select another."
    if category == "validation":
        return str(error)
    if category == "external":
        return "External service temporarily unavailable. Please try again."
    if category == "database":
        return "Database error. Please try again or contact support."
    return "An error occurred. Please try again or contact support."


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    meta = _get_request_meta(request)
    logger.warning(
        "API HTTPException",
        extra={
            "error": str(exc.detail),
            "status_code": exc.status_code,
            **meta,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "Request error",
            "code": "http",
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    meta = _get_request_meta(request)
    logger.warning(
        "API validation error",
        extra={
            "error": str(exc),
            "status_code": 422,
            **meta,
        },
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request payload.",
            "code": "validation",
            "details": [err.get("msg") for err in exc.errors()],
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    category = categorize_error(exc)
    status_code = http_status_for_error(exc)
    meta = _get_request_meta(request)

    logger.error(
        "API error",
        extra={
            "error": str(exc),
            "category": category,
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
            **meta,
        },
        exc_info=True,
    )

    payload: dict[str, Any] = {
        "error": _get_user_message(category, exc),
        "code": category,
    }

    if os.getenv("PYTHON_ENV") != "production" and os.getenv("NODE_ENV") != "production":
        payload["details"] = str(exc)
        payload["stack"] = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    return JSONResponse(status_code=status_code, content=payload)
