import logging
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes import get_current_user_id
from backend.models.tables import UserTable
from backend.utils.db import get_db

logger = logging.getLogger(__name__)


async def get_user_quota(db: AsyncSession, user_id: str) -> UserTable:
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)

    # Reset quotas if quota_reset_at is passed or not set
    if not user.quota_reset_at or now >= user.quota_reset_at:
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


def check_usage_limit(feature: str):
    """Enforces limits based on user's tier and features."""

    async def _check_limit(
        user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ) -> bool:
        user = await get_user_quota(db, user_id)

        if feature == "ai_messages":
            limit = (
                user.daily_ai_limit
                if user.daily_ai_limit is not None
                else (
                    2000
                    if user.tier == "elite"
                    else (200 if user.tier == "pro" else 10)
                )
            )
            if user.daily_ai_count >= limit:
                raise HTTPException(
                    status_code=429,
                    detail="AI Copilot usage limit reached. Upgrade to Pro for more.",
                )
        elif feature == "calendar_syncs":
            limit = (
                user.daily_sync_limit
                if user.daily_sync_limit is not None
                else (
                    500 if user.tier == "elite" else (50 if user.tier == "pro" else 3)
                )
            )
            if user.daily_sync_count >= limit:
                raise HTTPException(
                    status_code=429,
                    detail="Manual sync limit reached. Upgrade to Pro for more.",
                )

        return True

    return _check_limit


async def increment_usage(db: AsyncSession, user_id: str, feature: str):
    """Increment the user's usage counters."""
    user = await get_user_quota(db, user_id)

    if feature == "ai_messages":
        user.daily_ai_count += 1
    elif feature == "calendar_syncs":
        user.daily_sync_count += 1
    else:
        logger.debug(f"Unknown usage feature: {feature}")

    await db.commit()


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
