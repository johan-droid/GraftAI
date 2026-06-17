import logging
from datetime import UTC, datetime

import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserMFATable, UserTable

logger = logging.getLogger(__name__)


async def start_mfa_enrollment(db: AsyncSession, user_id: str) -> dict:
    """Generates a new TOTP secret for user enrollment."""
    secret = pyotp.random_base32()
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=f"user_{user_id}@graftai", issuer_name="GraftAI")
    return {"secret": secret, "otp_uri": otp_uri}


async def enable_mfa(db: AsyncSession, user_id: str, secret: str, token: str) -> bool:
    """Verifies the TOTP token and enables MFA for the user using UserMFATable."""
    totp = pyotp.TOTP(secret)
    if not totp.verify(token, valid_window=1):
        return False
    stmt = select(UserMFATable).where(UserMFATable.user_id == user_id)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        existing.secret = secret
        existing.is_enabled = True
        existing.verified_at = datetime.now(UTC)
        existing.updated_at = datetime.now(UTC)
    else:
        record = UserMFATable(user_id=user_id, mfa_type="totp", secret=secret, is_enabled=True, verified_at=datetime.now(UTC))
        db.add(record)
    await db.commit()
    return True


async def disable_mfa(db: AsyncSession, user_id: str) -> bool:
    """Disables MFA for the user."""
    stmt = select(UserMFATable).where(UserMFATable.user_id == user_id)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return False
    record.is_enabled = False
    record.secret = None
    record.verified_at = None
    record.updated_at = datetime.now(UTC)
    await db.commit()
    return True


async def verify_mfa_token(db: AsyncSession, user_id: str, token: str) -> bool:
    """Validates a TOTP token against the stored secret in UserMFATable."""
    stmt = select(UserMFATable).where(UserMFATable.user_id == user_id, UserMFATable.is_enabled == True)
    record = (await db.execute(stmt)).scalars().first()
    if not record or not record.secret:
        return False
    totp = pyotp.TOTP(record.secret)
    return totp.verify(token, valid_window=1)


async def is_mfa_enabled(db: AsyncSession, user_id: str) -> bool:
    """Returns whether MFA is enabled for the given user via UserMFATable."""
    stmt = select(UserMFATable).where(UserMFATable.user_id == user_id, UserMFATable.is_enabled == True)
    record = (await db.execute(stmt)).scalars().first()
    return record is not None
