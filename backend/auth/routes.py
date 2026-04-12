import os
import logging
from urllib.parse import quote_plus
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from starlette.responses import Response, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from jose import jwt

from backend.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user_with_dummy_password,
    decode_jwt_token,
    upsert_user_token,
)
from backend.services.oauth_service import (
    get_client_ip,
    build_oauth_state,
    parse_oauth_state,
    frontend_redirect_token,
)
from backend.utils.db import get_db
from backend.models.tables import UserTable, UserTokenTable
from backend.auth.schemes import get_current_user, get_current_user_id
from backend.services.usage import get_next_quota_reset, get_trial_days_left
from backend.services import google_auth, microsoft_auth
from backend.services.sso import get_provider_config
from backend.utils.rate_limit import rate_limit, api_limits
from backend.auth.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ACCESS_TOKEN_TYPE,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_TYPE,
    SECRET_KEY,
)

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", os.getenv("FRONTEND_URL", "http://localhost:3000")).rstrip("/")

# OAuth state expiration (10 minutes)
OAUTH_STATE_EXPIRY_SECONDS = 600
# Allowed redirect paths (prevent open redirect)
ALLOWED_REDIRECT_PATHS = {"/dashboard", "/settings", "/calendar", "/profile", "/auth-callback"}


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])

from pydantic import BaseModel

class SocialExchangeRequest(BaseModel):
    provider: str
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    email: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class OnboardingRequest(BaseModel):
    name: Optional[str] = None
    timezone: Optional[str] = None
    work_hours_start: Optional[str] = None
    work_hours_end: Optional[str] = None
    notifications_enabled: Optional[bool] = True
    ai_suggestions_enabled: Optional[bool] = True

@router.post("/social/exchange")
async def social_exchange(req: SocialExchangeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["login"])

    if req.provider not in ["google", "microsoft", "microsoft-entra-id"]:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    if not req.access_token:
        raise HTTPException(status_code=400, detail="Access token required for social exchange")
        
    try:
        if req.provider == "google":
            provider_profile = await google_auth.verify_google_token(req.access_token)
        else:
            provider_profile = await microsoft_auth.verify_microsoft_token(req.access_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    email = provider_profile.get("email") or req.email
    if not email:
        raise HTTPException(status_code=400, detail="Email required for social login")
    
    from backend.services.auth_service import create_user_with_dummy_password
    user = await create_user_with_dummy_password(db, email=email, full_name=provider_profile.get("full_name") or req.name or "", verified=True)
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Store provider logic if needed
    await upsert_user_token(db, str(user.id), req.provider, req.access_token, req.id_token)
    
    return {"access_token": access_token, "refresh_token": refresh_token}


def _set_auth_cookies(response: Optional[Response], access_token: str, refresh_token: str):
    if response is None:
        return

    # Force secure cookies if deployed on Render to satisfy cross-origin requirements
    is_production = os.getenv("ENV", "development") == "production"
    is_render = os.getenv("RENDER") is not None
    secure = is_production or is_render
    samesite = "none" if secure else "lax"

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
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["login"])

    user = await authenticate_user(form_data, db)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
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
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["login"])

    user = await authenticate_user(form_data, db)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
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
        payload = decode_jwt_token(raw_token, expected_type=ACCESS_TOKEN_TYPE)
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

    payload = decode_jwt_token(token_value, expected_type=REFRESH_TOKEN_TYPE)
    stmt = select(UserTable).where(UserTable.id == payload["sub"])
    user = (await db.execute(stmt)).scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
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


