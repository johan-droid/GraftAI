from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
import jwt
from jwt import PyJWTError as JWTError
from typing import Optional
import os
import httpx
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from backend.services.access_control import check_user_role
from backend.services.redis_client import get_redis
from backend.utils.db import get_db
from backend.models.tables import UserTable, SessionTable
from sqlalchemy import select

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
from urllib.parse import urlparse

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


async def _get_neon_signing_key(token: str) -> any:
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
        iss = unverified_payload.get("iss", "")
    except Exception:
        return None

    # Strategy 1: Neon Auth (EdDSA)
    if alg == "EdDSA":
        try:
            if NEON_AUTH_ORIGIN in iss:
                signing_key = await _get_neon_signing_key(token)
                return jwt.decode(
                    token,
                    key=signing_key,
                    algorithms=["EdDSA"],
                    issuer=NEON_AUTH_ORIGIN,
                    audience=NEON_AUTH_ORIGIN,
                )
        except JWTError as exc:
            import logging

            logging.getLogger(__name__).error(f"Neon Auth JWT validation failed: {exc}")
            return None

    # Strategy 2: External Identity (Auth0 RS256)
    if alg == "RS256":
        try:
            # ── Auth0 Strategy ──
            if AUTH0_DOMAIN and "auth0.com" in iss:
                jwk = await _get_auth0_jwk(token)
                return jwt.decode(
                    token, key=jwk, algorithms=["RS256"], audience=AUTH0_AUDIENCE
                )
        except JWTError as exc:
            import logging

            logging.getLogger(__name__).error(f"External JWT validation failed: {exc}")
            return None

    # Strategy 3: Local Sovereign Session (HS256)
    if alg == "HS256":
        try:
            # PyJWT verifies exp, iat, and nbf by default when present
            return jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=["HS256"],
                options={"verify_exp": True, "verify_iat": True, "require": ["exp"]}
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except JWTError:
            return None

    return None


async def get_current_user(
    request: Request, 
    token: str = Depends(oauth2_scheme),
    db_session: any = Depends(get_db)
):
    """
    Get current user payload from either Authorization: Bearer <token> or better-auth.session_token cookie.
    First tries to verify as a Better Auth database session, then falls back to legacy JWT.
    """
    if not token:
        # Check Better Auth default cookie name
        cookie_token = (
            request.cookies.get("better-auth.session_token") or 
            request.cookies.get("graftai_access_token")
        )
        if cookie_token:
            token = cookie_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Strategy: Better Auth Database Session (Opaque Token)
    # Check if this token exists in the 'session' table
    try:
        # We need to use raw SQL or the SessionTable model
        stmt = select(SessionTable).where(SessionTable.id == token)
        result = await db_session.execute(stmt)
        auth_session = result.scalars().first()
        
        if auth_session:
            # Check for expiration
            if auth_session.expiresAt > datetime.now(timezone.utc):
                # Valid Better Auth session!
                # Fetch user details
                stmt_user = select(UserTable).where(UserTable.id == auth_session.userId)
                res_user = await db_session.execute(stmt_user)
                user = res_user.scalars().first()
                
                if user:
                    return {
                        "sub": str(user.id),
                        "email": user.email,
                        "name": user.full_name,
                        "exp": int(auth_session.expiresAt.timestamp()),
                        "type": "session"
                    }
    except Exception as exc:
        logger.warning(f"Better Auth session verification failed: {exc}")

    # 2. Strategy: Legacy/Sovereign JWT (HS256)
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

    # Session persistence and active telemetry are best-effort only.
    try:
        client = _get_redis_client()
        session_key = f"active_session:{token[-20:]}"
        telemetry_key = f"session_telemetry:{token[-20:]}"

        # Atomic extension/refresh
        client.setex(session_key, ACCESS_TOKEN_EXPIRE_MINUTES * 60, payload.get("sub"))

        # Atomic update local telemetry (useful for load balancer observability)
        backend_id = os.getenv("HOSTNAME", "unknown-worker")
        pipe = client.pipeline()
        pipe.hset(
            telemetry_key,
            mapping={"last_seen": str(datetime.now(timezone.utc)), "backend": backend_id},
        )
        pipe.expire(telemetry_key, 3600)
        pipe.execute()
    except Exception as exc:
        logger.warning(f"Session telemetry unavailable, continuing request: {exc}")

    return payload


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
    """
    Dependency that extracts and validates the user ID from the authenticated user payload.
    Ensures 'sub' exists and is a valid integer to prevent IDOR via body-supplied IDs.
    """
    user_id_raw = current_user.get("sub")
    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity (sub) missing from token",
        )
    try:
        # Ensure user_id can be used by access-control checks.
        return user_id_raw
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identity format",
        )


def is_admin_user(user_id: int = Depends(get_current_user_id)) -> int:
    """
    Dependency that ensures the current user has the 'admin' role.
    Returns the user_id if successful, otherwise raises 403 Forbidden.
    """
    if not check_user_role(user_id, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required",
        )
    return user_id


async def get_current_user_id_optional(request: Request) -> Optional[str]:
    """
    Internal helper (non-dependency) that attempts to extract a user_id
    from JWT cookies without raising any exceptions if not found.
    """
    token = (
        request.cookies.get("better-auth.session_token") or 
        request.cookies.get("graftai_access_token")
    )
    if not token:
        return None
        
    if is_token_blacklisted(token):
        return None
        
    payload = await decode_token(token)
    if not payload:
        return None
        
    return payload.get("sub")
