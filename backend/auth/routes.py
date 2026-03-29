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
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load backend .env for auth settings
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

# Initialize logger
logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# Services and models
from backend.api.deps import get_db
from backend.services.sync_engine import sync_engine
from backend.utils.security import encrypt_token, decrypt_token
from backend.models.tables import UserTable
from backend.services import (
    sso,
    auth_utils,
)

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")

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

from backend.services.redis_client import get_redis, check_rate_limit
# Redundant _get_redis_client removed, centralized in backend.services.redis_client


def get_rate_limiter(max_requests: int, window_seconds: int):
    """Dependency-based rate limiter for FastAPI routes using centralized Redis."""

    async def rate_limiter(request: Request):
        try:
            client_ip = request.headers.get(
                "x-forwarded-for", request.client.host if request.client else "unknown"
            )
            if "," in client_ip:
                client_ip = client_ip.split(",")[0].strip()

            # Use a path-specific key to avoid cross-endpoint leakage
            key = f"auth_rate_limit:{client_ip}:{request.url.path}"
            
            allowed = await check_rate_limit(key, max_requests, window_seconds)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many attempts. Please try again in {window_seconds} seconds.",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Rate limiter failed (failing open): {e}")

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


from backend.services.provisioning import provision_default_organization

async def _create_jwt_token(sub: str, email: Optional[str] = None, db: Optional[AsyncSession] = None):
    """Create access and refresh tokens and persist refresh token in Redis (Async)."""
    now = datetime.now(timezone.utc)
    
    # Ensure user has an organization (and migrate legacy data) if DB session is provided
    if db:
        await provision_default_organization(db, str(sub))

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

    try:
        from backend.services.redis_client import redis_service
        client = redis_service.client
        
        await client.setex(
            f"refresh:{refresh_token}", REFRESH_TOKEN_EXPIRE_DAYS * 86400, str(sub)
        )
        await client.sadd(f"user_tokens:{sub}", refresh_token)

        # Register this specific access session in Redis
        session_key = f"active_session:{access_token[-20:]}"
        await client.setex(session_key, ACCESS_TOKEN_EXPIRE_MINUTES * 60, str(sub))

        await client.expire(f"user_tokens:{sub}", REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    except Exception as e:
        logger.warning(f"Failed to persist token in Redis (failing open for session): {e}")

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

    # Tokens with Provisioning
    tokens = await _create_jwt_token(str(user.id), email=user.email, db=db)
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

        # 1. Check if this is a 'Connect' flow (Linking account to an existing user)
        if state_data.get("flow") == "connect":
            user_id = state_data.get("user_id")
            if not user_id: 
                raise HTTPException(status_code=400, detail="User mapping lost during connection")
            
            async with db.begin():
                result = await db.execute(select(UserTable).where(UserTable.id == user_id))
                user = result.scalars().first()
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                # Save tokens based on provider
                if provider_name == "google":
                    user.google_access_token = encrypt_token(token["access_token"])
                    if "refresh_token" in token:
                        user.google_refresh_token = encrypt_token(token["refresh_token"])
                    user.google_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token["expires_in"])
                    user.google_id = profile.get("id")
                elif provider_name == "microsoft":
                    user.microsoft_access_token = encrypt_token(token["access_token"])
                    if "refresh_token" in token:
                        user.microsoft_refresh_token = encrypt_token(token["refresh_token"])
                    user.microsoft_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token["expires_in"])
                    user.microsoft_id = profile.get("id")

            # Trigger initial sync in background
            if provider_name == "google":
                await sync_engine.sync_google_calendar(user_id, db)
            elif provider_name == "microsoft":
                await sync_engine.sync_microsoft_calendar(user_id, db)

            frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
            return RedirectResponse(f"{frontend_base}/dashboard/settings?{provider_name}=connected")

        # 2. Default Login flow
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

        # Store own provider token in Redis for potential future revocation
        if token:
            from backend.services.redis_client import redis_service
            await redis_service.client.setex(
                f"sso_token:{user_id}", 
                timedelta(days=7), 
                json.dumps({"provider": provider_name, "token": token})
            )

        # Access & Refresh Tokens (with Multi-Tenant Provisioning)
        own_token = await _create_jwt_token(user_id, email=email, db=db)
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



