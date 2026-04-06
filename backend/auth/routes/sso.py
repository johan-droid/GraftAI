import os
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.utils.db import get_db
from backend.models.tables import UserTable
from backend.models.user_token import UserTokenTable
from backend.services import sso
from backend.auth import logic

router = APIRouter(tags=["auth-sso"])
logger = logging.getLogger(__name__)

# SameSite=None + Secure=True for cross-domain SSO callback handoff (Render -> SPA)
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN") # e.g. .graftai.tech
SECURE_COOKIES = os.getenv("RENDER_EXTERNAL_URL", "").startswith("https")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@router.get("/sso/start")
async def sso_start(provider: str, redirect_to: str = "/dashboard"):
    """
    Initializes OAuth2 flow and returns a redirect to the provider.
    """
    try:
        auth_url, state = await sso.get_authorization_url(provider, redirect_to)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[SSO]: Failed to start {provider} flow: {e}")
        raise HTTPException(status_code=500, detail="SSO initialization failed")

@router.get("/sso/callback")
async def sso_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Handles OAuth2 callback, creates/updates user, persists tokens, and issues session.
    Uses Token Bridge for frontend handoff if cross-domain.
    """
    try:
        # Complete OAuth flow (exchanges code for tokens + gets user profile)
        sso_data = await sso.complete_oauth2_flow(request, code, state)
        if not sso_data:
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=sso_failed")

        email = sso_data.get("email")
        if not email:
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=email_missing")

        # 1. UPSERT User
        stmt = select(UserTable).where(UserTable.email == email)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            user = UserTable(
                email=email,
                full_name=sso_data.get("full_name", email.split("@")[0]),
                profile_image=sso_data.get("picture"),
                is_active=True,
                auth_provider=sso_data.get("provider", "google")
            )
            db.add(user)
            await db.flush() # Get ID
            logger.info(f"[AUTH]: New SSO user created: {email}")
            
            # 1.5 Send Welcome Email & Trigger Initial Sync
            try:
                from backend.services.bg_tasks import enqueue_welcome_email, enqueue_calendar_sync
                await enqueue_welcome_email(
                    user_email=email,
                    full_name=user.full_name
                )
                await enqueue_calendar_sync(user_id=str(user.id))
            except Exception as e:
                logger.warning(f"Failed to enqueue onboarding tasks for {email}: {e}")
        else:
            # Update profile info if changed
            user.full_name = sso_data.get("full_name", user.full_name)
            user.profile_image = sso_data.get("picture", user.profile_image)
            user.auth_provider = sso_data.get("provider", user.auth_provider)
            
            # Also trigger a re-sync for existing users to ensure data is fresh
            try:
                from backend.services.bg_tasks import enqueue_calendar_sync
                await enqueue_calendar_sync(user_id=str(user.id))
            except Exception as e:
                logger.info(f"Background sync trigger skipped for {email}: {e}")

        # 2. Persist OAuth Tokens for backend sync (Google Calendar, etc.)
        try:
            provider = sso_data.get("provider", "google").lower()
            token_info = sso_data.get("token", {})
            
            # Check for existing token
            stmt_tk = select(UserTokenTable).where(
                and_(UserTokenTable.user_id == user.id, UserTokenTable.provider == provider)
            )
            res_tk = await db.execute(stmt_tk)
            user_token_rec = res_tk.scalars().first()

            if user_token_rec:
                user_token_rec.access_token = token_info.get("access_token")
                user_token_rec.refresh_token = token_info.get("refresh_token") or user_token_rec.refresh_token
                user_token_rec.expires_at = datetime.fromtimestamp(token_info.get("expires_at")) if token_info.get("expires_at") else None
                user_token_rec.scopes = json.dumps(token_info.get("scope", "").split(" ")) if token_info.get("scope") else user_token_rec.scopes
                user_token_rec.updated_at = datetime.now(timezone.utc)
            else:
                user_token_rec = UserTokenTable(
                    user_id=user.id,
                    provider=provider,
                    access_token=token_info.get("access_token"),
                    refresh_token=token_info.get("refresh_token"),
                    expires_at=datetime.fromtimestamp(token_info.get("expires_at")) if token_info.get("expires_at") else None,
                    scopes=json.dumps(token_info.get("scope", "").split(" ")) if token_info.get("scope") else None,
                )
                db.add(user_token_rec)
        except Exception as exc:
            logger.error(f"[AUTH]: Critical failure persisting SSO tokens for {email}: {exc}")
            # Non-fatal to login, but means sync won't work

        await db.commit()

        # 3. Create Session
        access_token = logic.create_access_token(data={"sub": str(user.id)})
        refresh_token = logic.create_refresh_token(data={"sub": str(user.id)})

        # 4. Redirect with Handoff
        target_path = sso_data.get("redirect_to", sso_data.get("original_redirect", "/dashboard"))
        
        # If Token Bridge is enabled, we use a middle-man redirect to ensure token transfer
        bridge_url = logic.get_token_bridge_url(access_token, refresh_token, target_path)
        response = RedirectResponse(url=bridge_url)
        
        # Also sets fallback cookies for the backend domain itself
        logic.set_auth_cookies(response, access_token, refresh_token)
        return response

    except Exception as e:
        logger.error(f"[AUTH]: SSO Callback unhandled error: {e}")
        return RedirectResponse(url="/auth/login?error=server_error")
