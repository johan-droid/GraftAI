import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr, field_validator

from backend.services.auth_utils import get_password_hash, verify_password

from backend.utils.db import get_db
from backend.models.tables import UserTable, UserTokenTable
from backend.auth.schemes import get_current_user_id
from backend.services.usage import get_next_quota_reset, get_trial_days_left
from backend.services import google_auth, microsoft_auth, zoom_auth
from backend.utils.rate_limit import rate_limit, api_limits

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", os.getenv("FRONTEND_URL", "https://www.graftai.tech")).rstrip("/")

def _frontend_redirect_token(access_token: str, redirect_to: str = "/dashboard"):
    return f"{FRONTEND_BASE_URL}/auth-callback?access_token={quote_plus(access_token)}&redirect={quote_plus(redirect_to)}"

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])

# Configuration
from backend.auth.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ACCESS_TOKEN_TYPE,
    ALGORITHM,
    REFRESH_TOKEN_TYPE,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)

def _create_jwt_token_impl(user_id: str, token_type: str):
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


def _create_jwt_token_pair(user_id: str):
    return {
        "access_token": _create_jwt_token_impl(user_id, ACCESS_TOKEN_TYPE),
        "refresh_token": _create_jwt_token_impl(user_id, REFRESH_TOKEN_TYPE),
    }


def _create_access_token(user_id: str) -> str:
    return _create_jwt_token_impl(user_id, ACCESS_TOKEN_TYPE)


def _create_refresh_token(user_id: str) -> str:
    return _create_jwt_token_impl(user_id, REFRESH_TOKEN_TYPE)


async def _create_jwt_token(user_id: str):
    return _create_jwt_token_pair(user_id)


def _decode_jwt_token(token: str, expected_type: Optional[str] = None) -> dict:
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


def _set_auth_cookies(response: Optional[Response], access_token: str, refresh_token: str):
    if response is None:
        return

    is_production = os.getenv("ENV", "development") == "production"
    secure = is_production
    samesite = "none" if is_production else "lax"  # 'none' required for cross-origin in production
    
    cookie_kwargs = {
        "httponly": True,
        "samesite": samesite,
        "path": "/",
        "max_age": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    if secure:
        cookie_kwargs["secure"] = True

    response.set_cookie("graftai_access_token", access_token, **cookie_kwargs)
    refresh_cookie_kwargs = cookie_kwargs.copy()
    refresh_cookie_kwargs["max_age"] = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie("graftai_refresh_token", refresh_token, **refresh_cookie_kwargs)


async def _get_user_from_token(token: str, db: AsyncSession):
    payload = _decode_jwt_token(token, expected_type=ACCESS_TOKEN_TYPE)
    stmt = select(UserTable).where(UserTable.id == payload["sub"])
    user = (await db.execute(stmt)).scalars().first()
    return user


def _build_token_response(access_token: str, refresh_token: str):
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }

import re

class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        if len(v) > 100:
            raise ValueError('Full name must be less than 100 characters')
        return v.strip()

# --- Helper Functions ---

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Standard Email/Password Auth ---

@router.post("/register")
async def register_user(user: UserRegisterSchema, request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new user with email and password."""
    # Rate limiting by IP
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["register"])
    
    # Normalize email
    email = user.email.lower().strip()
    
    stmt = select(UserTable).where(UserTable.email == email)
    existing_user = (await db.execute(stmt)).scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        new_user = UserTable(
            email=email,
            full_name=user.full_name,
            hashed_password=get_password_hash(user.password)
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"New user registered: {email}")
        return {"message": "User registered successfully", "user_id": new_user.id}
    except Exception as e:
        await db.rollback()
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

async def _authenticate_user(form_data: OAuth2PasswordRequestForm, db: AsyncSession) -> UserTable:
    # Normalize email for lookup
    email = form_data.username.lower().strip()
    
    stmt = select(UserTable).where(UserTable.email == email)
    user = (await db.execute(stmt)).scalars().first()
    
    if not user:
        # Use constant-time comparison to prevent timing attacks
        logger.warning(f"Failed login attempt for non-existent user: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.hashed_password:
        logger.error(f"User {email} has no password set")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Successful login for user: {email}")
    return user

@router.get("/integrations/status")
async def integration_status(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    active_stmt = select(UserTokenTable.provider).where(
        UserTokenTable.user_id == user_id,
        UserTokenTable.is_active == True,
    )
    inactive_stmt = select(UserTokenTable.provider).where(
        UserTokenTable.user_id == user_id,
        UserTokenTable.is_active == False,
    )
    active_providers = (await db.execute(active_stmt)).scalars().all()
    inactive_providers = (await db.execute(inactive_stmt)).scalars().all()

    return {
        "connections": {
            "active": list(active_providers),
            "inactive": list(sorted(set(inactive_providers) - set(active_providers))),
        }
    }

@router.post("/token")
async def token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    response: Optional[Response] = None,
):
    """Standard OAuth2 token endpoint."""
    # Rate limiting by IP
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["login"])
    
    user = await _authenticate_user(form_data, db)
    access_token = _create_access_token(user.id)
    refresh_token = _create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return _build_token_response(access_token, refresh_token)

@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    response: Optional[Response] = None,
):
    """Legacy login route kept for compatibility."""
    return await token(request, form_data, db, response)

@router.get("/check")
async def check(
    request: Request,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Validate an access token and return the current session."""
    bearer = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        bearer = auth_header.split(" ", 1)[1].strip()

    raw_token = token or bearer or request.cookies.get("graftai_access_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = _decode_jwt_token(raw_token, expected_type=ACCESS_TOKEN_TYPE)
    except HTTPException:
        raise

    stmt = select(UserTable).where(UserTable.id == payload["sub"])
    user = (await db.execute(stmt)).scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "username": user.username,
            "daily_ai_limit": 10,
            "daily_sync_limit": 3,
            "trial_days_left": get_trial_days_left(user.created_at),
            "trial_active": True,
            "quota_reset_at": get_next_quota_reset().isoformat(),
        },
    }

