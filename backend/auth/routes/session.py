import os
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.api.deps import get_db
from backend.models.tables import UserTable, UserTier
from backend.models.user_token import UserTokenTable
from backend.auth.schemes import get_current_user, get_current_user_id
from backend.services.usage import get_tier_usage_limits, get_next_quota_reset, get_trial_days_left
from backend.services import access_control
from backend.auth.logic import (
    get_redis_client,
    create_jwt_token,
    attach_jwt_cookies,
    is_secure_request,
    ALGORITHM,
    SECRET_KEY
)
import jwt
from jwt import PyJWTError as JWTError
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TimezoneSyncRequest(BaseModel):
    timezone: str

class ConsentSyncRequest(BaseModel):
    consent_analytics: Optional[bool] = None
    consent_notifications: Optional[bool] = None
    consent_ai_training: Optional[bool] = None

@router.post("/sync-consent")
async def sync_consent(
    data: ConsentSyncRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
    logger.info(f"Updated consents for user {user_id}")
    return {"status": "success"}

@router.post("/sync-timezone")
async def sync_timezone(
    data: TimezoneSyncRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.get("sub")
    async with db.begin():
        result = await db.execute(select(UserTable).where(UserTable.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.timezone = data.timezone
    logger.info(f"Updated timezone to {data.timezone} for user {user_id}")
    return {"status": "success", "timezone": data.timezone}

@router.post("/sync")
async def sync_session(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.get("sub")
    email = current_user.get("email")
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    if not user:
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

@router.get("/check")
async def check_auth(
    request: Request, 
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.get("sub")
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    user_data = current_user.copy()
    if user:
        user_data["name"] = user.full_name
        user_data["full_name"] = user.full_name
        user_data["timezone"] = user.timezone
        user_data["tier"] = user.tier
        user_data["subscription_status"] = user.subscription_status
        user_data["daily_ai_count"] = user.daily_ai_count
        user_data["daily_sync_count"] = user.daily_sync_count
        tier = UserTier(user.tier) if user.tier else UserTier.FREE
        tier_limits = get_tier_usage_limits(tier)
        user_data["daily_ai_limit"] = tier_limits["ai_messages"]
        user_data["daily_sync_limit"] = tier_limits["calendar_syncs"]
        user_data["ai_remaining"] = max(0, tier_limits["ai_messages"] - user.daily_ai_count)
        user_data["sync_remaining"] = max(0, tier_limits["calendar_syncs"] - user.daily_sync_count)
        user_data["quota_reset_at"] = get_next_quota_reset().isoformat()
        trial_days_left = get_trial_days_left(user.created_at)
        user_data["trial_days_left"] = trial_days_left
        if user.created_at:
            created_at = user.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            user_data["trial_expires_at"] = (
                (created_at + timedelta(days=int(os.getenv("FREE_TRIAL_DAYS", "7"))))
                .isoformat()
            )
        else:
            user_data["trial_expires_at"] = None
        user_data["trial_active"] = trial_days_left > 0 and user.subscription_status != "active"
        user_data["consent_analytics"] = user.consent_analytics
        user_data["consent_notifications"] = user.consent_notifications
        user_data["consent_ai_training"] = user.consent_ai_training
    
    env_name = (os.getenv("ENV") or os.getenv("NODE_ENV") or "production").lower()
    is_prod = env_name == "production"
    is_https = is_secure_request(request) or os.getenv("PROTOCOL") == "https" or is_prod
    origin = request.headers.get("origin", "")
    is_localhost = "localhost" in origin or "127.0.0.1" in origin
    if is_https and not (is_localhost and not is_prod):
        same_site_value = "none"
        secure_value = True
    else:
        same_site_value = "lax"
        secure_value = False
    xsrf_token = request.cookies.get("xsrf-token") or secrets.token_urlsafe(32)
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
        key="xsrf-token", value=xsrf_token, httponly=False,
        secure=secure_value, samesite=same_site_value, max_age=86400, path="/"
    )
    response.headers["x-xsrf-token"] = xsrf_token
    return response

@router.get("/integrations/status")
async def get_integration_status(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = str(current_user.get("sub"))
    providers = ["google", "microsoft"]
    stmt = select(
        UserTokenTable.provider, UserTokenTable.is_active, UserTokenTable.updated_at
    ).where(UserTokenTable.user_id == user_id, UserTokenTable.provider.in_(providers))
    result = await db.execute(stmt)
    status_map = {p: False for p in providers}
    last_connected_at = {p: None for p in providers}
    for provider, is_active, updated_at in result.all():
        if provider not in status_map: continue
        status_map[provider] = status_map[provider] or bool(is_active)
        if is_active and updated_at:
            ts = updated_at.isoformat()
            if not last_connected_at[provider] or ts > last_connected_at[provider]:
                last_connected_at[provider] = ts
    return {
        "connections": status_map,
        "providers": [
            {"id": p, "connected": status_map[p], "last_connected_at": last_connected_at[p]}
            for p in providers
        ],
    }

@router.post("/refresh")
async def refresh_token(request: Request, payload: Optional[RefreshTokenRequest] = None):
    client = get_redis_client()
    refresh_token_value = (payload.refresh_token if payload else None) or request.cookies.get("graftai_refresh_token") or request.query_params.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    user_id = client.get(f"refresh:{refresh_token_value}")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    if isinstance(user_id, bytes): user_id = user_id.decode()
    try:
        token_payload = jwt.decode(refresh_token_value, SECRET_KEY, algorithms=[ALGORITHM])
        if token_payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    client.delete(f"refresh:{refresh_token_value}")
    client.srem(f"user_tokens:{user_id}", refresh_token_value)
    token_data = create_jwt_token(user_id)
    response = JSONResponse(content={"message": "Token refreshed successfully"})
    attach_jwt_cookies(response, token_data, request)
    return response

@router.post("/logout")
def logout(request: Request, current_user=Depends(get_current_user)):
    client = get_redis_client()
    refresh_token = request.cookies.get("graftai_refresh_token")
    if refresh_token:
        client.delete(f"refresh:{refresh_token}")
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="graftai_access_token", path="/")
    response.delete_cookie(key="graftai_refresh_token", path="/")
    return response

@router.delete("/account")
async def delete_account(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.get("sub")
    email = current_user.get("email")
    full_name = current_user.get("name", "User")
    try:
        async with db.begin():
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            await db.execute(delete(UserTable).where(UserTable.id == user_id))
        client = get_redis_client()
        client.delete(f"sso_token:{user_id}")
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Account deletion failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")
    try:
        from backend.services.notifications import notify_account_deleted_email
        await notify_account_deleted_email(user_email=email, full_name=user.full_name or full_name)
    except Exception as e:
        logger.warning(f"Farewell email failed for {email}: {e}")
    response = JSONResponse(content={"message": "Account deleted successfully"})
    response.delete_cookie(key="graftai_access_token", path="/")
    response.delete_cookie(key="graftai_refresh_token", path="/")
    token_key = f"user_tokens:{user_id}"
    tokens = client.smembers(token_key)
    if tokens:
        for t in tokens:
            client.delete(f"refresh:{t if isinstance(t, str) else t.decode()}")
    client.delete(token_key)
    return response

@router.post("/revoke")
def revoke_sessions(
    target_user_id: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
):
    client = get_redis_client()
    revoke_id = current_user_id
    if target_user_id and target_user_id != current_user_id:
        if not access_control.check_user_role(current_user_id, "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative privileges required")
        revoke_id = target_user_id
    token_key = f"user_tokens:{revoke_id}"
    tokens = client.smembers(token_key)
    deleted_count = 0
    if tokens:
        for t in tokens:
            if client.delete(f"refresh:{t if isinstance(t, str) else t.decode()}"):
                deleted_count += 1
        client.delete(token_key)
    logger.info(f"User {current_user_id} revoked {deleted_count} sessions for {revoke_id}")
    return {"message": f"Successfully revoked {deleted_count} sessions for {revoke_id}"}
