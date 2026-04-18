import logging
import os
import traceback
from typing import Any

from starlette.requests import Request
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


def _is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv("PYTHON_ENV") == "production" or os.getenv("ENV") == "production"


async def http_exception_handler(request: Request, exc: Exception):
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    meta = _get_request_meta(request)

    # Get request ID for correlation
    request_id = getattr(request.state, "request_id", None)

    logger.warning(
        "API HTTPException",
        extra={
            "error": str(exc.detail),
            "status_code": exc.status_code,
            "request_id": request_id,
            **meta,
        },
    )

    # Sanitize error message in production (don't expose internal details)
    if _is_production() and exc.status_code >= 500:
        user_message = (
            "An internal error occurred. Please try again or contact support."
        )
    else:
        user_message = exc.detail if isinstance(exc.detail, str) else "Request error"

    content = {
        "error": user_message,
        "code": "http",
        "detail": exc.detail,
    }

    # Include request ID for debugging (safe to expose)
    if request_id:
        content["request_id"] = request_id

    # Only include details in non-production
    if not _is_production():
        content["details"] = str(exc.detail)

    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_exception_handler(request: Request, exc: Exception):
    if not isinstance(exc, RequestValidationError):
        raise exc
    meta = _get_request_meta(request)
    request_id = getattr(request.state, "request_id", None)

    logger.warning(
        "API validation error",
        extra={
            "error": str(exc),
            "status_code": 422,
            "request_id": request_id,
            **meta,
        },
    )

    content = {
        "error": "Invalid request payload.",
        "code": "validation",
    }

    # Include request ID for debugging
    if request_id:
        content["request_id"] = request_id

    # Only include detailed field errors in non-production
    # (to prevent schema information leakage)
    if not _is_production():
        normalized_errors = []
        for err in exc.errors():
            normalized_errors.append(
                {
                    "loc": list(err.get("loc", [])),
                    "msg": err.get("msg"),
                    "type": err.get("type"),
                }
            )
        content["detail"] = normalized_errors
        content["details"] = [err.get("msg") for err in normalized_errors]

    return JSONResponse(status_code=422, content=content)


async def generic_exception_handler(request: Request, exc: Exception):
    category = categorize_error(exc)
    status_code = http_status_for_error(exc)
    meta = _get_request_meta(request)
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        "API error",
        extra={
            "error": str(exc),
            "category": category,
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
            "request_id": request_id,
            **meta,
        },
        exc_info=True,
    )

    payload: dict[str, Any] = {
        "error": _get_user_message(category, exc),
        "code": category,
    }

    # Always include request ID for error correlation
    if request_id:
        payload["request_id"] = request_id

    # Only include internal details in non-production
    if not _is_production():
        payload["details"] = str(exc)
        payload["stack"] = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )

    return JSONResponse(status_code=status_code, content=payload)
