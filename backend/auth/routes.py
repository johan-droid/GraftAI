import asyncio
import logging
import os
from datetime import UTC, datetime
from time import perf_counter
from urllib.parse import quote_plus

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse, Response

from backend.auth.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ACCESS_TOKEN_TYPE,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_TYPE,
    SECRET_KEY,
)
from backend.auth.schemes import get_current_user, get_current_user_id
from backend.core.redis import (
    cache_delete_if_value,
    cache_exists,
    cache_get,
    cache_set,
    cache_set_if_not_exists,
)
from backend.models.tables import UserTable, UserTokenTable
from backend.services import google_auth, microsoft_auth
from backend.services.auth_service import (
    create_access_token,
    create_refresh_token,
    create_user_from_oauth,
    decode_jwt_token,
    get_user_by_email,
    get_user_by_provider_account_id,
    upsert_user_token,
)
from backend.services.oauth_service import (
    build_oauth_state,
    frontend_redirect_token,
    get_client_ip,
    parse_oauth_state,
)
from backend.services.sso import get_provider_config
from backend.services.usage import get_next_quota_reset, get_trial_days_left
from backend.utils.db import get_db
from backend.utils.rate_limit import api_limits, rate_limit

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", os.getenv("FRONTEND_URL", "http://localhost:3000")).rstrip("/")
OAUTH_STATE_EXPIRY_SECONDS = 600
ALLOWED_REDIRECT_PATHS = {"/dashboard", "/settings", "/calendar", "/profile", "/auth-callback"}
logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])
SOCIAL_EXCHANGE_PROVIDER_TIMEOUT_SECONDS = 12
SOCIAL_EXCHANGE_TASK_DISPATCH_TIMEOUT_SECONDS = 1.5
REFRESH_ROTATION_CACHE_TTL_SECONDS = 5 * 60
REFRESH_ROTATION_LOCK_TTL_SECONDS = 10
REFRESH_ROTATION_LOCK_WAIT_ATTEMPTS = 8
REFRESH_ROTATION_LOCK_WAIT_INTERVAL_SECONDS = 0.25

def _mask_token(token: str | None) -> str | None:
    if not token:
        return None
    s = str(token)
    if len(s) <= 8:
        return s[:2] + "..." + s[-2:]
    return s[:4] + "..." + s[-4:]

async def _dispatch_calendar_sync_task(user_id: str) -> None:
    """Dispatch Celery sync task without blocking auth response path."""
    try:
        from backend.tasks.calendar_tasks import sync_all_integrations
        await asyncio.wait_for(asyncio.to_thread(sync_all_integrations.delay, user_id), timeout=SOCIAL_EXCHANGE_TASK_DISPATCH_TIMEOUT_SECONDS)
        logger.info("Triggered full background sync for user %s", user_id)
    except TimeoutError:
        logger.warning("Celery dispatch timed out after %.1fs for user %s; auth exchange succeeded without blocking", SOCIAL_EXCHANGE_TASK_DISPATCH_TIMEOUT_SECONDS, user_id)
    except Exception:
        logger.exception("Failed to dispatch background sync for user %s", user_id)

def _queue_calendar_sync_task(user_id: str) -> None:
    """Queue the Celery sync task without waiting for broker round-trips."""
    try:
        from backend.tasks.calendar_tasks import sync_all_integrations
        sync_all_integrations.delay(user_id)
        logger.info("Queued full background sync for user %s", user_id)
    except Exception:
        logger.exception("Failed to queue background sync for user %s", user_id)
from pydantic import BaseModel


class SocialExchangeRequest(BaseModel):
    provider: str
    id_token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    email: str | None = None
    name: str | None = None
    image: str | None = None
    provider_account_id: str | None = None

class OnboardingRequest(BaseModel):
    name: str | None = None
    timezone: str | None = None
    work_hours_start: str | None = None
    work_hours_end: str | None = None
    notifications_enabled: bool | None = True
    ai_suggestions_enabled: bool | None = True

class RefreshRequest(BaseModel):
    refresh_token: str | None = None

