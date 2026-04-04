from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, Response
import secrets
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from jwt import PyJWTError as JWTError
from datetime import datetime, timedelta, timezone
import os
import logging
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Load backend .env for auth settings
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Initialize logger
logger = logging.getLogger(__name__)

from backend.services.redis_client import get_redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# Services and models
from backend.services import (
    passwordless,
    mfa,
    access_control,
    fido2_did,
    auth_utils,
    sso,
)
from backend.models.tables import UserTable
from backend.api.deps import get_db

# Auth dependencies
from backend.auth.schemes import (
    get_current_user,
    get_current_user_id,
)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
AUTH_METHODS = [
    m.strip()
    for m in os.getenv("AUTH_METHODS", "passwordless,mfa").split(",")
    if m.strip()
]

def _get_redis_client():
    return get_redis()


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
                detail=f"Too many attempts. Please try again in {window_seconds} seconds.",
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


class TimezoneSyncRequest(BaseModel):
    timezone: str


class ConsentSyncRequest(BaseModel):
    consent_analytics: Optional[bool] = None
    consent_notifications: Optional[bool] = None
    consent_ai_training: Optional[bool] = None


def _create_jwt_token(sub: str, email: Optional[str] = None):
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

    client = _get_redis_client()
    client.setex(
        f"refresh:{refresh_token}", REFRESH_TOKEN_EXPIRE_DAYS * 86400, str(sub)
    )
    client.sadd(f"user_tokens:{sub}", refresh_token)

    # Register this specific access session in Redis
    session_key = f"active_session:{access_token[-20:]}"
    tokens_key = f"user_tokens:{sub}"
    
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


def _attach_jwt_cookies(response: Response, token_data: dict):
    # For SPA frontends on different domains/origins, SameSite=None is required
    # so browser includes cookies in cross-site requests from localhost:3000 etc.
    # IMPORTANT: SameSite=None REQUIRES Secure flag in modern browsers.
    # In production we use secure=True; in local dev we also use secure=True when using HTTPS.
    # For HTTP localhost development, we must use SameSite=Lax instead.
    is_prod = os.getenv("NODE_ENV") == "production"
    is_https = os.getenv("PROTOCOL") == "https" or is_prod

    # SameSite=None requires Secure flag. For HTTP localhost, use Lax.
    if is_https:
        same_site_value = "none"
        secure_value = True
    else:
        # Development over HTTP: use Lax which works without Secure
        same_site_value = "lax"
        secure_value = False

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

    # Always ensure XSRF token is available for double-submit CSRF checks.
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
    response.set_cookie(
        key="graftai_refresh_token",
        value=token_data["refresh_token"],
        httponly=True,
        secure=secure_value,
        samesite=same_site_value,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60)),
):
    # Query database for the user with normalized email
    email = auth_utils.canonical_email(form_data.username)
    result = await db.execute(select(UserTable).where(UserTable.email == email))
    user = result.scalars().first()

    if not user or not auth_utils.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    tokens = _create_jwt_token(str(user.id), email=user.email)
    response = JSONResponse(
        content={
            "message": "Login successful",
            "user": {"id": user.id, "email": user.email}
        }
    )
    _attach_jwt_cookies(response, tokens)
    return response


@router.post("/register")
async def register(
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=3, window_seconds=60)),
):
    # Normalize email & Validate password complexity
    email = auth_utils.canonical_email(user_in.email)
    if not auth_utils.validate_password_complexity(user_in.password):
        raise HTTPException(
            status_code=400,
            detail="Password does not meet complexity requirements (12+ chars, mixed cases, digits, symbols)",
        )

    # Register user with explicit transaction block (including existence check within a single transaction)
    try:
        async with db.begin():
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            if result.scalars().first():
                logger.warning(f"Registration attempt for existing email: {email}")
                raise HTTPException(
                    status_code=400,
                    detail="Registration failed. Please try a different email or login.",
                )

            new_user = UserTable(
                id=str(uuid.uuid4()),
                email=email,
                full_name=user_in.full_name,
                hashed_password=auth_utils.get_password_hash(user_in.password),
                timezone=user_in.timezone or "UTC",
                is_active=True,
                is_superuser=False,
                tier="free",
                subscription_status="inactive",
                daily_ai_count=0,
                daily_sync_count=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                consent_analytics=True,
                consent_notifications=True,
                consent_ai_training=False,
            )
            db.add(new_user)
            await db.flush()

        # Offload welcome email to background worker outside DB transaction
        try:
            from backend.services.bg_tasks import enqueue_welcome_email
            await enqueue_welcome_email(
                user_email=email,
                full_name=user_in.full_name or email.split("@")[0],
            )
        except Exception as e:
            logger.warning(f"Failed to enqueue welcome email in register: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Registration failed")
        raise HTTPException(status_code=500, detail="Registration failed")

    return {"message": "User registered successfully", "id": new_user.id}


