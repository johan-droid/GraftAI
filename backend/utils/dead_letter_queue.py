"""
Dead Letter Queue (DLQ) for Failed Actions.

Stores failed operations for later retry, ensuring no data is lost
during transient failures or service outages.

Usage:
    # Queue a failed action
    await dlq.enqueue(
        action_type="send_email",
        payload={"to": "user@example.com", "subject": "Hello"},
        error="SendGrid timeout",
        max_retries=3
    )

    # Process queued items
    await dlq.process_queue()
"""
import inspect
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import DeadLetterQueueItem
from backend.utils.db import get_db
from backend.utils.logger import get_logger

logger = get_logger(__name__)

async def _await_if_needed(value):
    if inspect.isawaitable(value):
        return await value
    return value

class DLQStatus(Enum):
    """Status of a dead letter queue item."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DLQItem:
    """Data class representing a dead letter queue item."""
    id: str
    action_type: str
    payload: dict[str, Any]
    error_message: str | None
    status: str
    max_retries: int
    retry_count: int
    created_at: datetime
    updated_at: datetime
    next_retry_at: datetime | None
    last_error_at: datetime | None
    context: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"id": self.id, "action_type": self.action_type, "payload": self.payload, "error_message": self.error_message, "status": self.status, "max_retries": self.max_retries, "retry_count": self.retry_count, "created_at": self.created_at.isoformat() if self.created_at else None, "updated_at": self.updated_at.isoformat() if self.updated_at else None, "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None, "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None, "context": self.context}

class DeadLetterQueue:
    """
    Dead Letter Queue for managing failed operations.

    Provides:
    - Enqueue failed operations
    - Retry with exponential backoff
    - Queue monitoring and statistics
    - Manual retry/cancel operations
    """
    RETRY_DELAYS = [60, 300, 900, 3600, 7200]

    def __init__(self):
        self._action_handlers: dict[str, callable] = {}

    def register_handler(self, action_type: str, handler: callable):
        """
        Register a handler for a specific action type.

        Args:
            action_type: Type of action (e.g., "send_email")
            handler: Async function to process the action
        """
        self._action_handlers[action_type] = handler
        logger.info("[DLQ] Registered handler for action: %s", action_type)

    async def enqueue(self, action_type: str, payload: dict[str, Any], error: str, max_retries: int=3, context: dict[str, Any] | None=None, db: AsyncSession | None=None) -> str:
        """
        Enqueue a failed action for retry.

        Args:
            action_type: Type of action (e.g., "send_email", "send_sms")
            payload: Action payload/data
            error: Error message explaining failure
            max_retries: Maximum number of retry attempts
            context: Additional context (user_id, booking_id, etc.)
            db: Database session (optional, will create new if not provided)

        Returns:
            ID of the queued item
        """
        item_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        next_retry = now + timedelta(seconds=self.RETRY_DELAYS[0])
        item = DeadLetterQueueItem(id=item_id, task_id=item_id, task_type=action_type, payload=payload, error_message=error, status=DLQStatus.PENDING.value, max_retries=max_retries, retry_count=0, created_at=now, updated_at=now, next_retry_at=next_retry, last_retry_at=None)
        async with get_db() as session:
            session.add(item)
            await _await_if_needed(session.commit())
        logger.info("[DLQ] Enqueued item %s (action: %s, max_retries: %s)", item_id, action_type, max_retries)
        return item_id

    async def dequeue_pending(self, limit: int=100, db: AsyncSession | None=None) -> list[DLQItem]:
        """
        Get pending items ready for retry.

        Args:
            limit: Maximum number of items to return
            db: Database session

        Returns:
            List of pending DLQ items
        """
        now = datetime.now(UTC)
        async with get_db() as session:
            result = await _await_if_needed(session.execute(select(DeadLetterQueueItem).where(and_(DeadLetterQueueItem.status == DLQStatus.PENDING.value, DeadLetterQueueItem.next_retry_at <= now)).order_by(DeadLetterQueueItem.next_retry_at).limit(limit)))
            items = result.scalars().all()
            for item in items:
                item.status = DLQStatus.PROCESSING.value
                item.updated_at = now
            await _await_if_needed(session.commit())
            return [DLQItem(id=item.id, action_type=item.__dict__.get("task_type") if item.__dict__.get("task_type") is not None else item.__dict__.get("action_type"), payload=item.payload, error_message=item.error_message, status=item.status, max_retries=item.max_retries, retry_count=item.retry_count, created_at=item.created_at, updated_at=item.updated_at, next_retry_at=item.next_retry_at, last_error_at=item.__dict__.get("last_retry_at") if item.__dict__.get("last_retry_at") is not None else item.__dict__.get("last_error_at"), context=None) for item in items]

    async def mark_completed(self, item_id: str):
        """Mark a queue item as successfully completed."""
        async with get_db() as session:
            result = await _await_if_needed(session.execute(select(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id)))
            item = result.scalar_one_or_none()
            if item:
                item.status = DLQStatus.COMPLETED.value
                item.updated_at = datetime.now(UTC)
                await _await_if_needed(session.commit())
                logger.info("[DLQ] Item %s marked as completed", item_id)

    async def mark_failed(self, item_id: str, error: str, retry: bool=True):
        """
        Mark a queue item as failed.

        Args:
            item_id: ID of the item
            error: Error message
            retry: Whether to schedule another retry (if retries remain)
        """
        now = datetime.now(UTC)
        async with get_db() as session:
            result = await _await_if_needed(session.execute(select(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id)))
            item = result.scalar_one_or_none()
            if not item:
                return
            item.retry_count += 1
            item.last_retry_at = now
            item.error_message = error
            item.updated_at = now
            if retry and item.retry_count < item.max_retries:
                delay_index = min(item.retry_count - 1, len(self.RETRY_DELAYS) - 1)
                delay = self.RETRY_DELAYS[delay_index]
                item.next_retry_at = now + timedelta(seconds=delay)
                item.status = DLQStatus.PENDING.value
                logger.info("[DLQ] Item %s scheduled for retry %s/%s in %ss", item_id, item.retry_count, item.max_retries, delay)
            else:
                item.status = DLQStatus.FAILED.value
                logger.warning("[DLQ] Item %s failed permanently after %s retries", item_id, item.retry_count)
            await _await_if_needed(session.commit())

    async def process_queue(self, limit: int=50) -> dict[str, int]:
        """
        Process pending items in the queue.

        Args:
            limit: Maximum number of items to process

        Returns:
            Statistics dict with counts
        """
        stats = {"processed": 0, "succeeded": 0, "failed": 0, "errors": 0}
        items = await self.dequeue_pending(limit=limit)
        for item in items:
            stats["processed"] += 1
            handler = self._action_handlers.get(item.action_type)
            if not handler:
                logger.error("[DLQ] No handler registered for action: %s", item.action_type)
                await self.mark_failed(item.id, f"No handler for action type: {item.action_type}", retry=False)
                stats["errors"] += 1
                continue
            try:
                result = await handler(item.payload)
                if result.get("success"):
                    await self.mark_completed(item.id)
                    stats["succeeded"] += 1
                    logger.info("[DLQ] Successfully processed item %s", item.id)
                else:
                    error = result.get("error", "Unknown error")
                    await self.mark_failed(item.id, error, retry=True)
                    stats["failed"] += 1
            except Exception as e:
                logger.exception("[DLQ] Error processing item %s: %s", item.id, e)
                await self.mark_failed(item.id, str(e), retry=True)
                stats["errors"] += 1
        return stats

    async def get_statistics(self) -> dict[str, Any]:
        """Get queue statistics."""
        async with get_db() as session:
            from sqlalchemy import func
            result = await _await_if_needed(session.execute(select(DeadLetterQueueItem.status, func.count(DeadLetterQueueItem.id)).group_by(DeadLetterQueueItem.status)))
            status_counts = dict(result.all())
            total_result = await _await_if_needed(session.execute(select(func.count(DeadLetterQueueItem.id))))
            total = total_result.scalar()
            yesterday = datetime.now(UTC) - timedelta(days=1)
            recent_failed = await _await_if_needed(session.execute(select(func.count(DeadLetterQueueItem.id)).where(and_(DeadLetterQueueItem.status == DLQStatus.FAILED.value, DeadLetterQueueItem.last_retry_at >= yesterday))))
            return {"total": total, "by_status": status_counts, "recent_failed": recent_failed.scalar(), "handlers_registered": list(self._action_handlers.keys())}

    async def cancel_item(self, item_id: str) -> bool:
        """Manually cancel a pending item."""
        async with get_db() as session:
            result = await _await_if_needed(session.execute(select(DeadLetterQueueItem).where(and_(DeadLetterQueueItem.id == item_id, DeadLetterQueueItem.status.in_([DLQStatus.PENDING.value, DLQStatus.PROCESSING.value])))))
            item = result.scalar_one_or_none()
            if item:
                item.status = DLQStatus.CANCELLED.value
                item.updated_at = datetime.now(UTC)
                await _await_if_needed(session.commit())
                logger.info("[DLQ] Item %s cancelled", item_id)
                return True
            return False

    async def retry_item_now(self, item_id: str) -> bool:
        """Manually retry a failed or pending item immediately."""
        async with get_db() as session:
            result = await _await_if_needed(session.execute(select(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id)))
            item = result.scalar_one_or_none()
            if not item:
                return False
            if item.status == DLQStatus.FAILED.value:
                item.status = DLQStatus.PENDING.value
                item.retry_count = 0
                item.next_retry_at = datetime.now(UTC)
                item.updated_at = datetime.now(UTC)
            else:
                item.next_retry_at = datetime.now(UTC)
                item.status = DLQStatus.PENDING.value
                item.updated_at = datetime.now(UTC)
            await _await_if_needed(session.commit())
            logger.info("[DLQ] Item %s scheduled for immediate retry", item_id)
            return True

    async def cleanup_old_items(self, days: int=30) -> int:
        """
        Remove old completed/failed items.

        Args:
            days: Remove items older than this many days

        Returns:
            Number of items removed
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        async with get_db() as session:
            result = await _await_if_needed(session.execute(delete(DeadLetterQueueItem).where(and_(DeadLetterQueueItem.status.in_([DLQStatus.COMPLETED.value, DLQStatus.FAILED.value, DLQStatus.CANCELLED.value]), DeadLetterQueueItem.updated_at < cutoff))))
            await _await_if_needed(session.commit())
            deleted_count = result.rowcount
            logger.info("[DLQ] Cleaned up %s old items", deleted_count)
            return deleted_count
_dlq_instance: DeadLetterQueue | None = None

def get_dlq() -> DeadLetterQueue:
    """Get or create global DLQ instance."""
    global _dlq_instance
    if _dlq_instance is None:
        _dlq_instance = DeadLetterQueue()
    return _dlq_instance
