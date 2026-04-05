import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from fastapi import BackgroundTasks

from backend.services import scheduler


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
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow() + timedelta(hours=1),
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

    event_data = {
        "user_id": 2,
        "title": "Test No Conflict",
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow() + timedelta(hours=1),
        "category": "meeting",
        "description": "Test event",
        "color": "#8A2BE2",
        "metadata_payload": {},
        "is_remote": True,
        "status": "confirmed",
    }

    # simulate db.get for user email retrieval
    user_obj = AsyncMock(email="user@example.com")
    db_mock.get.return_value = user_obj

    background_tasks = BackgroundTasks()
    event = await scheduler.create_event(db_mock, event_data, background_tasks=background_tasks)

    db_mock.commit.assert_called_once()
    assert len(background_tasks.tasks) == 2
    assert any(getattr(task, "func", None) == scheduler.sync_event_to_ai for task in background_tasks.tasks)
    assert any(getattr(task, "func", None) == scheduler._safe_notify for task in background_tasks.tasks)
