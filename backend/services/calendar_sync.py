import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTokenTable
from backend.services.integrations.calendar_provider import (
    get_calendar_provider_for_token,
)
from backend.services.sync_engine import sync_user_calendar as sync_user_calendar_events
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
        days_from_now = max(0, (start - datetime.now(UTC)).days)
        if days_from_now > 30:
            return 3600
        if days_from_now > 7:
            return 900
        return 300

    async def invalidate_user_calendar_busy_cache(self, user_id: str) -> None:
        await delete_cache_pattern(f"{CACHE_PREFIX}:{user_id}:*")

    async def sync_calendar(self, user_id: str, provider: str="google") -> dict:
        """
        Syncs calendar for a specific user and provider.
        This is the method expected by the Celery tasks.
        """
        async with get_db_context() as db:
            event_summary = await sync_user_calendar_events(db, user_id)
            await self.sync_calendar_for_user(db, user_id, provider=provider)
            return {"synced": int(event_summary.get("items_processed", 0)), "conflicts": 0, "summary": event_summary}

    async def sync_calendar_for_user(self, db: AsyncSession, user_id: str, provider: str | None=None) -> None:
        stmt = select(UserTokenTable).where(UserTokenTable.user_id == user_id, UserTokenTable.is_active)
        if provider:
            stmt = stmt.where(UserTokenTable.provider == provider)
        tokens = (await db.execute(stmt)).scalars().all()
        if not tokens:
            logger.info("No active calendar credentials found for user %s", user_id)
            return
        start_date = datetime.now(UTC)
        for token in tokens:
            provider_impl = get_calendar_provider_for_token(token)
            if not provider_impl:
                logger.warning("Skipping unsupported calendar provider for token %s: %s", token.id, token.provider)
                continue
            for chunk_index in range(0, DEFAULT_LOOKAHEAD_DAYS, CHUNK_DAYS):
                range_start = start_date + timedelta(days=chunk_index)
                range_end = range_start + timedelta(days=CHUNK_DAYS)
                cache_key = self._cache_key(user_id, token.id, range_start)
                if await get_cache(cache_key) is not None:
                    continue
                try:
                    busy_windows = await provider_impl.get_busy_windows(db, range_start, range_end)
                    await set_cache(cache_key, busy_windows, expire_seconds=self._ttl_seconds(range_start))
                except Exception as exc:
                    logger.exception("Calendar busy-time sync failed for user=%s token=%s provider=%s range=%s-%s: %s", user_id, token.id, token.provider, range_start.isoformat(), range_end.isoformat(), exc)

    async def create_event(self, user_id: str, provider: str, event_data: dict) -> dict:
        """Creates an event in the user's external calendar."""
        async with get_db_context() as db:
            stmt = select(UserTokenTable).where(UserTokenTable.user_id == user_id, UserTokenTable.provider == provider, UserTokenTable.is_active)
            token = (await db.execute(stmt)).scalars().first()
            if not token:
                msg = f"No active {provider} token found for user {user_id}"
                raise ValueError(msg)
            provider_impl = get_calendar_provider_for_token(token)
            if not provider_impl:
                msg = f"Unsupported provider: {provider}"
                raise ValueError(msg)
            return await provider_impl.create_event(event_data)

    async def delete_event(self, user_id: str, provider: str, external_event_id: str) -> bool:
        """Deletes an event from the user's external calendar."""
        async with get_db_context() as db:
            stmt = select(UserTokenTable).where(UserTokenTable.user_id == user_id, UserTokenTable.provider == provider, UserTokenTable.is_active)
            token = (await db.execute(stmt)).scalars().first()
            if not token:
                msg = f"No active {provider} token found for user {user_id}"
                raise ValueError(msg)
            provider_impl = get_calendar_provider_for_token(token)
            if not provider_impl:
                msg = f"Unsupported provider: {provider}"
                raise ValueError(msg)
            return await provider_impl.delete_event(external_event_id)

    async def check_conflicts(self, user_id: str, start_time: str, end_time: str) -> dict:
        """Checks for conflicts in the user's calendar for a given time range."""
        from datetime import datetime
        try:
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except ValueError:
            return {"has_conflicts": False, "conflicts": [], "error": "Invalid time format"}
        async with get_db_context() as db:
            stmt = select(UserTokenTable).where(UserTokenTable.user_id == user_id, UserTokenTable.is_active)
            tokens = (await db.execute(stmt)).scalars().all()
            all_busy = []
            for token in tokens:
                provider_impl = get_calendar_provider_for_token(token)
                if provider_impl:
                    busy = await provider_impl.get_busy_windows(db, start, end)
                    all_busy.extend(busy)
            conflicts = []
            for slot in all_busy:
                slot_start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
                slot_end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00"))
                if start < slot_end and end > slot_start:
                    conflicts.append(slot)
            return {"has_conflicts": len(conflicts) > 0, "conflicts": conflicts}

async def sync_calendar_for_user(db: AsyncSession, user_id: str) -> None:
    await CalendarSyncService().sync_calendar_for_user(db, user_id)

async def invalidate_user_calendar_busy_cache(user_id: str) -> None:
    await CalendarSyncService().invalidate_user_calendar_busy_cache(user_id)
