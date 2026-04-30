import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.models.tables import UserTokenTable
from backend.services.integrations.calendar_provider import (
    get_calendar_provider_for_token,
)
from backend.services.audit import log_activity

logger = logging.getLogger(__name__)


async def sync_calendar_token(db: AsyncSession, token_record: UserTokenTable):
    provider = get_calendar_provider_for_token(token_record)
    if not provider:
        logger.warning(
            f"Calendar sync skipped: unsupported provider '{token_record.provider}'"
        )
        await log_activity(
            db,
            action="calendar.sync.skipped",
            user_id=token_record.user_id,
            resource_type="calendar_provider",
            resource_id=token_record.provider,
            status="skipped",
            event_category="calendar",
            severity="warning",
            metadata={"reason": "unsupported_provider"},
        )
        return

    try:
        processed = await provider.sync(db)
        logger.info(
            f"{provider.name} sync completed for user {token_record.user_id}: {processed} item(s) processed."
        )
        await log_activity(
            db,
            action="calendar.sync.completed",
            user_id=token_record.user_id,
            resource_type="calendar_provider",
            resource_id=provider.name,
            status="success",
            event_category="calendar",
            metadata={"items_processed": processed},
        )
    except Exception as e:
        logger.error(
            f"{provider.name} Sync FAILED for user {token_record.user_id}: {e}"
        )
        await log_activity(
            db,
            action="calendar.sync.failed",
            user_id=token_record.user_id,
            resource_type="calendar_provider",
            resource_id=provider.name,
            status="failure",
            event_category="calendar",
            severity="error",
            metadata={"error": str(e)},
        )
        await db.rollback()


async def sync_google_events(db: AsyncSession, token_record: UserTokenTable):
    return await sync_calendar_token(db, token_record)


async def sync_ms_graph_events(db: AsyncSession, token_record: UserTokenTable):
    return await sync_calendar_token(db, token_record)


async def sync_user_calendar(db: AsyncSession, user_id: str):
    """Straightforward orchestrator without Redis locks or SSE publishing."""
    stmt = select(UserTokenTable).where(
        and_(UserTokenTable.user_id == user_id, UserTokenTable.is_active == True)
    )
    tokens = (await db.execute(stmt)).scalars().all()

    for token in tokens:
        await sync_calendar_token(db, token)
