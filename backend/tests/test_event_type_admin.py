import pytest
import pytz
from datetime import datetime, timedelta
from sqlalchemy import select

from backend.models.tables import UserTable, EventTypeTable, BookingTable, EventTypeTeamMemberTable
from backend.services.bookings import (
    add_event_type_team_member,
    create_event_type,
    create_public_booking,
    delete_event_type_team_member,
    list_event_type_team_members,
)
from backend.utils.db import AsyncSessionLocal


async def create_test_user(db, username: str, email: str):
    user = UserTable(
        email=email,
        username=username,
        timezone="UTC",
        hashed_password="test",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_event_type_with_availability_and_custom_questions():
    async with AsyncSessionLocal() as db:
        user = await create_test_user(db, "admin_user", "admin@test.local")
        payload = {
            "name": "Premium Strategy Call",
            "slug": "premium-strategy",
            "duration_minutes": 45,
            "availability": {
                "monday": ["10:00-12:00"],
                "wednesday": ["13:00-16:00"],
            },
            "exceptions": ["2025-06-01"],
            "custom_questions": [
                {"id": "company", "question": "Company name", "type": "text", "required": True},
            ],
            "requires_payment": True,
            "payment_amount": 125.0,
            "payment_currency": "USD",
            "team_assignment_method": "round_robin",
        }

        event_type = await create_event_type(db, user.id, payload)
        assert event_type is not None
        assert event_type.availability["monday"] == ["10:00-12:00"]
        assert event_type.exceptions == ["2025-06-01"]
        assert event_type.custom_questions[0]["id"] == "company"
        assert event_type.requires_payment is True
        assert event_type.payment_amount == 125.0


@pytest.mark.asyncio
async def test_public_booking_requires_payment_and_custom_questions():
    async with AsyncSessionLocal() as db:
        user = await create_test_user(db, "merchant_user", "merchant@test.local")
        payload = {
            "name": "Consultation",
            "slug": "consultation",
            "duration_minutes": 60,
            "availability": {"tuesday": ["15:00-16:00"]},
            "exceptions": [],
            "custom_questions": [
                {"id": "phone", "question": "Phone number", "type": "text", "required": True},
            ],
            "requires_payment": True,
            "payment_amount": 200.0,
            "payment_currency": "USD",
        }
        event_type = await create_event_type(db, user.id, payload)

        now_utc = datetime.now(pytz.UTC)
        days_until_tuesday = (1 - now_utc.weekday() + 7) % 7 or 7
        slot = (now_utc + timedelta(days=days_until_tuesday)).replace(hour=15, minute=0, second=0, microsecond=0)
        booking_payload = {
            "full_name": "Test User",
            "email": "customer@example.com",
            "start_time": slot,
            "end_time": (slot + timedelta(minutes=60)),
            "time_zone": "UTC",
            "questions": {"phone": "555-1234"},
            "metadata": {"payment_status": "paid", "payment_verified": True},
        }

        booking = await create_public_booking(db, user, event_type, booking_payload)
        assert booking is not None
        assert booking.status == "confirmed"
        assert booking.questions["phone"] == "555-1234"
        assert booking.metadata_payload["payment"]["payment_status"] == "paid"


@pytest.mark.asyncio
async def test_event_type_team_member_crud():
    async with AsyncSessionLocal() as db:
        owner = await create_test_user(db, "owner_user", "owner@test.local")
        member_user = await create_test_user(db, "team_user", "team@test.local")

        event_type = EventTypeTable(
            user_id=owner.id,
            name="Team Meeting",
            slug="team-meeting",
            duration_minutes=30,
            is_public=True,
        )
        db.add(event_type)
        await db.commit()
        await db.refresh(event_type)

        member = await add_event_type_team_member(
            db,
            owner.id,
            event_type.id,
            member_user.username,
            "first_available",
            1,
        )

        assert member["username"] == member_user.username
        assert member["assignment_method"] == "first_available"
        assert member["priority"] == 1

        members = await list_event_type_team_members(db, owner.id, event_type.id)
        assert len(members) == 1
        assert members[0]["username"] == member_user.username

        deleted = await delete_event_type_team_member(db, owner.id, event_type.id, member["id"])
        assert deleted is True

        members = await list_event_type_team_members(db, owner.id, event_type.id)
        assert len(members) == 0
