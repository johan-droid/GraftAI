import logging
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes import get_current_user_id
from backend.models.tables import UserTable
from backend.utils.db import get_db
from backend.core.saas_config import get_limit, Feature, has_feature
from backend.services.audit import log_activity

logger = logging.getLogger(__name__)


async def get_user_quota(db: AsyncSession, user_id: str) -> UserTable:
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)
    
    # Handle potentially naive datetimes from SQLite
    reset_at = user.quota_reset_at
    if reset_at and reset_at.tzinfo is None:
        reset_at = reset_at.replace(tzinfo=timezone.utc)

    # Reset quotas if quota_reset_at is passed or not set
    if not reset_at or now >= reset_at:
        user.daily_ai_count = 0
        user.daily_sync_count = 0

        # Calculate next midnight UTC
        next_midnight = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        user.quota_reset_at = next_midnight

        await db.commit()
        await db.refresh(user)

    return user


def check_usage_limit(feature_key: str):
    """Enforces limits based on user's tier and declarative SaaS config."""

    async def _check_limit(
        user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ) -> bool:
        user = await get_user_quota(db, user_id)
        
        # 1. Check Feature Gate first
        feature_map = {
            "ai_messages": Feature.AI_COPILOT,
            "calendar_syncs": Feature.CALENDAR_SYNC,
            "team_management": Feature.TEAM_MANAGEMENT,
            "analytics": Feature.ADVANCED_ANALYTICS,
        }
        
        target_feature = feature_map.get(feature_key)
        if target_feature and not has_feature(user.tier, target_feature):
            await log_activity(
                db, 
                action="feature.denied", 
                user_id=user_id, 
                metadata={"feature": feature_key, "tier": user.tier},
                status="denied"
            )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"The {feature_key} feature is not available on your {user.tier} plan. Please upgrade.",
            )

        # 2. Check Numeric Limits
        limit_map = {
            "ai_messages": ("daily_ai_messages", user.daily_ai_count),
            "calendar_syncs": ("daily_calendar_syncs", user.daily_sync_count),
        }
        
        if feature_key in limit_map:
            limit_name, current_val = limit_map[feature_key]
            
            # Explicit override in DB takes precedence, otherwise use tier default
            limit = (
                user.daily_ai_limit if feature_key == "ai_messages" and user.daily_ai_limit is not None
                else user.daily_sync_limit if feature_key == "calendar_syncs" and user.daily_sync_limit is not None
                else get_limit(user.tier, limit_name)
            )
            
            if current_val >= limit:
                await log_activity(
                    db, 
                    action="quota.exceeded", 
                    user_id=user_id, 
                    metadata={"feature": feature_key, "usage": current_val, "limit": limit},
                    status="denied"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily usage limit for {feature_key} reached. Upgrade your plan for higher limits.",
                )

        return True

    return _check_limit


async def increment_usage(db: AsyncSession, user_id: str, feature: str, amount: int = 1):
    """Increment usage and log the activity for auditing."""
    user = await get_user_quota(db, user_id)

    if feature == "ai_messages":
        user.daily_ai_count += amount
    elif feature == "calendar_syncs":
        user.daily_sync_count += amount
    elif feature == "ai_tokens":
        user.total_ai_tokens += amount
    elif feature == "api_calls":
        user.total_api_calls += amount
    elif feature == "scheduling":
        user.total_scheduling_count += amount
    else:
        logger.debug(f"Unknown usage feature: {feature}")

    # SaaS Audit Logging for significant actions
    if feature in ["ai_messages", "scheduling", "calendar_syncs"]:
        await log_activity(
            db, 
            action=f"usage.{feature}", 
            user_id=user_id, 
            metadata={"increment": amount, "total_daily": getattr(user, f"daily_{feature.split('_')[1] if '_' in feature else feature}_count", None)}
        )

    await db.commit()


async def get_usage_counts(db: AsyncSession, user_id: str) -> dict:
    """Returns basic usage counts for a user."""
    user = await get_user_quota(db, user_id)
    return {
        "daily_ai_count": user.daily_ai_count,
        "daily_sync_count": user.daily_sync_count,
        "total_ai_tokens": user.total_ai_tokens,
        "total_api_calls": user.total_api_calls,
        "total_scheduling_count": user.total_scheduling_count,
        "tier": user.tier,
    }


def get_next_quota_reset() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)


def get_trial_days_left(created_at: datetime) -> int:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    else:
        created_at = created_at.astimezone(timezone.utc)

    trial_end = created_at + timedelta(days=14)
    now = datetime.now(timezone.utc)
    diff = (trial_end - now).days
    return max(0, diff)
