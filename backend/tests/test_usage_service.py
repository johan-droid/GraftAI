import pytest
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services import notifications
from backend.services.usage import increment_usage


class DummyUser:
    def __init__(self):
        self.id = "user-1"
        self.daily_ai_count = 0
        self.daily_sync_count = 0
        self.tier = "free"
        self.email = "test@example.com"
        self.full_name = "Test User"
        self.name = "Test User"
        self.ai_quota_warning_sent = False
        self.sync_quota_warning_sent = False


@pytest.mark.asyncio
async def test_increment_usage_increments_ai_and_commits():
    user = DummyUser()

    scalars = AsyncMock()
    scalars.first.return_value = user

    result = AsyncMock()
    result.scalars.return_value = scalars

    db = AsyncMock(spec=AsyncSession)
    db.execute.return_value = result

    await increment_usage(db, user.id, "ai_messages")

    assert user.daily_ai_count == 1
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_increment_usage_triggers_quota_warning_at_threshold(monkeypatch):
    user = DummyUser()
    user.daily_ai_count = 8

    scalars = AsyncMock()
    scalars.first.return_value = user

    result = AsyncMock()
    result.scalars.return_value = scalars

    db = AsyncMock(spec=AsyncSession)
    db.execute.return_value = result

    mock_notify = AsyncMock()
    monkeypatch.setattr(notifications, "notify_quota_warning", mock_notify)

    await increment_usage(db, user.id, "ai_messages")

    assert user.daily_ai_count == 9
    mock_notify.assert_awaited_once()
    assert user.ai_quota_warning_sent is True


@pytest.mark.asyncio
async def test_increment_usage_does_not_use_begin_context():
    user = DummyUser()

    scalars = AsyncMock()
    scalars.first.return_value = user

    result = AsyncMock()
    result.scalars.return_value = scalars

    db = AsyncMock(spec=AsyncSession)
    db.execute.return_value = result

    await increment_usage(db, user.id, "calendar_syncs")

    assert user.daily_sync_count == 1
    assert db.begin.call_count == 0
