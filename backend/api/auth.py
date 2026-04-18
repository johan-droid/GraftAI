"""
Authentication API Routes

Handles session management, token revocation, and security.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.db import get_db
from backend.api.deps import get_current_user
from backend.models.tables import UserTable
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/revoke-current-session")
async def revoke_current_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> dict:
    """
    Revoke the current user's session.

    This invalidates the current JWT token by adding it to a blocklist
    or by updating the user's token version.

    SECURITY: In production, this should use a Redis blocklist or similar
    for immediate revocation across all instances.
    """
    # Increment token version to invalidate current tokens
    # All tokens with older versions will be rejected
    current_user.token_version = (current_user.token_version or 0) + 1

    await db.commit()

    logger.info(f"🔒 Session revoked for user {current_user.id[:8]}...")

    return {
        "status": "revoked",
        "message": "Current session revoked. Please log in again.",
    }


@router.post("/revoke-all-sessions")
async def revoke_all_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> dict:
    """
    Revoke all sessions for the current user.

    This invalidates all active JWT tokens for the user across all devices.
    Useful for security incidents or password changes.
    """
    # Increment token version by a large amount to ensure all tokens are invalidated
    current_user.token_version = (current_user.token_version or 0) + 1000

    # Also update last password change timestamp if provided
    current_user.password_changed_at = datetime.now(timezone.utc)

    await db.commit()

    logger.warning(f"🔒 ALL sessions revoked for user {current_user.id[:8]}...")

    return {
        "status": "revoked",
        "message": "All sessions revoked. Please log in again on all devices.",
    }


@router.get("/sessions")
async def list_active_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> dict:
    """
    List active sessions for the current user.

    NOTE: This is a simplified implementation. In production,
    track actual sessions in a database or Redis with device info,
    IP addresses, and last activity timestamps.
    """
    # For now, return basic info
    # In production, query a sessions table for detailed session info
    return {
        "active_sessions": 1,  # Simplified - actual count from sessions table
        "token_version": current_user.token_version or 0,
        "last_login": current_user.last_login_at.isoformat()
        if current_user.last_login_at
        else None,
        "message": "Detailed session tracking not implemented yet.",
    }