@router.get("/zoom/connect")
async def zoom_connect(current_user: dict = Depends(get_current_user)):
    """
    Generates a Zoom Authorization URL for the current user to 'Connect' their account.
    """
    client_id = os.getenv("ZOOM_CLIENT_ID")
    redirect_uri = os.getenv("ZOOM_REDIRECT_URI", f"{APP_BASE_URL}/auth/zoom/callback")
    
    if not client_id:
        raise HTTPException(status_code=500, detail="Zoom Client ID not configured")
        
    # Standard Zoom Authorization URL (v2)
    # Scopes should be space-separated
    scopes = os.getenv("ZOOM_SCOPES", "user:read:user meeting:write:meeting meeting:read:meeting user:read:user.settings")
    
    # Use a state to thwart CSRF and identify the user in the callback
    state = str(uuid.uuid4())
    from backend.services.redis_client import redis_service
    await redis_service.client.setex(f"zoom_state:{state}", 600, current_user["sub"])
    
    auth_url = (
        f"https://zoom.us/oauth/authorize?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        f"&scope={scopes}"
    )
    
    return {"authorization_url": auth_url}


@router.get("/zoom/callback")
async def zoom_callback(
    code: str, 
    state: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Handles the Zoom OAuth redirect, exchanges code for tokens, and persists them.
    """
    from backend.services.redis_client import redis_service
    user_id = await redis_service.client.get(f"zoom_state:{state}")
    
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid or expired OAuth state")
    
    # Delete state immediately (one-time use)
    await redis_service.client.delete(f"zoom_state:{state}")
    
    # Exchange code for token
    client_id = os.getenv("ZOOM_CLIENT_ID")
    client_secret = os.getenv("ZOOM_CLIENT_SECRET")
    redirect_uri = os.getenv("ZOOM_REDIRECT_URI", f"{APP_BASE_URL}/auth/zoom/callback")
    
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://zoom.us/oauth/token",
            params={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        if resp.status_code != 200:
            logger.error(f"Zoom token exchange failed: {resp.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange code for Zoom tokens")
            
        token_data = resp.json()
        
    # Use ZoomService to persist tokens (handles encryption and DB write)
    from backend.services.zoom import zoom_service
    await zoom_service.save_user_tokens(user_id, token_data)
    
    # Redirect back to frontend dashboard with success message
    frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
    return RedirectResponse(f"{frontend_base}/dashboard/settings?zoom=connected")


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


@router.get("/google/connect")
async def google_connect(current_user: dict = Depends(get_current_user)):
    """Starts the persistent Google Calendar 'Strong Connection' flow."""
    user_id = current_user.get("sub")
    # Add scopes needed for calendar sync
    extra_data = {"flow": "connect", "user_id": user_id}
    return sso.start_oauth2_flow(provider="google", extra_data=extra_data)

@router.get("/microsoft/connect")
async def microsoft_microsoft_connect(current_user: dict = Depends(get_current_user)):
    """Starts the persistent Microsoft Graph 'Strong Connection' flow."""
    user_id = current_user.get("sub")
    extra_data = {"flow": "connect", "user_id": user_id}
    # Microsoft needs specific scopes for calendars
    return sso.start_oauth2_flow(provider="microsoft", extra_data=extra_data)

@router.post("/sync")
async def sync_calendars(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Triggers the Sovereign Sync Engine to fetch external events."""
    user_id = current_user.get("sub")
    try:
        await sync_engine.sync_google_calendar(user_id, db)
        await sync_engine.sync_microsoft_calendar(user_id, db)
        return {"status": "success", "message": "External calendars synchronized"}
    except Exception as e:
        logger.error(f"Manual Sync Sync Failed: {e}")
        raise HTTPException(status_code=500, detail="Synchronization failed")

@router.post("/sync/session")
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
    
    # Ensure user has an organization (and migrate legacy data)
    await provision_default_organization(db, str(user_id))

    await db.commit()
    logger.info(f"Synchronized session and provisioned for user {user_id}")
    return {"status": "synchronized", "user_id": user_id, "email": email}



@router.post("/passwordless/request")
async def _passwordless_request(
    email: str,
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=3, window_seconds=300)),
):
    return await passwordless.request_magic_link(email)