def _get_bearer_token_from_request(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None

@router.post("/social/exchange")
async def social_exchange(req: SocialExchangeRequest, request: Request, response: Response, background_tasks: BackgroundTasks, db: AsyncSession=Depends(get_db)):
    started_at = perf_counter()
    try:
        logger.info("[social_exchange] Incoming request | Host=%s Origin=%s Referer=%s UA=%s", request.headers.get("host"), request.headers.get("origin"), request.headers.get("referer"), request.headers.get("user-agent"))
        logger.info("[social_exchange] Payload preview | provider=%s provider_account_id=%s email=%s access_token=%s id_token=%s", req.provider, getattr(req, "provider_account_id", None), req.email, _mask_token(getattr(req, "access_token", None)), _mask_token(getattr(req, "id_token", None)))
    except Exception:
        logger.exception("[social_exchange] Failed to log request metadata")
    client_ip = get_client_ip(request)
    exchange_bucket_id = f"{client_ip}:{req.provider.lower()}:{(req.provider_account_id or req.email or 'unknown').lower()}"
    await rate_limit(exchange_bucket_id, api_limits["oauth_exchange"])
    normalized_provider = req.provider.lower()
    if normalized_provider not in ["google", "microsoft", "microsoft-entra-id"]:
        raise HTTPException(status_code=400, detail="Invalid provider")
    if not req.access_token:
        raise HTTPException(status_code=400, detail="Access token required for social exchange")
    try:
        if normalized_provider == "google":
            provider_profile = await asyncio.wait_for(google_auth.verify_google_token(req.access_token), timeout=SOCIAL_EXCHANGE_PROVIDER_TIMEOUT_SECONDS)
        else:
            provider_profile = await asyncio.wait_for(microsoft_auth.verify_microsoft_token(req.access_token), timeout=SOCIAL_EXCHANGE_PROVIDER_TIMEOUT_SECONDS)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Provider verification timed out. Please try again.")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    email = (provider_profile.get("email") or req.email or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email required for social login")
    full_name = provider_profile.get("full_name") or req.name or ""
    backend_provider = "microsoft" if normalized_provider == "microsoft-entra-id" else normalized_provider
    provider_account_id = req.provider_account_id or provider_profile.get("provider_account_id") or provider_profile.get("sub") or provider_profile.get("id") or provider_profile.get("oid")
    provider_account_id = str(provider_account_id).strip() if provider_account_id is not None else None
    user = None
    if provider_account_id:
        user = await get_user_by_provider_account_id(db, backend_provider, provider_account_id)
    if not user:
        user = await get_user_by_email(db, email)
    if not user:
        user = await create_user_from_oauth(db, email=email, full_name=full_name, verified=True)
    else:
        if not user.email_verified:
            user.email_verified = True
        if full_name and (not user.full_name):
            user.full_name = full_name
    token_version = getattr(user, "token_version", 0) or 0
    access_token = await create_access_token(user.id, token_version=token_version)
    refresh_token = await create_refresh_token(user.id, token_version=token_version)
    token_payload: dict = {"access_token": req.access_token, "id_token": req.id_token, "metadata_payload": {"provider_account_id": provider_account_id, "provider_email": email}}
    if req.refresh_token:
        token_payload["refresh_token"] = req.refresh_token
    user.last_login_at = datetime.now(UTC)
    await upsert_user_token(db, user, backend_provider, token_payload)
    await db.commit()
    background_tasks.add_task(_queue_calendar_sync_task, user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    result = {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "username": user.username, "tier": user.tier, "subscription_status": user.subscription_status, "created_at": user.created_at.isoformat() if user.created_at else None, "daily_ai_count": user.daily_ai_count, "daily_ai_limit": user.daily_ai_limit, "total_ai_tokens": user.total_ai_tokens, "total_api_calls": user.total_api_calls, "total_scheduling_count": user.total_scheduling_count}}
    logger.info("[social_exchange] Completed in %.2fms | provider=%s user_id=%s email=%s", (perf_counter() - started_at) * 1000, normalized_provider, user.id, email)
    return result

