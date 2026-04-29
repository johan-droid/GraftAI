"""
Bookings API Routes with AI Automation

Provides endpoints for creating bookings and triggering AI agent automation.
"""

import html
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json
from sqlalchemy import select, and_, text

from backend.utils.db import get_db, get_async_session_maker
from backend.api.deps import get_current_user
from backend.core.redis import (
    cache_set,
    cache_get,
    cache_delete,
    publish_message,
    get_redis,
)
from backend.utils.cache import acquire_lock, invalidate_user_calendar_cache
from backend.models.tables import (
    UserTable,
    BookingTable,
    AIAutomationTable,
    generate_uuid,
)
from backend.services.booking_automation import AutomationResult
from backend.utils.logger import get_logger
from backend.utils.idempotency import (
    check_idempotency_key,
    store_idempotency_key,
    idempotency_key_header,
)
from dateutil import parser as date_parser
from backend.utils.pagination import PaginationParams, get_pagination_params

logger = get_logger(__name__)
router = APIRouter(prefix="/bookings", tags=["bookings"])


# ═══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class BookingCreateRequest(BaseModel):
    """Request to create a new booking"""

    title: str = Field(..., json_schema_extra={"example": "Quarterly business review"}, description="Meeting title")
    description: Optional[str] = Field(
        None,
        json_schema_extra={"example": "Discuss roadmap and action items."},
        description="Meeting description",
    )
    start_time: datetime = Field(
        ..., json_schema_extra={"example": "2026-05-01T14:00:00Z"}, description="Start time (ISO format with timezone)"
    )
    duration_minutes: int = Field(
        30, gt=0, json_schema_extra={"example": 60}, description="Duration in minutes"
    )
    attendees: list[str] = Field(
        ..., json_schema_extra={"example": ["alice@example.com", "bob@example.com"]}, description="List of attendee emails"
    )

    @field_validator('attendees')
    @classmethod
    def validate_attendees_emails(cls, v: list[str]) -> list[str]:
        import re
        email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
        for email in v:
            if not email_regex.match(email):
                raise ValueError(f"Invalid email address: {email}")
        return v
    organizer_id: Optional[str] = Field(
        None,
        json_schema_extra={"example": "user_1234"},
        description="Organizer user ID",
    )
    location: Optional[str] = Field(
        None, json_schema_extra={"example": "Conference Room A"}, description="Meeting location"
    )
    meeting_type: str = Field(
        "consultation", json_schema_extra={"example": "strategy"}, description="Type of meeting"
    )

    model_config = ConfigDict(extra='forbid')

    @field_validator('title', 'description', 'location', 'meeting_type', mode='before')
    @classmethod
    def sanitize_html(cls, v: str | None) -> str | None:
        """Neutralizes malicious script tags into harmless plain text."""
        import re
        if v is None:
            return v
        # basic escaping
        escaped = html.escape(v.strip())
        # strip out dangerous attributes like onerror
        return re.sub(r'(?i)(on[a-z]+)=', 'data-stripped-attr=', escaped)

    @field_validator('start_time', mode='before')
    @classmethod
    def ensure_tz_aware(cls, v: str | datetime) -> datetime:
        """Forces all incoming times to be timezone-aware UTC."""
        if isinstance(v, str):
            try:
                dt = date_parser.parse(v)
            except Exception:
                raise ValueError("Invalid datetime format. Use ISO 8601 format (e.g., 2026-05-01T14:00:00Z)")
        elif isinstance(v, datetime):
            dt = v
        else:
            raise ValueError("Invalid datetime type")
        
        if dt.tzinfo is None:
            raise ValueError("All datetimes must include timezone information (e.g., ending in 'Z' or '+00:00').")
        
        # Normalize to UTC for database storage
        dt_utc = dt.astimezone(timezone.utc)

        if dt_utc < datetime.now(timezone.utc):
            raise ValueError("Booking start time must be in the future.")

        return dt_utc
    
    estimated_value: Optional[float] = Field(
        None, json_schema_extra={"example": 2500.0}, description="Estimated business value"
    )


class BookingCreateResponse(BaseModel):
    """Response after creating booking"""

    status: str
    booking_id: str
    automation: str
    message: str


class AutomationStatusResponse(BaseModel):
    """Automation status for a booking"""

    booking_id: str
    status: str  # pending, in_progress, completed, failed
    automation_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    decision_score: Optional[int] = None
    risk_assessment: Optional[str] = None
    actions_completed: int = 0
    actions_total: int = 0
    current_action: Optional[str] = None
    error: Optional[str] = None


