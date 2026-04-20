import os
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import UserTable
from backend.services.usage import get_usage_counts, increment_usage
from backend.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_DAILY_AI_LIMIT = int(os.getenv("DEFAULT_DAILY_AI_LIMIT", "20"))
DEFAULT_DAILY_SYNC_LIMIT = int(os.getenv("DEFAULT_DAILY_SYNC_LIMIT", "5"))


def get_daily_ai_limit(user: UserTable) -> int:
    if user.daily_ai_limit is not None:
        return user.daily_ai_limit
    return DEFAULT_DAILY_AI_LIMIT


def get_daily_sync_limit(user: UserTable) -> int:
    if user.daily_sync_limit is not None:
        return user.daily_sync_limit
    return DEFAULT_DAILY_SYNC_LIMIT


async def is_ai_quota_available(
    db: AsyncSession, user: UserTable
) -> Tuple[bool, str]:
    usage = await get_usage_counts(db, user.id)
    limit = get_daily_ai_limit(user)
    current = usage["daily_ai_count"]

    if limit <= 0:
        return True, "AI usage unlimited"

    if current >= limit:
        return False, (
            f"Daily AI request limit reached ({current}/{limit}). "
            "Upgrade your plan or wait until quota resets."
        )

    return True, "Within AI quota"


async def increment_ai_count(db: AsyncSession, user: UserTable) -> None:
    await increment_usage(db, user.id, "ai_messages")


def get_ai_quota_header(user: UserTable) -> str:
    limit = get_daily_ai_limit(user)
    usage = user.daily_ai_count or 0
    return f"{usage}/{limit if limit > 0 else 'unlimited'}"
