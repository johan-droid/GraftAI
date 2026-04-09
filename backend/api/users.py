from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import re

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable, UserTokenTable

router = APIRouter(prefix="/users", tags=["users"])

class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None

    @validator("username")
    def username_must_be_valid(cls, value: Optional[str]):
        if value is None:
            return value
        if not re.fullmatch(r"[a-zA-Z0-9_-]{3,30}", value):
            raise ValueError("Username must be 3-30 characters and contain only letters, numbers, hyphens, or underscores.")
        return value.lower()

@router.get("/me")
async def get_my_profile(current_user: UserTable = Depends(get_current_user)):
    """Fetch current user profile for the monolithic dashboard."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name
    }

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

    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "created_at": user.created_at
    }
