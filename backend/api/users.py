from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import re
import uuid

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable, UserTokenTable
from backend.services.api_keys import create_user_api_key, list_user_api_keys, revoke_user_api_key

router = APIRouter(prefix="/users", tags=["users"])

class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    preferences: Optional[dict] = None

    @validator("username")
    def username_must_be_valid(cls, value: Optional[str]):
        if value is None:
            return value
        if not re.fullmatch(r"[a-zA-Z0-9_-]{3,30}", value):
            raise ValueError("Username must be 3-30 characters and contain only letters, numbers, hyphens, or underscores.")
        return value.lower()


class ApiKeyCreateRequest(BaseModel):
    name: Optional[str] = None


class OutOfOfficeBlockCreateRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None

    @validator("end_time")
    def end_must_be_after_start(cls, value: datetime, values: Dict[str, Any]):
        start_time = values.get("start_time")
        if start_time and value <= start_time:
            raise ValueError("end_time must be after start_time")
        return value


def _normalize_preferences(user: UserTable) -> Dict[str, Any]:
    prefs = user.preferences or {}
    if not isinstance(prefs, dict):
        return {}
    return dict(prefs)


def _serialize_profile(user: UserTable) -> Dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "tier": user.tier,
        "subscription_status": user.subscription_status,
        "razorpay_subscription_id": user.razorpay_subscription_id,
        "daily_ai_count": user.daily_ai_count,
        "daily_ai_limit": user.daily_ai_limit,
        "daily_sync_count": user.daily_sync_count,
        "daily_sync_limit": user.daily_sync_limit,
        "quota_reset_at": user.quota_reset_at.isoformat() if user.quota_reset_at else None,
        "trial_active": user.trial_active,
        "trial_expires_at": user.trial_expires_at.isoformat() if user.trial_expires_at else None,
        "preferences": user.preferences or {},
    }


def _to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat()


def _extract_out_of_office_blocks(user: UserTable) -> List[Dict[str, Any]]:
    prefs = _normalize_preferences(user)
    blocks = prefs.get("out_of_office") or []
    if not isinstance(blocks, list):
        return []
    normalized = [item for item in blocks if isinstance(item, dict)]
    normalized.sort(key=lambda item: item.get("start_time") or "")
    return normalized


def _set_out_of_office_blocks(user: UserTable, blocks: List[Dict[str, Any]]) -> None:
    prefs = _normalize_preferences(user)
    prefs["out_of_office"] = blocks
    user.preferences = prefs

@router.get("/me")
async def get_my_profile(current_user: UserTable = Depends(get_current_user)):
    """Fetch current user profile for the monolithic dashboard."""
    return _serialize_profile(current_user)

@router.get("/me/integrations")
async def get_my_integrations(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns a list of connected services (e.g., ['google', 'microsoft'])."""
    active_stmt = select(UserTokenTable.provider).where(
        and_(UserTokenTable.user_id == current_user.id, UserTokenTable.is_active == True)
    )
    inactive_stmt = select(UserTokenTable.provider).where(
        and_(UserTokenTable.user_id == current_user.id, UserTokenTable.is_active == False)
    )
    active_providers = (await db.execute(active_stmt)).scalars().all()
    inactive_providers = (await db.execute(inactive_stmt)).scalars().all()
    return {
        "active_providers": list(active_providers),
        "inactive_providers": list(sorted(set(inactive_providers) - set(active_providers)))
    }

@router.delete("/me/integrations/{provider}")
async def disconnect_integration(
    provider: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes or deactivates the OAuth token for a specific provider."""
    stmt = select(UserTokenTable).where(
        and_(UserTokenTable.user_id == current_user.id, UserTokenTable.provider == provider)
    )
    token = (await db.execute(stmt)).scalars().first()
    
    if not token:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    await db.delete(token)
    await db.commit()
    return {"message": f"{provider} disconnected successfully"}

@router.patch("/me")
async def update_current_user_profile(
    payload: UserProfileUpdateRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile (Full Name only)."""
    user_id = current_user.id
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() or user.full_name

    if payload.username is not None:
        username = payload.username.strip().lower()
        if username and username != user.username:
            stmt = select(UserTable).where(UserTable.username == username)
            existing = (await db.execute(stmt)).scalars().first()
            if existing:
                raise HTTPException(status_code=409, detail="Username already taken")
            user.username = username

    if payload.preferences is not None:
        # Merge new preferences with existing ones, if any
        current_prefs = _normalize_preferences(user)
        new_prefs = current_prefs.copy()
        new_prefs.update(payload.preferences)
        user.preferences = new_prefs

    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "preferences": user.preferences,
        "created_at": user.created_at,
    }


@router.get("/me/api-keys")
async def list_current_user_api_keys(current_user: UserTable = Depends(get_current_user)):
    return {"items": list_user_api_keys(current_user)}


@router.post("/me/api-keys")
async def create_current_user_api_key(
    payload: ApiKeyCreateRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    created_key, raw_key = create_user_api_key(current_user, payload.name)
    await db.commit()
    await db.refresh(current_user)
    return {**created_key, "token": raw_key}


@router.delete("/me/api-keys/{key_id}")
async def revoke_current_user_api_key(
    key_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    changed = revoke_user_api_key(current_user, key_id)
    if not changed:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.commit()
    await db.refresh(current_user)
    return {"status": "revoked", "id": key_id}


@router.get("/me/out-of-office")
async def list_current_user_out_of_office(current_user: UserTable = Depends(get_current_user)):
    return {"items": _extract_out_of_office_blocks(current_user)}


@router.post("/me/out-of-office")
async def create_current_user_out_of_office(
    payload: OutOfOfficeBlockCreateRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    blocks = _extract_out_of_office_blocks(current_user)
    block = {
        "id": uuid.uuid4().hex,
        "start_time": _to_utc_iso(payload.start_time),
        "end_time": _to_utc_iso(payload.end_time),
        "reason": (payload.reason or "").strip() or None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    blocks.append(block)
    _set_out_of_office_blocks(current_user, blocks)
    await db.commit()
    await db.refresh(current_user)
    return block


@router.delete("/me/out-of-office/{block_id}")
async def delete_current_user_out_of_office(
    block_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    blocks = _extract_out_of_office_blocks(current_user)
    filtered = [item for item in blocks if item.get("id") != block_id]
    if len(filtered) == len(blocks):
        raise HTTPException(status_code=404, detail="Out-of-office block not found")

    _set_out_of_office_blocks(current_user, filtered)
    await db.commit()
    await db.refresh(current_user)
    return {"status": "deleted", "id": block_id}
