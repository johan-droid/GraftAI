"""
Dead Letter Queue (DLQ) Service

Handles failed tasks that need retry or manual resolution.
Provides monitoring, retry logic, and resolution workflows.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_

from backend.models.tables import DeadLetterQueueItem
from backend.utils.logger import get_logger
from backend.utils.db import AsyncSessionLocal

logger = get_logger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [60, 300, 1800]  # 1min, 5min, 30min


class DLQService:
    """Service for managing the Dead Letter Queue."""

    @staticmethod
    async def enqueue(
        db: AsyncSession,
        task_id: str,
        task_type: str,
        payload: Dict[str, Any],
        error_message: str,
        error_type: str = "unknown",
        stack_trace: Optional[str] = None,
        max_retries: int = MAX_RETRIES,
    ) -> DeadLetterQueueItem:
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
        # Calculate next retry time
        next_retry = datetime.now(timezone.utc) + timedelta(seconds=RETRY_DELAYS[0])

        dlq_item = DeadLetterQueueItem(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            max_retries=max_retries,
            status="pending",
            next_retry_at=next_retry,
        )

        db.add(dlq_item)
        await db.commit()
        await db.refresh(dlq_item)

        logger.warning(
            f"🚨 DLQ: Enqueued failed task {task_id} ({task_type}): {error_message[:100]}"
        )

        return dlq_item

    @staticmethod
    async def get_pending_items(
        db: AsyncSession,
        limit: int = 100,
    ) -> List[DeadLetterQueueItem]:
        """Get pending DLQ items that are ready for retry."""
        now = datetime.now(timezone.utc)

        stmt = (
            select(DeadLetterQueueItem)
            .where(
                and_(
                    DeadLetterQueueItem.status.in_(["pending", "retrying"]),
                    or_(
                        DeadLetterQueueItem.next_retry_at <= now,
                        DeadLetterQueueItem.next_retry_at.is_(None),
                    ),
                    DeadLetterQueueItem.retry_count < DeadLetterQueueItem.max_retries,
                )
            )
            .order_by(DeadLetterQueueItem.created_at)
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def mark_retrying(
        db: AsyncSession,
        item_id: str,
    ) -> None:
        """Mark a DLQ item as currently being retried."""
        stmt = (
            update(DeadLetterQueueItem)
            .where(DeadLetterQueueItem.id == item_id)
            .values(
                status="retrying",
                last_retry_at=datetime.now(timezone.utc),
            )
        )

        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def mark_success(
        db: AsyncSession,
        item_id: str,
        resolution: str = "auto",
    ) -> None:
        """Mark a DLQ item as successfully resolved."""
        now = datetime.now(timezone.utc)

        stmt = (
            update(DeadLetterQueueItem)
            .where(DeadLetterQueueItem.id == item_id)
            .values(
                status="resolved",
                resolution=resolution,
                resolved_at=now,
            )
        )

        await db.execute(stmt)
        await db.commit()

        logger.info(f"✅ DLQ: Item {item_id[:8]}... resolved ({resolution})")

    @staticmethod
    async def mark_failed(
        db: AsyncSession,
        item_id: str,
        error_message: str,
    ) -> bool:
        """
        Mark a retry attempt as failed.
        Returns True if more retries available, False if permanently failed.
        """
        # Get current item
        stmt = select(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return False

        new_retry_count = item.retry_count + 1
        now = datetime.now(timezone.utc)

        if new_retry_count >= item.max_retries:
            # Permanently failed
            stmt = (
                update(DeadLetterQueueItem)
                .where(DeadLetterQueueItem.id == item_id)
                .values(
                    status="failed",
                    retry_count=new_retry_count,
                    error_message=f"{item.error_message}\nRetry {new_retry_count}: {error_message}",
                    last_retry_at=now,
                )
            )
            await db.execute(stmt)
            await db.commit()

            logger.error(
                f"💥 DLQ: Item {item_id[:8]}... permanently failed after {new_retry_count} retries"
            )
            return False
        else:
            # Schedule next retry
            delay = RETRY_DELAYS[min(new_retry_count, len(RETRY_DELAYS) - 1)]
            next_retry = now + timedelta(seconds=delay)

            stmt = (
                update(DeadLetterQueueItem)
                .where(DeadLetterQueueItem.id == item_id)
                .values(
                    status="pending",
                    retry_count=new_retry_count,
                    error_message=f"{item.error_message}\nRetry {new_retry_count}: {error_message}",
                    last_retry_at=now,
                    next_retry_at=next_retry,
                )
            )
            await db.execute(stmt)
            await db.commit()

            logger.info(
                f"🔄 DLQ: Item {item_id[:8]}... scheduled for retry {new_retry_count} (in {delay}s)"
            )
            return True

    @staticmethod
    async def manual_resolve(
        db: AsyncSession,
        item_id: str,
        user_id: str,
        resolution: str = "manual",
    ) -> None:
        """Manually resolve a DLQ item (e.g., after admin intervention)."""
        now = datetime.now(timezone.utc)

        stmt = (
            update(DeadLetterQueueItem)
            .where(DeadLetterQueueItem.id == item_id)
            .values(
                status="resolved",
                resolution=resolution,
                resolved_at=now,
                resolved_by=user_id,
            )
        )

        await db.execute(stmt)
        await db.commit()

        logger.info(
            f"👤 DLQ: Item {item_id[:8]}... manually resolved by {user_id[:8]}..."
        )

    @staticmethod
    async def get_stats(db: AsyncSession) -> Dict[str, int]:
        """Get DLQ statistics."""
        from sqlalchemy import func

        stmt = select(DeadLetterQueueItem.status, func.count().label("count")).group_by(
            DeadLetterQueueItem.status
        )

        result = await db.execute(stmt)
        rows = result.all()

        stats = {"total": 0, "pending": 0, "retrying": 0, "failed": 0, "resolved": 0}
        for status, count in rows:
            stats[status] = count
            stats["total"] += count

        return stats


# Background task processor for DLQ retries
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

                # TODO: Implement actual retry logic based on task_type
                # For now, mark as failed to demonstrate the flow
                success = await service.mark_failed(
                    db, item.id, "Retry not implemented"
                )

                if success:
                    processed += 1

            except Exception as e:
                logger.error(f"💥 DLQ: Error processing item {item.id[:8]}...: {e}")

        return processed
