"""Backwards-compatible re-exports.

Canonical auth dependencies live in :mod:`backend.auth.schemes`
(cookie-aware ``get_current_user`` + ``require_admin``).
This module re-exports them so existing ``from backend.api.deps import ...``
imports keep working, and adds ``require_active_subscription``.
"""

from fastapi import Depends

from backend.auth.schemes import (
    get_current_user,
    get_current_user_id,
    oauth2_scheme,
    require_admin,
)
from backend.models.tables import UserTable
from backend.utils.db import get_db

__all__ = [
    "get_current_user",
    "get_current_user_id",
    "get_db",
    "oauth2_scheme",
    "require_active_subscription",
    "require_admin",
]

async def require_active_subscription(current_user: UserTable=Depends(get_current_user)) -> UserTable:
    """Dependency to enforce active paid subscription or active trial for premium endpoints."""
    if current_user.subscription_status == "active":
        return current_user
    if current_user.trial_active:
        return current_user
    raise HTTPException(status_code=402, detail="Active subscription required to access this resource")
