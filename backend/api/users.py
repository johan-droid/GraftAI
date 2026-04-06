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
    bio: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None


class UserRoleResponse(BaseModel):
    user_id: str
    role: str
    is_superuser: bool
    has_admin_access: bool
    allowed_roles: list[str]


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
    if payload.bio is not None:
        user.bio = payload.bio.strip()
    if payload.job_title is not None:
        user.job_title = payload.job_title.strip()
    if payload.location is not None:
        user.location = payload.location.strip()

    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "timezone": user.timezone,
        "bio": user.bio,
        "job_title": user.job_title,
        "location": user.location,
        "created_at": user.created_at,
    }


@router.get("/me/role", response_model=UserRoleResponse)
async def read_current_user_role(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Postman-friendly RBAC endpoint to inspect the caller's effective role."""
    user_id = str(current_user.get("sub"))
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = user.role or "member"
    allowed_roles = ["member"]
    if role == "service_account":
        allowed_roles.append("service_account")
    if role == "admin" or user.is_superuser:
        allowed_roles.append("admin")

    return UserRoleResponse(
        user_id=user.id,
        role=role,
        is_superuser=bool(user.is_superuser),
        has_admin_access=bool(user.is_superuser or role == "admin"),
        allowed_roles=allowed_roles,
    )


# Additional user endpoints can be added here
