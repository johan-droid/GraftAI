"""
Authentication API Routes

Handles session management, token revocation, and security.
"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.models.tables import UserTable
from backend.utils.db import get_db
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/revoke-current-session")
async def revoke_current_session(request: Request, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> dict:
    """
    Revoke the current user's session.

    This invalidates the current JWT token by adding it to a blocklist
    or by updating the user's token version.

    SECURITY: In production, this should use a Redis blocklist or similar
    for immediate revocation across all instances.
    """
    from sqlalchemy import select
    stmt = select(UserTable).where(UserTable.id == current_user.id).with_for_update()
    result = await db.execute(stmt)
    locked_user = result.scalars().first()
    if not locked_user:
        raise HTTPException(status_code=401, detail="User not found")
    locked_user.token_version = (locked_user.token_version or 0) + 1
    await db.commit()
    try:
        import hashlib

        from backend.auth.config import REFRESH_TOKEN_EXPIRE_DAYS
        from backend.core.redis import cache_set
        auth_header = request.headers.get("Authorization")
        current_token = None
        if auth_header and auth_header.startswith("Bearer "):
            current_token = auth_header.split(" ", 1)[1].strip()
        else:
            current_token = request.cookies.get("graftai_access_token")
        if current_token:
            token_hash = hashlib.sha256(current_token.encode()).hexdigest()
            blacklist_key = f"token_blacklist:{token_hash}"
            await cache_set(blacklist_key, "revoked", expire=REFRESH_TOKEN_EXPIRE_DAYS * 86400)
            logger.info("Token added to blacklist for user %s...", locked_user.id[:8])
    except Exception as e:
        logger.exception("Failed to blacklist token: %s", e)
    logger.info("🔒 Session revoked for user %s...", locked_user.id[:8])
    return {"status": "revoked", "message": "Current session revoked. Please log in again."}

@router.post("/revoke-all-sessions")
async def revoke_all_sessions(db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> dict:
    """
    Revoke all sessions for the current user.

    This invalidates all active JWT tokens for the user across all devices.
    Useful for security incidents or password changes.
    """
    current_user.token_version = (current_user.token_version or 0) + 1000
    current_user.password_changed_at = datetime.now(UTC)
    await db.commit()
    logger.warning("🔒 ALL sessions revoked for user %s...", current_user.id[:8])
    return {"status": "revoked", "message": "All sessions revoked. Please log in again on all devices."}

@router.get("/sessions")
async def list_active_sessions(db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> dict:
    """
    List active sessions for the current user.

    NOTE: This is a simplified implementation. In production,
    track actual sessions in a database or Redis with device info,
    IP addresses, and last activity timestamps.
    """
    return {"active_sessions": 1, "token_version": current_user.token_version or 0, "last_login": current_user.last_login_at.isoformat() if current_user.last_login_at else None, "message": "Detailed session tracking not implemented yet."}
