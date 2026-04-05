from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
import hashlib
import jwt
from jwt import PyJWTError as JWTError
from typing import Optional, Any
import os
import httpx
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db
from backend.services.access_control import check_user_role
from backend.services.redis_client import get_redis

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

NEON_AUTH_BASE_URL = os.getenv(
    "NEON_AUTH_BASE_URL",
    "https://ep-steep-glade-a1b1tcdq.ap-southeast-1.aws.neon.tech/neondb/auth",
)
NEON_JWKS_URL = f"{NEON_AUTH_BASE_URL}/.well-known/jwks.json"

# Inferred Origin from NEON_AUTH_BASE_URL
_parsed_neon = urlparse(NEON_AUTH_BASE_URL)
NEON_AUTH_ORIGIN = f"{_parsed_neon.scheme}://{_parsed_neon.netloc}"

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")

def _get_redis_client():
    return get_redis()


def blacklist_token(token: str, expires_in: int):
    """Add token to blacklist with TTL matching token expiry."""
    try:
        client = _get_redis_client()
        client.setex(f"token:blacklist:{token}", expires_in, "1")
    except Exception as exc:
        logger.warning(f"Failed to persist token blacklist entry: {exc}")


def is_token_blacklisted(token: str) -> bool:
    """Check if token has been revoked."""
    try:
        client = _get_redis_client()
        return client.exists(f"token:blacklist:{token}") > 0
    except Exception as exc:
        logger.warning(f"Blacklist check unavailable, defaulting to not blacklisted: {exc}")
        return False


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def _session_cache_key(token: str) -> str:
    """Hash the full token for a collision-safe Redis session key."""
    digest = hashlib.sha256(str(token).encode()).hexdigest()[:32]
    return f"active_session:{digest}"


