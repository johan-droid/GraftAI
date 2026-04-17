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
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.db import get_db
from backend.utils.logger import get_logger
from backend.models.base import Base
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON

logger = get_logger(__name__)


class DLQStatus(Enum):
    """Status of a dead letter queue item."""
    PENDING = "pending"      # Waiting to be processed
    PROCESSING = "processing"  # Currently being retried
    COMPLETED = "completed"   # Successfully processed
    FAILED = "failed"        # Exhausted all retries
    CANCELLED = "cancelled"   # Manually cancelled


class DeadLetterQueueItem(Base):
    """Database model for dead letter queue items."""
    __tablename__ = "dead_letter_queue"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_type = Column(String(50), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    error_message = Column(Text)
    status = Column(String(20), default="pending", index=True)
    
    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    next_retry_at = Column(DateTime, index=True)
    last_error_at = Column(DateTime)
    
    # Processing metadata
    context = Column(JSON)  # Additional context (user_id, booking_id, etc.)
    processor_id = Column(String(100))  # ID of worker processing this item


@dataclass
class DLQItem:
    """Data class representing a dead letter queue item."""
    id: str
    action_type: str
    payload: Dict[str, Any]
    error_message: Optional[str]
    status: str
    max_retries: int
    retry_count: int
    created_at: datetime
    updated_at: datetime
    next_retry_at: Optional[datetime]
    last_error_at: Optional[datetime]
    context: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action_type": self.action_type,
            "payload": self.payload,
            "error_message": self.error_message,
            "status": self.status,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
            "context": self.context,
        }