@router.post("/passwordless/verify")
async def _passwordless_verify(
    email: str,
    code: str,
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60)),
):
    if not await passwordless.verify_magic_link_code(email, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP"
        )

    # Fetch user to get ID and ensure they exist
    result = await db.execute(select(UserTable).where(UserTable.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User account not found"
        )

    # Token generation (with Org Provisioning)
    token_data = await _create_jwt_token(str(user.id), email=email, db=db)
    response = JSONResponse(content=token_data)
    _attach_jwt_cookies(response, token_data)
    return response


@router.post("/mfa/setup")
async def _mfa_setup(user_id: int = Depends(get_current_user_id)):
    return await mfa.start_mfa_enrollment(user_id)


@router.post("/mfa/verify")
async def _mfa_verify(
    token: str,
    user_id: int = Depends(get_current_user_id),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60)),
):
    if not await mfa.verify_mfa_token(user_id, token):
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
        # Consent fields
        user_data["consent_analytics"] = user.consent_analytics
        user_data["consent_notifications"] = user.consent_notifications
        user_data["consent_ai_training"] = user.consent_ai_training
        # OAuth Connection Flags
        user_data["zoom_connected"] = bool(user.zoom_access_token)
        user_data["google_connected"] = bool(user.google_access_token)
        user_data["microsoft_connected"] = bool(user.microsoft_access_token)

    return {
        "authenticated": True,
        "user": user_data,
        "session": {
            "token": request.cookies.get("graftai_access_token"),
            "expires_at": current_user.get("exp")
        }
    }


@router.post("/refresh")
async def refresh_token(
    request: Request, 
    payload: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get a new access token using a refresh token."""
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

    # Try to verify/rotate token in Redis
    try:
        from backend.services.redis_client import redis_service
        client = redis_service.client
        # Check if refresh token exists in Redis and not revoked
        user_id_from_redis = await client.get(f"refresh:{refresh_token_value}")
        
        # ONE-TIME-USE refresh token semantics (rotate token)
        await client.delete(f"refresh:{refresh_token_value}")
        
        if user_id_from_redis:
            # Cleanup user token mapping
            await client.srem(f"user_tokens:{user_id_from_redis}", refresh_token_value)
    except Exception as e:
        logger.warning(f"Redis refresh token rotation failed (infra issue): {e}")

    # Verify the refresh token JWT (Sovereign mode - we still trust the cryptographically signed JWT if Redis is down)
    try:
        token_payload = jwt.decode(refresh_token_value, SECRET_KEY, algorithms=[ALGORITHM])
        if token_payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )
        user_id = token_payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Generate new token pair
    # Token generation (with Org Provisioning)
    # We use sub (user_id) from the decoded refresh token
    token_data = await _create_jwt_token(user_id, email=token_payload.get("email"), db=db)
    response = JSONResponse(content=token_data)
    _attach_jwt_cookies(response, token_data)
    return response


@router.post("/logout")
async def logout(request: Request, current_user=Depends(get_current_user)):
    """Revoke refresh token and clear HttpOnly cookies (Async)."""
    from backend.services.redis_client import redis_service
    client = redis_service.client

    refresh_token = request.cookies.get("graftai_refresh_token")
    if refresh_token:
        try:
            await client.delete(f"refresh:{refresh_token}")
        except Exception as e:
            logger.warning(f"Logout Redis cleanup failed (failing open): {e}")

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
        sso_data_raw = None
        try:
            from backend.services.redis_client import redis_service
            sso_data_raw = await redis_service.client.get(f"sso_token:{user_id}")
        except Exception:
            pass
        
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
                try:
                    from backend.services.redis_client import redis_service
                    await redis_service.client.delete(f"sso_token:{user_id}")
                except Exception:
                    pass
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
    try:
        from backend.services.redis_client import redis_service
        token_key = f"user_tokens:{user_id}"
        tokens = await redis_service.client.smembers(token_key)
        if tokens:
            for t in tokens:
                await redis_service.client.delete(f"refresh:{t}")
        await redis_service.client.delete(token_key)
    except Exception as e:
        logger.warning(f"Account deletion Redis cleanup failed: {e}")
    
    return response


@router.post("/revoke")
async def revoke_sessions(
    target_user_id: Optional[int] = None,
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Revoke all sessions for a user (Async).
    - If target_user_id is provided, requires admin privileges.
    - If not provided, revokes current user's own sessions.
    """
    from backend.services.redis_client import redis_service
    client = redis_service.client

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
    deleted_count: int = 0
    try:
        token_key = f"user_tokens:{revoke_id}"
        tokens = await client.smembers(token_key)

        if tokens:
            # Delete each refresh token from Redis and count successes
            for t in tokens:
                if await client.delete(f"refresh:{t}"):
                    deleted_count += 1

            # Clear the user's token set
            await client.delete(token_key)
    except Exception as e:
        logger.warning(f"Session revocation Redis failure: {e}")

    logger.info(
        f"User {current_user_id} revoked {deleted_count} sessions for user {revoke_id}"
    )
    return {
        "message": f"Successfully revoked {deleted_count} sessions for user {revoke_id}"
    }
