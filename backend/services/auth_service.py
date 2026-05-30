import json
import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ACCESS_TOKEN_TYPE,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_TYPE,
    SECRET_KEY,
)
from backend.core.secret_manager import get_secret_manager
from jose import jwt as jose_jwt
from jose import JWTError as JoseJWTError
import os
from backend.models.tables import UserTable, UserTokenTable
from backend.services.token_encryption import decrypt_token_value, encrypt_token_value

logger = logging.getLogger(__name__)

def _normalize_scope_set(raw_scopes: object | None) -> set[str]:
    if raw_scopes is None:
        return set()
    if isinstance(raw_scopes, str):
        candidate = raw_scopes.strip()
        if not candidate:
            return set()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return {str(item).strip() for item in parsed if str(item).strip()}
        except ValueError:
            pass
        return {scope.strip() for scope in candidate.replace(",", " ").split() if scope.strip()}
    if isinstance(raw_scopes, (list, tuple, set)):
        return {str(item).strip() for item in raw_scopes if str(item).strip()}
    return set()

def _contains_calendar_scopes(raw_scopes: object | None) -> bool:
    scope_set = _normalize_scope_set(raw_scopes)
    return any("calendar" in scope.lower() for scope in scope_set)

async def _create_jwt_token_impl(user_id: str, token_type: str, token_version: int=0) -> str:
    now = datetime.now(UTC)
    if token_type == REFRESH_TOKEN_TYPE:
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "type": token_type, "version": token_version, "exp": expire, "iat": now}
    # Feature flag to enable RS256 signing using a private key stored in secret manager.
    use_rs256 = os.getenv("AUTH_USE_RS256", "false").lower() in {"1", "true", "yes"}
    if use_rs256:
        try:
            mgr = get_secret_manager()
            raw = await mgr.get_secret("auth/jwks/active_kids")
            import json

            kids = []
            if raw:
                try:
                    kids = json.loads(raw)
                except Exception:
                    kids = []
            if not kids:
                # fallback to symmetric signing
                return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            kid = kids[-1]
            private_pem = await mgr.get_secret(f"auth/jwks/{kid}")
            if not private_pem:
                return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            # Sign with RS256 using the private PEM
            return jose_jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": kid})
        except Exception:
            # Any error falls back to symmetric signing for safety
            return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def create_access_token(user_id: str, token_version: int=0) -> str:
    return await _create_jwt_token_impl(user_id, ACCESS_TOKEN_TYPE, token_version=token_version)


async def create_refresh_token(user_id: str, token_version: int=0) -> str:
    return await _create_jwt_token_impl(user_id, REFRESH_TOKEN_TYPE, token_version=token_version)


async def create_token_pair(user_id: str, token_version: int=0) -> dict[str, str]:
    access = await create_access_token(user_id, token_version=token_version)
    refresh = await create_refresh_token(user_id, token_version=token_version)
    return {"access_token": access, "refresh_token": refresh}

async def decode_jwt_token(token: str, expected_type: str | None=None) -> dict:
    try:
        # Support both HS256 (symmetric) and RS256 (asymmetric via JWKS in secret manager)
        header = jose_jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        if alg.upper().startswith("RS"):
            kid = header.get("kid")
            if not kid:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing kid in token header", headers={"WWW-Authenticate": "Bearer"})
            mgr = get_secret_manager()
            pub_pem = mgr.get_secret(f"auth/jwks/{kid}")
            if hasattr(pub_pem, "__await__"):
                import asyncio

                pub_pem = asyncio.get_event_loop().run_until_complete(pub_pem)
            if not pub_pem:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Public key not found", headers={"WWW-Authenticate": "Bearer"})
            # jose can accept the PEM bytes for verification
            payload = jose_jwt.decode(token, pub_pem, algorithms=["RS256"])
        else:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (JWTError, JoseJWTError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate token", headers={"WWW-Authenticate": "Bearer"}) from exc
    if payload.get("sub") is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload missing subject", headers={"WWW-Authenticate": "Bearer"})
    if expected_type and payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token type mismatch", headers={"WWW-Authenticate": "Bearer"})
    return payload

async def get_user_by_email(db: AsyncSession, email: str) -> UserTable | None:
    stmt = select(UserTable).where(UserTable.email == email)
    return (await db.execute(stmt)).scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str) -> UserTable | None:
    stmt = select(UserTable).where(UserTable.id == user_id)
    return (await db.execute(stmt)).scalars().first()