class DeadLetterQueue:
    """
    Dead Letter Queue for managing failed operations.
    
    Provides:
    - Enqueue failed operations
    - Retry with exponential backoff
    - Queue monitoring and statistics
    - Manual retry/cancel operations
    """
    
    # Exponential backoff delays (in seconds)
    RETRY_DELAYS = [60, 300, 900, 3600, 7200]  # 1min, 5min, 15min, 1hr, 2hr
    
    def __init__(self):
        self._action_handlers: Dict[str, callable] = {}
    
    def register_handler(self, action_type: str, handler: callable):
        """
        Register a handler for a specific action type.
        
        Args:
            action_type: Type of action (e.g., "send_email")
            handler: Async function to process the action
        """
        self._action_handlers[action_type] = handler
        logger.info(f"[DLQ] Registered handler for action: {action_type}")
    
    async def enqueue(
        self,
        action_type: str,
        payload: Dict[str, Any],
        error: str,
        max_retries: int = 3,
        context: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None
    ) -> str:
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
        now = datetime.utcnow()
        
        # Calculate next retry time (first retry after 1 minute)
        next_retry = now + timedelta(seconds=self.RETRY_DELAYS[0])
        
        item = DeadLetterQueueItem(
            id=item_id,
            action_type=action_type,
            payload=payload,
            error_message=error,
            status=DLQStatus.PENDING.value,
            max_retries=max_retries,
            retry_count=0,
            created_at=now,
            updated_at=now,
            next_retry_at=next_retry,
            last_error_at=now,
            context=context or {}
        )
        
        async with get_db() as session:
            session.add(item)
            await session.commit()
        
        logger.info(
            f"[DLQ] Enqueued item {item_id} "
            f"(action: {action_type}, max_retries: {max_retries})"
        )
        
        return item_id
    
    async def dequeue_pending(
        self,
        limit: int = 100,
        db: Optional[AsyncSession] = None
    ) -> List[DLQItem]:
        """
        Get pending items ready for retry.
        
        Args:
            limit: Maximum number of items to return
            db: Database session
            
        Returns:
            List of pending DLQ items
        """
        now = datetime.utcnow()
        
        async with get_db() as session:
            result = await session.execute(
                select(DeadLetterQueueItem)
                .where(
                    and_(
                        DeadLetterQueueItem.status == DLQStatus.PENDING.value,
                        DeadLetterQueueItem.next_retry_at <= now
                    )
                )
                .order_by(DeadLetterQueueItem.next_retry_at)
                .limit(limit)
            )
            
            items = result.scalars().all()
            
            # Mark as processing
            for item in items:
                item.status = DLQStatus.PROCESSING.value
                item.updated_at = now
            
            await session.commit()
            
            return [
                DLQItem(
                    id=item.id,
                    action_type=item.action_type,
                    payload=item.payload,
                    error_message=item.error_message,
                    status=item.status,
                    max_retries=item.max_retries,
                    retry_count=item.retry_count,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    next_retry_at=item.next_retry_at,
                    last_error_at=item.last_error_at,
                    context=item.context,
                )
                for item in items
            ]
    
    async def mark_completed(self, item_id: str):
        """Mark a queue item as successfully completed."""
        async with get_db() as session:
            result = await session.execute(
                select(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if item:
                item.status = DLQStatus.COMPLETED.value
                item.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"[DLQ] Item {item_id} marked as completed")
    
    async def mark_failed(
        self,
        item_id: str,
        error: str,
        retry: bool = True
    ):
        """
        Mark a queue item as failed.
        
        Args:
            item_id: ID of the item
            error: Error message
            retry: Whether to schedule another retry (if retries remain)
        """
        now = datetime.utcnow()
        
        async with get_db() as session:
            result = await session.execute(
                select(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return
            
            item.retry_count += 1
            item.last_error_at = now
            item.error_message = error
            item.updated_at = now
            
            if retry and item.retry_count < item.max_retries:
                # Schedule next retry with exponential backoff
                delay_index = min(item.retry_count - 1, len(self.RETRY_DELAYS) - 1)
                delay = self.RETRY_DELAYS[delay_index]
                item.next_retry_at = now + timedelta(seconds=delay)
                item.status = DLQStatus.PENDING.value
                
                logger.info(
                    f"[DLQ] Item {item_id} scheduled for retry {item.retry_count}/"
                    f"{item.max_retries} in {delay}s"
                )
            else:
                # Exhausted retries
                item.status = DLQStatus.FAILED.value
                logger.warning(
                    f"[DLQ] Item {item_id} failed permanently after "
                    f"{item.retry_count} retries"
                )
            
            await session.commit()
    
    async def process_queue(self, limit: int = 50) -> Dict[str, int]:
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
                logger.error(f"[DLQ] No handler registered for action: {item.action_type}")
                await self.mark_failed(
                    item.id,
                    f"No handler for action type: {item.action_type}",
                    retry=False
                )
                stats["errors"] += 1
                continue
            
            try:
                # Execute the handler
                result = await handler(item.payload)
                
                if result.get("success"):
                    await self.mark_completed(item.id)
                    stats["succeeded"] += 1
                    logger.info(f"[DLQ] Successfully processed item {item.id}")
                else:
                    error = result.get("error", "Unknown error")
                    await self.mark_failed(item.id, error, retry=True)
                    stats["failed"] += 1
                    
            except Exception as e:
                logger.error(f"[DLQ] Error processing item {item.id}: {e}")
                await self.mark_failed(item.id, str(e), retry=True)
                stats["errors"] += 1
        
        return stats
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics."""
        async with get_db() as session:
            # Count by status
            from sqlalchemy import func
            
            result = await session.execute(
                select(
                    DeadLetterQueueItem.status,
                    func.count(DeadLetterQueueItem.id)
                ).group_by(DeadLetterQueueItem.status)
            )
            
            status_counts = {status: count for status, count in result.all()}
            
            # Total count
            total_result = await session.execute(
                select(func.count(DeadLetterQueueItem.id))
            )
            total = total_result.scalar()
            
            # Recent failed items (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_failed = await session.execute(
                select(func.count(DeadLetterQueueItem.id))
                .where(
                    and_(
                        DeadLetterQueueItem.status == DLQStatus.FAILED.value,
                        DeadLetterQueueItem.last_error_at >= yesterday
                    )
                )
            )
            
            return {
                "total": total,
                "by_status": status_counts,
                "recent_failed": recent_failed.scalar(),
                "handlers_registered": list(self._action_handlers.keys()),
            }
    
    async def cancel_item(self, item_id: str) -> bool:
        """Manually cancel a pending item."""
        async with get_db() as session:
            result = await session.execute(
                select(DeadLetterQueueItem).where(
                    and_(
                        DeadLetterQueueItem.id == item_id,
                        DeadLetterQueueItem.status.in_([
                            DLQStatus.PENDING.value,
                            DLQStatus.PROCESSING.value
                        ])
                    )
                )
            )
            item = result.scalar_one_or_none()
            
            if item:
                item.status = DLQStatus.CANCELLED.value
                item.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"[DLQ] Item {item_id} cancelled")
                return True
            
            return False
    
    async def retry_item_now(self, item_id: str) -> bool:
        """Manually retry a failed or pending item immediately."""
        async with get_db() as session:
            result = await session.execute(
                select(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return False
            
            if item.status == DLQStatus.FAILED.value:
                # Reset for another retry cycle
                item.status = DLQStatus.PENDING.value
                item.retry_count = 0
                item.next_retry_at = datetime.utcnow()
                item.updated_at = datetime.utcnow()
            else:
                # Just set to retry now
                item.next_retry_at = datetime.utcnow()
                item.status = DLQStatus.PENDING.value
                item.updated_at = datetime.utcnow()
            
            await session.commit()
            logger.info(f"[DLQ] Item {item_id} scheduled for immediate retry")
            return True
    
    async def cleanup_old_items(self, days: int = 30) -> int:
        """
        Remove old completed/failed items.
        
        Args:
            days: Remove items older than this many days
            
        Returns:
            Number of items removed
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        async with get_db() as session:
            result = await session.execute(
                delete(DeadLetterQueueItem).where(
                    and_(
                        DeadLetterQueueItem.status.in_([
                            DLQStatus.COMPLETED.value,
                            DLQStatus.FAILED.value,
                            DLQStatus.CANCELLED.value
                        ]),
                        DeadLetterQueueItem.updated_at < cutoff
                    )
                )
            )
            await session.commit()
            
            deleted_count = result.rowcount
            logger.info(f"[DLQ] Cleaned up {deleted_count} old items")
            return deleted_count


# Global DLQ instance
_dlq_instance: Optional[DeadLetterQueue] = None


def get_dlq() -> DeadLetterQueue:
    """Get or create global DLQ instance."""
    global _dlq_instance
    if _dlq_instance is None:
        _dlq_instance = DeadLetterQueue()
    return _dlq_instance