def _set_auth_cookies(response: Response | None, access_token: str, refresh_token: str):
    if response is None:
        return
    is_production = os.getenv("ENV", "development") == "production"
    is_render = os.getenv("RENDER") is not None
    secure = is_production or is_render
    samesite = "none" if secure else "lax"
    cookie_kwargs = {"httponly": True, "samesite": samesite, "path": "/", "max_age": ACCESS_TOKEN_EXPIRE_MINUTES * 60}
    if secure:
        cookie_kwargs["secure"] = True
    response.set_cookie("graftai_access_token", access_token, **cookie_kwargs)
    refresh_cookie_kwargs = cookie_kwargs.copy()
    refresh_cookie_kwargs["max_age"] = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie("graftai_refresh_token", refresh_token, **refresh_cookie_kwargs)

def _is_production_env() -> bool:
    return os.getenv("ENV", "development").strip().lower() in {"production", "prod", "live"}

def _build_refresh_payload(access_token: str, refresh_token: str, token_type: str="bearer") -> dict:
    return {"message": "Token refreshed successfully", "access_token": access_token, "token_type": token_type, "refresh_token": refresh_token}

def _build_token_response(access_token: str, refresh_token: str):
    return {"message": "Login successful", "access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.get("/integrations/status")
async def integration_status(user_id: str=Depends(get_current_user_id), db: AsyncSession=Depends(get_db)):
    active_stmt = select(UserTokenTable.provider).where(UserTokenTable.user_id == user_id, UserTokenTable.is_active)
    inactive_stmt = select(UserTokenTable.provider).where(UserTokenTable.user_id == user_id, not UserTokenTable.is_active)
    active_providers = (await db.execute(active_stmt)).scalars().all()
    inactive_providers = (await db.execute(inactive_stmt)).scalars().all()
    return {"connections": {"active": list(active_providers), "inactive": sorted(set(inactive_providers) - set(active_providers))}}

@router.get("/check")
async def check(request: Request, db: AsyncSession=Depends(get_db)):
    raw_token = _get_bearer_token_from_request(request) or request.cookies.get("graftai_access_token")
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = await decode_jwt_token(raw_token, expected_type=ACCESS_TOKEN_TYPE)
    except HTTPException:
        raise
    stmt = select(UserTable).where(UserTable.id == payload["sub"])
    user = (await db.execute(stmt)).scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user not found", headers={"WWW-Authenticate": "Bearer"})
    token_version = int(payload.get("version", 0))
    if getattr(user, "token_version", 0) > token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token has been revoked. Please log in again.", headers={"WWW-Authenticate": "Bearer"})
    return {"authenticated": True, "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "username": user.username, "daily_ai_count": user.daily_ai_count, "daily_ai_limit": user.daily_ai_limit, "total_ai_tokens": user.total_ai_tokens, "total_api_calls": user.total_api_calls, "total_scheduling_count": user.total_scheduling_count, "trial_days_left": get_trial_days_left(user.created_at), "trial_active": user.trial_active, "quota_reset_at": get_next_quota_reset().isoformat()}}

@router.post("/refresh", response_model=None)
async def refresh(request: Request, response: Response, refresh_request: RefreshRequest | None=None, db: AsyncSession=Depends(get_db)):
    token_value = (refresh_request.refresh_token if refresh_request else None) or request.cookies.get("graftai_refresh_token")
    if not token_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required", headers={"WWW-Authenticate": "Bearer"})
    rotation_key = f"refresh_rotation:{token_value}"
    blacklist_key = f"blacklist:{token_value}"
    lock_key = f"refresh_lock:{token_value}"
    lock_owner = f"pid:{os.getpid()}:{id(request)}"
    lock_acquired = False

    def _rotation_payload_from_cache(cached_rotation: object) -> dict | None:
        if not isinstance(cached_rotation, dict):
            return None
        access_token = cached_rotation.get("access_token")
        refresh_token = cached_rotation.get("refresh_token")
        token_type = cached_rotation.get("token_type", "bearer")
        if isinstance(access_token, str) and isinstance(refresh_token, str):
            return _build_refresh_payload(access_token, refresh_token, str(token_type))
        return None
    try:
        cached_rotation = await cache_get(rotation_key)
        replay_payload = _rotation_payload_from_cache(cached_rotation)
        if replay_payload:
            _set_auth_cookies(response, replay_payload["access_token"], replay_payload["refresh_token"])
            return replay_payload
    except Exception as exc:
        if _is_production_env():
            logger.exception("Refresh replay cache unavailable in production: %s", exc)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service temporarily unavailable")
        logger.warning("Refresh replay cache unavailable; continuing without replay cache in dev fallback: %s", exc)
    try:
        lock_acquired = await cache_set_if_not_exists(lock_key, lock_owner, expire=REFRESH_ROTATION_LOCK_TTL_SECONDS)
    except Exception as exc:
        if _is_production_env():
            logger.exception("Refresh lock service unavailable in production: %s", exc)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service temporarily unavailable")
        logger.warning("Refresh lock unavailable; continuing without lock in dev fallback: %s", exc)
        lock_acquired = True
    if not lock_acquired:
        for _ in range(REFRESH_ROTATION_LOCK_WAIT_ATTEMPTS):
            await asyncio.sleep(REFRESH_ROTATION_LOCK_WAIT_INTERVAL_SECONDS)
            cached_rotation = await cache_get(rotation_key)
            replay_payload = _rotation_payload_from_cache(cached_rotation)
            if replay_payload:
                _set_auth_cookies(response, replay_payload["access_token"], replay_payload["refresh_token"])
                return replay_payload
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Refresh already in progress. Retry shortly.")
    try:
        cached_rotation = await cache_get(rotation_key)
        replay_payload = _rotation_payload_from_cache(cached_rotation)
        if replay_payload:
            _set_auth_cookies(response, replay_payload["access_token"], replay_payload["refresh_token"])
            return replay_payload
        try:
            is_blacklisted = await cache_exists(blacklist_key)
        except Exception as exc:
            if _is_production_env():
                logger.exception("Refresh blacklist service unavailable in production: %s", exc)
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service temporarily unavailable")
            logger.warning("Cache/Redis error checking refresh blacklist; proceeding without blacklist (dev fallback): %s", exc)
            is_blacklisted = False
        if is_blacklisted:
            cached_rotation = await cache_get(rotation_key)
            replay_payload = _rotation_payload_from_cache(cached_rotation)
            if replay_payload:
                _set_auth_cookies(response, replay_payload["access_token"], replay_payload["refresh_token"])
                return replay_payload
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has already been used (blacklisted)", headers={"WWW-Authenticate": "Bearer"})
        decoded_payload = await decode_jwt_token(token_value, expected_type=REFRESH_TOKEN_TYPE)
        stmt = select(UserTable).where(UserTable.id == decoded_payload["sub"])
        user = (await db.execute(stmt)).scalars().first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token user not found", headers={"WWW-Authenticate": "Bearer"})
        token_version = int(decoded_payload.get("version", 0))
        if getattr(user, "token_version", 0) > token_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked. Please log in again.", headers={"WWW-Authenticate": "Bearer"})
        token_version = getattr(user, "token_version", 0) or 0
        new_access_token = await create_access_token(user.id, token_version=token_version)
        new_refresh_token = await create_refresh_token(user.id, token_version=token_version)
        refresh_payload = _build_refresh_payload(new_access_token, new_refresh_token)
        try:
            await cache_set(rotation_key, {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}, expire=REFRESH_ROTATION_CACHE_TTL_SECONDS)
        except Exception as exc:
            if _is_production_env():
                logger.exception("Cache/Redis error setting refresh rotation cache in production: %s", exc)
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service temporarily unavailable")
            logger.warning("Cache/Redis error setting refresh rotation cache; continuing without replay cache (dev fallback): %s", exc)
        try:
            await cache_set(blacklist_key, "used", expire=REFRESH_TOKEN_EXPIRE_DAYS * 86400)
        except Exception as exc:
            if _is_production_env():
                logger.exception("Cache/Redis error setting refresh blacklist in production: %s", exc)
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service temporarily unavailable")
            logger.warning("Cache/Redis error setting refresh blacklist for token; continuing without blacklist (dev fallback): %s", exc)
        _set_auth_cookies(response, new_access_token, new_refresh_token)
        return refresh_payload
    finally:
        if lock_acquired:
            try:
                await cache_delete_if_value(lock_key, lock_owner)
            except Exception as exc:
                logger.warning("Failed to release refresh lock: %s", exc)

@router.post("/logout", response_model=None)
async def logout(response: Response):
    response.delete_cookie("graftai_access_token", path="/")
    response.delete_cookie("graftai_refresh_token", path="/")
    return {"message": "Logged out"}

@router.get("/google/login")
async def google_login(request: Request, redirect_to: str | None=None, redirect_uri: str | None=None, force_consent: bool=False, frontend_url: str | None=None):
    try:
        bearer_token = _get_bearer_token_from_request(request)
        user_id = None
        if bearer_token:
            try:
                payload = await decode_jwt_token(bearer_token, expected_type=ACCESS_TOKEN_TYPE)
                user_id = payload.get("sub")
            except Exception:
                pass
        redirect_to = redirect_to or redirect_uri or "/dashboard"
        state = build_oauth_state(user_id, redirect_to, provider="google", frontend_url=frontend_url)
        auth_url = await google_auth.get_google_auth_url(state, prompt=("consent" if force_consent else None))
        return RedirectResponse(url=auth_url, status_code=303)
    except ValueError as e:
        logger.exception("Google OAuth Configuration Error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: str | None=None, db: AsyncSession=Depends(get_db)):
    try:
        logger.info("[google_callback] Incoming callback | Host=%s Origin=%s Referer=%s UA=%s Query=%s", request.headers.get("host"), request.headers.get("origin"), request.headers.get("referer"), request.headers.get("user-agent"), dict(request.query_params))
    except Exception:
        logger.exception("[google_callback] Failed to log callback metadata")
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
            logger.warning("OAuth state contained user_id (ignoring for security): %s...", user_id[:8])
            user_id = None
        result = await db.execute(select(UserTable).where(UserTable.email == email))
        user = result.scalars().first()
        if not user:
            user = await create_user_from_oauth(db, email=email, full_name=data.get("full_name", email.split("@")[0]), verified=True, email_verification_code=None, email_verification_expires_at=None)
            logger.info("New user created via Google OAuth: %s", email)
        elif not user.email_verified:
            user.email_verified = True
            user.email_verification_code = None
            user.email_verification_expires_at = None
        token_info = data.get("token", {})
        access_token = token_info.get("access_token")
        if not access_token:
            logger.error("Google OAuth returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")
        user.last_login_at = datetime.now(UTC)
        await upsert_user_token(db, user, "google", token_info)
        await db.commit()
        logger.info("Google OAuth successful for user: %s", email)
        token_version = getattr(user, "token_version", 0) or 0
        backend_access_token = await create_access_token(user.id, token_version=token_version)
        backend_refresh_token = await create_refresh_token(user.id, token_version=token_version)
        return RedirectResponse(url=frontend_redirect_token(backend_access_token, redirect_to, frontend_url, backend_refresh_token), status_code=303)
    except ValueError as e:
        logger.exception("Google OAuth Configuration Error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Google Callback Error: %s", e, exc_info=True)
        error_msg = str(e).lower()
        if "invalid_grant" in error_msg or "expired" in error_msg or "mismatch" in error_msg:
            return RedirectResponse(url=f"{FRONTEND_BASE_URL}/login?error=Session expired. Please log in again.", status_code=303)
        raise HTTPException(status_code=500, detail="Authentication failed")

@router.get("/sso/callback")
async def sso_callback(request: Request, code: str, state: str | None=None, fetch: bool | None=None, db: AsyncSession=Depends(get_db)):
    """
    Unified SSO callback endpoint that routes to the correct provider.

    When fetch=true, returns JSON with token for frontend to handle.
    Otherwise, redirects to frontend with token in URL.
    """
    try:
        logger.info("[sso_callback] Incoming callback | Host=%s Origin=%s Referer=%s UA=%s Query=%s", request.headers.get("host"), request.headers.get("origin"), request.headers.get("referer"), request.headers.get("user-agent"), dict(request.query_params))
    except Exception:
        logger.exception("[sso_callback] Failed to log callback metadata")
    client_ip = get_client_ip(request)
    await rate_limit(client_ip, api_limits["oauth_callback"])
    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state parameter")
    try:
        user_id, redirect_to, parsed_provider, frontend_url = parse_oauth_state(state)
        if parsed_provider == "google":
            data = await google_auth.fetch_google_tokens(code)
            provider = "google"
        elif parsed_provider == "microsoft":
            data = await microsoft_auth.fetch_microsoft_tokens(code)
            provider = "microsoft"
        else:
            logger.warning("OAuth state missing provider, attempting detection")
            try:
                data = await google_auth.fetch_google_tokens(code)
                provider = "google"
            except Exception:
                try:
                    data = await microsoft_auth.fetch_microsoft_tokens(code)
                    provider = "microsoft"
                except Exception:
                    raise HTTPException(status_code=400, detail="Unable to determine OAuth provider from state. Please try again.")
        email = data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Failed to retrieve email from OAuth provider")
        email = email.lower().strip()
        if user_id:
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = result.scalars().first()
        else:
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            user = result.scalars().first()
        if not user:
            user = await create_user_from_oauth(db, email=email, full_name=data.get("full_name", email.split("@")[0]), verified=True)
            logger.info("New user created via %s OAuth: %s", provider, email)
        elif not user.email_verified:
            user.email_verified = True
        token_info = data.get("token", {})
        access_token = token_info.get("access_token")
        if not access_token:
            logger.error("%s OAuth returned no access token", provider)
            raise HTTPException(status_code=400, detail="Failed to retrieve access token from OAuth provider")
        user.last_login_at = datetime.now(UTC)
        await upsert_user_token(db, user, provider, token_info)
        await db.commit()
        token_version = getattr(user, "token_version", 0) or 0
        access_token = await create_access_token(user.id, token_version=token_version)
        refresh_token = await create_refresh_token(user.id, token_version=token_version)
        logger.info("%s OAuth successful for user: %s", provider, email)
        if fetch:
            return {"token": {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}, "redirect_to": redirect_to, "user": {"id": user.id, "email": user.email, "full_name": user.full_name}}
        return RedirectResponse(url=frontend_redirect_token(access_token, redirect_to, frontend_url, refresh_token), status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("SSO callback error: %s", e, exc_info=True)
        error_msg = str(e).lower()
        if "invalid_grant" in error_msg or "expired" in error_msg or "mismatch" in error_msg:
            return RedirectResponse(url=f"{FRONTEND_BASE_URL}/login?error=Session expired. Please log in again.", status_code=303)
        raise HTTPException(status_code=500, detail="Authentication failed")

@router.get("/sso/start")
async def sso_start(provider: str, redirect_to: str | None=None, redirect_uri: str | None=None):
    provider = provider.lower()
    if get_provider_config(provider) is None:
        raise HTTPException(status_code=400, detail="Unsupported SSO provider")
    final_redirect = redirect_to or redirect_uri or "/dashboard"
    

# --- JWKS and key rotation helpers (simple, low-risk cutover) ---
from backend.core.secret_manager import get_secret_manager, secret_manager
from backend.core.secret_manager import SecretMetadata, SecretType
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64
from uuid import uuid4


def _base64url_uint(n: int) -> str:
    """Encode an integer to base64url without padding (RFC7517)"""
    by = n.to_bytes((n.bit_length() + 7) // 8, "big") or b"\x00"
    return base64.urlsafe_b64encode(by).rstrip(b"=").decode("ascii")


def _public_jwk_from_private_pem(pem_bytes: bytes, kid: str) -> dict:
    priv = serialization.load_pem_private_key(pem_bytes, password=None)
    pub = priv.public_key()
    numbers = pub.public_numbers()
    jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": _base64url_uint(numbers.n),
        "e": _base64url_uint(numbers.e),
    }
    return jwk


@router.get("/jwks")
async def jwks():
    """Return JWKS (public keys). Keys are stored in the secret manager under auth/jwks/{kid}.
    If no secret manager is configured, returns an empty set.
    """
    keys = []
    try:
        mgr = get_secret_manager()
        raw = await mgr.get_secret("auth/jwks/active_kids")
        if not raw:
            return {"keys": []}
        try:
            import json

            kids = json.loads(raw)
        except Exception:
            kids = []
        for kid in kids:
            pem = await mgr.get_secret(f"auth/jwks/{kid}")
            if not pem:
                continue
            try:
                jwk = _public_jwk_from_private_pem(pem.encode("utf-8"), kid)
                keys.append(jwk)
            except Exception:
                continue
    except Exception:
        # If secret manager unavailable, surface no keys rather than failing calls
        return {"keys": []}
    return {"keys": keys}


@router.post("/jwks/rotate")
async def rotate_jwks(request: Request):
    """Rotate JWKS: generate an RSA keypair, store private key in secret manager, add kid to active list.
    Protected by a simple admin header 'X-ADMIN-SECRET' that must equal SECRET_KEY.
    This is intentionally small and synchronous-friendly for fast cutover; production should use a proper key management system.
    """
    from backend.auth.config import SECRET_KEY as AUTH_SECRET
    admin_api_key = os.getenv("ADMIN_API_KEY")

    def _is_admin_request(req: Request) -> bool:
        # 1) Check header X-ADMIN-SECRET equals app SECRET_KEY (legacy)
        hdr = req.headers.get("X-ADMIN-SECRET") or req.headers.get("Authorization")
        if hdr and (hdr == AUTH_SECRET or hdr == f"Bearer {AUTH_SECRET}"):
            return True
        # 2) Check admin API key header
        if admin_api_key:
            h = req.headers.get("X-ADMIN-API-KEY")
            if h and h == admin_api_key:
                return True
        # 3) Check internal allowed IPs (comma-separated env var)
        allowed = os.getenv("INTERNAL_ALLOWED_IPS", "").split(",")
        client_host = None
        try:
            client_host = req.client.host
        except Exception:
            client_host = None
        if client_host and any(client_host.strip() == a.strip() for a in allowed if a.strip()):
            return True
        return False

    if not _is_admin_request(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    # generate RSA key
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    kid = uuid4().hex
    # store in secret manager
    try:
        mgr = get_secret_manager()
        meta = SecretMetadata(name=f"auth/jwks/{kid}", type=SecretType.JWT_SECRET, provider=None, created_at=datetime.now(UTC), updated_at=datetime.now(UTC), version=1, rotation_enabled=False, rotation_interval_days=None, last_rotated=None)
        await mgr.set_secret(f"auth/jwks/{kid}", private_pem.decode("utf-8"), meta)
        # update active_kids list
        raw = await mgr.get_secret("auth/jwks/active_kids") or "[]"
        try:
            import json

            kids = json.loads(raw)
        except Exception:
            kids = []
        kids.append(kid)
        await mgr.set_secret("auth/jwks/active_kids", json.dumps(kids), meta)
    except Exception:
        logger.exception("Failed to rotate JWKS")
        raise HTTPException(status_code=500, detail="Rotation failed")
    return {"kid": kid}


class DeprecateKidRequest(BaseModel):
    kid: str
    delete_private: bool = False


@router.post("/jwks/deprecate")
async def deprecate_jwk(req: DeprecateKidRequest, request: Request):
    # Admin-protected: same rules as rotate
    from backend.auth.config import SECRET_KEY as AUTH_SECRET
    admin_api_key = os.getenv("ADMIN_API_KEY")

    def _is_admin_request(req_: Request) -> bool:
        hdr = req_.headers.get("X-ADMIN-SECRET") or req_.headers.get("Authorization")
        if hdr and (hdr == AUTH_SECRET or hdr == f"Bearer {AUTH_SECRET}"):
            return True
        if admin_api_key:
            h = req_.headers.get("X-ADMIN-API-KEY")
            if h and h == admin_api_key:
                return True
        allowed = os.getenv("INTERNAL_ALLOWED_IPS", "").split(",")
        client_host = None
        try:
            client_host = req_.client.host
        except Exception:
            client_host = None
        if client_host and any(client_host.strip() == a.strip() for a in allowed if a.strip()):
            return True
        return False

    if not _is_admin_request(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        mgr = get_secret_manager()
        raw = await mgr.get_secret("auth/jwks/active_kids") or "[]"
        import json

        try:
            kids = json.loads(raw)
        except Exception:
            kids = []
        if req.kid not in kids:
            raise HTTPException(status_code=404, detail="kid not found")
        kids = [k for k in kids if k != req.kid]
        # write back active list
        await mgr.set_secret("auth/jwks/active_kids", json.dumps(kids), SecretMetadata(name="auth/jwks/active_kids", type=SecretType.JWT_SECRET, provider=None, created_at=datetime.now(UTC), updated_at=datetime.now(UTC), version=1, rotation_enabled=False, rotation_interval_days=None, last_rotated=None))
        if req.delete_private:
            # delete private key entry
            try:
                await mgr.delete_secret(f"auth/jwks/{req.kid}")
            except Exception:
                logger.exception("Failed to delete private key for kid %s", req.kid)
        return {"status": "deprecated", "kid": req.kid}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to deprecate kid %s", req.kid)
        raise HTTPException(status_code=500, detail="Failed to deprecate kid")
    query_parts = []
    if final_redirect:
        query_parts.append(f"redirect_to={quote_plus(final_redirect)}")
    target_url = f"/api/v1/auth/{provider}/login"
    if query_parts:
        target_url = f"{target_url}?{'&'.join(query_parts)}"
    return RedirectResponse(url=target_url, status_code=303)

@router.get("/microsoft/login")
async def microsoft_login(request: Request, redirect_to: str | None=None, redirect_uri: str | None=None, frontend_url: str | None=None):
    try:
        bearer_token = _get_bearer_token_from_request(request)
        user_id = None
        if bearer_token:
                try:
                    payload = await decode_jwt_token(bearer_token, expected_type=ACCESS_TOKEN_TYPE)
                    user_id = payload.get("sub")
                except Exception:
                    pass
        redirect_to = redirect_to or redirect_uri or "/dashboard"
        state = build_oauth_state(user_id, redirect_to, provider="microsoft", frontend_url=frontend_url)
        auth_url = await microsoft_auth.get_microsoft_auth_url(state)
        return RedirectResponse(url=auth_url, status_code=303)
    except ValueError as e:
        logger.exception("Microsoft OAuth Configuration Error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/microsoft/callback")
async def microsoft_callback(request: Request, code: str, state: str | None=None, db: AsyncSession=Depends(get_db)):
    try:
        logger.info("[microsoft_callback] Incoming callback | Host=%s Origin=%s Referer=%s UA=%s Query=%s", request.headers.get("host"), request.headers.get("origin"), request.headers.get("referer"), request.headers.get("user-agent"), dict(request.query_params))
    except Exception:
        logger.exception("[microsoft_callback] Failed to log callback metadata")
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
            user = await create_user_from_oauth(db, email=email, full_name=data.get("full_name", email.split("@")[0]), verified=True, email_verification_code=None, email_verification_expires_at=None)
            logger.info("New user created via Microsoft OAuth: %s", email)
        elif not user.email_verified:
            user.email_verified = True
            user.email_verification_code = None
            user.email_verification_expires_at = None
        token_info = data.get("token", {})
        if not token_info.get("access_token"):
            logger.error("Microsoft OAuth returned no access token")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")
        user.last_login_at = datetime.now(UTC)
        await upsert_user_token(db, user, "microsoft", token_info)
        await db.commit()
        logger.info("Microsoft OAuth successful for user: %s", email)
        token_version = getattr(user, "token_version", 0) or 0
        backend_access_token = await create_access_token(user.id, token_version=token_version)
        backend_refresh_token = await create_refresh_token(user.id, token_version=token_version)
        return RedirectResponse(url=frontend_redirect_token(backend_access_token, redirect_to, frontend_url, backend_refresh_token), status_code=303)
    except ValueError as e:
        logger.exception("Microsoft OAuth Configuration Error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Microsoft Callback Error: %s", e, exc_info=True)
        await db.rollback()
        error_msg = str(e).lower()
        if "invalid_grant" in error_msg or "expired" in error_msg or "mismatch" in error_msg:
            return RedirectResponse(url=f"{FRONTEND_BASE_URL}/login?error=Session expired. Please log in again.", status_code=303)
        if "aadsts" in error_msg or "unauthorized_client" in error_msg:
            raise HTTPException(status_code=400, detail="Microsoft OAuth configuration error. Please contact support.")
        raise HTTPException(status_code=500, detail="Authentication failed")

@router.post("/onboarding")
async def complete_onboarding(req: OnboardingRequest, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """Complete user onboarding process."""
    if req.name:
        current_user.full_name = req.name
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
    current_user.onboarding_completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(current_user)
    return {"message": "Onboarding completed successfully", "user": {"id": current_user.id, "email": current_user.email, "name": current_user.full_name, "onboarding_completed": True}}
