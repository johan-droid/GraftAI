import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.services.bookings import (
    get_user_by_username,
    get_event_type,
    list_monthly_availability,
    create_public_booking,
)
from backend.utils.rate_limit import api_limits, rate_limit
from backend.utils.errors import BookingConflictError, TimezoneError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Public"])


class PublicEventResponse(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: int
    meeting_provider: Optional[str] = None
    username: str
    event_type_slug: str
    timezone: str


class PublicAvailabilityResponse(BaseModel):
    availability: Dict[str, List[str]]


class PublicBookingRequest(BaseModel):
    full_name: str
    email: EmailStr
    start_time: datetime
    end_time: datetime
    questions: Optional[Dict[str, Any]] = None
    time_zone: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PublicBookingConfirmation(BaseModel):
    success: bool
    booking_id: str
    event_id: str
    organizer_start_time: str
    organizer_end_time: str
    invitee_start_time: str
    invitee_end_time: str
    invitee_zone: str
    meeting_url: Optional[str] = None


@router.get("/public/events/{username}/{event_type}", response_model=PublicEventResponse)
async def get_public_event_details(
    username: str,
    event_type: str,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    event_type_obj = await get_event_type(db, user.id, event_type)
    if not event_type_obj or not event_type_obj.is_public:
        raise HTTPException(status_code=404, detail="Event type not found")

    return {
        "title": event_type_obj.name,
        "description": event_type_obj.description,
        "duration_minutes": event_type_obj.duration_minutes,
        "meeting_provider": event_type_obj.meeting_provider,
        "username": user.username,
        "event_type_slug": event_type_obj.slug,
        "timezone": user.timezone or "UTC",
    }


@router.get("/public/events/{username}/{event_type}/availability", response_model=PublicAvailabilityResponse)
async def get_public_event_availability(
    request: Request,
    username: str,
    event_type: str,
    month: str = Query(..., description="Month in YYYY-MM format."),
    time_zone: Optional[str] = Query(None, description="Optional guest timezone."),
    db: AsyncSession = Depends(get_db),
):
    client_id = request.client.host if request.client else "anonymous"
    await rate_limit(client_id, api_limits["availability"])
    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    event_type_obj = await get_event_type(db, user.id, event_type)
    if not event_type_obj or not event_type_obj.is_public:
        raise HTTPException(status_code=404, detail="Event type not found")

    try:
        availability = await list_monthly_availability(db, user, event_type_obj, month, time_zone)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"availability": availability}


@router.post("/public/events/{username}/{event_type}/book", response_model=PublicBookingConfirmation)
async def book_public_event(
    username: str,
    event_type: str,
    payload: PublicBookingRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    event_type_obj = await get_event_type(db, user.id, event_type)
    if not event_type_obj or not event_type_obj.is_public:
        raise HTTPException(status_code=404, detail="Event type not found")

    try:
        booking = await create_public_booking(db, user, event_type_obj, payload.model_dump())
    except BookingConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except (ValidationError, TimezoneError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Booking creation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to create booking.")

    organizer_tz = pytz.timezone(user.timezone or "UTC")
    invitee_tz = pytz.timezone(booking.time_zone or user.timezone or "UTC")

    return {
        "success": True,
        "booking_id": booking.id,
        "event_id": booking.event_id,
        "organizer_start_time": booking.start_time.astimezone(organizer_tz).strftime("%Y-%m-%d %I:%M %p"),
        "organizer_end_time": booking.end_time.astimezone(organizer_tz).strftime("%Y-%m-%d %I:%M %p"),
        "invitee_start_time": booking.start_time.astimezone(invitee_tz).strftime("%Y-%m-%d %I:%M %p"),
        "invitee_end_time": booking.end_time.astimezone(invitee_tz).strftime("%Y-%m-%d %I:%M %p"),
        "invitee_zone": str(invitee_tz),
        "meeting_url": booking.event.meeting_url if booking.event else None,
    }