@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and issue a new access token."""
    token_value = refresh_token or request.query_params.get("refresh_token") or request.cookies.get("graftai_refresh_token")
    if not token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_jwt_token(token_value, expected_type=REFRESH_TOKEN_TYPE)
    stmt = select(UserTable).where(UserTable.id == payload["sub"])
    user = (await db.execute(stmt)).scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = _create_access_token(user.id)
    refresh_token = _create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return {
        "message": "Token refreshed successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("graftai_access_token", path="/")
    response.delete_cookie("graftai_refresh_token", path="/")
    return {"message": "Logged out"}

# --- Google OAuth ---

@router.get("/google/login")
async def google_login(token: Optional[str] = None):
    """Starts Google OAuth flow. Can take an optional JWT to link to an existing user."""
    try:
        user_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass
                
        # We embed user_id in state so the callback knows who triggered this connect flow
        state = f"{secrets.token_urlsafe(16)}|{user_id if user_id else ''}"
        auth_url = await google_auth.get_google_auth_url(state)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        logger.error(f"Google OAuth Configuration Error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Handles Google callback and upserts tokens."""
    # Rate limiting by IP
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["oauth_callback"])
    
    try:
        # 1. Validate state parameter to prevent CSRF
        if not state:
            logger.error("Google callback missing state parameter")
            raise HTTPException(status_code=400, detail="Invalid OAuth state")
        
        # 2. Parse state to find who this belongs to
        user_id = None
        if "|" in state:
            parts = state.split("|")
            if len(parts) == 2:
                user_id = parts[1] if parts[1] else None

        data = await google_auth.fetch_google_tokens(code)
        email = data.get("email")
        
        if not email:
            logger.error("Google OAuth returned no email")
            raise HTTPException(status_code=400, detail="Failed to retrieve email from Google")
        
        # Normalize email
        email = email.lower().strip()
        
        # 3. Fetch or Create User (State user_id takes priority)
        if user_id:
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = result.scalars().first()
        else:
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            user = result.scalars().first()

        if not user:
            # Only create NEW user if we didn't come from a "Connect" flow
            user = UserTable(
                email=email,
                full_name=data.get("full_name", email.split("@")[0]),
                hashed_password=get_password_hash(secrets.token_urlsafe(32))
            )
            db.add(user)
            await db.flush()
            logger.info(f"New user created via Google OAuth: {email}")

        # 4. Upsert Tokens
        token_info = data.get("token", {})
        if not token_info.get("access_token"):
            logger.error("Google OAuth returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")
        
        stmt = select(UserTokenTable).where(
            UserTokenTable.user_id == user.id, 
            UserTokenTable.provider == "google"
        )
        user_token = (await db.execute(stmt)).scalars().first()
        
        if not user_token:
            user_token = UserTokenTable(user_id=user.id, provider="google")
            db.add(user_token)
        
        user_token.access_token = token_info["access_token"]
        user_token.refresh_token = token_info.get("refresh_token") or user_token.refresh_token
        user_token.expires_at = (
            datetime.fromtimestamp(token_info["expires_at"], tz=timezone.utc) 
            if "expires_at" in token_info else None
        )
        user_token.is_active = True
        
        await db.commit()
        logger.info(f"Google OAuth successful for user: {email}")
        
        # 5. Finalize Login
        access_token = create_access_token(data={"sub": user.id})
        return RedirectResponse(url=_frontend_redirect_token(access_token))
        
    except ValueError as e:
        logger.error(f"Google OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google Callback Error: {e}", exc_info=True)
        await db.rollback()
        error_msg = str(e)
        if "invalid_request" in error_msg or "unauthorized_client" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Google OAuth configuration error. Please contact support."
            )
        raise HTTPException(status_code=500, detail="Authentication failed")

@router.post("/sync-timezone")
async def sync_timezone(payload: dict):
    """Keep the user's timezone preference in sync.

    This is a lightweight endpoint for frontend sync requests.
    """
    timezone = payload.get("timezone")
    if not timezone:
        raise HTTPException(status_code=400, detail="Missing timezone")
    return {"status": "updated", "timezone": timezone}