class AutomationResultResponse(BaseModel):
    """Complete automation result"""

    booking_id: str
    status: str
    decision_score: int
    risk_assessment: str
    execution_time_ms: float
    timestamp: str
    agent_decisions: Dict[str, Any]
    actions_executed: list[Dict[str, Any]]
    external_ids: Dict[str, Optional[str]]


class BookingResponse(BaseModel):
    """Response schema for a single booking"""
    id: str
    user_id: str
    full_name: str
    email: str
    time_zone: Optional[str]
    start_time: datetime
    end_time: datetime
    status: str
    automation_status: Optional[str] = "pending"
    decision_score: Optional[int] = 0
    risk_level: Optional[str] = "unknown"
    created_at: datetime
    updated_at: datetime
    metadata_payload: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class BookingUpdateSchema(BaseModel):
    """Schema for updating a booking"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    time_zone: Optional[str] = None
    status: Optional[str] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class BookingRescheduleSchema(BaseModel):
    """Schema for rescheduling a booking"""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None


# ═══════════════════════════════════════════════════════════════════
# AUTOMATION STATE TRACKING
# ═══════════════════════════════════════════════════════════════════

# NOTE: All automation state is stored in Redis for multi-replica consistency
# Removed in-memory _automation_tasks dict to prevent state desync across workers


def _automation_state_key(booking_id: str) -> str:
    return f"automation:status:{booking_id}"


async def _store_automation_state(
    booking_id: str, payload: dict, expire_seconds: int = 3600
) -> None:
    try:
        await cache_set(_automation_state_key(booking_id), payload, expire_seconds)
    except Exception as exc:
        logger.warning(
            "Unable to persist automation state to Redis for booking %s: %s",
            booking_id,
            exc,
        )


async def _load_automation_state(booking_id: str) -> Optional[dict]:
    try:
        return await cache_get(_automation_state_key(booking_id))
    except Exception as exc:
        logger.warning(
            "Unable to load automation state from Redis for booking %s: %s",
            booking_id,
            exc,
        )
        return None


async def _delete_automation_state(booking_id: str) -> None:
    try:
        await cache_delete(_automation_state_key(booking_id))
    except Exception as exc:
        logger.warning(
            "Unable to delete automation state from Redis for booking %s: %s",
            booking_id,
            exc,
        )


def _serialize_automation_result(result: AutomationResult) -> dict:
    return {
        "booking_id": result.booking_id,
        "automation_status": result.automation_status,
        "decision_score": result.decision_score,
        "risk_assessment": result.risk_assessment,
        "execution_time_ms": result.execution_time_ms,
        "timestamp": result.timestamp,
        "agent_decisions": result.agent_decisions,
        "actions_executed": result.actions_executed,
        "external_results": result.external_results,
    }


async def _track_automation_start(
    booking_id: str, task: Optional[asyncio.Task] = None, automation_id: Optional[str] = None
) -> str:
    """Track the start of an automation task (Celery or asyncio)."""
    automation_id = (
        automation_id or f"auto_{booking_id}_{datetime.now(timezone.utc).timestamp()}"
    )

    state = {
        "automation_id": automation_id,
        "status": "in_progress",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "result": None,
        "decision_score": 0,
        "risk_assessment": "unknown",
        "actions_completed": 0,
        "actions_total": 0,
        "current_action": None,
        "error": None,
    }

    # Always use Redis for automation state - no in-memory storage
    # This ensures consistency across multiple backend replicas
    await _store_automation_state(booking_id, state)
    await _publish_automation_update(booking_id, state)
    return automation_id


async def _publish_automation_update(booking_id: str, payload: dict) -> None:
    channel = f"automation:stream:{booking_id}"
    try:
        await publish_message(channel, payload)
    except Exception as exc:
        logger.warning(
            "Unable to publish automation update for booking %s: %s",
            booking_id,
            exc,
        )


async def _persist_automation_result(
    booking_id: str,
    user_id: str,
    result: Optional[AutomationResult] = None,
    automation_id: Optional[str] = None,
    error: Optional[str] = None,
    trigger_source: str = "api",
) -> None:
    session_factory = get_async_session_maker()
    async with session_factory() as session:
        async with session.begin():
            booking_result = await session.execute(
                select(BookingTable)
                .where(BookingTable.id == booking_id)
                .with_for_update()
            )
            booking = booking_result.scalar_one_or_none()

            now = datetime.now(timezone.utc)
            if booking:
                booking.automation_status = (
                    result.automation_status if result else "failed"
                )
                booking.automation_run_at = now
                booking.decision_score = result.decision_score if result else 0
                booking.risk_level = result.risk_assessment if result else "unknown"
                session.add(booking)

            automation_query = select(AIAutomationTable).where(
                AIAutomationTable.booking_id == booking_id,
                AIAutomationTable.user_id == user_id,
            )
            if automation_id:
                automation_query = automation_query.where(
                    AIAutomationTable.id == automation_id
                )
            automation_query = automation_query.order_by(
                AIAutomationTable.created_at.desc()
            )
            automation_result = await session.execute(automation_query)
            automation_record = automation_result.scalars().first()

            actions = result.actions_executed if result else []
            agent_decisions = (
                result.agent_decisions if result else {"error": error or "unknown"}
            )
            fallback_mode = None
            if isinstance(agent_decisions, dict):
                fallback_mode = agent_decisions.get("mode")

            if automation_record is None:
                automation_record = AIAutomationTable(
                    id=automation_id or generate_uuid(),
                    booking_id=booking_id,
                    user_id=user_id,
                    status=result.automation_status if result else "failed",
                    decision_score=result.decision_score if result else 0,
                    risk_assessment=result.risk_assessment if result else "unknown",
                    agent_decisions=agent_decisions,
                    actions_executed=actions,
                    external_results=result.external_results if result else {},
                    execution_time_ms=result.execution_time_ms if result else 0,
                    started_at=now,
                    completed_at=now,
                    error_message=error,
                    fallback_mode=fallback_mode,
                    trigger_source=trigger_source,
                )
                session.add(automation_record)
            else:
                automation_record.status = (
                    result.automation_status if result else "failed"
                )
                automation_record.decision_score = (
                    result.decision_score if result else 0
                )
                automation_record.risk_assessment = (
                    result.risk_assessment if result else "unknown"
                )
                automation_record.agent_decisions = agent_decisions
                automation_record.actions_executed = actions
                automation_record.external_results = (
                    result.external_results if result else {}
                )
                automation_record.execution_time_ms = (
                    result.execution_time_ms if result else 0
                )
                automation_record.completed_at = now
                automation_record.error_message = error
                automation_record.fallback_mode = fallback_mode
                automation_record.trigger_source = trigger_source
                if automation_record.started_at is None:
                    automation_record.started_at = now

            await session.flush()


async def _update_automation_result(
    booking_id: str,
    result: AutomationResult,
    automation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trigger_source: str = "api",
) -> None:
    if user_id is None:
        return

    await _persist_automation_result(
        booking_id=booking_id,
        user_id=user_id,
        result=result,
        automation_id=automation_id,
        trigger_source=trigger_source,
    )

    # Build state payload from result (all data comes from result, not in-memory dict)
    state_payload = {
        "automation_id": automation_id,
        "status": result.automation_status,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "result": _serialize_automation_result(result),
        "decision_score": result.decision_score,
        "risk_assessment": result.risk_assessment,
        "actions_completed": len(result.actions_executed),
        "actions_total": len(result.actions_executed),
        "current_action": None,
        "error": None,
        "done": True,
    }

    await _store_automation_state(booking_id, state_payload)
    await _publish_automation_update(booking_id, state_payload)


async def _update_automation_error(
    booking_id: str,
    error: str,
    automation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trigger_source: str = "api",
) -> None:
    if user_id is None:
        return

    await _persist_automation_result(
        booking_id=booking_id,
        user_id=user_id,
        automation_id=automation_id,
        error=error,
        trigger_source=trigger_source,
    )

    # Build error state payload (no in-memory dict references)
    state_payload = {
        "automation_id": automation_id,
        "status": "failed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "decision_score": 0,
        "risk_assessment": "unknown",
        "actions_completed": 0,
        "actions_total": 0,
        "current_action": None,
        "error": error,
        "done": True,
    }

    await _store_automation_state(booking_id, state_payload)
    await _publish_automation_update(booking_id, state_payload)


# ═══════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════


@router.post(
    "",
    response_model=BookingCreateResponse,
    summary="Create booking and trigger AI automation",
    description="""
    Creates a new booking in the database and triggers AI agent automation asynchronously.
    
    The automation runs in the background and the API returns immediately with
    "automation": "in_progress". Use the /automation endpoint to check status.
    
    The AI agent will:
    1. Analyze attendee reliability and booking characteristics
    2. Decide optimal actions (email, calendar, reminders, tasks)
    3. Execute actions automatically
    4. Store results for tracking
    """,
)
async def create_booking(
    request: Request,
    booking_data: BookingCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
    idempotency_key: Optional[str] = Depends(idempotency_key_header),
) -> BookingCreateResponse:
    """
    Create booking and trigger AI automation

    Args:
        booking_data: Booking details
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user

    Returns:
        Booking creation status with automation tracking
    """
    try:
        logger.info(
            f"📅 API: Creating booking '{booking_data.title}' for user {current_user.id}"
        )

        # Parse start_time and calculate end_time
        start_time = booking_data.start_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        end_time = start_time + timedelta(minutes=booking_data.duration_minutes)

        # Get first attendee info for the booking record

        attendees = getattr(booking_data, "attendees", [])
        if not isinstance(attendees, (list, tuple)):
            attendees = []

        # safely get the first attendee if any exists
        attendee_email = current_user.email
        if attendees and len(attendees) > 0:
            try:
                attendee_email = list(attendees)[0]
            except IndexError:
                pass

        if not attendee_email:
            attendee_email = current_user.email
        attendee_name = attendee_email.split("@")[0] if attendee_email else "Unknown"
        organizer_id = booking_data.organizer_id or current_user.id

        lock_key = (
            f"booking_slot:{organizer_id}:"
            f"{start_time.isoformat()}:{end_time.isoformat()}"
        )
        if not await acquire_lock(lock_key, ttl_seconds=30):
            raise HTTPException(
                status_code=409,
                detail="Requested slot is currently being claimed. Please retry.",
            )

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def ensure_transaction(session: AsyncSession):
            if session.in_transaction():
                async with session.begin_nested():
                    yield
            else:
                async with session.begin():
                    yield

        # Use a single atomic transaction for booking creation + automation tracking.
        try:
            bind = db.get_bind()
            if bind is not None and bind.dialect.name == "postgresql":
                await db.execute(text("SET LOCAL TRANSACTION ISOLATION LEVEL SERIALIZABLE"))

            await db.execute(
                select(UserTable).where(UserTable.id == organizer_id).with_for_update()
            )

            conflict_stmt = (
                select(BookingTable)
                .where(
                    and_(
                        BookingTable.user_id == organizer_id,
                        BookingTable.start_time < end_time,
                        BookingTable.end_time > start_time,
                    )
                )
                .with_for_update()
            )
            existing_conflict = (await db.execute(conflict_stmt)).scalars().first()
            if existing_conflict:
                raise HTTPException(
                    status_code=409,
                    detail="Requested slot is already booked or no longer available.",
                )

            # Check idempotency key for duplicate request prevention.
            if idempotency_key:
                cached_response = await check_idempotency_key(
                    db, idempotency_key, current_user.id, booking_data.model_dump()
                )
                if cached_response:
                    logger.info(
                        f"🔄 Returning cached response for idempotency key: {idempotency_key[:16]}..."
                    )
                    return BookingCreateResponse(**cached_response)

            booking = BookingTable(
                id=generate_uuid(),
                user_id=organizer_id,
                full_name=attendee_name,
                email=attendee_email,
                time_zone="UTC",  # Default, could be enhanced to detect from user prefs
                start_time=start_time,
                end_time=end_time,
                status="confirmed",
                is_reminder_sent=False,
                metadata_payload={
                    "title": booking_data.title,
                    "description": booking_data.description,
                    "attendees": booking_data.attendees,
                    "location": booking_data.location,
                    "meeting_type": booking_data.meeting_type,
                    "estimated_value": booking_data.estimated_value,
                    "duration_minutes": booking_data.duration_minutes,
                },
            )
            db.add(booking)
            await db.flush()

            # Track scheduling usage
            from backend.services.usage import increment_usage
            await increment_usage(db, organizer_id, "scheduling")

            automation_owner_id = organizer_id
            automation_record = AIAutomationTable(
                booking_id=booking.id,
                user_id=automation_owner_id,
                status="in_progress",
                started_at=datetime.now(timezone.utc),
                trigger_source="api",
            )
            db.add(automation_record)
            await db.flush()

            if idempotency_key:
                await store_idempotency_key(
                    db,
                    idempotency_key,
                    current_user.id,
                    booking_data.model_dump(),
                    {
                        "status": "created",
                        "booking_id": booking.id,
                        "automation": "in_progress",
                        "message": "Booking created successfully. AI automation is running in the background.",
                    },
                    201,
                )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e

        await db.refresh(booking)
        await db.refresh(automation_record)
        automation_id = automation_record.id

        logger.info(f"✅ API: Booking created with ID: {booking.id}")

        # CRITICAL FIX: Invalidate calendar cache to prevent stale data
        # This ensures newly created booking appears in subsequent queries
        await invalidate_user_calendar_cache(organizer_id)
        logger.info(f"🗑️ Cache invalidated for user {organizer_id[:8]}...")

        # Trigger AI automation asynchronously with fallback via Celery
        # Celery provides distributed execution, retry capability, and durability
        from backend.tasks.automation_tasks import run_booking_automation_task
        
        # Build attendee data from booking metadata
        attendee_data = None
        if booking.metadata_payload and booking.metadata_payload.get("attendees"):
            attendees = booking.metadata_payload["attendees"]
            if not isinstance(attendees, (list, tuple)):
                attendees = []

            attendee_email_val = booking.email
            if isinstance(attendees, (list, tuple)) and len(attendees) > 0:
                attendee_email_val = list(attendees)[0]

            attendee_data = {
                "email": attendee_email_val,
                "name": booking.full_name,
            }
        
        run_booking_automation_task.delay(
            booking_id=booking.id,
            automation_id=automation_id,
            user_id=automation_owner_id,
            attendee_data=attendee_data,
            booking_data=booking_data.model_dump(),
        )

        # Track automation start in Redis (no task object needed)
        automation_id = await _track_automation_start(
            booking.id, None, automation_id=automation_id
        )

        logger.info(f"🤖 API: Automation queued via Celery (ID: {automation_id})")

        # Return immediately - automation runs via Celery worker
        response_data = {
            "status": "created",
            "booking_id": booking.id,
            "automation": "in_progress",
            "message": "Booking created successfully. AI automation is running in the background.",
        }

        return BookingCreateResponse(**response_data)

    except Exception as e:
        import traceback
        logger.error(f"❌ API: Failed to create booking: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create booking: {str(e)}"
        )


@router.get(
    "",
    response_model=List[BookingResponse],
    summary="List all bookings for current user",
)
async def list_bookings(
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> List[BookingResponse]:
    """List bookings with optional status filter and pagination."""
    stmt = select(BookingTable).where(BookingTable.user_id == current_user.id)
    
    if status:
        stmt = stmt.where(BookingTable.status == status)
        
    stmt = stmt.order_by(BookingTable.start_time.desc())
    
    # We use list return for now to match test_api_bookings.py
    # But we apply limit/offset from pagination
    stmt = stmt.limit(pagination.size).offset((pagination.page - 1) * pagination.size)
    
    result = await db.execute(stmt)
    bookings = result.scalars().all()
    
    return [BookingResponse.model_validate(b) for b in bookings]


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Get details of a specific booking",
)
async def get_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> BookingResponse:
    """Get a single booking by ID."""
    stmt = select(BookingTable).where(
        and_(BookingTable.id == booking_id, BookingTable.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    return BookingResponse.model_validate(booking)


@router.patch(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Update booking details",
)
async def update_booking(
    booking_id: str,
    update_data: BookingUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> BookingResponse:
    """Update booking fields."""
    stmt = select(BookingTable).where(
        and_(BookingTable.id == booking_id, BookingTable.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Update fields if provided
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(booking, key, value)
        
    booking.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(booking)
    
    return BookingResponse.model_validate(booking)


@router.delete(
    "/{booking_id}",
    status_code=204,
    summary="Cancel or delete a booking",
)
async def cancel_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Cancel a booking (soft delete or status change)."""
    stmt = select(BookingTable).where(
        and_(BookingTable.id == booking_id, BookingTable.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    booking.status = "cancelled"
    booking.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    return None


@router.patch(
    "/{booking_id}/reschedule",
    response_model=BookingResponse,
    summary="Reschedule an existing booking",
)
async def reschedule_booking(
    booking_id: str,
    reschedule_data: BookingRescheduleSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> BookingResponse:
    """Change the time of an existing booking."""
    stmt = select(BookingTable).where(
        and_(BookingTable.id == booking_id, BookingTable.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Calculate end time if not provided
    start_time = reschedule_data.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
        
    end_time = reschedule_data.end_time
    if not end_time:
        duration = reschedule_data.duration_minutes
        if not duration:
            # Fallback to existing duration
            old_duration = (booking.end_time - booking.start_time).total_seconds() / 60
            duration = int(old_duration)
        end_time = start_time + timedelta(minutes=duration)
        
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
        
    booking.start_time = start_time
    booking.end_time = end_time
    booking.status = "rescheduled"
    booking.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(booking)
    
    return BookingResponse.model_validate(booking)


@router.get(
    "/{booking_id}/automation",
    response_model=AutomationStatusResponse,
    summary="Get automation status for booking",
    description="""
    Get the current status of AI automation for a specific booking.
    
    Returns:
    - Status: pending, in_progress, completed, failed
    - Progress: actions completed vs total
    - Current action being executed
    - Decision score and risk assessment (when complete)
    - Error details (if failed)
    """,
)
async def get_automation_status(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> AutomationStatusResponse:
    """
    Get automation status for a booking

    Args:
        booking_id: Booking ID to check
        db: Database session
        current_user: Authenticated user

    Returns:
        Current automation status and progress
    """
    try:
        # Always load from Redis for multi-replica consistency
        auto = await _load_automation_state(booking_id)

        if auto:
            result = auto.get("result") or {}
            return AutomationStatusResponse(
                booking_id=booking_id,
                status=auto.get("status", "pending"),
                automation_id=auto.get("automation_id"),
                started_at=auto.get("started_at"),
                completed_at=auto.get("completed_at"),
                decision_score=auto.get("decision_score"),
                risk_assessment=auto.get("risk_assessment"),
                actions_completed=auto.get("actions_completed", 0),
                actions_total=len(result.get("actions_executed", [])) if isinstance(result, dict) else 0,
                current_action=auto.get("current_action"),
                error=auto.get("error"),
            )

        # Check database for completed automations
        db_result = await db.execute(
            select(AIAutomationTable)
            .where(
                AIAutomationTable.booking_id == booking_id,
                AIAutomationTable.user_id == current_user.id,
            )
            .order_by(AIAutomationTable.created_at.desc())
        )
        automation_record = db_result.scalars().first()
        if automation_record:
            actions = automation_record.actions_executed or []
            return AutomationStatusResponse(
                booking_id=booking_id,
                status=automation_record.status,
                automation_id=automation_record.id,
                started_at=automation_record.started_at.isoformat()
                if automation_record.started_at
                else None,
                completed_at=automation_record.completed_at.isoformat()
                if automation_record.completed_at
                else None,
                decision_score=automation_record.decision_score,
                risk_assessment=automation_record.risk_assessment,
                actions_completed=sum(
                    1
                    for action in actions
                    if isinstance(action, dict) and action.get("success")
                ),
                actions_total=len(actions),
                current_action=None,
                error=automation_record.error_message,
            )

        # If not found, return not found
        raise HTTPException(
            status_code=404,
            detail=f"No automation found for booking {booking_id}. "
            f"The automation may not have started yet or the booking doesn't exist.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving automation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{booking_id}/automation/result",
    response_model=AutomationResultResponse,
    summary="Get complete automation result",
    description="""
    Get the complete automation result including:
    - Decision score (0-100)
    - Risk assessment
    - Actions executed with results
    - External IDs (email, calendar, task)
    - Agent decisions and reasoning
    
    Only available when automation is completed.
    """,
)
async def get_automation_result(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> AutomationResultResponse:
    """
    Get complete automation result

    Args:
        booking_id: Booking ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Complete automation result
    """
    try:
        # Always load from Redis for multi-replica consistency
        auto = await _load_automation_state(booking_id)
        result = auto.get("result") if auto else None

        if result:
            result_data = result if isinstance(result, dict) else _serialize_automation_result(result)
            if auto.get("status") not in {"completed", "partial"}:
                raise HTTPException(
                    status_code=404,
                    detail=f"Automation result not yet available for {booking_id}",
                )

            return AutomationResultResponse(
                booking_id=result_data.get("booking_id", booking_id),
                status=result_data.get("automation_status", auto.get("status", "unknown")),
                decision_score=result_data.get("decision_score", 0),
                risk_assessment=result_data.get("risk_assessment", "unknown"),
                execution_time_ms=result_data.get("execution_time_ms", 0),
                timestamp=result_data.get("timestamp", auto.get("completed_at") or auto.get("started_at") or datetime.now(timezone.utc).isoformat()),
                agent_decisions=result_data.get("agent_decisions", {}),
                actions_executed=result_data.get("actions_executed", []),
                external_ids=result_data.get("external_results", {}),
            )

        db_result = await db.execute(
            select(AIAutomationTable)
            .where(
                AIAutomationTable.booking_id == booking_id,
                AIAutomationTable.user_id == current_user.id,
            )
            .order_by(AIAutomationTable.created_at.desc())
        )
        automation_record = db_result.scalars().first()

        if automation_record and automation_record.status in {"completed", "partial"}:
            actions = automation_record.actions_executed or []
            return AutomationResultResponse(
                booking_id=automation_record.booking_id,
                status=automation_record.status,
                decision_score=automation_record.decision_score or 0,
                risk_assessment=automation_record.risk_assessment or "unknown",
                execution_time_ms=automation_record.execution_time_ms or 0,
                timestamp=(
                    automation_record.completed_at or automation_record.created_at
                ).isoformat(),
                agent_decisions=automation_record.agent_decisions or {},
                actions_executed=actions,
                external_ids=automation_record.external_results or {},
            )

        raise HTTPException(
            status_code=404,
            detail=f"No automation result found for booking {booking_id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving automation result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{booking_id}/automation/stream")
async def stream_automation_status(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    Stream automation status updates using Server-Sent Events (SSE).

    This provides real-time updates instead of polling.
    Client connects and receives status updates as they happen.
    """

    async def event_generator():
        last_status = None
        max_attempts = 60  # 2 minutes max (2s intervals)
        attempts = 0
        channel = f"automation:stream:{booking_id}"
        pubsub = None

        async def build_state_payload(state: dict) -> dict:
            return {
                "booking_id": booking_id,
                "automation_id": state.get("automation_id"),
                "status": state.get("status"),
                "decision_score": state.get("decision_score"),
                "risk_assessment": state.get("risk_assessment"),
                "execution_time_ms": state.get("execution_time_ms"),
                "timestamp": state.get("completed_at") or state.get("started_at"),
                "actions_executed": state.get("result", {}).get("actions_executed", []),
                "done": state.get("done", state.get("status") in {"completed", "failed", "partial"}),
                "error": state.get("error"),
            }

        async def load_latest_state() -> Optional[dict]:
            state = await _load_automation_state(booking_id)
            if state:
                return await build_state_payload(state)

            async with get_async_session_maker() as session:
                db_result = await session.execute(
                    select(AIAutomationTable)
                    .where(
                        AIAutomationTable.booking_id == booking_id,
                        AIAutomationTable.user_id == current_user.id,
                    )
                    .order_by(AIAutomationTable.created_at.desc())
                )
                automation_record = db_result.scalars().first()

                if automation_record:
                    return {
                        "booking_id": automation_record.booking_id,
                        "automation_id": automation_record.id,
                        "status": automation_record.status,
                        "decision_score": automation_record.decision_score,
                        "risk_assessment": automation_record.risk_assessment,
                        "execution_time_ms": automation_record.execution_time_ms,
                        "timestamp": (
                            automation_record.completed_at or automation_record.created_at
                        ).isoformat()
                        if automation_record.completed_at or automation_record.created_at
                        else None,
                        "actions_executed": automation_record.actions_executed or [],
                        "done": automation_record.status in {"completed", "failed", "partial"},
                        "error": automation_record.error_message,
                    }
            return None

        try:
            try:
                redis = await get_redis()
                pubsub = redis.pubsub()
                await pubsub.subscribe(channel)
            except Exception as exc:
                logger.warning(
                    "Redis pubsub unavailable for booking stream %s: %s",
                    booking_id,
                    exc,
                )
                pubsub = None

            while attempts < max_attempts:
                if pubsub:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=2
                    )
                    if message and message.get("type") == "message":
                        data = json.loads(message.get("data", "{}"))
                        if data != last_status:
                            last_status = data
                            yield f"data: {json.dumps(data)}\n\n"
                        if data.get("done"):
                            return
                        attempts += 1
                        continue

                state = await load_latest_state()
                if state and state != last_status:
                    last_status = state
                    yield f"data: {json.dumps(state)}\n\n"
                    if state.get("done"):
                        return

                if last_status is None:
                    yield f"data: {json.dumps({'status': 'pending', 'booking_id': booking_id})}\n\n"

                attempts += 1
                await asyncio.sleep(2)

            yield f"data: {json.dumps({'error': 'Stream timeout', 'done': True})}\n\n"
        finally:
            if pubsub:
                try:
                    await pubsub.unsubscribe(channel)
                except Exception:
                    pass
                await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/{booking_id}/automation/retry",
    response_model=BookingCreateResponse,
    summary="Retry failed automation",
    description="Retry automation for a booking that previously failed",
)
async def retry_automation(
    booking_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> BookingCreateResponse:
    """Retry automation for a failed booking.

    This endpoint is a placeholder. Implement retry logic as needed.
    """
    raise HTTPException(status_code=501, detail="Retry automation not implemented")


@router.get(
    "/automation/queue",
    summary="Get automation queue status",
    description="Get status of all running and pending automations",
)
async def get_automation_queue(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get automation queue status

    Args:
        current_user: Authenticated user

    Returns:
        Queue status with counts and details
    """
    try:
        db_result = await db.execute(
            select(AIAutomationTable)
            .where(AIAutomationTable.user_id == current_user.id)
            .order_by(AIAutomationTable.created_at.desc())
        )
        automations = db_result.scalars().all()

        running = sum(
            1 for automation in automations if automation.status == "in_progress"
        )
        completed = sum(
            1 for automation in automations if automation.status == "completed"
        )
        failed = sum(1 for automation in automations if automation.status == "failed")

        recent_tasks = [
            {
                "booking_id": automation.booking_id,
                "status": automation.status,
                "started_at": automation.started_at.isoformat()
                if automation.started_at
                else None,
                "automation_id": automation.id,
                "completed_at": automation.completed_at.isoformat()
                if automation.completed_at
                else None,
            }
            for automation in automations[:10]
        ]

        return {
            "total": len(automations),
            "running": running,
            "completed": completed,
            "failed": failed,
            "recent_tasks": recent_tasks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# WEBHOOK ENDPOINT
# ═══════════════════════════════════════════════════════════════════

# Webhook secret - should be set via environment variable in production
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
AUTOMATION_WEBHOOK_SECRET = os.environ.get(
    "AUTOMATION_WEBHOOK_SECRET", "dev-webhook-secret-change-in-production"
)


@router.post(
    "/webhook/automation-complete",
    summary="Webhook for automation completion",
    description="Webhook called when automation completes (for external integrations). Requires X-Webhook-Secret header.",
)
async def automation_webhook(
    request: Request,
    booking_id: str,
    automation_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Webhook for automation completion

    Args:
        request: FastAPI request object (for header validation)
        booking_id: Booking ID
        automation_id: Automation ID
        status: Completion status
        result: Optional result data

    Returns:
        Acknowledgment
    """
    # Validate webhook secret from header
    webhook_secret = request.headers.get("X-Webhook-Secret")
    if not webhook_secret or webhook_secret != AUTOMATION_WEBHOOK_SECRET:
        logger.warning(
            f"❌ Unauthorized webhook attempt from {request.client.host if request.client else 'unknown'}"
        )
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing X-Webhook-Secret header",
        )

    logger.info(
        f"🔔 Webhook: Automation {automation_id} for {booking_id} completed: {status}"
    )

    db_result = await db.execute(
        select(AIAutomationTable).where(AIAutomationTable.id == automation_id)
    )
    automation_record = db_result.scalars().first()
    if automation_record is None:
        raise HTTPException(
            status_code=404, detail=f"Automation {automation_id} not found"
        )

    payload = result or {}
    automation_record.status = status
    automation_record.decision_score = payload.get(
        "decision_score", automation_record.decision_score
    )
    automation_record.risk_assessment = payload.get(
        "risk_assessment", automation_record.risk_assessment
    )
    automation_record.agent_decisions = payload.get(
        "agent_decisions", automation_record.agent_decisions
    )
    automation_record.actions_executed = payload.get(
        "actions_executed", automation_record.actions_executed
    )
    automation_record.external_results = payload.get(
        "external_results", automation_record.external_results
    )
    automation_record.execution_time_ms = payload.get(
        "execution_time_ms", automation_record.execution_time_ms
    )
    automation_record.completed_at = datetime.now(timezone.utc)
    automation_record.error_message = payload.get(
        "error", automation_record.error_message
    )
    automation_record.trigger_source = "webhook"

    booking_result = await db.execute(
        select(BookingTable).where(BookingTable.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()
    if booking:
        booking.automation_status = status
        booking.automation_run_at = automation_record.completed_at
        booking.decision_score = automation_record.decision_score
        booking.risk_level = automation_record.risk_assessment

    await db.commit()

    return {"status": "acknowledged"}
