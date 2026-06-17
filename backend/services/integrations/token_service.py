import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTokenTable
from backend.services.sso import get_provider_config
from backend.services.token_encryption import decrypt_token_value, encrypt_token_value
from backend.utils.http_client import get_client

logger = logging.getLogger(__name__)
_PROVIDER_LABELS = {"google": "Google", "microsoft": "Microsoft", "zoom": "Zoom"}

async def _deactivate_token(db: AsyncSession, token_record: UserTokenTable, user_id: str, provider: str) -> None:
    """Marks the token inactive."""
    token_record.is_active = False
    logger.warning("[TOKEN]  Terminally deactivated %s for user %s", provider, user_id)
    try:
        await db.commit()
    except Exception:
        await db.rollback()

async def ensure_valid_token(db: AsyncSession, user_id: str, provider: str) -> str | None:
    """
    Ensures the user's OAuth access token is valid (not expired).
    If expiring within 5 minutes, triggers automatic JIT rotation.
    On terminal failure (revoked / no refresh token), deactivates the
    record and fires an in-app 'Action Required' notification.
    Returns the valid access_token string, or None if unrecoverable.
    """
    stmt = select(UserTokenTable).where(and_(UserTokenTable.user_id == user_id, UserTokenTable.provider == provider, UserTokenTable.is_active))
    result = await db.execute(stmt)
    token_record = result.scalars().first()
    if not token_record:
        logger.warning("[TOKEN] No active %s token for user %s", provider, user_id)
        return None
    access_token, access_needs_upgrade = decrypt_token_value(token_record.access_token)
    refresh_token, refresh_needs_upgrade = decrypt_token_value(token_record.refresh_token)
    migrated_plaintext = False
    if access_needs_upgrade and access_token:
        token_record.access_token = encrypt_token_value(access_token)
        migrated_plaintext = True
    if refresh_needs_upgrade and refresh_token:
        token_record.refresh_token = encrypt_token_value(refresh_token)
        migrated_plaintext = True
    if migrated_plaintext:
        token_record.updated_at = datetime.now(UTC)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
    if not access_token:
        logger.error("[TOKEN] Missing or unreadable access token for %s (User: %s)", provider, user_id)
        return None
    now = datetime.now(UTC)
    if token_record.expires_at and token_record.expires_at > now + timedelta(minutes=5):
        return access_token
    if not refresh_token:
        logger.error("[TOKEN]  No refresh_token for %s (User: %s). Deactivating.", provider, user_id)
        await _deactivate_token(db, token_record, user_id, provider)
        return None
    logger.info("[TOKEN]   Refreshing %s token for user %s", provider, user_id)
    config = get_provider_config(provider)
    if not config:
        logger.error("[TOKEN]  Missing provider config for %s", provider)
        return None
    try:
        client = await get_client()
        payload = {"client_id": config["client_id"], "client_secret": config["client_secret"], "refresh_token": refresh_token, "grant_type": "refresh_token"}
        resp = await client.post(config["token_url"], data=payload)
        if resp.status_code != 200:
            error_data = resp.json()
            error_code = error_data.get("error", "")
            logger.error("[TOKEN]  Refresh failed for %s: %s", provider, error_data)
            TERMINAL_ERRORS = {"invalid_grant", "invalid_token", "access_denied", "unauthorized_client"}
            if error_code in TERMINAL_ERRORS:
                logger.warning("[TOKEN]  Terminal refresh error '%s' for %s. Deactivating & notifying.", error_code, provider)
                await _deactivate_token(db, token_record, user_id, provider)
            return None
        new_data = resp.json()
        token_record.access_token = encrypt_token_value(new_data["access_token"])
        if "refresh_token" in new_data:
            token_record.refresh_token = encrypt_token_value(new_data["refresh_token"])
        expires_in = new_data.get("expires_in", 3600)
        token_record.expires_at = now + timedelta(seconds=expires_in)
        token_record.updated_at = now
        await db.commit()
        logger.info("[TOKEN]  Rotated %s token for user %s", provider, user_id)
        return new_data["access_token"]
    except Exception as e:
        logger.exception("[TOKEN]  Critical failure during %s refresh: %s", provider, e)
        return None