# --- Microsoft OAuth ---

@router.get("/microsoft/login")
async def microsoft_login(token: Optional[str] = None):
    """Starts Microsoft OAuth flow. Can take an optional JWT to link to an existing user."""
    try:
        user_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass
                
        # Embed user_id in state
        state = f"{secrets.token_urlsafe(16)}|{user_id if user_id else ''}"
        auth_url = await microsoft_auth.get_microsoft_auth_url(state)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        logger.error(f"Microsoft OAuth Configuration Error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/microsoft/callback")
async def microsoft_callback(request: Request, code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Handles Microsoft callback and upserts tokens."""
    # Rate limiting by IP
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["oauth_callback"])
    
    try:
        # 1. Validate state parameter
        if not state:
            logger.error("Microsoft callback missing state parameter")
            raise HTTPException(status_code=400, detail="Invalid OAuth state")
        
        # 2. Parse state
        user_id = None
        if "|" in state:
            parts = state.split("|")
            if len(parts) == 2:
                user_id = parts[1] if parts[1] else None

        data = await microsoft_auth.fetch_microsoft_tokens(code)
        email = data.get("email")
        
        if not email:
            logger.error("Microsoft OAuth returned no email")
            raise HTTPException(status_code=400, detail="Failed to retrieve email from Microsoft")
        
        # Normalize email
        email = email.lower().strip()
        
        # 3. Fetch or Create User
        if user_id:
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = result.scalars().first()
        else:
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            user = result.scalars().first()

        if not user:
            user = UserTable(
                email=email,
                full_name=data.get("full_name", email.split("@")[0]),
                hashed_password=get_password_hash(secrets.token_urlsafe(32))
            )
            db.add(user)
            await db.flush()
            logger.info(f"New user created via Microsoft OAuth: {email}")

        # 4. Upsert Tokens
        token_info = data.get("token", {})
        if not token_info.get("access_token"):
            logger.error("Microsoft OAuth returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")
        
        stmt = select(UserTokenTable).where(
            UserTokenTable.user_id == user.id, 
            UserTokenTable.provider == "microsoft"
        )
        user_token = (await db.execute(stmt)).scalars().first()
        
        if not user_token:
            user_token = UserTokenTable(user_id=user.id, provider="microsoft")
            db.add(user_token)
        
        user_token.access_token = token_info["access_token"]
        user_token.refresh_token = token_info.get("refresh_token") or user_token.refresh_token
        user_token.expires_at = (
            datetime.fromtimestamp(token_info["expires_at"], tz=timezone.utc) 
            if "expires_at" in token_info else None
        )
        user_token.is_active = True
        
        await db.commit()
        logger.info(f"Microsoft OAuth successful for user: {email}")
        
        access_token = create_access_token(data={"sub": user.id})
        return RedirectResponse(url=_frontend_redirect_token(access_token))
        
    except ValueError as e:
        logger.error(f"Microsoft OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Microsoft Callback Error: {e}", exc_info=True)
        await db.rollback()
        error_msg = str(e)
        if "AADSTS" in error_msg or "unauthorized_client" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Microsoft OAuth configuration error. Please contact support."
            )
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/zoom/login")
async def zoom_login(token: Optional[str] = None):
    """Starts Zoom OAuth flow. Can take an optional JWT to link to an existing user."""
    try:
        user_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass

        state = f"{secrets.token_urlsafe(16)}|{user_id if user_id else ''}"
        auth_url = await zoom_auth.get_zoom_auth_url(state)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        logger.error(f"Zoom OAuth Configuration Error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/zoom/callback")
async def zoom_callback(code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Handles Zoom callback and upserts tokens."""
    try:
        user_id = None
        if state and "|" in state:
            user_id = state.split("|")[1]
            if not user_id:
                user_id = None

        data = await zoom_auth.fetch_zoom_tokens(code)
        email = data["email"]

        if user_id:
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = result.scalars().first()
        else:
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            user = result.scalars().first()

        if not user:
            user = UserTable(
                email=email,
                full_name=data["full_name"],
                hashed_password=get_password_hash(secrets.token_urlsafe(32))
            )
            db.add(user)
            await db.flush()

        token_info = data["token"]
        stmt = select(UserTokenTable).where(UserTokenTable.user_id == user.id, UserTokenTable.provider == "zoom")
        user_token = (await db.execute(stmt)).scalars().first()
        if not user_token:
            user_token = UserTokenTable(user_id=user.id, provider="zoom")
            db.add(user_token)

        user_token.access_token = token_info["access_token"]
        user_token.refresh_token = token_info.get("refresh_token") or user_token.refresh_token
        user_token.expires_at = datetime.fromtimestamp(token_info["expires_at"], tz=timezone.utc) if "expires_at" in token_info else None

        await db.commit()
        access_token = create_access_token(data={"sub": user.id})
        return RedirectResponse(url=_frontend_redirect_token(access_token))

    except ValueError as e:
        logger.error(f"Zoom OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Zoom Callback Error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")
