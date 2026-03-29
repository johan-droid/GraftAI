import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from backend.services import scheduler
from backend.models.tables import EventTable


@pytest.mark.asyncio
async def test_create_event_overlapping_raises():
    db_mock = AsyncMock()

    # Setup db execute to return conflict
    conflict_result = AsyncMock()

    class DummyScalars:
        def __init__(self, val):
            self._val = val

        def first(self):
            return self._val

    conflict_result.scalars = lambda: DummyScalars(object())
    db_mock.execute = AsyncMock(return_value=conflict_result)

    event_data = {
        "user_id": 1,
        "title": "Test",
        "start_time": datetime.now(timezone.utc),
        "end_time": datetime.now(timezone.utc) + timedelta(hours=1),
        "category": "meeting",
        "description": "Test event",
        "color": "#8A2BE2",
        "metadata_payload": {},
        "is_remote": True,
        "status": "confirmed",
    }

    with pytest.raises(ValueError):
        await scheduler.create_event(db_mock, event_data)


@pytest.mark.asyncio
async def test_create_event_success_commits_and_notify(monkeypatch):
    db_mock = AsyncMock()

    # no conflict
    conflict_result = AsyncMock()

    class DummyScalars:
        def __init__(self, val):
            self._val = val

        def first(self):
            return self._val

    conflict_result.scalars = lambda: DummyScalars(None)
    db_mock.execute = AsyncMock(return_value=conflict_result)

    # stub background sync
    monkeypatch.setattr(scheduler, '_run_sync_and_notify', AsyncMock())

    event_data = {
        "user_id": 2,
        "title": "Test No Conflict",
        "start_time": datetime.now(timezone.utc),
        "end_time": datetime.now(timezone.utc) + timedelta(hours=1),
        "category": "meeting",
        "description": "Test event",
        "color": "#8A2BE2",
        "metadata_payload": {},
        "is_remote": True,
        "status": "confirmed",
    }

    # simulate db.get for user email retrieval
    user_obj = MagicMock()
    user_obj.email = "user@example.com"
    user_obj.google_refresh_token = "some-token"
    user_obj.google_access_token = "acc"
    user_obj.google_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    user_obj.microsoft_refresh_token = None
    user_obj.microsoft_access_token = None
    user_obj.microsoft_token_expires_at = None
    db_mock.get.return_value = user_obj

    # execute
    event = await scheduler.create_event(db_mock, event_data)

    import asyncio
    await asyncio.sleep(0.01)

    db_mock.commit.assert_called_once()
    scheduler._run_sync_and_notify.assert_awaited_once()
