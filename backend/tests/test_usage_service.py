import pytest
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.usage import increment_usage


class DummyUser:
    def __init__(self):
        self.id = "user-1"
        self.daily_ai_count = 0
        self.daily_sync_count = 0


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
