import asyncio
import logging
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTokenTable
from backend.services.audit import log_activity
from backend.services.integrations.calendar_provider import (
    get_calendar_provider_for_token,
)
from backend.utils.db import get_db_context

logger = logging.getLogger(__name__)

async def sync_calendar_token(db: AsyncSession, token_record: UserTokenTable):
    provider = get_calendar_provider_for_token(token_record)
    if not provider:
        logger.warning("Calendar sync skipped: unsupported provider '%s'", token_record.provider)
        await log_activity(db, action="calendar.sync.skipped", user_id=token_record.user_id, resource_type="calendar_provider", resource_id=token_record.provider, status="skipped", event_category="calendar", severity="warning", metadata={"reason": "unsupported_provider"})
        return {"status": "skipped", "provider": token_record.provider, "processed": 0, "reason": "unsupported_provider"}
    try:
        processed = await provider.sync(db)
        logger.info("%s sync completed for user %s: %s item(s) processed.", provider.name, token_record.user_id, processed)
        await log_activity(db, action="calendar.sync.completed", user_id=token_record.user_id, resource_type="calendar_provider", resource_id=provider.name, status="success", event_category="calendar", metadata={"items_processed": processed})
        return {"status": "success", "provider": provider.name, "processed": processed}
    except Exception as e:
        logger.exception("%s Sync FAILED for user %s: %s", provider.name, token_record.user_id, e)
        await log_activity(db, action="calendar.sync.failed", user_id=token_record.user_id, resource_type="calendar_provider", resource_id=provider.name, status="failure", event_category="calendar", severity="error", metadata={"error": str(e)})
        await db.rollback()
        return {"status": "failed", "provider": provider.name, "processed": 0, "reason": str(e)}

async def sync_google_events(db: AsyncSession, token_record: UserTokenTable):
    return await sync_calendar_token(db, token_record)

async def sync_ms_graph_events(db: AsyncSession, token_record: UserTokenTable):
    return await sync_calendar_token(db, token_record)

async def sync_user_calendar(db: AsyncSession, user_id: str):
    """Straightforward orchestrator without Redis locks or SSE publishing."""
    stmt = select(UserTokenTable.id).where(and_(UserTokenTable.user_id == user_id, UserTokenTable.is_active, UserTokenTable.provider.in_(["google", "microsoft", "caldav", "apple"])))
    token_ids = (await db.execute(stmt)).scalars().all()
    if not token_ids:
        return {"total_tokens": 0, "successful_tokens": 0, "failed_tokens": 0, "skipped_tokens": 0, "items_processed": 0, "failures": []}

    async def _sync_token(tid: str):
        async with get_db_context() as session:
            token = (await session.execute(select(UserTokenTable).where(UserTokenTable.id == tid))).scalars().first()
            if token:
                result = await sync_calendar_token(session, token)
                await session.commit()
                return result
            return {"status": "skipped", "provider": "unknown", "processed": 0, "reason": "token_not_found"}
    token_results: list[Any] = await asyncio.gather(*[_sync_token(tid) for tid in token_ids])
    successful = [r for r in token_results if isinstance(r, dict) and r.get("status") == "success"]
    failed = [r for r in token_results if isinstance(r, dict) and r.get("status") == "failed"]
    skipped = [r for r in token_results if isinstance(r, dict) and r.get("status") == "skipped"]
    return {"total_tokens": len(token_ids), "successful_tokens": len(successful), "failed_tokens": len(failed), "skipped_tokens": len(skipped), "items_processed": sum(int(r.get("processed", 0)) for r in successful), "failures": [{"provider": r.get("provider", "unknown"), "reason": r.get("reason", "unknown")} for r in failed]}
