"""
Dead Letter Queue (DLQ) Service

Handles failed tasks that need retry or manual resolution.
Provides monitoring, retry logic, and resolution workflows.
"""
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import DeadLetterQueueItem
from backend.utils.db import AsyncSessionLocal
from backend.utils.logger import get_logger

logger = get_logger(__name__)
MAX_RETRIES = 3
RETRY_DELAYS = [60, 300, 1800]

class DLQService:
    """Service for managing the Dead Letter Queue."""

    @staticmethod
    async def enqueue(db: AsyncSession, task_id: str, task_type: str, payload: dict[str, Any], error_message: str, error_type: str="unknown", stack_trace: str | None=None, max_retries: int=MAX_RETRIES) -> DeadLetterQueueItem:
        """
        Add a failed task to the DLQ.

        Args:
            task_id: Unique identifier for the task
            task_type: Type of task (e.g., 'booking_automation', 'email_send')
            payload: The original task payload
            error_message: Human-readable error description
            error_type: Classification of the error
            stack_trace: Optional stack trace for debugging
            max_retries: Maximum retry attempts

        Returns:
            The created DLQ item
        """
        next_retry = datetime.now(UTC) + timedelta(seconds=RETRY_DELAYS[0])
        dlq_item = DeadLetterQueueItem(task_id=task_id, task_type=task_type, payload=payload, error_message=error_message, error_type=error_type, stack_trace=stack_trace, max_retries=max_retries, status="pending", next_retry_at=next_retry)
        db.add(dlq_item)
        await db.commit()
        await db.refresh(dlq_item)
        logger.warning("🚨 DLQ: Enqueued failed task %s (%s): %s", task_id, task_type, error_message[:100])
        return dlq_item

    @staticmethod
    async def get_pending_items(db: AsyncSession, limit: int=100) -> list[DeadLetterQueueItem]:
        """Get pending DLQ items that are ready for retry."""
        now = datetime.now(UTC)
        stmt = select(DeadLetterQueueItem).where(and_(DeadLetterQueueItem.status.in_(["pending", "retrying"]), or_(DeadLetterQueueItem.next_retry_at <= now, DeadLetterQueueItem.next_retry_at.is_(None)), DeadLetterQueueItem.retry_count < DeadLetterQueueItem.max_retries)).order_by(DeadLetterQueueItem.created_at).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def mark_retrying(db: AsyncSession, item_id: str) -> None:
        """Mark a DLQ item as currently being retried."""
        stmt = update(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id).values(status="retrying", last_retry_at=datetime.now(UTC))
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def mark_success(db: AsyncSession, item_id: str, resolution: str="auto") -> None:
        """Mark a DLQ item as successfully resolved."""
        now = datetime.now(UTC)
        stmt = update(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id).values(status="resolved", resolution=resolution, resolved_at=now)
        await db.execute(stmt)
        await db.commit()
        logger.info("✅ DLQ: Item %s... resolved (%s)", item_id[:8], resolution)

    @staticmethod
    async def mark_failed(db: AsyncSession, item_id: str, error_message: str) -> bool:
        """
        Mark a retry attempt as failed.
        Returns True if more retries available, False if permanently failed.
        """
        stmt = select(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            return False
        new_retry_count = item.retry_count + 1
        now = datetime.now(UTC)
        if new_retry_count >= item.max_retries:
            stmt = update(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id).values(status="failed", retry_count=new_retry_count, error_message=f"{item.error_message}\nRetry {new_retry_count}: {error_message}", last_retry_at=now)
            await db.execute(stmt)
            await db.commit()
            logger.error("💥 DLQ: Item %s... permanently failed after %s retries", item_id[:8], new_retry_count)
            return False
        delay = RETRY_DELAYS[min(new_retry_count, len(RETRY_DELAYS) - 1)]
        next_retry = now + timedelta(seconds=delay)
        stmt = update(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id).values(status="pending", retry_count=new_retry_count, error_message=f"{item.error_message}\nRetry {new_retry_count}: {error_message}", last_retry_at=now, next_retry_at=next_retry)
        await db.execute(stmt)
        await db.commit()
        logger.info("🔄 DLQ: Item %s... scheduled for retry %s (in %ss)", item_id[:8], new_retry_count, delay)
        return True

    @staticmethod
    async def manual_resolve(db: AsyncSession, item_id: str, user_id: str, resolution: str="manual") -> None:
        """Manually resolve a DLQ item (e.g., after admin intervention)."""
        now = datetime.now(UTC)
        stmt = update(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id).values(status="resolved", resolution=resolution, resolved_at=now, resolved_by=user_id)
        await db.execute(stmt)
        await db.commit()
        logger.info("👤 DLQ: Item %s... manually resolved by %s...", item_id[:8], user_id[:8])

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict[str, int]:
        """Get DLQ statistics."""
        from sqlalchemy import func
        stmt = select(DeadLetterQueueItem.status, func.count().label("count")).group_by(DeadLetterQueueItem.status)
        result = await db.execute(stmt)
        rows = result.all()
        stats = {"total": 0, "pending": 0, "retrying": 0, "failed": 0, "resolved": 0}
        for status, count in rows:
            stats[status] = count
            stats["total"] += count
        return stats

async def process_dlq_retries() -> int:
    """
    Background task to process DLQ retries.
    Called by the worker periodically.

    Returns:
        Number of items processed
    """
    async with AsyncSessionLocal() as db:
        service = DLQService()
        pending = await service.get_pending_items(db, limit=50)
        processed = 0
        for item in pending:
            try:
                await service.mark_retrying(db, item.id)
                success = await service.mark_failed(db, item.id, "Retry not implemented")
                if success:
                    processed += 1
            except Exception as e:
                logger.exception("💥 DLQ: Error processing item %s...: %s", item.id[:8], e)
        return processed
