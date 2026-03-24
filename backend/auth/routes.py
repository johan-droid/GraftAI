from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
from jose import jwt
from datetime import datetime, timedelta, timezone
import os
import redis
import functools
import logging

# Initialize logger
logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Services and models
from backend.services import sso, passwordless, mfa, access_control, fido2_did, auth_utils
from backend.models.tables import UserTable
from backend.api.deps import get_db

# Auth dependencies
from backend.auth.schemes import get_current_user, get_current_user_id, is_admin_user, blacklist_token

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
AUTH_METHODS = [m.strip() for m in os.getenv("AUTH_METHODS", "sso,passwordless,mfa").split(",") if m.strip()]

# Redis client for refresh tokens and rate limiting
_redis_client = None

def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def get_rate_limiter(max_requests: int, window_seconds: int):
    """Dependency-based rate limiter for FastAPI routes."""
    async def rate_limiter(request: Request):
        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        
        client = _get_redis_client()
        # Use a path-specific key to avoid cross-endpoint leakage
        key = f"auth_rate_limit:{client_ip}:{request.url.path}"
        
        current = client.get(key)
        if current is None:
            client.setex(key, window_seconds, 1)
        elif int(current) >= max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many attempts. Please try again in {window_seconds} seconds."
            )
        else:
            client.incr(key)
        return True
    return rate_limiter


router = APIRouter(prefix="/auth", tags=["auth"])


# ── Pydantic Request Models ──

class FIDO2AssertionRequest(BaseModel):
    user_id: int
    assertion: dict = {}

class FIDO2AttestationRequest(BaseModel):
    user_id: int
    attestation: dict = {}

class DIDVerifyRequest(BaseModel):
    user_id: int
    did: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    timezone: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


def _create_jwt_token(sub: str, response: Optional[JSONResponse] = None):
    """Create access and refresh tokens and optionally set HttpOnly cookies."""
    now = datetime.now(timezone.utc)
    
    # Access token - short lived
    access_expires_at = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({
        "sub": sub,
        "exp": int(access_expires_at.timestamp()),
        "type": "access"
    }, SECRET_KEY, algorithm=ALGORITHM)
    
    # Refresh token - long lived, stored in Redis
    refresh_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = jwt.encode({
        "sub": sub,
        "exp": int(refresh_expires_at.timestamp()),
        "type": "refresh"
    }, SECRET_KEY, algorithm=ALGORITHM)
    
    # Store refresh token in Redis
    client = _get_redis_client()
    client.setex(f"refresh:{refresh_token}", REFRESH_TOKEN_EXPIRE_DAYS * 86400, sub)
    
    # Track tokens per user for session revocation
    client.sadd(f"user_tokens:{sub}", refresh_token)
    client.expire(f"user_tokens:{sub}", REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    
    token_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

    if response:
        # Secure, HttpOnly cookie (no Secure = True on localhost unless needed)
        is_prod = os.getenv("NODE_ENV") == "production"
        response.set_cookie(
            key="graftai_access_token",
            value=access_token,
            httponly=True,
            secure=is_prod,
            samesite="strict",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/"
        )
        # Refresh token is also better as a cookie (XSS protection)
        response.set_cookie(
            key="graftai_refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_prod,
            samesite="strict",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/auth/refresh"
        )
    
    return token_data


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60))
):
    # Query database for the user with normalized email
    email = auth_utils.canonical_email(form_data.username)
    result = await db.execute(select(UserTable).where(UserTable.email == email))
    user = result.scalars().first()
    
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    response = JSONResponse(content={"status": "success"})
    tokens = _create_jwt_token(str(user.id), response=response)
    # Return basic user info + token meta in body, but real tokens in HttpOnly cookies
    response.body = JSONResponse(content={"token": tokens, "user": {"id": user.id, "email": user.email}}).body
    return response

