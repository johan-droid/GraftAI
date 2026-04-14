import os
import logging
from urllib.parse import quote_plus
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from starlette.responses import Response, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt

from backend.services.auth_service import (
    create_access_token,
    create_refresh_token,
    create_user_from_oauth,
    decode_jwt_token,
    get_user_by_email,
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
    # Identity tokens from the social provider
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    # Refresh token from the social provider (for calendar re-auth)
    refresh_token: Optional[str] = None
    # User profile data forwarded from NextAuth
    email: Optional[str] = None
    name: Optional[str] = None
    image: Optional[str] = None
    provider_account_id: Optional[str] = None


class OnboardingRequest(BaseModel):
    name: Optional[str] = None
    timezone: Optional[str] = None
    work_hours_start: Optional[str] = None
    work_hours_end: Optional[str] = None
    notifications_enabled: Optional[bool] = True
    ai_suggestions_enabled: Optional[bool] = True

@router.post("/social/exchange")
async def social_exchange(req: SocialExchangeRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["login"])

    normalized_provider = req.provider.lower()
    if normalized_provider not in ["google", "microsoft", "microsoft-entra-id"]:
        raise HTTPException(status_code=400, detail="Invalid provider")

    if not req.access_token:
        raise HTTPException(status_code=400, detail="Access token required for social exchange")

    # ── Verify the provider token and extract the user profile ───────────────
    try:
        if normalized_provider == "google":
            provider_profile = await google_auth.verify_google_token(req.access_token)
        else:
            provider_profile = await microsoft_auth.verify_microsoft_token(req.access_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    # Prefer verified email from socialised profile; fall back to what NextAuth sent
    email = (provider_profile.get("email") or req.email or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email required for social login")

    # Prefer provider display name, fall back to what NextAuth forwarded
    full_name = provider_profile.get("full_name") or req.name or ""

    # ── Upsert the GraftAI user record ────────────────────────────────────────
    user = await get_user_by_email(db, email)
    if not user:
        user = await create_user_from_oauth(
            db,
            email=email,
            full_name=full_name,
            verified=True,
        )
    else:
        # Keep profile data fresh on every login
        if not user.email_verified:
            user.email_verified = True
        if full_name and not user.full_name:
            user.full_name = full_name

    # ── Issue GraftAI JWTs ────────────────────────────────────────────────────
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # ── Persist the provider OAuth token for calendar / graph integration ─────
    # Use the canonical backend provider name regardless of what NextAuth sent
    backend_provider = "microsoft" if normalized_provider == "microsoft-entra-id" else normalized_provider
    token_payload: dict = {
        "access_token": req.access_token,
        "id_token": req.id_token,
    }
    # If NextAuth forwarded a provider refresh token, store it for JIT rotation
    if req.refresh_token:
        token_payload["refresh_token"] = req.refresh_token

    await upsert_user_token(db, user, backend_provider, token_payload)
    await db.commit()

    # ── Issue legacy cookies for backward compatibility ──────────────────
    _set_auth_cookies(response, access_token, refresh_token)

    # ── Return tokens + user profile (avoids a second /users/me round-trip) ──
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "username": user.username,
            "tier": user.tier,
            "subscription_status": user.subscription_status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


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
            user = await create_user_from_oauth(
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
            user = await create_user_from_oauth(
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
            user = await create_user_from_oauth(
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


