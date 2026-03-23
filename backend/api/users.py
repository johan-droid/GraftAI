from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User
from ..utils.db import get_db
from ..auth.schemes import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def read_current_user(current_user=Depends(get_current_user)):
    return current_user

# Additional user endpoints can be added here
