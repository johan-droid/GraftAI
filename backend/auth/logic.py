import os
import secrets
import hashlib
import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Request, Response, status
from backend.utils.redis_singleton import get_redis

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENV") == "production":
        logger.critical("[AUTH] 🚨 FATAL: SECRET_KEY environment variable is MISSING in production.")
        raise RuntimeError("SECRET_KEY environment variable is required for production security.")
    else:
        logger.warning("[AUTH] ⚠ SECRET_KEY not set - using insecure dev default.")
        SECRET_KEY = "dev_insecure_token_signing_key_change_me_in_production"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def get_redis_client():
    return get_redis()

_AUTH_RATE_LIMIT_LUA = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end
if current > limit then
    return 0
end
return 1
"""

def get_rate_limiter(max_requests: int, window_seconds: int):
    """Dependency-based rate limiter for FastAPI routes."""
    async def rate_limiter(request: Request):
        if os.getenv("TESTING") == "1":
            return True

        client_ip = request.headers.get(
            "x-forwarded-for", request.client.host if request.client else "unknown"
        )
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        client = get_redis_client()
        key = f"auth_rate_limit:{client_ip}:{request.url.path}"

        try:
            allowed = client.eval(_AUTH_RATE_LIMIT_LUA, 1, key, max_requests, window_seconds)
        except Exception as e:
            logger.error(f"Rate limiter Redis failure: {e}")
            return True

        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many attempts. Please try again in {window_seconds} seconds.",
            )
        return True
    return rate_limiter

def create_jwt_token(sub: str, email: Optional[str] = None):
    """Create access and refresh tokens and persist refresh token in Redis."""
    now = datetime.now(timezone.utc)

    # Access Token
    access_expires_at = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_payload = {
        "sub": str(sub),
        "email": email,
        "exp": int(access_expires_at.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
        "iss": "graftai-sovereign",
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)

    # Refresh Token
    refresh_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_payload = {
        "sub": str(sub),
        "email": email,
        "exp": int(refresh_expires_at.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh",
        "iss": "graftai-sovereign",
    }
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)

    client = get_redis_client()
    client.setex(
        f"refresh:{refresh_token}", REFRESH_TOKEN_EXPIRE_DAYS * 86400, str(sub)
    )
    client.sadd(f"user_tokens:{sub}", refresh_token)

    # Register this specific access session in Redis
    cache_key = hashlib.sha256(access_token.encode()).hexdigest()[:32]
    session_key = f"active_session:{cache_key}"
    tokens_key = f"user_tokens:{sub}"
    
    logger.info(f"[AUTH_DEBUG]: Persisting session in Redis for sub={sub}. Key: {session_key}")
    
    pipe = client.pipeline()
    pipe.setex(session_key, ACCESS_TOKEN_EXPIRE_MINUTES * 60, str(sub))
    pipe.sadd(tokens_key, refresh_token)
    pipe.expire(tokens_key, REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    pipe.execute()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
    rt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Store in Redis for revocation checks
    sub = data.get("sub")
    if sub:
        client = get_redis_client()
        client.setex(f"refresh:{rt}", REFRESH_TOKEN_EXPIRE_DAYS * 86400, str(sub))
        client.sadd(f"user_tokens:{sub}", rt)
    
    return rt

def get_token_bridge_url(access_token: str, refresh_token: str, target: str) -> str:
    """
    Constructs a URL for the 'Token Bridge' - a middleman page that transfers
    tokens from the backend domain to the frontend domain via localstorage/cookies.
    """
    frontend_url = os.getenv("FRONTEND_URL", "https://www.graftai.tech")
    # Base URL for the frontend dashboard
    if target.startswith("/"):
        full_target = f"{frontend_url}{target}"
    else:
        full_target = target

    import urllib.parse
    params = {
        "at": access_token,
        "rt": refresh_token,
        "redirect": full_target
    }
    # We use a specific bridge route on the frontend if it exists, otherwise dashboard
    # The frontend should have a route like /auth/bridge to handle these params
    return f"{frontend_url}/auth/bridge?{urllib.parse.urlencode(params)}"

def set_auth_cookies(response: Response, access_token: str, refresh_token: str, request: Optional[Request] = None):
    """Alias for attach_jwt_cookies with modern param names."""
    return attach_jwt_cookies(response, {"access_token": access_token, "refresh_token": refresh_token}, request)

def attach_jwt_cookies(response: Response, token_data: dict, request: Optional[Request] = None):
    env_name = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "production").lower()
    is_prod = env_name == "production"

    is_https = is_secure_request(request) or os.getenv("PROTOCOL") == "https" or is_prod
    
    if is_https:
        same_site_value = "none"
        secure_value = True
        logger.info("[AUTH_DEBUG]: Using SameSite=None; Secure for cross-domain compatibility.")
    else:
        same_site_value = "lax"
        secure_value = False
        logger.warning("[AUTH_DEBUG]: Using SameSite=Lax (Insecure environment). Cross-domain SSO may fail.")

    response.set_cookie(
        key="graftai_access_token",
        value=token_data["access_token"],
        httponly=True,
        secure=secure_value,
        samesite=same_site_value,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="graftai_refresh_token",
        value=token_data["refresh_token"],
        httponly=True,
        secure=secure_value,
        samesite=same_site_value,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )

    xsrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="xsrf-token",
        value=xsrf_token,
        httponly=False, 
        secure=secure_value,
        samesite=same_site_value,
        max_age=86400,
        path="/",
    )
    return response
