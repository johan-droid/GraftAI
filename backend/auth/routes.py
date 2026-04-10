import hashlib
import hmac
import os
import secrets
import logging
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, unquote_plus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from starlette.responses import Response, RedirectResponse
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
from backend.services.notifications import send_email_verification_code
from backend.services import google_auth, microsoft_auth, zoom_auth
from backend.services.sso import get_provider_config
from backend.utils.rate_limit import rate_limit, api_limits
from backend.auth.config import SECRET_KEY

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", os.getenv("FRONTEND_URL", "http://localhost:3000")).rstrip("/")

# OAuth state expiration (10 minutes)
OAUTH_STATE_EXPIRY_SECONDS = 600
# Allowed redirect paths (prevent open redirect)
ALLOWED_REDIRECT_PATHS = {"/dashboard", "/settings", "/calendar", "/profile"}


def _frontend_redirect_token(access_token: str, redirect_to: str = "/dashboard"):
    return f"{FRONTEND_BASE_URL}/auth-callback?access_token={quote_plus(access_token)}&redirect={quote_plus(redirect_to)}"


def _build_oauth_state(user_id: Optional[str], redirect_to: Optional[str] = "/dashboard") -> str:
    """
    Build signed OAuth state parameter with expiration.
    
    Format: timestamp:nonce:user_id:redirect:signature
    """
    # Validate redirect_to to prevent open redirect attacks
    safe_redirect = _sanitize_redirect(redirect_to or "/dashboard")
    
    # Generate components
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(16)
    user_id_str = user_id or ""
    
    # Create payload for signing
    payload = f"{timestamp}:{nonce}:{user_id_str}:{safe_redirect}"
    
    # Generate HMAC signature
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    
    return f"{timestamp}:{nonce}:{user_id_str}:{safe_redirect}:{signature}"


def _parse_oauth_state(state: str) -> tuple[Optional[str], str]:
    """
    Parse and validate OAuth state parameter.
    
    Validates:
    - Signature integrity
    - Expiration (10 minutes)
    - Redirect URL safety
    
    Returns:
        tuple: (user_id, redirect_to)
    
    Raises:
        HTTPException: If state is invalid or expired
    """
    if not state:
        logger.error("OAuth callback missing state parameter")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state: missing state"
        )
    
    # Parse state components
    parts = state.split(":")
    if len(parts) != 5:
        logger.error(f"Invalid OAuth state format: {len(parts)} parts instead of 5")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state: malformed"
        )
    
    timestamp_str, nonce, user_id, redirect_to, signature = parts
    
    # Reconstruct payload for signature verification
    payload = f"{timestamp_str}:{nonce}:{user_id}:{redirect_to}"
    expected_signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    
    # Verify signature using constant-time comparison
    if not hmac.compare_digest(signature, expected_signature):
        logger.error("OAuth state signature mismatch - possible CSRF attack")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state: signature verification failed"
        )
    
    # Check expiration
    try:
        state_time = int(timestamp_str)
        current_time = int(time.time())
        if current_time - state_time > OAUTH_STATE_EXPIRY_SECONDS:
            logger.error(f"OAuth state expired: {current_time - state_time}s old")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth state: expired"
            )
    except ValueError:
        logger.error("OAuth state contains invalid timestamp")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state: invalid timestamp"
        )
    
    # Validate redirect URL (additional safety check)
    decoded_redirect = unquote_plus(redirect_to)
    safe_redirect = _sanitize_redirect(decoded_redirect)
    
    # Return parsed values
    return user_id or None, safe_redirect


def _sanitize_redirect(redirect: str) -> str:
    """
    Sanitize redirect URL to prevent open redirect attacks.
    
    Only allows:
    - Relative paths starting with /
    - Known safe application paths
    """
    if not redirect:
        return "/dashboard"
    
    # Decode if URL-encoded
    decoded = unquote_plus(redirect)
    
    # Block absolute URLs (potential open redirect)
    if decoded.startswith(("http://", "https://", "//")):
        logger.warning(f"Blocked open redirect attempt: {decoded}")
        return "/dashboard"
    
    # Ensure relative path
    if not decoded.startswith("/"):
        decoded = "/" + decoded
    
    # Validate path is in allowed list (or default to dashboard)
    # Extract base path for validation
    base_path = decoded.split("?")[0].split("#")[0]
    
    # Allow exact matches and subpaths of allowed paths
    for allowed in ALLOWED_REDIRECT_PATHS:
        if base_path == allowed or base_path.startswith(allowed + "/"):
            return decoded
    
    # Log blocked redirect for security monitoring
    logger.warning(f"Blocked redirect to non-allowed path: {decoded}")
    return "/dashboard"


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])

