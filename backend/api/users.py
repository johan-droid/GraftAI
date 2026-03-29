from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.db import get_db
from backend.auth.schemes import get_current_user
from backend.services.prefetcher import prefetcher

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def read_current_user(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns current user info and proactively prefetches AI context for lightning-fast orchestration.
    """
    # Trigger AI context pre-warming in the background
    background_tasks.add_task(prefetcher.prefetch_user_context, db, current_user.get("sub"))
    
    return current_user


# Additional user endpoints can be added here