@router.get("/sso/start")
async def sso_start(provider: str = "google", redirect_to: str = "/dashboard"):
    """
    Initializes OAuth2 login flow for the given provider.
    """
    try:
        result = sso.start_oauth2_flow(provider, redirect_to)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=result["authorization_url"], status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSO start failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate SSO")


@router.get("/sso/callback")
async def sso_callback(
    code: str, 
    state: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Handles the OAuth2 provider callback, creates/syncs the user record, 
    sets HttpOnly cookies, and returns session data for the SPA.
    """
    try:
        # 1. Complete OAuth flow via authlib
        sso_data = await sso.complete_oauth2_flow(code, state)
        profile = sso_data.get("profile", {})
        email = auth_utils.canonical_email(profile.get("email"))
        name = profile.get("name")
        
        if not email:
            raise HTTPException(
                status_code=400, 
                detail="Provider did not return a valid email address. Authentication aborted."
            )
            
        # 2. Check if user already exists in local DB
        result = await db.execute(select(UserTable).where(UserTable.email == email))
        user = result.scalars().first()
        
        if not user:
            # 3. Provision new user record for first-time social login
            user = UserTable(
                id=str(uuid.uuid4()),
                email=email,
                full_name=name or email.split("@")[0],
                hashed_password=None,  # No password for SSO users
                timezone="UTC",
                is_active=True,
                is_superuser=False,
                tier="free",
                subscription_status="inactive",
                daily_ai_count=0,
                daily_sync_count=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                consent_analytics=True,
                consent_notifications=True,
                consent_ai_training=False,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Created new SSO user: {email} ({sso_data.get('provider')})")
        else:
            logger.info(f"SSO login for existing user: {email}")
            
        # 4. Issue local JWT session tokens
        tokens = _create_jwt_token(str(user.id), email=user.email)
        
        # 5. Prepare standard payload for frontend callback handler
        response_data = {
            "message": "SSO sign-in successful",
            "authenticated": True,
            "user": {
                "id": user.id, 
                "email": user.email,
                "name": user.full_name
            },
            "token": tokens, # Contains access_token and refresh_token
            "redirect_to": sso_data.get("redirect_to", "/dashboard")
        }
        
        response = JSONResponse(content=response_data)
        _attach_jwt_cookies(response, tokens)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSO callback exception: {e}")
        # Return structured error so frontend can show a user-friendly message
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/sync-consent")
async def sync_consent(
    data: ConsentSyncRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the user's privacy and consent preferences.
    """
    user_id = current_user.get("sub")
    
    async with db.begin():
        result = await db.execute(select(UserTable).where(UserTable.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if data.consent_analytics is not None:
            user.consent_analytics = data.consent_analytics
        if data.consent_notifications is not None:
            user.consent_notifications = data.consent_notifications
        if data.consent_ai_training is not None:
            user.consent_ai_training = data.consent_ai_training
        
        # Commit happens automatically
    
    logger.info(f"Updated consents for user {user_id}")
    return {"status": "success"}


@router.post("/sync-timezone")
async def sync_timezone(
    data: TimezoneSyncRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the user's preferred timezone.
    """
    user_id = current_user.get("sub")
    
    async with db.begin():
        result = await db.execute(select(UserTable).where(UserTable.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.timezone = data.timezone
        # Commit happens automatically
    
    logger.info(f"Updated timezone to {data.timezone} for user {user_id}")
    return {"status": "success", "timezone": data.timezone}


@router.post("/sync")
async def sync_session(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Synchronize the authenticated session with the local environment.
    This route confirms that the session is valid and the user is registered.
    """
    user_id = current_user.get("sub")
    email = current_user.get("email")
    
    # Ensure user exists in local UserTable (safety check for external providers)
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    
    if not user:
        # Safety fallback: create a local user record when session exists but user row is missing.
        user = UserTable(
            id=user_id,
            email=email,
            full_name=current_user.get("name", email.split("@")[0]),
            is_active=True
        )
        db.add(user)
        await db.commit()

    logger.info(f"Synchronized session for user {user_id}")
    return {"status": "synchronized", "user_id": user_id, "email": email}



@router.post("/passwordless/request")
def _passwordless_request(
    email: str,
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=3, window_seconds=300)),
):
    return passwordless.request_magic_link(email)


@router.post("/passwordless/verify")
def _passwordless_verify(
    email: str,
    code: str,
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60)),
):
    if not passwordless.verify_magic_link_code(email, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP"
        )
    token_data = _create_jwt_token(email)
    response = JSONResponse(content=token_data)
    _attach_jwt_cookies(response, token_data)
    return response


