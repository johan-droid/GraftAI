from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
import hashlib
import jwt
from jwt import PyJWTError as JWTError
from typing import Optional
import os
import json
import httpx
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db
from backend.services.access_control import check_user_role
from backend.utils.redis_singleton import safe_get, safe_set, safe_delete

# Initialize logger
logger = logging.getLogger(__name__)

# Ensure environment variables are loaded from backend/.env first
project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
SESSION_CACHE_TTL = 300  # 5 minutes


def blacklist_token(token: str, expires_in: int) -> None:
    safe_set(f"token:blacklist:{token}", "1", ex=expires_in)


def is_token_blacklisted(token: str) -> bool:
    return safe_get(f"token:blacklist:{token}") is not None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


# ── JWKS helpers ──────────────────────────────────────────────────────────────

async def _get_auth0_jwk(token: str) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise JWTError("Missing kid in token header")
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
    except Exception as exc:
        raise JWTError(f"Unable to fetch JWKS from Auth0: {exc}")
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise JWTError("Appropriate key not found in Auth0 JWKS")


async def decode_token(token: str) -> Optional[dict]:
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return None

    if alg == "RS256":
        try:
            issuer = jwt.decode(token, options={"verify_signature": False}).get("iss", "")
            if AUTH0_DOMAIN and "auth0.com" in issuer:
                jwk = await _get_auth0_jwk(token)
                return jwt.decode(token, key=jwk, algorithms=["RS256"], audience=AUTH0_AUDIENCE)
        except JWTError as exc:
            logger.error(f"External JWT validation failed: {exc}")
            return None

    if alg == "HS256":
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except JWTError:
            return None

    return None


# ── Better Auth session with Redis caching ───────────────────────────────────

async def verify_better_auth_session(token: str, db: AsyncSession) -> Optional[dict]:
    cache_key = f"session:ba:{token[-32:]}"
    cached = safe_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    from sqlalchemy import text

    try:
        result = await db.execute(
            text('SELECT "userId", "expiresAt" FROM public.session WHERE token = :t'),
            {"t": token},
        )
        row = result.fetchone()
        if not row:
            return None

        user_id, expires_at = row
        if expires_at is None:
            return None

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            return None

        user_res = await db.execute(
            text('SELECT id, email, name FROM public.users WHERE id = :uid'),
            {"uid": user_id},
        )
        user = user_res.fetchone()
        if not user:
            return None

        payload = {"sub": str(user[0]), "email": user[1], "name": user[2], "type": "better-auth"}
        safe_set(cache_key, json.dumps(payload), ex=SESSION_CACHE_TTL)
        return payload
    except Exception as exc:
        logger.error(f"Better Auth session verification failed: {exc}")
        return None


def _session_cache_key(token: str) -> str:
    digest = hashlib.sha256(str(token).encode()).hexdigest()[:32]
    return f"active_session:{digest}"


def _get_cookie_token(request: Request) -> Optional[str]:
    for cookie_name in ("graftai_access_token", "better-auth.session_token"):
        token = request.cookies.get(cookie_name)
        if token:
            return token
    return None


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    if not token:
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()

        if not token:
            x_auth = request.headers.get("X-Authorization") or request.headers.get("x-authorization")
            if x_auth:
                token = x_auth[7:].strip() if x_auth.lower().startswith("bearer ") else x_auth.strip()

        if not token:
            token = request.query_params.get("token") or request.query_params.get("access_token")

        if not token:
            token = _get_cookie_token(request)

    if token and isinstance(token, str):
        token = token.strip().strip('"').strip("'")
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

    if not token:
        logger.warning("Authentication failed: no token found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token.count(".") != 2:
        payload = await verify_better_auth_session(token, db)
        if payload:
            return payload
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = await decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_key = _session_cache_key(token)
    if safe_get(session_key) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or was revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity (sub) missing from token",
        )
    return str(user_id)


def is_admin_user(user_id: str = Depends(get_current_user_id)) -> str:
    if not check_user_role(user_id, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required",
        )
    return user_id


async def get_current_user_id_optional(request: Request) -> Optional[str]:
    token = request.cookies.get("graftai_access_token")
    if not token or is_token_blacklisted(token):
        return None

    payload = await decode_token(token)
    if not payload:
        return None

    return payload.get("sub")
