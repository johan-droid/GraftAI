from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from backend.services.sync_engine import sync_calendar_token


@pytest.mark.unit
async def test_sync_calendar_token_logs_completed_audit_event():
    db = AsyncMock()
    token = SimpleNamespace(user_id="user-1", provider="google")
    provider = SimpleNamespace(name="google", sync=AsyncMock(return_value=3))

    with patch("backend.services.sync_engine.get_calendar_provider_for_token", return_value=provider), \
         patch("backend.services.sync_engine.log_activity", new=AsyncMock()) as mock_log_activity:
        await sync_calendar_token(db, token)

    mock_log_activity.assert_awaited_once()
    kwargs = mock_log_activity.await_args.kwargs
    assert kwargs["action"] == "calendar.sync.completed"
    assert kwargs["user_id"] == "user-1"
    assert kwargs["metadata"]["items_processed"] == 3


@pytest.mark.unit
async def test_sync_calendar_token_logs_failure_audit_event():
    db = AsyncMock()
    token = SimpleNamespace(user_id="user-2", provider="google")
    provider = SimpleNamespace(name="google", sync=AsyncMock(side_effect=RuntimeError("boom")))

    with patch("backend.services.sync_engine.get_calendar_provider_for_token", return_value=provider), \
         patch("backend.services.sync_engine.log_activity", new=AsyncMock()) as mock_log_activity:
        await sync_calendar_token(db, token)

    mock_log_activity.assert_awaited_once()
    kwargs = mock_log_activity.await_args.kwargs
    assert kwargs["action"] == "calendar.sync.failed"
    assert kwargs["status"] == "failure"
    db.rollback.assert_awaited_once()


@pytest.mark.unit
async def test_sync_calendar_token_logs_skipped_provider_audit_event():
    db = AsyncMock()
    token = SimpleNamespace(user_id="user-3", provider="unknown")

    with patch("backend.services.sync_engine.get_calendar_provider_for_token", return_value=None), \
         patch("backend.services.sync_engine.log_activity", new=AsyncMock()) as mock_log_activity:
        await sync_calendar_token(db, token)

    mock_log_activity.assert_awaited_once()
    kwargs = mock_log_activity.await_args.kwargs
    assert kwargs["action"] == "calendar.sync.skipped"
    assert kwargs["status"] == "skipped"
    assert kwargs["resource_id"] == "unknown"