# ═══════════════════════════════════════════════════════════════════════════════
# SSO / OAUTH PROVIDERS (Google, Microsoft)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/google/login")
async def google_login(
    request: Request,
    token: Optional[str] = None,
    redirect_to: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    force_consent: bool = False,
    frontend_url: Optional[str] = None,
):
    try:
        user_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass

        # Extract frontend URL from query parameter or Referer header
        if not frontend_url:
            referer = request.headers.get("referer")
            if referer:
                # Extract origin from referer (scheme://host)
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                frontend_url = f"{parsed.scheme}://{parsed.netloc}"

        redirect_to = redirect_to or redirect_uri or "/dashboard"
        state = build_oauth_state(user_id, redirect_to, provider="google", frontend_url=frontend_url)
        auth_url = await google_auth.get_google_auth_url(
            state,
            prompt="consent" if force_consent else None,
        )
        return RedirectResponse(url=auth_url, status_code=303)
    except ValueError as e:
        logger.error(f"Google OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["oauth_callback"])

    try:
        if request.query_params.get("error"):
            error_desc = request.query_params.get("error_description") or request.query_params.get("error")
            logger.error("Google OAuth returned error: %s", error_desc)
            raise HTTPException(status_code=400, detail=f"Google OAuth error: {error_desc}")

        if not state:
            logger.error("Google callback missing state parameter")
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        user_id, redirect_to, _, frontend_url = parse_oauth_state(state)

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
            user = await create_user_with_dummy_password(
                db,
                email=email,
                full_name=data.get("full_name", email.split("@")[0]),
                verified=True,
                email_verification_code=None,
                email_verification_expires_at=None,
            )
            logger.info(f"New user created via Google OAuth: {email}")
        elif not user.email_verified:
            user.email_verified = True
            user.email_verification_code = None
            user.email_verification_expires_at = None

        token_info = data.get("token", {})
        access_token = token_info.get("access_token")
        if not access_token:
            logger.error("Google OAuth returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        await upsert_user_token(db, user, "google", token_info)
        await db.commit()
        logger.info(f"Google OAuth successful for user: {email}")

        backend_access_token = create_access_token(user.id)
        backend_refresh_token = create_refresh_token(user.id)
        return RedirectResponse(
            url=frontend_redirect_token(backend_access_token, redirect_to, frontend_url, backend_refresh_token),
            status_code=303,
        )

    except ValueError as e:
        logger.error(f"Google OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Google Callback Error: {e}", exc_info=True)
        error_msg = str(e).lower()
        if "invalid_grant" in error_msg or "expired" in error_msg or "mismatch" in error_msg:
            return RedirectResponse(
                url=f"{FRONTEND_BASE_URL}/login?error=Session expired. Please log in again.",
                status_code=303,
            )
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/sso/callback")
async def sso_callback(
    request: Request,
    code: str,
    state: Optional[str] = None,
    fetch: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Unified SSO callback endpoint that routes to the correct provider.
    
    When fetch=true, returns JSON with token for frontend to handle.
    Otherwise, redirects to frontend with token in URL.
    """
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["oauth_callback"])
    
    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state parameter")
    
    try:
        # Parse state to get redirect info and provider
        user_id, redirect_to, parsed_provider, frontend_url = parse_oauth_state(state)
        
        # Validate provider from state
        if parsed_provider == "google":
            data = await google_auth.fetch_google_tokens(code)
            provider = "google"
        elif parsed_provider == "microsoft":
            data = await microsoft_auth.fetch_microsoft_tokens(code)
            provider = "microsoft"
        else:
            # Fallback for old state format without provider - try to detect
            # This maintains backward compatibility
            logger.warning("OAuth state missing provider, attempting detection")
            try:
                data = await google_auth.fetch_google_tokens(code)
                provider = "google"
            except Exception:
                try:
                    data = await microsoft_auth.fetch_microsoft_tokens(code)
                    provider = "microsoft"
                except Exception:
                    raise HTTPException(
                        status_code=400, 
                        detail="Unable to determine OAuth provider from state. Please try again."
                    )
        
        email = data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Failed to retrieve email from OAuth provider")
        
        email = email.lower().strip()
        
        # Get or create user
        if user_id:
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = result.scalars().first()
        else:
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            user = result.scalars().first()
        
        if not user:
            user = await create_user_with_dummy_password(
                db,
                email=email,
                full_name=data.get("full_name", email.split("@")[0]),
                verified=True,
            )
            logger.info(f"New user created via {provider} OAuth: {email}")
        elif not user.email_verified:
            user.email_verified = True
        
        # Store tokens
        token_info = data.get("token", {})
        access_token = token_info.get("access_token")
        if not access_token:
            logger.error(f"{provider} OAuth returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token from OAuth provider")
        
        await upsert_user_token(db, user, provider, token_info)
        await db.commit()
        
        # Generate JWT tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        logger.info(f"{provider} OAuth successful for user: {email}")
        
        # Return JSON if fetch=true, otherwise redirect
        if fetch:
            return {
                "token": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                },
                "redirect_to": redirect_to,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name
                }
            }
        else:
            return RedirectResponse(
                url=frontend_redirect_token(access_token, redirect_to, frontend_url, refresh_token),
                status_code=303,
            )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"SSO callback error: {e}", exc_info=True)
        error_msg = str(e).lower()
        if "invalid_grant" in error_msg or "expired" in error_msg or "mismatch" in error_msg:
            return RedirectResponse(
                url=f"{FRONTEND_BASE_URL}/login?error=Session expired. Please log in again.",
                status_code=303,
            )
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/sso/start")
async def sso_start(
    provider: str,
    redirect_to: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    token: Optional[str] = None,
):
    provider = provider.lower()
    if get_provider_config(provider) is None:
        raise HTTPException(status_code=400, detail="Unsupported SSO provider")

    final_redirect = redirect_to or redirect_uri or "/dashboard"
    query_parts = []
    if final_redirect:
        query_parts.append(f"redirect_to={quote_plus(final_redirect)}")
    if token:
        query_parts.append(f"token={quote_plus(token)}")

    target_url = f"/api/v1/auth/{provider}/login"
    if query_parts:
        target_url = f"{target_url}?{'&'.join(query_parts)}"

    return RedirectResponse(url=target_url, status_code=303)


@router.get("/microsoft/login")
async def microsoft_login(
    request: Request,
    token: Optional[str] = None,
    redirect_to: Optional[str] = None,
    redirect_uri: Optional[str] = None,
):
    try:
        user_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass

        # Extract frontend URL from Referer header
        frontend_url = None
        referer = request.headers.get("referer")
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            frontend_url = f"{parsed.scheme}://{parsed.netloc}"

        redirect_to = redirect_to or redirect_uri or "/dashboard"
        state = build_oauth_state(user_id, redirect_to, provider="microsoft", frontend_url=frontend_url)
        auth_url = await microsoft_auth.get_microsoft_auth_url(state)
        return RedirectResponse(url=auth_url, status_code=303)
    except ValueError as e:
        logger.error(f"Microsoft OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/microsoft/callback")
async def microsoft_callback(request: Request, code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["oauth_callback"])

    try:
        if not state:
            logger.error("Microsoft callback missing state parameter")
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        user_id, redirect_to, _, frontend_url = parse_oauth_state(state)

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
            user = await create_user_with_dummy_password(
                db,
                email=email,
                full_name=data.get("full_name", email.split("@")[0]),
                verified=True,
                email_verification_code=None,
                email_verification_expires_at=None,
            )
            logger.info(f"New user created via Microsoft OAuth: {email}")
        elif not user.email_verified:
            user.email_verified = True
            user.email_verification_code = None
            user.email_verification_expires_at = None

        token_info = data.get("token", {})
        if not token_info.get("access_token"):
            logger.error("Microsoft OAuth returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        await upsert_user_token(db, user, "microsoft", token_info)
        await db.commit()
        logger.info(f"Microsoft OAuth successful for user: {email}")

        backend_access_token = create_access_token(user.id)
        backend_refresh_token = create_refresh_token(user.id)
        return RedirectResponse(
            url=frontend_redirect_token(backend_access_token, redirect_to, frontend_url, backend_refresh_token),
            status_code=303,
        )

    except ValueError as e:
        logger.error(f"Microsoft OAuth Configuration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Microsoft Callback Error: {e}", exc_info=True)
        await db.rollback()
        error_msg = str(e).lower()
        if "invalid_grant" in error_msg or "expired" in error_msg or "mismatch" in error_msg:
            return RedirectResponse(
                url=f"{FRONTEND_BASE_URL}/login?error=Session expired. Please log in again.",
                status_code=303,
            )
        if "aadsts" in error_msg or "unauthorized_client" in error_msg:
            raise HTTPException(status_code=400, detail="Microsoft OAuth configuration error. Please contact support.")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/forgot-password")
async def forgot_password(
    req: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Send password reset email to user."""
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["login"])
    
    # Find user by email
    stmt = select(UserTable).where(UserTable.email == req.email.lower().strip())
    user = (await db.execute(stmt)).scalars().first()
    
    if not user:
        # Don't reveal if email exists (security best practice)
        return {"message": "If an account exists with this email, you will receive a password reset link."}
    
    # Generate reset token
    import secrets
    from datetime import datetime, timedelta
    
    reset_token = secrets.token_urlsafe(32)
    user.password_reset_token = reset_token
    user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=24)
    
    await db.commit()
    
    # TODO: Send actual email with reset link
    # For now, log the token for development
    logger.info(f"Password reset requested for {req.email}")
    
    return {"message": "If an account exists with this email, you will receive a password reset link."}


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password (requires current password)."""
    from backend.services.auth_service import verify_password, get_password_hash
    
    # Verify current password
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    current_user.hashed_password = get_password_hash(req.new_password)
    current_user.password_reset_token = None
    current_user.password_reset_expires_at = None
    
    await db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/verify")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email with token."""
    from datetime import datetime
    
    # Find user with matching verification token
    stmt = select(UserTable).where(
        and_(
            UserTable.email_verification_code == token,
            UserTable.email_verification_expires_at > datetime.utcnow()
        )
    )
    user = (await db.execute(stmt)).scalars().first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    
    # Mark email as verified
    user.email_verified = True
    user.email_verification_code = None
    user.email_verification_expires_at = None
    
    await db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification_email(
    request: Request,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resend email verification link."""
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["high"])
    
    if current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new verification code
    import secrets
    current_user.email_verification_code = secrets.token_urlsafe(32)
    current_user.email_verification_expires_at = datetime.utcnow() + timedelta(hours=24)
    
    await db.commit()
    
    # TODO: Send actual email
    logger.info(f"Resent verification email to {current_user.email}")
    
    return {"message": "Verification email sent"}


@router.post("/onboarding")
async def complete_onboarding(
    req: OnboardingRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete user onboarding process."""
    # Update user profile with onboarding data
    if req.name:
        current_user.full_name = req.name
        current_user.name = req.name
    
    # Store preferences
    prefs = dict(current_user.preferences or {})
    if req.timezone:
        prefs["timezone"] = req.timezone
    if req.work_hours_start:
        prefs["work_hours_start"] = req.work_hours_start
    if req.work_hours_end:
        prefs["work_hours_end"] = req.work_hours_end
    if req.notifications_enabled is not None:
        prefs["notifications_enabled"] = req.notifications_enabled
    if req.ai_suggestions_enabled is not None:
        prefs["ai_suggestions_enabled"] = req.ai_suggestions_enabled
    
    current_user.preferences = prefs
    current_user.onboarding_completed = True
    current_user.onboarding_completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "message": "Onboarding completed successfully",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "onboarding_completed": True
        }
    }


