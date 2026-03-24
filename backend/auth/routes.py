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

from backend.services import sso, passwordless, mfa, access_control, fido2_did, auth_utils
from backend.models.tables import UserTable
from backend.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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


def rate_limit(max_requests: int, window_seconds: int):
    """Decorator to apply strict rate limiting to auth endpoints."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs or args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                for v in kwargs.values():
                    if isinstance(v, Request):
                        request = v
                        break
            
            if request:
                client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
                if "," in client_ip:
                    client_ip = client_ip.split(",")[0].strip()
                
                client = _get_redis_client()
                key = f"auth_rate_limit:{client_ip}:{func.__name__}"
                
                current = client.get(key)
                if current is None:
                    client.setex(key, window_seconds, 1)
                elif int(current) >= max_requests:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Too many attempts. Please try again in {window_seconds} seconds."
                    )
                else:
                    client.incr(key)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


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
@rate_limit(max_requests=5, window_seconds=60)  # 5 login attempts per minute
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db), request: Request = None):
    # Query database for the user
    result = await db.execute(select(UserTable).where(UserTable.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    response = JSONResponse(content={"status": "success"})
    tokens = _create_jwt_token(str(user.id), response=response)
    # Return basic user info + token meta in body, but real tokens in HttpOnly cookies
    response.body = JSONResponse(content={"token": tokens, "user": {"id": user.id, "email": user.email}}).body
    return response

@router.post("/register")
@rate_limit(max_requests=3, window_seconds=60)  # 3 registrations per minute
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db), request: Request = None):
    # Check if user already exists
    result = await db.execute(select(UserTable).where(UserTable.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Register user with explicit transaction block
    try:
        async with db.begin():
            new_user = UserTable(
                email=user_in.email,
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
        payload = sso.complete_oauth2_flow(code=code, state=state)
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
@rate_limit(max_requests=3, window_seconds=300)  # 3 OTP requests per 5 minutes
def _passwordless_request(email: str, request: Request = None):
    return passwordless.request_magic_link(email)


@router.post("/passwordless/verify")
@rate_limit(max_requests=5, window_seconds=60)  # 5 OTP verification attempts per minute
def _passwordless_verify(email: str, code: str, request: Request = None):
    if not passwordless.verify_magic_link_code(email, code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")
    return _create_jwt_token(email)


@router.post("/mfa/setup")
def _mfa_setup(user_id: int):
    return mfa.start_mfa_enrollment(user_id)


@router.post("/mfa/verify")
@rate_limit(max_requests=5, window_seconds=60)  # 5 TOTP attempts per minute
def _mfa_verify(user_id: int, token: str, request: Request = None):
    if not mfa.verify_mfa_token(user_id, token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP token")
    return {"status": "success"}


@router.get("/fido2/register")
def _fido2_start(user_id: int):
    return fido2_did.start_fido2_registration(user_id)


@router.post("/fido2/register")
def _fido2_complete(request: FIDO2AttestationRequest):
    if not fido2_did.complete_fido2_registration(request.user_id, request.attestation):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="FIDO2 registration failed")
    return {"status": "registered"}


@router.post("/fido2/verify")
def _fido2_verify(request: FIDO2AssertionRequest):
    if not fido2_did.verify_fido2_assertion(request.user_id, request.assertion):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="FIDO2 assertion failed")
    return {"status": "verified"}


@router.post("/did/issue")
def _did_issue(user_id: int):
    return {"did": fido2_did.issue_decentralized_id(user_id)}


@router.post("/did/verify")
def _did_verify(request: DIDVerifyRequest):
    valid = fido2_did.verify_decentralized_id(request.user_id, request.did)
    if not valid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DID not found")
    return {"status": "valid"}


@router.post("/authenticate")
async def authenticate(request: Request, db: AsyncSession = Depends(get_db)):
    # Fallback chain execution across multiple auth methods.
    errors = {}

    for method in AUTH_METHODS:
        try:
            if method == "sso":
                code = request.query_params.get("code")
                state = request.query_params.get("state")
                if code and state:
                    # Await the async sso_callback and pass required dependencies
                    return await sso_callback(code=code, state=state, request=request, db=db)
                raise RuntimeError("SSO requires code/state query params")
            if method == "passwordless":
                email = request.query_params.get("email")
                code = request.query_params.get("code")
                if email and code and passwordless.verify_magic_link_code(email, code):
                    return _create_jwt_token(email)
                raise RuntimeError("Passwordless failed")
            if method == "mfa":
                user_id = request.query_params.get("user_id")
                token = request.query_params.get("token")
                if user_id and token and mfa.verify_mfa_token(int(user_id), token):
                    return {"status": "mfa_success"}
                raise RuntimeError("MFA failed")
        except Exception as e:
            errors[method] = str(e)
            continue

    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"fallback_errors": errors})


@router.get("/access-control/check-role")
def check_role(user_id: int, role: str):
    return {"allowed": access_control.check_user_role(user_id, role)}


@router.get("/access-control/check-attribute")
def check_attribute(user_id: int, attribute: str, value: str):
    return {"allowed": access_control.check_user_attribute(user_id, attribute, value)}


from backend.auth.schemes import get_current_user, blacklist_token


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
def revoke_all_user_sessions(current_user=Depends(get_current_user)):
    """Admin endpoint to revoke all sessions for a user (force re-login)."""
    # This is a placeholder for full session management
    # In production, you'd track all refresh tokens per user
    return {"message": "Session revocation not fully implemented - delete refresh tokens from Redis manually"}
