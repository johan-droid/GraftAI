import inspect
import logging
from datetime import datetime, timezone
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTable
from backend.utils.cache import get_redis_client as _get_redis_client
from backend.utils.db import get_db

logger = logging.getLogger(__name__)

# STRIPPED DOWN: Muted for monolithic stability
# We no longer enforce daily limits in this simplified architecture.


def get_redis_client():
    return _get_redis_client()


def check_usage_limit(feature: str):
    """No-op dependency factory for simplified architecture.

    Returns an async dependency callable that always allows the request.
    """
    async def _check_limit(
        *,
        user_id: str = None,
        db: AsyncSession = Depends(get_db),
        **kwargs,
    ) -> bool:
        return True

    return _check_limit

async def increment_usage(db: AsyncSession, user_id: str, feature: str):
    """Increment the user's usage counters without enforcing a hard quota."""
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    scalar_result = result.scalars()
    if inspect.isawaitable(scalar_result):
        scalar_result = await scalar_result

    user = scalar_result.first()
    if inspect.isawaitable(user):
        user = await user

    if user is None:
        return

    if feature == "ai_messages":
        user.daily_ai_count = getattr(user, "daily_ai_count", 0) + 1
    elif feature == "calendar_syncs":
        user.daily_sync_count = getattr(user, "daily_sync_count", 0) + 1
    else:
        logger.debug(f"Unknown usage feature: {feature}")

    await db.commit()

def get_next_quota_reset() -> datetime:
    return datetime.now(timezone.utc)

def get_trial_days_left(created_at: datetime) -> int:
    return 999
