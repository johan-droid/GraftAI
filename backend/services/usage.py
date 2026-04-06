import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.utils.db import get_db, unwrap_result
from backend.models.tables import UserTable, UserTier
from backend.auth.schemes import get_current_user_id

logger = logging.getLogger(__name__)
DEFAULT_TRIAL_DAYS = int(os.getenv("FREE_TRIAL_DAYS", "7"))

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

def _start_of_utc_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

async def _reset_usage_if_needed(user: UserTable, db: AsyncSession):
    """Reset daily counters once per UTC day at midnight."""
    now = datetime.now(timezone.utc)

    # If last_usage_reset is naive, make it aware (for safety)
    last_reset = user.last_usage_reset
    if last_reset and last_reset.tzinfo is None:
        last_reset = last_reset.replace(tzinfo=timezone.utc)

    if not last_reset or last_reset < _start_of_utc_day(now):
        user.daily_ai_count = 0
        user.daily_sync_count = 0
        user.ai_quota_warning_sent = False
        user.sync_quota_warning_sent = False
        user.last_quota_warning_at = None
        user.last_usage_reset = now
        await db.commit()
        logger.info(f"📅 Reset daily usage for user {user.id}")


def _quota_warning_threshold() -> float:
    return 0.90


def _feature_label(feature: str) -> str:
    return {
        "ai_messages": "AI Copilot messages",
        "calendar_syncs": "calendar syncs",
    }.get(feature, feature.replace("_", " "))


def get_tier_usage_limits(tier: UserTier):
    return TIER_LIMITS.get(tier, TIER_LIMITS[UserTier.FREE])


def get_next_quota_reset() -> datetime:
    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)
    return _start_of_utc_day(tomorrow)


def get_trial_days_left(created_at: Optional[datetime]) -> int:
    if not created_at:
        return 0
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    expires_at = created_at + timedelta(days=DEFAULT_TRIAL_DAYS)
    now = datetime.now(timezone.utc)
    if expires_at <= now:
        return 0
    return max(0, int((expires_at - now).total_seconds() // 86400) + 1)


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
        scalars = await unwrap_result(result.scalars())
        user = await unwrap_result(scalars.first())
        
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
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    scalars = await unwrap_result(result.scalars())
    user = await unwrap_result(scalars.first())
    if not user:
        return

    if feature == "ai_messages":
        user.daily_ai_count = (user.daily_ai_count or 0) + 1
    elif feature == "calendar_syncs":
        user.daily_sync_count = (user.daily_sync_count or 0) + 1
    else:
        logger.warning(f"Unknown usage feature '{feature}' for user {user_id}")
        return

    await db.commit()
    logger.info(f"📈 Incremented {feature} for user {user_id}")

    # SaaS-grade quota warning: free tier users get a refill prompt when they hit 90%.
    tier = user.tier or UserTier.FREE
    if tier == UserTier.FREE:
        limit = TIER_LIMITS[tier].get(feature)
        current_count = user.daily_ai_count if feature == "ai_messages" else user.daily_sync_count
        if limit and current_count >= int(limit * _quota_warning_threshold()):
            warn_attr = "ai_quota_warning_sent" if feature == "ai_messages" else "sync_quota_warning_sent"
            if not getattr(user, warn_attr, False):
                try:
                    from backend.services.notifications import notify_quota_warning

                    await notify_quota_warning(
                        user_id=user.id,
                        user_email=user.email,
                        full_name=user.full_name or user.name or user.email,
                        feature=feature,
                        current_count=current_count,
                        limit=limit,
                    )
                    setattr(user, warn_attr, True)
                    user.last_quota_warning_at = datetime.now(timezone.utc)
                    await db.commit()
                    logger.info(f"📣 Sent quota warning for {feature} to user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to send quota warning email for {feature} / user {user_id}: {e}")
