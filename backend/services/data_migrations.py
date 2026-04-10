import logging
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import EventTypeTable

logger = logging.getLogger(__name__)


async def migrate_event_type_buffer_defaults(
    db: AsyncSession,
    batch_size: int = 100,
) -> int:
    """Migrate existing event types to a safe buffer default value.

    Sets buffer_before_minutes and buffer_after_minutes to 0 for rows that
    predate these fields or whose values are NULL.
    """

    stmt = (
        select(EventTypeTable)
        .where(
            or_(
                EventTypeTable.buffer_before_minutes.is_(None),
                EventTypeTable.buffer_after_minutes.is_(None),
            )
        )
        .limit(batch_size)
    )

    event_types = (await db.execute(stmt)).scalars().all()
    if not event_types:
        return 0

    updated = 0
    for event_type in event_types:
        changed = False
        if event_type.buffer_before_minutes is None:
            event_type.buffer_before_minutes = 0
            changed = True
        if event_type.buffer_after_minutes is None:
            event_type.buffer_after_minutes = 0
            changed = True
        if changed:
            updated += 1

    if updated:
        await db.commit()
        logger.info(
            "Migrated %s event_type record(s) to default buffer values.",
            updated,
        )

    return updated


async def migrate(
    db: AsyncSession,
    batch_size: int = 100,
) -> int:
    """Entrypoint compatible with migration runner tests."""
    return await migrate_event_type_buffer_defaults(db, batch_size=batch_size)
