from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from jwt import PyJWTError as JWTError
from datetime import datetime, timedelta, timezone
import os
import redis
import functools
import logging
import uuid
import json
from pathlib import Path
from dotenv import load_dotenv

# Load backend .env for auth settings
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Initialize logger
logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# Services and models
from backend.services import (
    sso,
    passwordless,
    mfa,
    access_control,
    fido2_did,
    auth_utils,
)
from backend.models.tables import UserTable
from backend.models.user_token import UserTokenTable
from backend.api.deps import get_db

# Auth dependencies
from backend.auth.schemes import (
    get_current_user,
    get_current_user_id,
    is_admin_user,
    blacklist_token,
)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
AUTH_METHODS = [
    m.strip()
    for m in os.getenv("AUTH_METHODS", "sso,passwordless,mfa").split(",")
    if m.strip()
]

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
    client.setex(session_key, ACCESS_TOKEN_EXPIRE_MINUTES * 60, str(sub))

    client.expire(f"user_tokens:{sub}", REFRESH_TOKEN_EXPIRE_DAYS * 86400)

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
        content={"token": tokens, "user": {"id": user.id, "email": user.email}}
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

    # Check if user already exists
    result = await db.execute(select(UserTable).where(UserTable.email == email))
    if result.scalars().first():
        # Generic message to prevent enumeration
        logger.warning(f"Registration attempt for existing email: {email}")
        raise HTTPException(
            status_code=400,
            detail="Registration failed. Please try a different email or login.",
        )

    # Register user with explicit transaction block
    try:
        async with db.begin():
            new_user = UserTable(
                email=email,
                full_name=user_in.full_name,
                hashed_password=auth_utils.get_password_hash(user_in.password),
                timezone=user_in.timezone,
            )
            db.add(new_user)
            await db.flush()
            
            # Send welcome email for new manual registration
            try:
                from backend.services.notifications import notify_welcome_email
                await notify_welcome_email(
                    user_email=email,
                    full_name=user_in.full_name or email.split("@")[0],
                )
            except Exception as e:
                logger.warning(f"Welcome email send failed for {email}: {e}")
    except Exception as e:
        logger.error(f"Registration failed: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Registration failed")

    return {"message": "User registered successfully", "id": new_user.id}


@router.get("/sso/start")
def sso_start(provider: str = "github", redirect_to: str = "/dashboard"):
    try:
        return sso.start_oauth2_flow(provider=provider, redirect_to=redirect_to)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


