import asyncio
import hmac
import logging
import threading

import pyotp
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTable
from backend.utils.db import get_async_session_maker


logger = logging.getLogger(__name__)


def _extract_device_fingerprints(preferences: dict) -> list[str]:
    stored = (
        preferences.get("trusted_device_fingerprints")
        or preferences.get("device_fingerprints")
        or preferences.get("mfa_device_fingerprints")
    )

    if stored is None:
        return []

    if isinstance(stored, str):
        stored = [stored]
    elif isinstance(stored, dict):
        stored = stored.get("fingerprints") or stored.get("fingerprint") or []

    if isinstance(stored, (list, tuple, set)):
        return [item.strip() for item in stored if isinstance(item, str) and item.strip()]

    return []


async def _check_device_fingerprint_async(user_id: str, fingerprint: str) -> bool:
    normalized_fingerprint = fingerprint.strip()
    if not normalized_fingerprint:
        logger.warning("Missing device fingerprint for user %s", user_id)
        return False

    try:
        session_factory = get_async_session_maker()
    except RuntimeError as exc:
        logger.warning(
            "Device fingerprint check unavailable for user %s: %s", user_id, exc
        )
        return False

    async with session_factory() as db:
        user = await db.get(UserTable, user_id)
        if not user:
            logger.warning("No user found for device fingerprint check: %s", user_id)
            return False

        preferences = user.preferences if isinstance(user.preferences, dict) else {}
        stored_fingerprints = _extract_device_fingerprints(preferences)
        if not stored_fingerprints:
            logger.info("No stored device fingerprint found for user %s", user_id)
            return False

        for stored_fingerprint in stored_fingerprints:
            if hmac.compare_digest(stored_fingerprint, normalized_fingerprint):
                return True

        logger.warning("Device fingerprint mismatch for user %s", user_id)
        return False


def _run_coroutine_sync(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, bool] = {}
    error: list[BaseException] = []

    def runner():
        try:
            result["value"] = asyncio.run(coro)
        except BaseException as exc:
            error.append(exc)

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if error:
        raise error[0]

    return result.get("value", False)


async def start_mfa_enrollment(db: AsyncSession, user_id: str) -> dict:
    """Generates a new TOTP secret for user enrollment."""
    secret = pyotp.random_base32()
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=f"user_{user_id}@graftai", issuer_name="GraftAI"
    )
    return {"secret": secret, "otp_uri": otp_uri}


async def enable_mfa(db: AsyncSession, user_id: str, secret: str) -> bool:
    """Persists the MFA secret and enables MFA for the user via preferences JSON."""
    user = await db.get(UserTable, user_id)
    if not user:
        return False

    prefs = dict(user.preferences or {})
    prefs["mfa_secret"] = secret
    prefs["mfa_enabled"] = True
    user.preferences = prefs
    await db.commit()
    return True


async def disable_mfa(db: AsyncSession, user_id: str) -> bool:
    """Disables MFA for the user."""
    user = await db.get(UserTable, user_id)
    if not user:
        return False

    prefs = dict(user.preferences or {})
    prefs["mfa_secret"] = None
    prefs["mfa_enabled"] = False
    user.preferences = prefs
    await db.commit()
    return True


async def verify_mfa_token(
    db: AsyncSession, user_id: str, token: str, temp_secret: str = None
) -> bool:
    """Validates a TOTP token against a stored or temporary secret."""
    if temp_secret:
        secret = temp_secret
    else:
        user = await db.get(UserTable, user_id)
        if not user:
            return False
        prefs = user.preferences or {}
        secret = prefs.get("mfa_secret") if isinstance(prefs, dict) else None
        if not secret:
            return False

    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


async def is_mfa_enabled(db: AsyncSession, user_id: str) -> bool:
    """Returns whether MFA is enabled for the given user."""
    user = await db.get(UserTable, user_id)
    if not user:
        return False
    prefs = user.preferences or {}
    return bool(prefs.get("mfa_enabled")) if isinstance(prefs, dict) else False


def check_device_fingerprint(user_id: str, fingerprint: str) -> bool:
    return _run_coroutine_sync(_check_device_fingerprint_async(user_id, fingerprint))
