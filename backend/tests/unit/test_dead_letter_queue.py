"""
Unit tests for Dead Letter Queue implementation.
Tests enqueue, dequeue, retry logic, and cleanup.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.utils.dead_letter_queue import (
    DeadLetterQueue,
    DLQItem,
    get_dlq,
)


def _make_mock_db_session(mock_get_db, execute_result=None):
    mock_session = MagicMock()
    mock_session.commit = AsyncMock(return_value=None)
    if execute_result is not None:
        mock_session.execute = AsyncMock(return_value=execute_result)
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    mock_get_db.return_value = mock_context
    return mock_session


class TestDLQItemModel:
    """Test the DLQItem dataclass."""

    def test_dlq_item_creation(self):
        """Test creating a DLQItem."""
        item = DLQItem(
            id=str(uuid4()),
            action_type="send_email",
            payload={"to": "test@example.com", "subject": "Test"},
            error_message="Timeout",
            status="pending",
            max_retries=3,
            retry_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            next_retry_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            last_error_at=datetime.now(timezone.utc),
            context={"user_id": "user-123"},
        )
        
        assert item.action_type == "send_email"
        assert item.status == "pending"
        assert item.max_retries == 3

    def test_dlq_item_to_dict(self):
        """Test converting DLQItem to dictionary."""
        now = datetime.now(timezone.utc)
        item = DLQItem(
            id="item-123",
            action_type="send_email",
            payload={"to": "test@example.com"},
            error_message="Error",
            status="pending",
            max_retries=3,
            retry_count=1,
            created_at=now,
            updated_at=now,
            next_retry_at=now,
            last_error_at=now,
            context={"user_id": "user-123"},
        )
        
        data = item.to_dict()
        
        assert data["id"] == "item-123"
        assert data["action_type"] == "send_email"
        assert data["status"] == "pending"
        assert "created_at" in data
        assert isinstance(data["created_at"], str)  # ISO format


class TestDeadLetterQueueEnqueue:
    """Test enqueueing items to DLQ."""

    @pytest.fixture
    def dlq(self):
        """Create a fresh DLQ instance."""
        return DeadLetterQueue()

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_enqueue_creates_item(self, mock_get_db, dlq):
        """Test that enqueue creates a DLQ item."""
        mock_session = _make_mock_db_session(mock_get_db)
        
        item_id = await dlq.enqueue(
            action_type="send_email",
            payload={"to": "test@example.com", "subject": "Hello"},
            error="SendGrid timeout",
            max_retries=3,
            context={"user_id": "user-123"},
        )
        
        assert item_id is not None
        assert isinstance(item_id, str)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_enqueue_sets_correct_next_retry(self, mock_get_db, dlq):
        """Test that enqueue sets next retry time correctly."""
        mock_session = _make_mock_db_session(mock_get_db)
        
        before_enqueue = datetime.now(timezone.utc)
        
        await dlq.enqueue(
            action_type="send_sms",
            payload={"to": "+1234567890", "body": "Hello"},
            error="Twilio error",
        )
        
        after_enqueue = datetime.now(timezone.utc)
        
        # Check the item was added with correct next_retry_at
        added_item = mock_session.add.call_args[0][0]
        assert added_item.next_retry_at > before_enqueue
        assert added_item.next_retry_at < after_enqueue + timedelta(minutes=2)


class TestDeadLetterQueueDequeue:
    """Test dequeuing items from DLQ."""

    @pytest.fixture
    def dlq(self):
        """Create a fresh DLQ instance."""
        return DeadLetterQueue()

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_dequeue_pending_returns_ready_items(self, mock_get_db, dlq):
        """Test that dequeue_pending returns items ready for retry."""
        # Create mock items
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.action_type = "send_email"
        mock_item.payload = {"to": "test@example.com"}
        mock_item.error_message = "Error"
        mock_item.status = "pending"
        mock_item.max_retries = 3
        mock_item.retry_count = 0
        mock_item.created_at = datetime.now(timezone.utc)
        mock_item.updated_at = datetime.now(timezone.utc)
        mock_item.next_retry_at = datetime.now(timezone.utc) - timedelta(minutes=1)  # Ready
        mock_item.last_error_at = datetime.now(timezone.utc)
        mock_item.context = {}
        
        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_item]
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        items = await dlq.dequeue_pending(limit=10)
        
        assert len(items) == 1
        assert items[0].id == "item-1"
        assert items[0].action_type == "send_email"

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_dequeue_pending_skips_future_items(self, mock_get_db, dlq):
        """Test that dequeue_pending skips items with future retry time."""
        # Create mock item with future retry time
        mock_item = MagicMock()
        mock_item.next_retry_at = datetime.now(timezone.utc) + timedelta(hours=1)  # Future
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No items returned
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        items = await dlq.dequeue_pending(limit=10)
        
        # Should return empty list since item's retry time is in future
        assert len(items) == 0

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_dequeue_pending_marks_as_processing(self, mock_get_db, dlq):
        """Test that dequeued items are marked as processing."""
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.status = "pending"
        mock_item.next_retry_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        mock_item.action_type = "send_email"
        mock_item.payload = {}
        mock_item.error_message = None
        mock_item.max_retries = 3
        mock_item.retry_count = 0
        mock_item.created_at = datetime.now(timezone.utc)
        mock_item.updated_at = datetime.now(timezone.utc)
        mock_item.last_error_at = None
        mock_item.context = None
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_item]
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        await dlq.dequeue_pending(limit=10)
        
        # Item should be marked as processing
        assert mock_item.status == "processing"
        mock_session.commit.assert_called_once()


class TestDeadLetterQueueRetryLogic:
    """Test DLQ retry logic and exponential backoff."""

    @pytest.fixture
    def dlq(self):
        """Create a fresh DLQ instance."""
        return DeadLetterQueue()

    def test_retry_delays(self, dlq):
        """Test that retry delays are correctly configured."""
        expected_delays = [60, 300, 900, 3600, 7200]  # 1min, 5min, 15min, 1hr, 2hr
        
        assert dlq.RETRY_DELAYS == expected_delays

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_mark_failed_schedules_next_retry(self, mock_get_db, dlq):
        """Test that mark_failed schedules next retry with exponential backoff."""
        # Mock item with 1 previous retry
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.retry_count = 1
        mock_item.max_retries = 3
        mock_item.status = "processing"
        mock_item.error_message = ""
        mock_item.last_error_at = None
        mock_item.next_retry_at = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_item
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        await dlq.mark_failed("item-1", "New error", retry=True)
        
        # Should schedule next retry
        assert mock_item.retry_count == 2
        assert mock_item.status == "pending"
        assert mock_item.next_retry_at is not None
        
        # Should be scheduled for ~5 minutes from now (index 1 in RETRY_DELAYS)
        expected_delay = 300  # 5 minutes
        now = datetime.now(timezone.utc)
        assert (mock_item.next_retry_at - now).total_seconds() <= expected_delay + 1

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_mark_failed_permanent_after_max_retries(self, mock_get_db, dlq):
        """Test that items are marked failed permanently after max retries."""
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.retry_count = 2  # Already retried twice
        mock_item.max_retries = 3
        mock_item.status = "processing"
        mock_item.error_message = ""
        mock_item.last_error_at = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_item
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        await dlq.mark_failed("item-1", "Final error", retry=True)
        
        # After max retries, should be marked as failed
        assert mock_item.retry_count == 3
        assert mock_item.status == "failed"

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_mark_completed(self, mock_get_db, dlq):
        """Test marking an item as completed."""
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.status = "processing"
        mock_item.updated_at = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_item
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        await dlq.mark_completed("item-1")
        
        assert mock_item.status == "completed"
        assert mock_item.updated_at is not None
        mock_session.commit.assert_called_once()


class TestDeadLetterQueueProcessing:
    """Test DLQ queue processing."""

    @pytest.fixture
    def dlq(self):
        """Create a fresh DLQ instance."""
        return DeadLetterQueue()

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_process_queue_with_handler(self, mock_get_db, dlq):
        """Test processing queue with registered handler."""
        # Register a handler
        mock_handler = AsyncMock(return_value={"success": True})
        dlq.register_handler("send_email", mock_handler)
        
        # Create mock item
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.action_type = "send_email"
        mock_item.payload = {"to": "test@example.com"}
        
        # Mock dequeue_pending
        dlq.dequeue_pending = AsyncMock(return_value=[
            DLQItem(
                id="item-1",
                action_type="send_email",
                payload={"to": "test@example.com"},
                error_message=None,
                status="pending",
                max_retries=3,
                retry_count=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                next_retry_at=None,
                last_error_at=None,
                context=None,
            )
        ])
        
        dlq.mark_completed = AsyncMock()
        
        stats = await dlq.process_queue(limit=10)
        
        assert stats["processed"] == 1
        assert stats["succeeded"] == 1
        mock_handler.assert_called_once()
        dlq.mark_completed.assert_called_once_with("item-1")

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_process_queue_no_handler(self, mock_get_db, dlq):
        """Test processing queue without registered handler."""
        # No handler registered for "send_email"
        
        dlq.dequeue_pending = AsyncMock(return_value=[
            DLQItem(
                id="item-1",
                action_type="send_email",
                payload={},
                error_message=None,
                status="pending",
                max_retries=3,
                retry_count=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                next_retry_at=None,
                last_error_at=None,
                context=None,
            )
        ])
        
        dlq.mark_failed = AsyncMock()
        
        stats = await dlq.process_queue(limit=10)
        
        assert stats["processed"] == 1
        assert stats["errors"] == 1
        dlq.mark_failed.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_process_queue_handler_failure(self, mock_get_db, dlq):
        """Test processing when handler fails."""
        # Register a failing handler
        mock_handler = AsyncMock(return_value={"success": False, "error": "Handler error"})
        dlq.register_handler("send_email", mock_handler)
        
        dlq.dequeue_pending = AsyncMock(return_value=[
            DLQItem(
                id="item-1",
                action_type="send_email",
                payload={},
                error_message=None,
                status="pending",
                max_retries=3,
                retry_count=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                next_retry_at=None,
                last_error_at=None,
                context=None,
            )
        ])
        
        dlq.mark_failed = AsyncMock()
        
        stats = await dlq.process_queue(limit=10)
        
        assert stats["processed"] == 1
        assert stats["failed"] == 1
        dlq.mark_failed.assert_called_once()


class TestDeadLetterQueueCleanup:
    """Test DLQ cleanup functionality."""

    @pytest.fixture
    def dlq(self):
        """Create a fresh DLQ instance."""
        return DeadLetterQueue()

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_cleanup_old_items(self, mock_get_db, dlq):
        """Test cleaning up old completed items."""
        mock_result = MagicMock()
        mock_result.rowcount = 5  # 5 items deleted
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        deleted_count = await dlq.cleanup_old_items(days=30)
        
        assert deleted_count == 5
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestDeadLetterQueueManualOperations:
    """Test manual DLQ operations."""

    @pytest.fixture
    def dlq(self):
        """Create a fresh DLQ instance."""
        return DeadLetterQueue()

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_cancel_item(self, mock_get_db, dlq):
        """Test cancelling a pending item."""
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.status = "pending"
        mock_item.updated_at = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_item
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        result = await dlq.cancel_item("item-1")
        
        assert result is True
        assert mock_item.status == "cancelled"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_cancel_item_not_found(self, mock_get_db, dlq):
        """Test cancelling a non-existent item."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        result = await dlq.cancel_item("non-existent")
        
        assert result is False

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_retry_item_now(self, mock_get_db, dlq):
        """Test manually retrying an item immediately."""
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.status = "failed"
        mock_item.retry_count = 2
        mock_item.next_retry_at = None
        mock_item.updated_at = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_item
        
        mock_session = _make_mock_db_session(mock_get_db, mock_result)
        
        result = await dlq.retry_item_now("item-1")
        
        assert result is True
        assert mock_item.status == "pending"
        assert mock_item.retry_count == 0  # Reset for new retry cycle
        assert mock_item.next_retry_at is not None