@router.post("/register")
async def register(
    user_in: UserRegister, 
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=3, window_seconds=60))
):
    # Normalize email & Validate password complexity
    email = auth_utils.canonical_email(user_in.email)
    if not auth_utils.validate_password_complexity(user_in.password):
        raise HTTPException(
            status_code=400,
            detail="Password does not meet complexity requirements (12+ chars, mixed cases, digits, symbols)"
        )

    # Check if user already exists
    result = await db.execute(select(UserTable).where(UserTable.email == email))
    if result.scalars().first():
        # Generic message to prevent enumeration
        logger.warning(f"Registration attempt for existing email: {email}")
        raise HTTPException(status_code=400, detail="Registration failed. Please try a different email or login.")
    
    # Register user with explicit transaction block
    try:
        async with db.begin():
            new_user = UserTable(
                email=email,
                full_name=user_in.full_name,
                hashed_password=auth_utils.get_password_hash(user_in.password),
                timezone=user_in.timezone
            )
            db.add(new_user)
            # Automatic commit on block exit
    except Exception as e:
        logger.error(f"Registration failed: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Registration failed")
    
    return {"message": "User registered successfully", "id": new_user.id}


@router.get("/sso/start")
def sso_start(provider: str = "github", redirect_to: str = "/dashboard"):
    try:
        return sso.start_oauth2_flow(provider=provider, redirect_to=redirect_to)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.get("/sso/callback")