from backend.auth.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ACCESS_TOKEN_TYPE,
    ALGORITHM,
    REFRESH_TOKEN_TYPE,
    REFRESH_TOKEN_EXPIRE_DAYS,
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
    samesite = "none" if is_production else "lax"

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

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        if len(v) > 100:
            raise ValueError("Full name must be less than 100 characters")
        return v.strip()


class EmailVerificationSchema(BaseModel):
    email: EmailStr
    code: str


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register")
async def register_user(user: UserRegisterSchema, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["register"])

    email = user.email.lower().strip()

    stmt = select(UserTable).where(UserTable.email == email)
    existing_user = (await db.execute(stmt)).scalars().first()

    code = str(secrets.randbelow(900000) + 100000)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    try:
        if existing_user:
            if existing_user.email_verified:
                raise HTTPException(status_code=400, detail="Email already registered")

            existing_user.full_name = user.full_name or existing_user.full_name
            existing_user.hashed_password = get_password_hash(user.password)
            existing_user.email_verification_code = code
            existing_user.email_verification_expires_at = expires_at
            await db.commit()
            await db.refresh(existing_user)
            await send_email_verification_code(email, existing_user.full_name or email, code)
            logger.info(f"Resent verification code to unverified user: {email}")
            return {"message": "Verification code resent to your email", "email": email}

        new_user = UserTable(
            email=email,
            full_name=user.full_name,
            hashed_password=get_password_hash(user.password),
            email_verified=False,
            email_verification_code=code,
            email_verification_expires_at=expires_at,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        await send_email_verification_code(email, user.full_name, code)
        logger.info(f"New user registered: {email}")
        return {"message": "Verification code sent to your email", "email": email}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/verify-email")
async def verify_email(payload: EmailVerificationSchema, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower().strip()
    stmt = select(UserTable).where(UserTable.email == email)
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email_verified:
        return {"message": "Email already verified"}
    if not user.email_verification_code or not user.email_verification_expires_at:
        raise HTTPException(status_code=400, detail="No verification code found. Please request a new code.")

    now = datetime.now(timezone.utc)
    if user.email_verification_expires_at < now:
        raise HTTPException(status_code=400, detail="Verification code expired. Please request a new code.")
    if user.email_verification_code != payload.code.strip():
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.email_verified = True
    user.email_verification_code = None
    user.email_verification_expires_at = None
    await db.commit()
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(payload: dict, db: AsyncSession = Depends(get_db)):
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    email = email.lower().strip()
    stmt = select(UserTable).where(UserTable.email == email)
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")

    code = str(secrets.randbelow(900000) + 100000)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    user.email_verification_code = code
    user.email_verification_expires_at = expires_at
    await db.commit()
    await send_email_verification_code(user.email, user.full_name or user.email, code)

    return {"message": "Verification code resent to your email"}


async def _authenticate_user(form_data: OAuth2PasswordRequestForm, db: AsyncSession) -> UserTable:
    email = form_data.username.lower().strip()

    stmt = select(UserTable).where(UserTable.email == email)
    user = (await db.execute(stmt)).scalars().first()

    if not user:
        logger.warning(f"Failed login attempt for non-existent user: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.email_verified:
        logger.warning(f"Login attempt for unverified email: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not verified. Please verify your email before signing in.",
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


@router.post("/token", response_model=None)
async def token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["login"])

    user = await _authenticate_user(form_data, db)
    access_token = _create_access_token(user.id)
    refresh_token = _create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return _build_token_response(access_token, refresh_token)


@router.post("/login", response_model=None)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Legacy login route kept for compatibility — delegates to /token logic directly."""
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["login"])

    user = await _authenticate_user(form_data, db)
    access_token = _create_access_token(user.id)
    refresh_token = _create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return _build_token_response(access_token, refresh_token)


@router.get("/check")
async def check(
    request: Request,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
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


@router.post("/refresh", response_model=None)
async def refresh(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
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

    new_access_token = _create_access_token(user.id)
    new_refresh_token = _create_refresh_token(user.id)
    _set_auth_cookies(response, new_access_token, new_refresh_token)
    return {
        "message": "Token refreshed successfully",
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
    }


@router.post("/logout", response_model=None)
async def logout(response: Response):
    response.delete_cookie("graftai_access_token", path="/")
    response.delete_cookie("graftai_refresh_token", path="/")
    return {"message": "Logged out"}


@router.get("/google/login")
async def google_login(
    token: Optional[str] = None,
    redirect_to: Optional[str] = "/dashboard",
    force_consent: bool = False,
):
    try:
        user_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass

        state = _build_oauth_state(user_id, redirect_to)
        auth_url = await google_auth.get_google_auth_url(
            state,
            prompt="consent" if force_consent else None,
        )
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        logger.error(f"Google OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["oauth_callback"])

    try:
        if not state:
            logger.error("Google callback missing state parameter")
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        user_id, redirect_to = _parse_oauth_state(state)

        data = await google_auth.fetch_google_tokens(code)
        email = data.get("email")

        if not email:
            logger.error("Google OAuth returned no email")
            raise HTTPException(status_code=400, detail="Failed to retrieve email from Google")

        email = email.lower().strip()

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
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                email_verified=True,
                email_verification_code=None,
                email_verification_expires_at=None,
            )
            db.add(user)
            await db.flush()
            logger.info(f"New user created via Google OAuth: {email}")
        elif not user.email_verified:
            user.email_verified = True
            user.email_verification_code = None
            user.email_verification_expires_at = None

        token_info = data.get("token", {})
        if not token_info.get("access_token"):
            logger.error("Google OAuth returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        stmt = select(UserTokenTable).where(
            UserTokenTable.user_id == user.id,
            UserTokenTable.provider == "google",
        )
        user_token = (await db.execute(stmt)).scalars().first()

        if not user_token:
            user_token = UserTokenTable(user_id=user.id, provider="google")
            db.add(user_token)

        user_token.access_token = token_info["access_token"]
        user_token.refresh_token = token_info.get("refresh_token") or user_token.refresh_token
        user_token.expires_at = (
            datetime.fromtimestamp(token_info["expires_at"], tz=timezone.utc)
            if "expires_at" in token_info
            else None
        )
        user_token.is_active = True

        await db.commit()
        logger.info(f"Google OAuth successful for user: {email}")

        access_token = create_access_token(data={"sub": user.id})
        return RedirectResponse(url=_frontend_redirect_token(access_token, redirect_to))

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
            raise HTTPException(status_code=400, detail="Google OAuth configuration error. Please contact support.")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/sync-timezone")
async def sync_timezone(payload: dict):
    tz = payload.get("timezone")
    if not tz:
        raise HTTPException(status_code=400, detail="Missing timezone")
    return {"status": "updated", "timezone": tz}


@router.get("/sso/start")
async def sso_start(
    provider: str,
    redirect_to: Optional[str] = "/dashboard",
    token: Optional[str] = None,
):
    provider = provider.lower()
    if get_provider_config(provider) is None:
        raise HTTPException(status_code=400, detail="Unsupported SSO provider")

    query_parts = []
    if redirect_to:
        query_parts.append(f"redirect_to={quote_plus(redirect_to)}")
    if token:
        query_parts.append(f"token={quote_plus(token)}")

    target_url = f"/api/v1/auth/{provider}/login"
    if query_parts:
        target_url = f"{target_url}?{'&'.join(query_parts)}"

    return RedirectResponse(url=target_url)


@router.get("/microsoft/login")
async def microsoft_login(token: Optional[str] = None, redirect_to: Optional[str] = "/dashboard"):
    try:
        user_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass

        state = _build_oauth_state(user_id, redirect_to)
        auth_url = await microsoft_auth.get_microsoft_auth_url(state)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        logger.error(f"Microsoft OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/microsoft/callback")
async def microsoft_callback(request: Request, code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["oauth_callback"])

    try:
        if not state:
            logger.error("Microsoft callback missing state parameter")
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        user_id, redirect_to = _parse_oauth_state(state)

        data = await microsoft_auth.fetch_microsoft_tokens(code)
        email = data.get("email")

        if not email:
            logger.error("Microsoft OAuth returned no email")
            raise HTTPException(status_code=400, detail="Failed to retrieve email from Microsoft")

        email = email.lower().strip()

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
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                email_verified=True,
                email_verification_code=None,
                email_verification_expires_at=None,
            )
            db.add(user)
            await db.flush()
            logger.info(f"New user created via Microsoft OAuth: {email}")
        elif not user.email_verified:
            user.email_verified = True
            user.email_verification_code = None
            user.email_verification_expires_at = None

        token_info = data.get("token", {})
        if not token_info.get("access_token"):
            logger.error("Microsoft OAuth returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        stmt = select(UserTokenTable).where(
            UserTokenTable.user_id == user.id,
            UserTokenTable.provider == "microsoft",
        )
        user_token = (await db.execute(stmt)).scalars().first()

        if not user_token:
            user_token = UserTokenTable(user_id=user.id, provider="microsoft")
            db.add(user_token)

        user_token.access_token = token_info["access_token"]
        user_token.refresh_token = token_info.get("refresh_token") or user_token.refresh_token
        user_token.expires_at = (
            datetime.fromtimestamp(token_info["expires_at"], tz=timezone.utc)
            if "expires_at" in token_info
            else None
        )
        user_token.is_active = True

        await db.commit()
        logger.info(f"Microsoft OAuth successful for user: {email}")

        access_token = create_access_token(data={"sub": user.id})
        return RedirectResponse(url=_frontend_redirect_token(access_token, redirect_to))

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
            raise HTTPException(status_code=400, detail="Microsoft OAuth configuration error. Please contact support.")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/zoom/login")
async def zoom_login(token: Optional[str] = None, redirect_to: Optional[str] = "/dashboard"):
    try:
        user_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass

        state = _build_oauth_state(user_id, redirect_to)
        auth_url = await zoom_auth.get_zoom_auth_url(state)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        logger.error(f"Zoom OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/zoom/callback")
async def zoom_callback(code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        user_id, redirect_to = _parse_oauth_state(state or "")

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
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                email_verified=True,
                email_verification_code=None,
                email_verification_expires_at=None,
            )
            db.add(user)
            await db.flush()
        elif not user.email_verified:
            user.email_verified = True
            user.email_verification_code = None
            user.email_verification_expires_at = None

        token_info = data["token"]
        stmt = select(UserTokenTable).where(UserTokenTable.user_id == user.id, UserTokenTable.provider == "zoom")
        user_token = (await db.execute(stmt)).scalars().first()
        if not user_token:
            user_token = UserTokenTable(user_id=user.id, provider="zoom")
            db.add(user_token)

        user_token.access_token = token_info["access_token"]
        user_token.refresh_token = token_info.get("refresh_token") or user_token.refresh_token
        user_token.expires_at = (
            datetime.fromtimestamp(token_info["expires_at"], tz=timezone.utc)
            if "expires_at" in token_info
            else None
        )

        await db.commit()
        access_token = create_access_token(data={"sub": user.id})
        return RedirectResponse(url=_frontend_redirect_token(access_token, redirect_to))

    except ValueError as e:
        logger.error(f"Zoom OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Zoom Callback Error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


# ═══════════════════════════════════════════════════════════════════════════════
# APPLE SIGN IN & CALENDAR
# ═══════════════════════════════════════════════════════════════════════════════

from backend.services import apple_auth


@router.get("/apple/login")
async def apple_login(token: Optional[str] = None, redirect_to: Optional[str] = "/dashboard"):
    """Initiate Apple Sign In OAuth flow."""
    try:
        user_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass

        state = _build_oauth_state(user_id, redirect_to)
        auth_url = await apple_auth.get_apple_auth_url(state)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        logger.error(f"Apple OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/apple/callback")
async def apple_callback(
    request: Request,
    code: str,
    state: Optional[str] = None,
    user: Optional[str] = None,  # Apple returns user data on first sign-in
    db: AsyncSession = Depends(get_db),
):
    """
    Apple Sign In callback.
    
    Note: Apple uses POST for the callback (response_mode=form_post).
    """
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(client_ip, api_limits["oauth_callback"])

    try:
        if not state:
            logger.error("Apple callback missing state parameter")
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        user_id, redirect_to = _parse_oauth_state(state)

        data = await apple_auth.fetch_apple_tokens(code)
        email = data.get("email")

        if not email:
            logger.error("Apple Sign In returned no email")
            raise HTTPException(status_code=400, detail="Failed to retrieve email from Apple")

        email = email.lower().strip()

        if user_id:
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            db_user = result.scalars().first()
        else:
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            db_user = result.scalars().first()

        if not db_user:
            db_user = UserTable(
                email=email,
                full_name=data.get("full_name", email.split("@")[0]),
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                email_verified=True,  # Apple verifies email
                email_verification_code=None,
                email_verification_expires_at=None,
            )
            db.add(db_user)
            await db.flush()
            logger.info(f"New user created via Apple Sign In: {email}")

        token_info = data.get("token", {})
        if not token_info.get("access_token"):
            logger.error("Apple Sign In returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        # Store or update Apple token
        stmt = select(UserTokenTable).where(
            UserTokenTable.user_id == db_user.id,
            UserTokenTable.provider == "apple",
        )
        user_token = (await db.execute(stmt)).scalars().first()

        if not user_token:
            user_token = UserTokenTable(user_id=db_user.id, provider="apple")
            db.add(user_token)

        user_token.access_token = token_info["access_token"]
        user_token.refresh_token = token_info.get("refresh_token") or user_token.refresh_token
        user_token.expires_at = (
            datetime.fromtimestamp(token_info["expires_at"], tz=timezone.utc)
            if "expires_at" in token_info
            else None
        )
        user_token.is_active = True
        
        # Store Apple-specific metadata
        user_token.metadata = {
            "apple_user_id": data.get("apple_user_id"),
            "auth_method": "sign_in_with_apple",
        }

        await db.commit()
        logger.info(f"Apple Sign In successful for user: {email}")

        access_token = create_access_token(data={"sub": db_user.id})
        return RedirectResponse(url=_frontend_redirect_token(access_token, redirect_to))

    except ValueError as e:
        logger.error(f"Apple OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apple Callback Error: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Authentication failed")