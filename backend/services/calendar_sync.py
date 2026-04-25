import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTokenTable
from backend.services.integrations.calendar_provider import (
    get_calendar_provider_for_token,
)
from backend.utils.cache import delete_cache_pattern, get_cache, set_cache

from backend.utils.db import get_db_context

logger = logging.getLogger(__name__)

CACHE_PREFIX = "calendar:busy_times"
DEFAULT_LOOKAHEAD_DAYS = 90
CHUNK_DAYS = 30


class CalendarSyncService:
    def _cache_key(self, user_id: str, token_id: str, start: datetime) -> str:
        return f"{CACHE_PREFIX}:{user_id}:{token_id}:{start.isoformat()}"

    def _ttl_seconds(self, start: datetime) -> int:
        days_from_now = max(0, (start - datetime.now(timezone.utc)).days)
        if days_from_now > 30:
            return 3600
        if days_from_now > 7:
            return 900
        return 300

    async def invalidate_user_calendar_busy_cache(self, user_id: str) -> None:
        await delete_cache_pattern(f"{CACHE_PREFIX}:{user_id}:*")

    async def sync_calendar(self, user_id: str, provider: str = "google") -> dict:
        """
        Syncs calendar for a specific user and provider.
        This is the method expected by the Celery tasks.
        """
        async with get_db_context() as db:
            # For now, this just calls the internal sync logic
            # and returns a summary compatible with the task expectation.
            await self.sync_calendar_for_user(db, user_id)
            return {"synced": 0, "conflicts": 0}

    async def sync_calendar_for_user(self, db: AsyncSession, user_id: str) -> None:
        stmt = select(UserTokenTable).where(
            UserTokenTable.user_id == user_id,
            UserTokenTable.is_active == True,
        )
        tokens = (await db.execute(stmt)).scalars().all()
        if not tokens:
            logger.info(f"No active calendar credentials found for user {user_id}")
            return

        start_date = datetime.now(timezone.utc)

        for token in tokens:
            # Filter by provider if needed, or sync all if no provider specified
            # For now, we sync all active tokens as they are all 'calendar' tokens.
            provider_impl = get_calendar_provider_for_token(token)
            if not provider_impl:
                logger.warning(
                    f"Skipping unsupported calendar provider for token {token.id}: {token.provider}"
                )
                continue

            for chunk_index in range(0, DEFAULT_LOOKAHEAD_DAYS, CHUNK_DAYS):
                range_start = start_date + timedelta(days=chunk_index)
                range_end = range_start + timedelta(days=CHUNK_DAYS)
                cache_key = self._cache_key(user_id, token.id, range_start)

                if await get_cache(cache_key) is not None:
                    continue

                try:
                    busy_windows = await provider_impl.get_busy_windows(
                        db, range_start, range_end
                    )
                    await set_cache(
                        cache_key,
                        busy_windows,
                        expire_seconds=self._ttl_seconds(range_start),
                    )
                except Exception as exc:
                    logger.error(
                        f"Calendar busy-time sync failed for user={user_id} token={token.id} provider={token.provider}"
                        f" range={range_start.isoformat()}-{range_end.isoformat()}: {exc}"
                    )


# Functional alias for backward compatibility
async def sync_calendar_for_user(db: AsyncSession, user_id: str) -> None:
    await CalendarSyncService().sync_calendar_for_user(db, user_id)


async def invalidate_user_calendar_busy_cache(user_id: str) -> None:
    await CalendarSyncService().invalidate_user_calendar_busy_cache(user_id)
