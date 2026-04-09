import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.models.tables import UserTokenTable
# Removed: NotificationTable deleted
from backend.services.sso import get_provider_config
from backend.utils.http_client import get_client

logger = logging.getLogger(__name__)

# Provider-friendly display names for user-facing notifications
_PROVIDER_LABELS = {
    "google": "Google",
    "microsoft": "Microsoft",
    "zoom": "Zoom",
}


async def _deactivate_token(db: AsyncSession, token_record: UserTokenTable, user_id: str, provider: str) -> None:
    """Marks the token inactive."""
    token_record.is_active = False
    logger.warning(f"[TOKEN] 🚫 Terminally deactivated {provider} for user {user_id}")
    try:
        await db.commit()
    except Exception:
        await db.rollback()


async def ensure_valid_token(db: AsyncSession, user_id: str, provider: str) -> Optional[str]:
    """
    Ensures the user's OAuth access token is valid (not expired).
    If expiring within 5 minutes, triggers automatic JIT rotation.
    On terminal failure (revoked / no refresh token), deactivates the
    record and fires an in-app 'Action Required' notification.
    Returns the valid access_token string, or None if unrecoverable.
    """
    stmt = select(UserTokenTable).where(
        and_(
            UserTokenTable.user_id == user_id,
            UserTokenTable.provider == provider,
            UserTokenTable.is_active == True,
        )
    )
    result = await db.execute(stmt)
    token_record = result.scalars().first()

    if not token_record:
        logger.warning(f"[TOKEN] No active {provider} token for user {user_id}")
        return None

    # ── Fast path: token still healthy ──────────────────────────────────────
    now = datetime.now(timezone.utc)
    if token_record.expires_at and token_record.expires_at > (now + timedelta(minutes=5)):
        return token_record.access_token

    # ── Token expired / expiring – need refresh ──────────────────────────────
    if not token_record.refresh_token:
        logger.error(f"[TOKEN] ⚠️ No refresh_token for {provider} (User: {user_id}). Deactivating.")
        await _deactivate_token(db, token_record, user_id, provider)
        return None

    logger.info(f"[TOKEN] ♻️  Refreshing {provider} token for user {user_id}")

    config = get_provider_config(provider)
    if not config:
        logger.error(f"[TOKEN] ❌ Missing provider config for {provider}")
        return None

    try:
        client = await get_client()
        payload = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "refresh_token": token_record.refresh_token,
            "grant_type": "refresh_token",
        }

        resp = await client.post(config["token_url"], data=payload)

        if resp.status_code != 200:
            error_data = resp.json()
            error_code = error_data.get("error", "")
            logger.error(f"[TOKEN] ❌ Refresh failed for {provider}: {error_data}")

            # Terminal errors: refresh token is permanently invalid
            TERMINAL_ERRORS = {"invalid_grant", "invalid_token", "access_denied", "unauthorized_client"}
            if error_code in TERMINAL_ERRORS:
                logger.warning(f"[TOKEN] 🚫 Terminal refresh error '{error_code}' for {provider}. Deactivating & notifying.")
                await _deactivate_token(db, token_record, user_id, provider)

            return None

        # ── Success: rotate tokens ───────────────────────────────────────────
        new_data = resp.json()
        token_record.access_token = new_data["access_token"]
        if "refresh_token" in new_data:
            token_record.refresh_token = new_data["refresh_token"]

        expires_in = new_data.get("expires_in", 3600)
        token_record.expires_at = now + timedelta(seconds=expires_in)
        token_record.updated_at = now

        await db.commit()
        logger.info(f"[TOKEN] ✅ Rotated {provider} token for user {user_id}")
        return token_record.access_token

    except Exception as e:
        logger.error(f"[TOKEN] ❌ Critical failure during {provider} refresh: {e}")
        return None
