import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ACCESS_TOKEN_TYPE,
    ALGORITHM,
    REFRESH_TOKEN_TYPE,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from backend.models.tables import UserTable, UserTokenTable
from backend.services.token_encryption import decrypt_token_value, encrypt_token_value

logger = logging.getLogger(__name__)

def _create_jwt_token_impl(user_id: str, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    if token_type == REFRESH_TOKEN_TYPE:
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "type": token_type,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: str) -> str:
    return _create_jwt_token_impl(user_id, ACCESS_TOKEN_TYPE)


def create_refresh_token(user_id: str) -> str:
    return _create_jwt_token_impl(user_id, REFRESH_TOKEN_TYPE)


def create_token_pair(user_id: str) -> dict[str, str]:
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
    }


def decode_jwt_token(token: str, expected_type: Optional[str] = None) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if expected_type and payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token type mismatch",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserTable]:
    stmt = select(UserTable).where(UserTable.email == email)
    return (await db.execute(stmt)).scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[UserTable]:
    stmt = select(UserTable).where(UserTable.id == user_id)
    return (await db.execute(stmt)).scalars().first()




async def create_user_from_oauth(
    db: AsyncSession,
    email: str,
    full_name: str,
    verified: bool = True,
    username: Optional[str] = None,
    **extra_fields,
) -> UserTable:
    """Create a passwordless user from OAuth identity."""
    preferences = extra_fields.pop("preferences", None)
    user = UserTable(
        email=email,
        username=username,
        full_name=full_name,
        email_verified=verified,
        hashed_password=None,  # Pure OAuth 2.0
        preferences=preferences or {},
        **extra_fields,
    )
    db.add(user)
    await db.flush()
    return user


async def upsert_user_token(
    db: AsyncSession,
    user: UserTable,
    provider: str,
    token_info: dict,
) -> UserTokenTable:
    stmt = select(UserTokenTable).where(
        UserTokenTable.user_id == user.id,
        UserTokenTable.provider == provider,
    )
    user_token = (await db.execute(stmt)).scalars().first()
    if not user_token:
        user_token = UserTokenTable(user_id=user.id, provider=provider)
        db.add(user_token)

    incoming_access_token = token_info.get("access_token")
    if incoming_access_token:
        user_token.access_token = encrypt_token_value(incoming_access_token)
    else:
        existing_access_token, access_needs_upgrade = decrypt_token_value(user_token.access_token)
        if access_needs_upgrade and existing_access_token:
            user_token.access_token = encrypt_token_value(existing_access_token)

    incoming_refresh_token = token_info.get("refresh_token")
    if incoming_refresh_token:
        user_token.refresh_token = encrypt_token_value(incoming_refresh_token)
    elif user_token.refresh_token:
        existing_refresh_token, refresh_needs_upgrade = decrypt_token_value(user_token.refresh_token)
        if refresh_needs_upgrade and existing_refresh_token:
            user_token.refresh_token = encrypt_token_value(existing_refresh_token)

    expires_at_raw = token_info.get("expires_at")
    if expires_at_raw is not None:
        expires_at_dt = None
        try:
            if isinstance(expires_at_raw, str):
                expires_at_raw = float(expires_at_raw)

            if isinstance(expires_at_raw, (int, float)):
                expires_at_dt = datetime.fromtimestamp(expires_at_raw, tz=timezone.utc)
            else:
                raise ValueError("expires_at must be an int, float, or numeric string")
        except (TypeError, ValueError, OverflowError) as exc:
            logger.warning(
                "Invalid expires_at value for user_token update: %r; provider=%s; user_id=%s", 
                expires_at_raw,
                provider,
                user.id,
            )

        if expires_at_dt is not None:
            user_token.expires_at = expires_at_dt
    user_token.is_active = True
    return user_token