async def _get_neon_signing_key(token: str) -> Any:
    """Fetch Neon Auth JWKS and extract the Ed25519 public key."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    import base64

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise JWTError("Missing kid in token header")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(NEON_JWKS_URL)
            response.raise_for_status()
            jwks = response.json()

        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Neon uses Ed25519 (EdDSA) with "x" param
                x = key["x"]
                # Add padding if necessary
                public_key_bytes = base64.urlsafe_b64decode(x + "==")
                return Ed25519PublicKey.from_public_bytes(public_key_bytes)

        raise JWTError("Matching kid not found in Neon JWKS")
    except Exception as exc:
        raise JWTError(f"Neon JWKS retrieval failed: {exc}")


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
    """
    Intelligent token decoder that selects validation strategy based on token algorithm and issuer.
    Supports: Auth0 (RS256), Supabase (RS256), and Sovereign Local (HS256).
    """
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        
        # Pre-decode to check issuer without verification (safe for strategy selection)
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
    except Exception as exc:
        logger.debug(f"[AUTH_DEBUG]: Token unverified decode failed: {exc}")
        return None

    # Only local sovereign JWT sessions are supported now.
    if alg == "HS256":
        try:
            return jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": True, "verify_iat": True, "require": ["exp"]},
            )
        except jwt.ExpiredSignatureError:
            logger.warning("[AUTH_DEBUG]: Token signature has expired")
            return None
        except JWTError as exc:
            logger.warning(f"[AUTH_DEBUG]: JWT decode error (Alg: {alg}): {exc}")
            return None

    logger.warning(f"[AUTH_DEBUG]: Unsupported token algorithm rejected: {alg}")
    # All other token algorithms are rejected in this simplified auth architecture.
    return None


async def verify_better_auth_session(token: str, db: AsyncSession) -> Optional[dict]:
    """
    Validate a Better Auth opaque session token using Better Auth's default snake_case schema.
    """
    from sqlalchemy import text

    try:
        result = await db.execute(
            text("SELECT user_id, expires_at FROM public.session WHERE token = :t"),
            {"t": token},
        )
        row = result.fetchone()
        if not row:
            logger.debug("[AUTH_DEBUG]: Better Auth: session token not found in DB")
            return None

        user_id, expires_at = row
        if expires_at is None:
            return None

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            logger.debug("[AUTH_DEBUG]: Better Auth: session token expired in DB")
            return None

        user_res = await db.execute(
            text("SELECT id, email, name FROM public.users WHERE id = :uid"),
            {"uid": user_id},
        )
        user_row = user_res.fetchone()
        if not user_row:
            logger.debug(f"[AUTH_DEBUG]: Better Auth: user {user_id} not found linked to session")
            return None

        return {
            "sub": str(user_row[0]),
            "email": user_row[1],
            "name": user_row[2],
            "type": "better-auth",
        }
    except Exception as exc:
        logger.error(f"[AUTH_DEBUG]: Better Auth session verification failed: {exc}")
        return None


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user payload from Authorization bearer token, cookie-based JWT, or Better Auth session cookie.
    ROBUSTNESS: Manually inspects headers and cookies to ensure proxies don't strip credentials.
    """
    # 1. Resolve Token source (Bearer header, Case-insensitive Authorization, X-Authorization, or Cookies)
    if not token:
        # Standard header (case-insensitive via FastAPI request object)
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            logger.info(f"[AUTH_DEBUG]: Found token in Authorization header: {token[:10]}...")
        
        # Custom header (for some proxies)
        if not token:
            x_auth = request.headers.get("X-Authorization") or request.headers.get("x-authorization")
            if x_auth:
                token = x_auth[7:].strip() if x_auth.lower().startswith("bearer ") else x_auth.strip()
                logger.info(f"[AUTH_DEBUG]: Found token in X-Authorization header: {token[:10]}...")

        # Query parameter fallback (e.g. frontend token bridge / one-time handoff)
        if not token:
            token = (
                request.query_params.get("token")
                or request.query_params.get("access_token")
                or request.query_params.get("refresh_token")
            )
            if token:
                logger.info(f"[AUTH_DEBUG]: Found token in query params: {token[:10]}...")

        # Cookie fallback
        if not token:
            token = (
                request.cookies.get("graftai_access_token")
                or request.cookies.get("better-auth.session_token")
            )
            if token:
                logger.info(f"[AUTH_DEBUG]: Found token in cookie: {token[:10]}...")

    # Cleanup token (Handle quotes if added by some middleware)
    if token and isinstance(token, str):
        token = token.strip().strip('"').strip("'")
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

    if not token:
        # DIAGNOSTIC DUMP: Help identify if Vercel/Render proxy is stripping headers/cookies
        header_keys = list(request.headers.keys())
        cookie_keys = list(request.cookies.keys())
        logger.warning(f"[AUTH_DIAGNOSTIC]: Authentication failed. No token found.")
        logger.warning(f"[AUTH_DIAGNOSTIC]: Available Headers: {header_keys}")
        logger.warning(f"[AUTH_DIAGNOSTIC]: Available Cookies: {cookie_keys}")
        logger.warning(f"[AUTH_DIAGNOSTIC]: Origin: {request.headers.get('origin')}, Host: {request.headers.get('host')}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Strategy Selection: Better Auth (opaque) vs. Sovereign (JWT)
    # Better Auth sessions generally do not contain two dots (not a JWT)
    if token.count(".") != 2:
        logger.debug("[AUTH_DEBUG]: Token is opaque (Better Auth). Verifying in database...")
        payload = await verify_better_auth_session(token, db)
        if payload:
            logger.info(f"[AUTH_DEBUG]: Better Auth session verified for sub={payload['sub']}")
            # Register in Redis for consistency across backend nodes
            client = _get_redis_client()
            session_key = _session_cache_key(token)
            client.setex(session_key, ACCESS_TOKEN_EXPIRE_MINUTES * 60, payload["sub"])
            return payload
        else:
             logger.warning("[AUTH_DEBUG]: Better Auth session verification failed or expired.")
    else:
        # JWT Flow
        logger.debug("[AUTH_DEBUG]: Token is JWT (Sovereign). Verifying signature...")
        
        # Check Revocation (Blacklist)
        if is_token_blacklisted(token):
            logger.warning("[AUTH_DEBUG]: Attempted to use blacklisted/revoked token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = await decode_token(token)
        if not payload:
            logger.warning("[AUTH_DEBUG]: JWT Decoding failed or signature invalid.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Redis Session Consistency Check
        client = _get_redis_client()
        session_key = _session_cache_key(token)
        if not client.exists(session_key):
            # This is a critical point for SSO handoff debugging
            logger.warning(f"[AUTH_DEBUG]: Session missing from Redis (Key: {session_key}) for sub={payload.get('sub')}")
            # AUTO-RECOVERY attempt: If the token is valid but missing from Redis, re-add it (SSO race condition handler)
            try:
                client.setex(session_key, ACCESS_TOKEN_EXPIRE_MINUTES * 60, str(payload.get("sub")))
                logger.info(f"[AUTH_DEBUG]: Auto-recovered session for sub={payload.get('sub')} in Redis")
            except Exception as e:
                logger.error(f"[AUTH_DEBUG]: Auto-recovery failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session has expired or was revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Happy path - Update Telemetry
        try:
            backend_id = os.getenv("HOSTNAME", "unknown-worker")
            telemetry_key = f"session_telemetry:{session_key}"
            client.hset(
                telemetry_key,
                mapping={"last_seen": str(datetime.now(timezone.utc)), "backend": backend_id},
            )
            client.expire(telemetry_key, 3600)
        except Exception as exc:
            logger.warning(f"[AUTH_DEBUG]: Telemetry update failed (non-blocking): {exc}")

        return payload

    # Final fallback
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Authentication strategy failure",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
    """
    Dependency that extracts and validates the user ID from the authenticated user payload.
    """
    user_id_raw = current_user.get("sub")
    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity (sub) missing from token",
        )
    return str(user_id_raw)


def is_admin_user(user_id: str = Depends(get_current_user_id)) -> str:
    """
    Dependency that ensures the current user has the 'admin' role.
    """
    if not check_user_role(str(user_id), "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required",
        )
    return user_id


async def get_current_user_id_optional(request: Request) -> Optional[str]:
    """
    Internal helper (non-dependency) that attempts to extract a user_id
    without raising exceptions.
    """
    token = request.cookies.get("graftai_access_token")
    if not token or is_token_blacklisted(token):
        return None

    payload = await decode_token(token)
    if not payload:
        return None

    return payload.get("sub")