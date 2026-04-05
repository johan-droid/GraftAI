from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth.schemes import get_current_user
from backend.api.deps import get_db
from backend.models.tables import UserTable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/users", tags=["users"])


class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None


@router.get("/me")
async def read_current_user(current_user=Depends(get_current_user)):
    return current_user


@router.patch("/me")
async def update_current_user_profile(
    payload: UserProfileUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = str(current_user.get("sub"))
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() or user.full_name
    if payload.timezone is not None:
        user.timezone = payload.timezone.strip() or user.timezone

    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "timezone": user.timezone,
    }


# Additional user endpoints can be added here
