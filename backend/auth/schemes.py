from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from typing import Optional
import os
import httpx
import redis

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
ALGORITHM = "HS256"

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")

# Ensure both are set to enable Auth0 validation
if (AUTH0_DOMAIN and not AUTH0_AUDIENCE) or (AUTH0_AUDIENCE and not AUTH0_DOMAIN):
    import logging
    logging.getLogger(__name__).warning("Partial Auth0 configuration detected. Both AUTH0_DOMAIN and AUTH0_AUDIENCE must be set to enable Auth0 JWT validation.")

AUTH0_ISSUER = f"https://{AUTH0_DOMAIN}/" if AUTH0_DOMAIN else ""

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
    # If Auth0 variables are configured, attempt RS256 / JWKS validation.
    if AUTH0_DOMAIN and AUTH0_AUDIENCE:
        try:
            jwk = await _get_auth0_jwk(token)
            payload = jwt.decode(
                token,
                jwk,
                algorithms=["RS256"],
                audience=AUTH0_AUDIENCE,
                issuer=AUTH0_ISSUER,
            )
            return payload
        except JWTError:
            # Fallback to local JWT if Auth0 validation fails (e.g. local test tokens).
            pass

    # Local symmetric JWT strategy (HS256) fallback.
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """
    Get current user payload from either Authorization: Bearer <token> or HttpOnly cookie.
    Allows both header and cookie-based auth for maximum flexibility and security.
    """
    # Prefer cookie if available (higher security)
    cookie_token = request.cookies.get("graftai_access_token")
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
    return payload
