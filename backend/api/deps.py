from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.db import get_db as _get_db
from backend.auth.schemes import get_current_user_id

async def get_db():
    async for session in _get_db():
        yield session

def require_role(role: str):
    """
    Returns a dependency that validates the current user has the required role.
    """
    async def role_checker(
        db: AsyncSession = Depends(get_db),
        user_id: str = Depends(get_current_user_id)
    ):
        from backend.services.access_control import check_user_role
        if not await check_user_role(db, user_id, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: {role}"
            )
        return user_id
    
    return role_checker

