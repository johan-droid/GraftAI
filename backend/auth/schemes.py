from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
import jwt
from jwt import PyJWTError as JWTError
from typing import Optional
import os
import httpx
import redis
from datetime import datetime, timezone
from backend.services.access_control import check_user_role

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
ALGORITHM = "HS256"

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

# Redis client for token blacklist
_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def blacklist_token(token: str, expires_in: int):
    """Add token to blacklist with TTL matching token expiry."""
    client = _get_redis_client()
    client.setex(f"token:blacklist:{token}", expires_in, "1")


def is_token_blacklisted(token: str) -> bool:
    """Check if token has been revoked."""
    client = _get_redis_client()
    return client.exists(f"token:blacklist:{token}") > 0


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

    # Strategy 2: Local Sovereign Session (HS256)
    if alg == "HS256":
        try:
            # We explicitly use only the local SECRET_KEY for HS256 to prevent 'alg none' or RS256/HS256 confusion attacks.
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except JWTError:
            return None

    return None


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """
    Get current user payload from either Authorization: Bearer <token> or HttpOnly cookie.
    Allows both header and cookie-based auth for maximum flexibility and security.
    """
    # Prefer cookie if available (higher security)
    cookie_token = request.cookies.get("graftai_access_token") or request.cookies.get("better-auth.session_token")
    if cookie_token:
        token = cookie_token

    if not token:
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

    # Session Persistence & Active Tracking
    client = _get_redis_client()
    session_key = f"active_session:{token[-20:]}"
    if not client.exists(session_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or was revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update local telemetry (useful for load balancer observability)
    # This tracks which exact container/worker is handling the user in Redis
    backend_id = os.getenv("HOSTNAME", "unknown-worker")
    client.hset(
        f"session_telemetry:{token[-20:]}",
        mapping={"last_seen": str(datetime.now(timezone.utc)), "backend": backend_id},
    )
    client.expire(f"session_telemetry:{token[-20:]}", 3600)

    return payload


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> int:
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
        return int(user_id_raw)
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
