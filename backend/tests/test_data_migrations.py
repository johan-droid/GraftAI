import asyncio
import uuid
from datetime import datetime, timedelta

import pytz
import pytest
from sqlalchemy import func, select

from backend.models.tables import BookingTable, EventTypeTable, UserTable
from backend.services.bookings import create_event_type, create_public_booking
from backend.services.data_migrations import migrate_event_type_buffer_defaults
from backend.utils.db import AsyncSessionLocal


async def _create_test_user(db):
    user = UserTable(
        id=str(uuid.uuid4()),
        email=f"migration-test-{uuid.uuid4().hex[:8]}@example.com",
        username=f"user-{uuid.uuid4().hex[:8]}",
        hashed_password="test-password",
        timezone="UTC",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_event_type_buffer_migration_preserves_existing_records():
    async with AsyncSessionLocal() as db:
        user = await _create_test_user(db)
        event_type = await create_event_type(
            db,
            user.id,
            {
                "name": "Buffer Migration Event",
                "slug": f"buffer-migration-{uuid.uuid4().hex[:8]}",
                "duration_minutes": 60,
            },
        )

        count_before = await db.scalar(select(func.count()).select_from(EventTypeTable))
        migrated = await migrate_event_type_buffer_defaults(db, batch_size=100)
        count_after = await db.scalar(select(func.count()).select_from(EventTypeTable))

        assert count_after == count_before
        assert migrated == 1

        await db.refresh(event_type)
        assert event_type.buffer_before_minutes == 0
        assert event_type.buffer_after_minutes == 0


@pytest.mark.asyncio
async def test_concurrent_booking_creation_during_buffer_migration():
    async with AsyncSessionLocal() as db:
        user = await _create_test_user(db)
        event_type = await create_event_type(
            db,
            user.id,
            {
                "name": "Concurrent Booking Event",
                "slug": f"concurrent-booking-{uuid.uuid4().hex[:8]}",
                "duration_minutes": 60,
            },
        )

    start_base = (
        datetime.now(pytz.UTC) + timedelta(days=1)
    ).replace(hour=10, minute=0, second=0, microsecond=0)

    async def migrate_task():
        async with AsyncSessionLocal() as migration_db:
            return await migrate_event_type_buffer_defaults(migration_db, batch_size=100)

    async def booking_task(offset_hours: int):
        async with AsyncSessionLocal() as booking_db:
            user_obj = await booking_db.get(UserTable, user.id)
            event_type_obj = await booking_db.get(EventTypeTable, event_type.id)
            start_time = start_base + timedelta(hours=offset_hours)
            end_time = start_time + timedelta(minutes=event_type_obj.duration_minutes)
            payload = {
                "full_name": "Concurrent Guest",
                "email": f"guest+{uuid.uuid4().hex[:8]}@example.com",
                "start_time": start_time,
                "end_time": end_time,
            }
            await create_public_booking(booking_db, user_obj, event_type_obj, payload)

    booking_count = 100
    tasks = [asyncio.create_task(migrate_task())]
    tasks += [asyncio.create_task(booking_task(i)) for i in range(booking_count)]

    await asyncio.gather(*tasks)

    async with AsyncSessionLocal() as verify_db:
        final_count = await verify_db.scalar(select(func.count()).select_from(BookingTable))

    assert final_count == booking_count