class TestDeadLetterQueueStatistics:
    """Test DLQ statistics."""

    @pytest.fixture
    def dlq(self):
        """Create a fresh DLQ instance."""
        return DeadLetterQueue()

    @pytest.mark.asyncio
    @patch("backend.utils.dead_letter_queue.get_db")
    async def test_get_statistics(self, mock_get_db, dlq):
        """Test getting queue statistics."""
        # Mock count results
        mock_count_result = MagicMock()
        mock_count_result.all.return_value = [
            ("pending", 5),
            ("completed", 10),
            ("failed", 2),
        ]
        
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 17
        
        mock_recent_result = MagicMock()
        mock_recent_result.scalar.return_value = 1
        
        mock_session = _make_mock_db_session(mock_get_db)
        mock_session.execute.side_effect = [
            mock_count_result,
            mock_total_result,
            mock_recent_result,
        ]
        
        stats = await dlq.get_statistics()
        
        assert stats["total"] == 17
        assert stats["by_status"]["pending"] == 5
        assert stats["by_status"]["completed"] == 10
        assert stats["by_status"]["failed"] == 2
        assert stats["recent_failed"] == 1


class TestGlobalDLQInstance:
    """Test the global DLQ instance getter."""

    def test_get_dlq_singleton(self):
        """Test that get_dlq returns a singleton."""
        dlq1 = get_dlq()
        dlq2 = get_dlq()
        
        assert dlq1 is dlq2

    def test_get_dlq_returns_dead_letter_queue(self):
        """Test that get_dlq returns a DeadLetterQueue instance."""
        dlq = get_dlq()
        
        assert isinstance(dlq, DeadLetterQueue)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