@router.post("/mfa/setup")
def _mfa_setup(user_id: int = Depends(get_current_user_id)):
    return mfa.start_mfa_enrollment(user_id)


@router.post("/mfa/verify")
def _mfa_verify(
    token: str,
    user_id: int = Depends(get_current_user_id),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60)),
):
    if not mfa.verify_mfa_token(user_id, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP token"
        )
    return {"status": "success"}


@router.get("/fido2/register")
def _fido2_start(user_id: int = Depends(get_current_user_id)):
    return fido2_did.start_fido2_registration(user_id)


@router.post("/fido2/register")
def _fido2_complete(attestation: dict, user_id: int = Depends(get_current_user_id)):
    if not fido2_did.complete_fido2_registration(user_id, attestation):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="FIDO2 registration failed"
        )
    return {"status": "registered"}


@router.post("/fido2/verify")
def _fido2_verify(assertion: dict, user_id: int = Depends(get_current_user_id)):
    if not fido2_did.verify_fido2_assertion(user_id, assertion):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="FIDO2 assertion failed"
        )
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
def check_attribute(
    attribute: str, value: str, user_id: int = Depends(get_current_user_id)
):
    return {"allowed": access_control.check_user_attribute(user_id, attribute, value)}


@router.get("/check")
async def check_auth(
    request: Request, 
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns authenticated user payload. Supports both Bearer token and cookie auth."""
    user_id = current_user.get("sub")
    
    # Fetch latest user data from DB to get the most up-to-date name/timezone
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    
    user_data = current_user.copy()
    if user:
        user_data["name"] = user.full_name
        user_data["full_name"] = user.full_name
        user_data["timezone"] = user.timezone
        # SaaS & Usage fields
        user_data["tier"] = user.tier
        user_data["subscription_status"] = user.subscription_status
        user_data["daily_ai_count"] = user.daily_ai_count
        user_data["daily_sync_count"] = user.daily_sync_count
        # Consent fields
        user_data["consent_analytics"] = user.consent_analytics
        user_data["consent_notifications"] = user.consent_notifications
        user_data["consent_ai_training"] = user.consent_ai_training

    # Ensure a readable XSRF cookie is present for the double-submit pattern.
    # The cookie must NOT be HttpOnly so client-side JS can read it and include
    # it in the `X-XSRF-TOKEN` header for mutating requests.
    is_prod = os.getenv("NODE_ENV") == "production"
    is_https = os.getenv("PROTOCOL") == "https" or is_prod

    if is_https:
        same_site_value = "none"
        secure_value = True
    else:
        same_site_value = "lax"
        secure_value = False

    xsrf_token = request.cookies.get("xsrf-token")
    if not xsrf_token:
        xsrf_token = secrets.token_urlsafe(32)

    content = {
        "authenticated": True,
        "user": user_data,
        "session": {
            "token": request.cookies.get("graftai_access_token"),
            "expires_at": current_user.get("exp")
        }
    }

    response = JSONResponse(content=content)
    response.set_cookie(
        key="xsrf-token",
        value=xsrf_token,
        httponly=False,
        secure=secure_value,
        samesite=same_site_value,
        max_age=86400,
        path="/",
    )
    # Expose CSRF token in response for SPA clients to read (when CORS expose headers are set)
    response.headers["x-xsrf-token"] = xsrf_token

    return response


@router.post("/refresh")
@router.post("/auth/refresh")
def refresh_token(request: Request, payload: Optional[RefreshTokenRequest] = None):
    """Get a new access token using a refresh token."""
    client = _get_redis_client()

    refresh_token_value = None
    # Prefer explicit JSON body, fallback to cookie.
    if payload and getattr(payload, "refresh_token", None):
        refresh_token_value = payload.refresh_token
    else:
        refresh_token_value = request.cookies.get("graftai_refresh_token")

    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    # Check if refresh token exists in Redis and not revoked
    user_id = client.get(f"refresh:{refresh_token_value}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Verify the refresh token JWT
    try:
        token_payload = jwt.decode(refresh_token_value, SECRET_KEY, algorithms=[ALGORITHM])
        if token_payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # ONE-TIME-USE refresh token semantics (rotate token)
    client.delete(f"refresh:{refresh_token_value}")
    client.srem(f"user_tokens:{user_id}", refresh_token_value)

    # Refresh tokens (Token Rotation is enforced)
    token_data = _create_jwt_token(user_id)
    response = JSONResponse(content={"message": "Token refreshed successfully"})
    _attach_jwt_cookies(response, token_data)
    return response


@router.post("/logout")
def logout(request: Request, current_user=Depends(get_current_user)):
    """Revoke refresh token and clear HttpOnly cookies."""
    client = _get_redis_client()

    refresh_token = request.cookies.get("graftai_refresh_token")
    if refresh_token:
        client.delete(f"refresh:{refresh_token}")

    response = JSONResponse(content={"message": "Successfully logged out"})
    # Clear HttpOnly cookies
    response.delete_cookie(key="graftai_access_token", path="/")
    response.delete_cookie(key="graftai_refresh_token", path="/")

    return response


@router.delete("/account")
async def delete_account(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete the user's account and all associated data.
    """
    user_id = current_user.get("sub")
    email = current_user.get("email")
    full_name = current_user.get("name", "User")

    # 1. Fetch user and delete within a single explicit transaction
    try:
        async with db.begin():
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            await db.execute(delete(UserTable).where(UserTable.id == user_id))

        # 2. Delete any cached provider metadata
        client = _get_redis_client()
        client.delete(f"sso_token:{user_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account deletion failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")

    # 3. Send Farewell Email
    try:
        from backend.services.notifications import notify_account_deleted_email
        await notify_account_deleted_email(user_email=email, full_name=user.full_name or full_name)
    except Exception as e:
        logger.warning(f"Farewell email failed for {email}: {e}")

    # 4. Clear cookies and return success
    response = JSONResponse(content={"message": "Account deleted successfully"})
    response.delete_cookie(key="graftai_access_token", path="/")
    response.delete_cookie(key="graftai_refresh_token", path="/")
    
    # 5. Cleanup Redis sessions - Revoke all active devices
    client = _get_redis_client()
    token_key = f"user_tokens:{user_id}"
    tokens = client.smembers(token_key)
    if tokens:
        for t in tokens:
            client.delete(f"refresh:{t}")
    client.delete(token_key)
    
    return response


@router.post("/revoke")
def revoke_sessions(
    target_user_id: Optional[int] = None,
    current_user_id: int = Depends(get_current_user_id),
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
                detail="Administrative privileges required to revoke other users' sessions",
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

    logger.info(
        f"User {current_user_id} revoked {deleted_count} sessions for user {revoke_id}"
    )
    return {
        "message": f"Successfully revoked {deleted_count} sessions for user {revoke_id}"
    }
