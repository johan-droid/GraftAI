import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytz
from sqlalchemy import select

from backend.models.tables import UserTable, EventTypeTable, EventTable, BookingTable
from backend.services.bookings import (
    create_public_booking,
    list_monthly_availability,
)
from backend.utils.cache import get_cache
from backend.utils.db import AsyncSessionLocal


async def create_test_user(db):
    user = UserTable(
        email="availability@test.local",
        username="availability_user",
        timezone="UTC",
        hashed_password="test",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_test_event_type(db, user, availability=None, minimum_notice=0):
    event_type = EventTypeTable(
        user_id=user.id,
        name="Test Meeting",
        slug="test-meeting",
        duration_minutes=60,
        is_public=True,
        availability=availability or {"tuesday": ["15:00-16:00"]},
        exceptions=[],
        minimum_notice_minutes=minimum_notice,
        buffer_before_minutes=0,
        buffer_after_minutes=0,
    )
    db.add(event_type)
    await db.commit()
    await db.refresh(event_type)
    return event_type


@pytest.mark.asyncio
async def test_race_condition_two_simultaneous_bookings():
    async with AsyncSessionLocal() as db:
        user = await create_test_user(db)
        event_type = await create_test_event_type(db, user)

        slot = datetime.fromisoformat("2025-04-15T15:00:00+00:00")
        payload = {
            "full_name": "Test User",
            "email": "test1@example.com",
            "start_time": slot,
            "end_time": slot + timedelta(hours=1),
            "time_zone": "UTC",
        }

        async def make_booking(email):
            local_payload = payload.copy()
            local_payload["email"] = email
            try:
                booking = await create_public_booking(db, user, event_type, local_payload)
                return booking
            except ValueError as exc:
                return exc

        booking1, booking2 = await asyncio.gather(
            make_booking("first@example.com"),
            make_booking("second@example.com"),
        )

        results = [booking1, booking2]
        successes = [r for r in results if isinstance(r, BookingTable)]
        failures = [r for r in results if isinstance(r, Exception)]

        assert len(successes) == 1
        assert len(failures) == 1
        assert isinstance(failures[0], ValueError)


@pytest.mark.asyncio
async def test_respects_calendar_busy_times():
    async with AsyncSessionLocal() as db:
        user = await create_test_user(db)
        event_type = await create_test_event_type(db, user)

        busy_start = datetime.fromisoformat("2025-04-15T15:00:00+00:00")
        busy_end = busy_start + timedelta(hours=1)
        busy_event = EventTable(
            user_id=user.id,
            event_type_id=event_type.id,
            external_id="busy-event",
            title="Busy Slot",
            description="Calendar conflict",
            start_time=busy_start,
            end_time=busy_end,
            source="google",
            fingerprint="busy-event",
        )
        db.add(busy_event)
        await db.commit()

        availability = await list_monthly_availability(db, user, event_type, "2025-04")
        all_slots = [slot for day_slots in availability.values() for slot in day_slots]

        assert "2025-04-15 03:00 PM" not in all_slots


def convert_to_timezone(value: str, target_timezone: str) -> str:
    dt = datetime.fromisoformat(value)
    tz = pytz.timezone(target_timezone)
    converted = dt.astimezone(tz)
    return converted.isoformat()


def test_timezone_conversion_nyc_to_tokyo():
    organizer_time = "2025-04-15T15:00:00-05:00"
    invitee_time = convert_to_timezone(organizer_time, "Asia/Tokyo")
    assert invitee_time.startswith("2025-04-16T04:00:00")
    assert invitee_time.endswith("+09:00")


@pytest.mark.asyncio
async def test_prevents_double_booking_with_select_for_update():
    async with AsyncSessionLocal() as db:
        user = await create_test_user(db)
        event_type = await create_test_event_type(db, user)

        slot = datetime.fromisoformat("2025-04-16T15:00:00+00:00")
        payload = {
            "full_name": "Lock Test",
            "email": "lock@example.com",
            "start_time": slot,
            "end_time": slot + timedelta(hours=1),
            "time_zone": "UTC",
        }

        booking = await create_public_booking(db, user, event_type, payload)
        assert booking.id is not None

        async with db.begin():
            stmt = select(BookingTable).where(BookingTable.start_time == slot).with_for_update()
            result = await db.execute(stmt)
            locked = result.scalars().first()
            assert locked is not None
            assert locked.id == booking.id


@pytest.mark.asyncio
async def test_respects_minimum_notice():
    async with AsyncSessionLocal() as db:
        user = await create_test_user(db)
        event_type = await create_test_event_type(db, user, minimum_notice=24 * 60)

        today = datetime.now(timezone.utc)
        day = today.strftime("%Y-%m")
        availability = await list_monthly_availability(db, user, event_type, day)

        # No slots within the next 24 hours should be returned.
        for day_key, day_slots in availability.items():
            for slot in day_slots:
                slot_dt = datetime.strptime(slot, "%Y-%m-%d %I:%M %p")
                assert slot_dt.replace(tzinfo=timezone.utc) > today + timedelta(hours=24)


@pytest.mark.asyncio
async def test_caches_availability_with_ttl():
    async with AsyncSessionLocal() as db:
        user = await create_test_user(db)
        event_type = await create_test_event_type(db, user)

        month = "2025-04"
        availability = await list_monthly_availability(db, user, event_type, month)
        cache_key = f"availability:{user.id}:{event_type.slug}:{month}:default"
        cached = await get_cache(cache_key)

        assert cached == availability
