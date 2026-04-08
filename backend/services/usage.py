import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import UserTable

logger = logging.getLogger(__name__)

# STRIPPED DOWN: Muted for monolithic stability
# We no longer enforce daily limits in this simplified architecture.

def check_usage_limit(feature: str):
    """No-op dependency factory for simplified architecture.

    Returns an async dependency callable that always allows the request.
    """
    async def _check_limit() -> bool:
        return True

    return _check_limit

async def increment_usage(db: AsyncSession, user_id: str, feature: str):
    """No-op: All features are now effectively unlimited."""
    logger.debug(f"Usage skip: {feature} for {user_id}")
    return

def get_next_quota_reset() -> datetime:
    return datetime.now(timezone.utc)

def get_trial_days_left(created_at: datetime) -> int:
    return 999