async def sso_callback(code: str, state: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    This endpoint is hit TWICE during OAuth:
    1. By Google (browser navigation) → we redirect to the frontend WITHOUT consuming state.
    2. By the frontend's fetch() call → we consume the state and return JSON with the token.
    """
    fetch_param = request.query_params.get("fetch") == "true"
    accept_header = request.headers.get("accept", "").lower()
    is_json_accept = "application/json" in accept_header

    is_navigation = not fetch_param and not is_json_accept

    if is_navigation:
        # STEP 1: Browser redirect from Google → send to frontend. DO NOT consume state.
        frontend_base = os.getenv("FRONTEND_BASE_URL", "https://graft-ai-two.vercel.app").rstrip("/")
        # The frontend will then call back with ?fetch=true
        return RedirectResponse(
            f"{frontend_base}/auth-callback?code={code}&state={state}",
            status_code=302,
        )

    # STEP 2: Frontend API call → complete the OAuth flow (consumes the state).
    try:
        payload = await sso.complete_oauth2_flow(code=code, state=state)
        profile = payload["profile"]
        email = profile.get("email")

        # Sync user to database with transaction safety
        if email:
            async with db.begin():
                result = await db.execute(select(UserTable).where(UserTable.email == email))
                user = result.scalars().first()
                if not user:
                    user = UserTable(
                        email=email,
                        full_name=profile.get("name"),
                        is_active=True
                    )
                    db.add(user)
                    # Automatically committed
            
            # Re-fetch user_id after potential creation (outside or inside block depends on session state)
            # Since we just used db.begin() (sub-transaction), the session might need a fresh query or refresh.
            # For simplicity, we query again or just use the user object if it was already in session.
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            final_user = result.scalars().first()
            user_id = str(final_user.id) if final_user else "unknown"
        else:
            user_id = str(profile.get("id", "unknown"))

        response = JSONResponse(content={"status": "success"})
        own_token = _create_jwt_token(user_id, response=response)
        
        return JSONResponse(content={
            "auth": payload, 
            "token": own_token, 
            "user_id": user_id,
            "redirect_to": payload.get("redirect_to", "/dashboard")
        }, headers=dict(response.headers))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/passwordless/request")
def _passwordless_request(
    email: str, 
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=3, window_seconds=300))
):
    return passwordless.request_magic_link(email)


@router.post("/passwordless/verify")
def _passwordless_verify(
    email: str, 
    code: str, 
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60))
):
    if not passwordless.verify_magic_link_code(email, code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")
    return _create_jwt_token(email)


@router.post("/mfa/setup")
def _mfa_setup(user_id: int = Depends(get_current_user_id)):
    return mfa.start_mfa_enrollment(user_id)


@router.post("/mfa/verify")
def _mfa_verify(
    token: str, 
    user_id: int = Depends(get_current_user_id),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60))
):
    if not mfa.verify_mfa_token(user_id, token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP token")
    return {"status": "success"}


@router.get("/fido2/register")
def _fido2_start(user_id: int = Depends(get_current_user_id)):
    return fido2_did.start_fido2_registration(user_id)


@router.post("/fido2/register")
def _fido2_complete(attestation: dict, user_id: int = Depends(get_current_user_id)):
    if not fido2_did.complete_fido2_registration(user_id, attestation):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="FIDO2 registration failed")
    return {"status": "registered"}


@router.post("/fido2/verify")
def _fido2_verify(assertion: dict, user_id: int = Depends(get_current_user_id)):
    if not fido2_did.verify_fido2_assertion(user_id, assertion):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="FIDO2 assertion failed")
    return {"status": "verified"}


@router.post("/did/issue")
def _did_issue(user_id: int = Depends(get_current_user_id)):
    return {"did": fido2_did.issue_decentralized_id(user_id)}


@router.post("/did/verify")
def _did_verify(did: str, user_id: int = Depends(get_current_user_id)):
    return {"status": "valid"}


# REMOVED: /auth/authenticate catch-all endpoint (Master Key risk)


@router.get("/access-control/check-role")
def check_role(role: str, user_id: int = Depends(get_current_user_id)):
    return {"allowed": access_control.check_user_role(user_id, role)}


@router.get("/access-control/check-attribute")
def check_attribute(attribute: str, value: str, user_id: int = Depends(get_current_user_id)):
    return {"allowed": access_control.check_user_attribute(user_id, attribute, value)}





@router.get("/check")
def check_auth(current_user=Depends(get_current_user)):
    # returns user payload if authenticated
    return {"authenticated": True, "user": current_user}


@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest):
    """Get a new access token using a refresh token."""
    client = _get_redis_client()
    
    # Check if refresh token exists in Redis
    user_id = client.get(f"refresh:{request.refresh_token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Verify the refresh token JWT
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Generate new token pair
    return _create_jwt_token(user_id)


@router.post("/logout")
def logout(request: RefreshTokenRequest, current_user=Depends(get_current_user)):
    """Revoke refresh token and clear HttpOnly cookies."""
    client = _get_redis_client()
    
    # Delete refresh token from Redis
    client.delete(f"refresh:{request.refresh_token}")
    
    response = JSONResponse(content={"message": "Successfully logged out"})
    # Clear HttpOnly cookies
    response.delete_cookie(key="graftai_access_token", path="/")
    response.delete_cookie(key="graftai_refresh_token", path="/auth/refresh")
    
    return response


@router.post("/revoke")
def revoke_sessions(
    target_user_id: Optional[int] = None,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Revoke all sessions for a user.
    - If target_user_id is provided, requires admin privileges.
    - If not provided, revokes current user's own sessions.
    """
    client = _get_redis_client()
    
    # Identify the user whose sessions will be revoked
    revoke_id = current_user_id
    if target_user_id and target_user_id != current_user_id:
        # Check admin role for targeted revocation
        if not access_control.check_user_role(current_user_id, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrative privileges required to revoke other users' sessions"
            )
        revoke_id = target_user_id

    # Get all refresh tokens for this user
    token_key = f"user_tokens:{revoke_id}"
    tokens = client.smembers(token_key)
    
    deleted_count: int = 0
    if tokens:
        # Delete each refresh token from Redis and count successes
        deleted_count = sum(1 for t in tokens if client.delete(f"refresh:{t}"))
        
        # Clear the user's token set
        client.delete(token_key)
    
    logger.info(f"User {current_user_id} revoked {deleted_count} sessions for user {revoke_id}")
    return {"message": f"Successfully revoked {deleted_count} sessions for user {revoke_id}"}