async def get_user_by_provider_account_id(db: AsyncSession, provider: str, provider_account_id: str) -> UserTable | None:
    """
    Resolve a user via provider-specific subject/account id stored in token metadata.
    This keeps social logins bound to a stable internal user profile even if the
    provider email alias changes.
    """
    normalized_provider = (provider or "").strip().lower()
    normalized_account_id = (provider_account_id or "").strip().lower()
    if not normalized_provider or not normalized_account_id:
        return None
    stmt = select(UserTokenTable).where(UserTokenTable.provider == normalized_provider)
    tokens = (await db.execute(stmt)).scalars().all()
    for token in tokens:
        metadata_payload = token.metadata_payload or {}
        if not isinstance(metadata_payload, dict):
            continue
        candidate = metadata_payload.get("provider_account_id")
        if isinstance(candidate, str) and candidate.strip().lower() == normalized_account_id:
            return await get_user_by_id(db, token.user_id)
    return None

async def create_user_from_oauth(db: AsyncSession, email: str, full_name: str, verified: bool=True, username: str | None=None, **extra_fields) -> UserTable:
    """Create a passwordless user from OAuth identity."""
    preferences = extra_fields.pop("preferences", None)
    now = datetime.now(UTC)
    user = UserTable(email=email, username=username, full_name=full_name, email_verified=verified, hashed_password=None, preferences=preferences or {}, tier="free", trial_active=False, trial_expires_at=now + timedelta(days=14), **extra_fields)
    db.add(user)
    await db.flush()
    return user

async def upsert_user_token(db: AsyncSession, user: UserTable, provider: str, token_info: dict) -> UserTokenTable:
    now = datetime.now(UTC)
    stmt = select(UserTokenTable).where(UserTokenTable.user_id == user.id, UserTokenTable.provider == provider)
    user_token = (await db.execute(stmt)).scalars().first()
    if not user_token:
        user_token = UserTokenTable(user_id=user.id, provider=provider)
        db.add(user_token)
    else:
        user_token.is_active = True
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
    incoming_scopes = token_info.get("scopes") or token_info.get("scope")
    existing_scopes = user_token.scopes
    if incoming_scopes is not None:
        if provider in {"google", "microsoft"} and _contains_calendar_scopes(existing_scopes) and (not _contains_calendar_scopes(incoming_scopes)):
            logger.info("Preserving existing calendar scopes for user_id=%s provider=%s", user.id, provider)
        else:
            user_token.scopes = incoming_scopes
    incoming_metadata = token_info.get("metadata_payload") or token_info.get("metadata")
    if incoming_metadata is not None:
        if isinstance(incoming_metadata, str):
            try:
                incoming_metadata = json.loads(incoming_metadata)
            except ValueError:
                incoming_metadata = {"metadata": incoming_metadata}
        metadata_payload = dict(user_token.metadata_payload or {})
        metadata_payload.update(incoming_metadata)
        user_token.metadata_payload = metadata_payload
    if provider in {"google", "microsoft"}:
        metadata_payload = dict(user_token.metadata_payload or {})
        metadata_payload.setdefault("calendar_connected", True)
        user_token.metadata_payload = metadata_payload
    expires_at_raw = token_info.get("expires_at")
    if expires_at_raw is not None:
        expires_at_dt = None
        try:
            if isinstance(expires_at_raw, str):
                expires_at_raw = float(expires_at_raw)
            if isinstance(expires_at_raw, (int, float)):
                expires_at_dt = datetime.fromtimestamp(expires_at_raw, tz=UTC)
            else:
                msg = "expires_at must be an int, float, or numeric string"
                raise ValueError(msg)
        except (TypeError, ValueError, OverflowError):
            logger.warning("Invalid expires_at value for user_token update: %r; provider=%s; user_id=%s", expires_at_raw, provider, user.id)
        if expires_at_dt is not None:
            user_token.expires_at = expires_at_dt
    user_token.updated_at = now
    return user_token