@router.get("/sso/callback")
async def sso_callback(
    code: str, state: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    This endpoint is hit TWICE during OAuth:
    1. By Google (browser navigation) → we redirect to the frontend WITHOUT consuming state.
    2. By the frontend's fetch() call → we consume the state and return JSON with the token.
    
    CRITICAL: The state must be retrieved BEFORE completing the OAuth flow,
    because complete_oauth2_flow may delete the state from Redis.
    """
    fetch_param = request.query_params.get("fetch") == "true"
    accept_header = request.headers.get("accept", "").lower()
    is_json_accept = "application/json" in accept_header

    is_navigation = not fetch_param and not is_json_accept

    if is_navigation:
        # STEP 1: Browser redirect from provider → send to frontend callback page.
        # This does not consume state, the second (fetch=true) call does.
        frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")

        # If no frontend route is present, `auth-callback` will be 404 from the frontend side.
        # This almost always means the callback URL used in provider settings is wrong.
        redirect_url = f"{frontend_base}/auth-callback?code={code}&state={state}"

        return RedirectResponse(redirect_url, status_code=302)

    # STEP 2: Frontend API call → complete the OAuth flow (consumes the state).
    try:
        # IMPORTANT: Verify and retrieve state data BEFORE calling complete_oauth2_flow
        # This preserves redirect_to and other session data
        verified_state = sso._verify_state(state)
        if not verified_state:
            raise HTTPException(status_code=403, detail="OAuth state signature verification failed")
        
        # Get state data before it gets consumed
        state_data = sso._get_oauth_state(verified_state)
        if not state_data:
            raise RuntimeError("Invalid or expired state")
        
        # Now complete the OAuth flow (this will fetch tokens and user profile)
        payload = await sso.complete_oauth2_flow(code=code, state=state)
        profile = payload.get("profile", {})
        token = payload.get("token")
        provider_name = payload.get("provider", "google")

        logger.info(
            f"SSO callback success for provider={provider_name} state=[...truncated]"
        )

        # Upsert user in one transaction
        async with db.begin():
            email = profile.get("email")
            if not email:
                raise HTTPException(status_code=400, detail="Email required from SSO provider")
            
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            user = result.scalars().first()
            
            if not user:
                user_id = str(uuid.uuid4())
                user = UserTable(
                    id=user_id,
                    email=email,
                    full_name=profile.get("name"),
                    is_active=True,
                    timezone=profile.get("timezone", "UTC"),
                )
                db.add(user)
                await db.flush()
                
                # Send welcome email ONLY for new users
                try:
                    from backend.services.notifications import notify_welcome_email
                    await notify_welcome_email(
                        user_email=email,
                        full_name=user.full_name or profile.get("name", "User"),
                    )
                except Exception as e:
                    logger.warning(f"Welcome email send failed for {email}: {e}")
            else:
                user_id = str(user.id)
                user.full_name = profile.get("name") or user.full_name

        # 1. Store provider token in DB for synchronization and revocation
        if token:
            async with db.begin():
                # Check if we already have a token for this provider/user combination
                from sqlalchemy import and_
                stmt = select(UserTokenTable).where(
                    and_(
                        UserTokenTable.user_id == user_id,
                        UserTokenTable.provider == provider_name
                    )
                )
                result = await db.execute(stmt)
                existing_token = result.scalars().first()

                token_data = {
                    "user_id": user_id,
                    "provider": provider_name,
                    "access_token": token.get("access_token"),
                    "refresh_token": token.get("refresh_token"),
                    "scopes": token.get("scope"),
                    "is_active": True
                }
                if token.get("expires_at"):
                    token_data["expires_at"] = datetime.fromtimestamp(token["expires_at"], tz=timezone.utc)

                if existing_token:
                    for key, value in token_data.items():
                        if value is not None:
                            setattr(existing_token, key, value)
                    logger.info(f"🔄 Updated {provider_name} tokens in DB for system user {user_id}")
                else:
                    db.add(UserTokenTable(**token_data))
                    logger.info(f"➕ Saved new {provider_name} tokens in DB for system user {user_id}")

            # Also maintain temporary session in Redis for revocation
            redis_client = _get_redis_client()
            redis_client.setex(
                f"sso_token:{user_id}", 
                timedelta(days=7), 
                json.dumps({"provider": provider_name, "token": token})
            )

        own_token = _create_jwt_token(user_id, email=email)
        response = JSONResponse(
            content={
                "auth": {k: v for k, v in payload.items() if k != "token"}, # Don't leak provider token to frontend
                "token": own_token,
                "user_id": user_id,
                "redirect_to": payload.get("redirect_to", "/dashboard"),
            }
        )
        _attach_jwt_cookies(response, own_token)
        return response
    except HTTPException as e:
        logger.error(
            f"SSO callback failure for signed_state={state}, code={code}, err={e.detail}"
        )
        raise e
    except Exception as e:
        logger.error(
            f"SSO callback failure for signed_state={state}, code={code}, err={e}"
        )

        msg = str(e)
        if not msg.strip():
            msg = f"{type(e).__name__} during OAuth flow"
            
        if "Invalid or expired state" in msg or "OAuth state" in msg:
            if is_navigation:
                frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
                redirect_url = f"{frontend_base}/login?error=oauth_state_expired"
                return RedirectResponse(redirect_url, status_code=302)
            raise HTTPException(status_code=status.HTTP_410_GONE, detail=msg)

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


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
        # This shouldn't happen with Better Auth as it writes to the same DB,
        # but kept for robustness against other future providers.
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

    return {
        "authenticated": True,
        "user": user_data,
        "session": {
            "token": request.cookies.get("graftai_access_token"),
            "expires_at": current_user.get("exp")
        }
    }


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

    # Generate new token pair
    token_data = _create_jwt_token(user_id)
    response = JSONResponse(content=token_data)
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
        # Pre-fetch SSO token for revocation since we need user_id
        client = _get_redis_client()
        sso_data_raw = client.get(f"sso_token:{user_id}")
        
        async with db.begin():
            # Ensure existence and get name for email
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = result.scalars().first()
            if not user:
                # We can't raise inside the transaction block without proper rollback, 
                # but async with db.begin() handles exception rollback implicitly.
                raise HTTPException(status_code=404, detail="User not found")
            
            # Deletion (DB constraints ON DELETE CASCADE handle events, etc.)
            await db.execute(delete(UserTable).where(UserTable.id == user_id))
            # Commit happens automatically on exit
        
        # 2. Revoke Provider Token (SaaS-grade disconnection)
        if sso_data_raw:
            try:
                sso_data = json.loads(sso_data_raw)
                await sso.revoke_provider_token(
                    provider=sso_data.get("provider"), 
                    token=sso_data.get("token")
                )
                client.delete(f"sso_token:{user_id}")
            except Exception as e:
                logger.warning(f"Provider revocation failed for {user_id}: {e}")

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
