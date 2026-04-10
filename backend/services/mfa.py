import pyotp
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import UserTable


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


async def verify_mfa_token(db: AsyncSession, user_id: str, token: str, temp_secret: str = None) -> bool:
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
    return True