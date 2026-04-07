import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.utils.db import get_db
from backend.models.tables import UserTable, UserTier
from backend.auth.schemes import get_current_user_id
from backend.utils.cache import get_redis_client

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
    High-Performance FastAPI dependency: 
    Checks Redis first (Sub-ms) before falling back to DB (Slow).
    """
    async def _check_limit(
        user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db)
    ) -> bool:
        redis = await get_redis_client()
        
        # 1. High-Performance Redis Path
        if redis:
            current_count = await redis.get(f"usage:{user_id}:{feature}")
            if current_count is not None:
                current_count = int(current_count)
                # Find tier from Redis-cached user info if possible (Optimization for later)
                # For now, hit DB for tier only if not in Redis
                user_tier_raw = await redis.get(f"user:{user_id}:tier")
                tier = UserTier(user_tier_raw.decode()) if user_tier_raw else UserTier.FREE
                
                limit = TIER_LIMITS.get(tier, TIER_LIMITS[UserTier.FREE]).get(feature)
                if limit and current_count >= limit:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Daily limit reached for {feature.replace('_', ' ')}. Upgrade for more."
                    )
                return True

        # 2. Local/DB Fallback Path (If Redis is down or key expired)
        stmt = select(UserTable).where(UserTable.id == user_id)
        user = (await db.execute(stmt)).scalars().first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        
        await _reset_usage_if_needed(user, db)
        
        # Seed Redis with DB state if missing
        if redis:
            await redis.setex(f"usage:{user_id}:ai_messages", 86400, user.daily_ai_count or 0)
            await redis.setex(f"usage:{user_id}:calendar_syncs", 86400, user.daily_sync_count or 0)
            await redis.setex(f"user:{user_id}:tier", 86400, user.tier.value if user.tier else "free")
        
        tier = user.tier or UserTier.FREE
        limit = TIER_LIMITS.get(tier, TIER_LIMITS[UserTier.FREE]).get(feature)
        current_count = getattr(user, f"daily_{'ai' if 'ai' in feature else 'sync'}_count", 0)
        
        if limit and current_count >= limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Daily limit reached for {feature.replace('_', ' ')}."
            )
            
        return True
    return _check_limit

async def increment_usage(db: AsyncSession, user_id: str, feature: str):
    """
    Advanced Write-Behind Increment:
    Increments in Redis and pushes to a 'Flush Queue' for batch DB updates.
    """
    redis = await get_redis_client()
    
    # 1. Update Redis (Instant)
    current_count = 0
    if redis:
        current_count = await redis.incr(f"usage:{user_id}:{feature}")
        # Add to Flush Queue for background worker persistence
        await redis.sadd("usage:flush_queue", user_id)
    else:
        # Fallback to DB if Redis is down
        stmt = select(UserTable).where(UserTable.id == user_id)
        user = (await db.execute(stmt)).scalars().first()
        if user:
            if feature == "ai_messages": user.daily_ai_count += 1
            else: user.daily_sync_count += 1
            await db.commit()
            current_count = user.daily_ai_count if "ai" in feature else user.daily_sync_count

    logger.info(f"📈 Incremented {feature} for user {user_id} (New count: {current_count})")
    
    # 2. Trigger Real-Time UI Sync (SSE)
    from backend.utils.arq_utils import enqueue_job
    await enqueue_job("task_emit_quota_update", user_id=user_id, feature=feature, count=current_count)

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
