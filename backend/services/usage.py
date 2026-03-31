import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.utils.db import get_db
from backend.models.tables import UserTable, UserTier
from backend.auth.schemes import get_current_user_id

logger = logging.getLogger(__name__)

# Daily Usage Limits PER TIER
TIER_LIMITS = {
    UserTier.FREE: {
        "ai_messages": 10,
        "calendar_syncs": 3,
    },
    UserTier.PRO: {
        "ai_messages": 200,
        "calendar_syncs": 50,
    },
    UserTier.ELITE: {
        "ai_messages": 2000, # Soft limit for security
        "calendar_syncs": 500,
    }
}

async def _reset_usage_if_needed(user: UserTable, db: AsyncSession):
    """Reset daily counters if 24h have passed since last reset."""
    now = datetime.now(timezone.utc)
    
    # If last_usage_reset is naive, make it aware (for safety)
    last_reset = user.last_usage_reset
    if last_reset and last_reset.tzinfo is None:
        last_reset = last_reset.replace(tzinfo=timezone.utc)
        
    if not last_reset or (now - last_reset) >= timedelta(days=1):
        user.daily_ai_count = 0
        user.daily_sync_count = 0
        user.last_usage_reset = now
        await db.commit()
        logger.info(f"📅 Reset daily usage for user {user.id}")

def check_usage_limit(feature: str):
    """
    FastAPI dependency factory to check if a user has exceeded their tier limits.
    Usage: Depends(check_usage_limit("ai_messages"))
    """
    async def _check_limit(
        user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db)
    ) -> bool:
        result = await db.execute(select(UserTable).where(UserTable.id == user_id))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 1. Reset if new day
        await _reset_usage_if_needed(user, db)
        
        # 2. Get limits for current tier
        tier = user.tier or UserTier.FREE
        limits = TIER_LIMITS.get(tier, TIER_LIMITS[UserTier.FREE])
        
        limit = limits.get(feature)
        if limit is None:
            return True # No limit defined for this feature
        
        # 3. Check current count
        current_count = 0
        if feature == "ai_messages":
            current_count = user.daily_ai_count
        elif feature == "calendar_syncs":
            current_count = user.daily_sync_count
            
        if current_count >= limit:
            logger.warning(f"🚫 User {user_id} ({tier}) reached {feature} limit: {current_count}/{limit}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You have reached your daily limit for {feature.replace('_', ' ')}. Upgrade your plan for higher limits."
            )
            
        return True
        
    return _check_limit

async def increment_usage(db: AsyncSession, user_id: str, feature: str):
    """Increment the daily usage counter for a specific feature."""
    async with db.begin():
        result = await db.execute(select(UserTable).where(UserTable.id == user_id))
        user = result.scalars().first()
        if user:
            if feature == "ai_messages":
                user.daily_ai_count += 1
            elif feature == "calendar_syncs":
                user.daily_sync_count += 1
            logger.info(f"📈 Incremented {feature} for user {user_id}")
