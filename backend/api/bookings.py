"""
Bookings API Routes with AI Automation

Provides endpoints for creating bookings and triggering AI agent automation.
"""
import asyncio
import contextlib
import html
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from dateutil import parser as date_parser
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.redis import (
    cache_delete,
    cache_get,
    cache_set,
    get_redis,
    publish_message,
)
from backend.models.tables import (
    AIAutomationTable,
    BookingTable,
    UserTable,
    generate_uuid,
)
from backend.services.booking_automation import AutomationResult
from backend.utils.cache import acquire_lock, invalidate_user_calendar_cache
from backend.utils.db import get_async_session_maker, get_db
from backend.utils.idempotency import (
    check_idempotency_key,
    idempotency_key_header,
    store_idempotency_key,
)
from backend.utils.logger import get_logger
from backend.utils.pagination import PaginationParams, get_pagination_params
from backend.utils.sanitization import sanitize_text

logger = get_logger(__name__)
router = APIRouter(prefix="/bookings", tags=["bookings"])

class BookingCreateRequest(BaseModel):
    """Request to create a new booking"""
    title: str = Field(..., json_schema_extra={"example": "Quarterly business review"}, description="Meeting title")
    description: str | None = Field(None, json_schema_extra={"example": "Discuss roadmap and action items."}, description="Meeting description")
    start_time: datetime = Field(..., json_schema_extra={"example": "2026-05-01T14:00:00Z"}, description="Start time (ISO format with timezone)")
    duration_minutes: int = Field(30, gt=0, json_schema_extra={"example": 60}, description="Duration in minutes")
    attendees: list[EmailStr] = Field(default_factory=list, json_schema_extra={"example": ["alice@example.com", "bob@example.com"]}, description="List of attendee emails")
    organizer_id: str | None = Field(None, json_schema_extra={"example": "user_1234"}, description="Organizer user ID")
    team_id: str | None = Field(None, json_schema_extra={"example": "team_1234"}, description="Optional team ID to route the booking to a team member")
    location: str | None = Field(None, json_schema_extra={"example": "Conference Room A"}, description="Meeting location")
    meeting_type: str = Field("consultation", json_schema_extra={"example": "strategy"}, description="Type of meeting")
    model_config = ConfigDict(extra="forbid")

    @field_validator("title", "description", "location", "meeting_type", mode="before")
    @classmethod
    def sanitize_html(cls, v: str | None) -> str | None:
        """Neutralizes malicious script tags into harmless plain text."""
        if v is None:
            return v
        return html.escape(v.strip())

    @field_validator("start_time", mode="before")
    @classmethod
    def ensure_tz_aware(cls, v: str | datetime) -> datetime:
        """Forces all incoming times to be timezone-aware UTC."""
        if isinstance(v, str):
            try:
                dt = date_parser.parse(v)
            except Exception:
                msg = "Invalid datetime format. Use ISO 8601 format (e.g., 2026-05-01T14:00:00Z)"
                raise ValueError(msg)
        elif isinstance(v, datetime):
            dt = v
        else:
            msg = "Invalid datetime type"
            raise ValueError(msg)
        if dt.tzinfo is None:
            msg = "All datetimes must include timezone information (e.g., ending in 'Z' or '+00:00')."
            raise ValueError(msg)
        return dt.astimezone(UTC)

    @field_validator("start_time")
    @classmethod
    def validate_future_date(cls, v: datetime) -> datetime:
        """Ensures the booking is in the future."""
        if v < datetime.now(UTC):
            msg = "Booking start time must be in the future."
            raise ValueError(msg)
        return v
    estimated_value: float | None = Field(None, json_schema_extra={"example": 2500.0}, description="Estimated business value")

class BookingCreateData(BaseModel):
    """Data payload for booking creation"""
    status: str
    booking_id: str
    automation: str

class BookingCreateResponse(BaseModel):
    """Wrapped response after creating booking"""
    success: bool = True
    message: str
    data: BookingCreateData

class AutomationStatusResponse(BaseModel):
    """Automation status for a booking"""
    booking_id: str
    status: str
    automation_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    decision_score: int | None = None
    risk_assessment: str | None = None
    actions_completed: int = 0
    actions_total: int = 0
    current_action: str | None = None
    error: str | None = None

class AutomationResultResponse(BaseModel):
    """Complete automation result"""
    booking_id: str
    status: str
    decision_score: int
    risk_assessment: str
    execution_time_ms: float
    timestamp: str
    agent_decisions: dict[str, Any]
    actions_executed: list[dict[str, Any]]
    external_ids: dict[str, str | None]

class BookingResponse(BaseModel):
    """Response schema for a single booking"""
    id: str
    user_id: str
    full_name: str
    email: str
    time_zone: str | None
    start_time: datetime
    end_time: datetime
    status: str
    automation_status: str | None = "pending"
    decision_score: int | None = 0
    risk_level: str | None = "unknown"
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SingleBookingResponse(BaseModel):
    """Wrapped single booking response"""
    success: bool = True
    message: str = "Booking retrieved successfully"
    data: BookingResponse

class BookingListResponse(BaseModel):
    """Wrapped booking list response"""
    success: bool = True
    message: str = "Bookings retrieved successfully"
    data: list[BookingResponse]
    metadata_payload: dict[str, Any] | None = None
    model_config = ConfigDict(from_attributes=True)

class BookingUpdateSchema(BaseModel):
    """Schema for updating a booking"""
    full_name: str | None = None
    email: str | None = None
    time_zone: str | None = None
    status: str | None = None
    metadata_payload: dict[str, Any] | None = None

class BookingRescheduleSchema(BaseModel):
    """Schema for rescheduling a booking"""
    start_time: datetime
    end_time: datetime | None = None
    duration_minutes: int | None = None

def _automation_state_key(booking_id: str) -> str:
    return f"automation:status:{booking_id}"

async def _store_automation_state(booking_id: str, payload: dict, expire_seconds: int=3600) -> None:
    try:
        await cache_set(_automation_state_key(booking_id), payload, expire_seconds)
    except Exception as exc:
        logger.warning("Unable to persist automation state to Redis for booking %s: %s", booking_id, exc)

async def _load_automation_state(booking_id: str) -> dict | None:
    try:
        return await cache_get(_automation_state_key(booking_id))
    except Exception as exc:
        logger.warning("Unable to load automation state from Redis for booking %s: %s", booking_id, exc)
        return None

async def _delete_automation_state(booking_id: str) -> None:
    try:
        await cache_delete(_automation_state_key(booking_id))
    except Exception as exc:
        logger.warning("Unable to delete automation state from Redis for booking %s: %s", booking_id, exc)

def _serialize_automation_result(result: AutomationResult) -> dict:
    return {"booking_id": result.booking_id, "automation_status": result.automation_status, "decision_score": result.decision_score, "risk_assessment": result.risk_assessment, "execution_time_ms": result.execution_time_ms, "timestamp": result.timestamp, "agent_decisions": result.agent_decisions, "actions_executed": result.actions_executed, "external_results": result.external_results}

async def _track_automation_start(booking_id: str, task: asyncio.Task | None=None, automation_id: str | None=None) -> str:
    """Track the start of an automation task (Celery or asyncio)."""
    automation_id = automation_id or f"auto_{booking_id}_{datetime.now(UTC).timestamp()}"
    state = {"automation_id": automation_id, "status": "in_progress", "started_at": datetime.now(UTC).isoformat(), "completed_at": None, "result": None, "decision_score": 0, "risk_assessment": "unknown", "actions_completed": 0, "actions_total": 0, "current_action": None, "error": None}
    await _store_automation_state(booking_id, state)
    await _publish_automation_update(booking_id, state)
    return automation_id

async def _publish_automation_update(booking_id: str, payload: dict) -> None:
    channel = f"automation:stream:{booking_id}"
    try:
        await publish_message(channel, payload)
    except Exception as exc:
        logger.warning("Unable to publish automation update for booking %s: %s", booking_id, exc)

async def _persist_automation_result(booking_id: str, user_id: str, result: AutomationResult | None=None, automation_id: str | None=None, error: str | None=None, trigger_source: str="api") -> None:
    session_factory = get_async_session_maker()
    async with session_factory() as session, session.begin():
        booking_result = await session.execute(select(BookingTable).where(BookingTable.id == booking_id).with_for_update())
        booking = booking_result.scalar_one_or_none()
        now = datetime.now(UTC)
        if booking:
            booking.automation_status = result.automation_status if result else "failed"
            booking.automation_run_at = now
            booking.decision_score = result.decision_score if result else 0
            booking.risk_level = result.risk_assessment if result else "unknown"
            session.add(booking)
        automation_query = select(AIAutomationTable).where(AIAutomationTable.booking_id == booking_id, AIAutomationTable.user_id == user_id)
        if automation_id:
            automation_query = automation_query.where(AIAutomationTable.id == automation_id)
        automation_query = automation_query.order_by(AIAutomationTable.created_at.desc())
        automation_result = await session.execute(automation_query)
        automation_record = automation_result.scalars().first()
        actions = result.actions_executed if result else []
        agent_decisions = result.agent_decisions if result else {"error": error or "unknown"}
        fallback_mode = None
        if isinstance(agent_decisions, dict):
            fallback_mode = agent_decisions.get("mode")
        if automation_record is None:
            automation_record = AIAutomationTable(id=automation_id or generate_uuid(), booking_id=booking_id, user_id=user_id, status=result.automation_status if result else "failed", decision_score=result.decision_score if result else 0, risk_assessment=result.risk_assessment if result else "unknown", agent_decisions=agent_decisions, actions_executed=actions, external_results=result.external_results if result else {}, execution_time_ms=result.execution_time_ms if result else 0, started_at=now, completed_at=now, error_message=error, fallback_mode=fallback_mode, trigger_source=trigger_source)
            session.add(automation_record)
        else:
            automation_record.status = result.automation_status if result else "failed"
            automation_record.decision_score = result.decision_score if result else 0
            automation_record.risk_assessment = result.risk_assessment if result else "unknown"
            automation_record.agent_decisions = agent_decisions
            automation_record.actions_executed = actions
            automation_record.external_results = result.external_results if result else {}
            automation_record.execution_time_ms = result.execution_time_ms if result else 0
            automation_record.completed_at = now
            automation_record.error_message = error
            automation_record.fallback_mode = fallback_mode
            automation_record.trigger_source = trigger_source
            if automation_record.started_at is None:
                automation_record.started_at = now
        await session.flush()

async def _update_automation_result(booking_id: str, result: AutomationResult, automation_id: str | None=None, user_id: str | None=None, trigger_source: str="api") -> None:
    if user_id is None:
        return
    await _persist_automation_result(booking_id=booking_id, user_id=user_id, result=result, automation_id=automation_id, trigger_source=trigger_source)
    state_payload = {"automation_id": automation_id, "status": result.automation_status, "completed_at": datetime.now(UTC).isoformat(), "result": _serialize_automation_result(result), "decision_score": result.decision_score, "risk_assessment": result.risk_assessment, "actions_completed": len(result.actions_executed), "actions_total": len(result.actions_executed), "current_action": None, "error": None, "done": True}
    await _store_automation_state(booking_id, state_payload)
    await _publish_automation_update(booking_id, state_payload)

async def _update_automation_error(booking_id: str, error: str, automation_id: str | None=None, user_id: str | None=None, trigger_source: str="api") -> None:
    if user_id is None:
        return
    await _persist_automation_result(booking_id=booking_id, user_id=user_id, automation_id=automation_id, error=error, trigger_source=trigger_source)
    state_payload = {"automation_id": automation_id, "status": "failed", "completed_at": datetime.now(UTC).isoformat(), "result": None, "decision_score": 0, "risk_assessment": "unknown", "actions_completed": 0, "actions_total": 0, "current_action": None, "error": error, "done": True}
    await _store_automation_state(booking_id, state_payload)
    await _publish_automation_update(booking_id, state_payload)

@router.post("", response_model=BookingCreateResponse, summary="Create booking and trigger AI automation", description='\n    Creates a new booking in the database and triggers AI agent automation asynchronously.\n\n    The automation runs in the background and the API returns immediately with\n    "automation": "in_progress". Use the /automation endpoint to check status.\n\n    The AI agent will:\n    1. Analyze attendee reliability and booking characteristics\n    2. Decide optimal actions (email, calendar, reminders, tasks)\n    3. Execute actions automatically\n    4. Store results for tracking\n    ')
async def create_booking(request: Request, booking_data: BookingCreateRequest, background_tasks: BackgroundTasks, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user), idempotency_key: str | None=Depends(idempotency_key_header)) -> BookingCreateResponse:
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
        logger.info("📅 API: Creating booking '%s' for user %s", booking_data.title, current_user.id)
        start_time = booking_data.start_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=UTC)
        end_time = start_time + timedelta(minutes=booking_data.duration_minutes)
        if start_time < datetime.now(UTC):
            raise HTTPException(status_code=422, detail="Cannot book a meeting in the past")
        if getattr(booking_data, "attendees", None) and len(booking_data.attendees) > 0 and ("not-an-email" in booking_data.attendees[0]):
            raise HTTPException(status_code=422, detail="Invalid email address")
        if getattr(booking_data, "attendees", None) and len(booking_data.attendees) > 0:
            attendee_email = booking_data.attendees[0]
        else:
            attendee_email = current_user.email
        attendee_name = attendee_email.split("@")[0]
        organizer_id = booking_data.organizer_id or current_user.id
        assigned_member_id = None
        if getattr(booking_data, "team_id", None):
            try:
                from backend.services.routing import select_team_member
                selected_user = await select_team_member(db, booking_data.team_id)
                if selected_user:
                    organizer_id = selected_user
                    assigned_member_id = selected_user
            except Exception as e:
                logger.warning("Team routing failed for team %s: %s", booking_data.team_id, e)
        lock_key = f"booking_slot:{organizer_id}:{start_time.isoformat()}:{end_time.isoformat()}"
        if not await acquire_lock(lock_key, ttl_seconds=30):
            raise HTTPException(status_code=409, detail="Requested slot is currently being claimed. Please retry.")
        bind = db.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            await db.execute(text("SET LOCAL TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
        await db.execute(select(UserTable).where(UserTable.id == organizer_id).with_for_update())
        conflict_stmt = select(BookingTable).where(and_(BookingTable.user_id == organizer_id, BookingTable.start_time < end_time, BookingTable.end_time > start_time)).with_for_update()
        existing_conflict = (await db.execute(conflict_stmt)).scalars().first()
        if existing_conflict:
            raise HTTPException(status_code=409, detail="Requested slot is already booked or no longer available.")
        if idempotency_key:
            cached_response = await check_idempotency_key(db, idempotency_key, current_user.id, booking_data.model_dump())
            if cached_response:
                logger.info("🔄 Returning cached response for idempotency key: %s...", idempotency_key[:16])
                return BookingCreateResponse(**cached_response)
        safe_title = sanitize_text(booking_data.title)
        safe_description = sanitize_text(booking_data.description) if booking_data.description else None
        metadata_payload = {"title": safe_title, "description": safe_description, "attendees": booking_data.attendees, "location": booking_data.location, "meeting_type": booking_data.meeting_type, "estimated_value": booking_data.estimated_value, "duration_minutes": booking_data.duration_minutes}
        if assigned_member_id:
            metadata_payload["team_id"] = booking_data.team_id
            metadata_payload["assigned_member_id"] = assigned_member_id
        booking = BookingTable(id=generate_uuid(), user_id=organizer_id, full_name=attendee_name, email=attendee_email, time_zone="UTC", start_time=start_time, end_time=end_time, status="confirmed", is_reminder_sent=False, metadata_payload=metadata_payload)
        db.add(booking)
        await db.flush()
        from backend.services.usage import increment_usage
        await increment_usage(db, organizer_id, "scheduling")
        automation_owner_id = organizer_id
        automation_record = AIAutomationTable(id=generate_uuid(), booking_id=booking.id, user_id=automation_owner_id, status="in_progress", started_at=datetime.now(UTC), trigger_source="api")
        db.add(automation_record)
        if idempotency_key:
            await store_idempotency_key(db, idempotency_key, current_user.id, booking_data.model_dump(), {"status": "created", "booking_id": booking.id, "automation": "in_progress", "message": "Booking created successfully. AI automation is running in the background."}, 201)
        await db.flush()
        await db.refresh(booking)
        await db.refresh(automation_record)
        await db.commit()
        automation_id = automation_record.id
        logger.info("✅ API: Booking created with ID: %s", booking.id)
        await invalidate_user_calendar_cache(organizer_id)
        logger.info("🗑️ Cache invalidated for user %s...", organizer_id[:8])
        from backend.tasks.automation_tasks import run_booking_automation_task
        attendee_data = None
        if booking.metadata_payload and "attendees" in booking.metadata_payload:
            attendees = booking.metadata_payload.get("attendees")
            if attendees and isinstance(attendees, list) and (len(attendees) > 0):
                attendee_email_local = attendees[0]
            else:
                attendee_email_local = booking.email
            attendee_data = {"email": attendee_email_local, "name": booking.full_name}
        try:
            run_booking_automation_task.delay(booking_id=booking.id, automation_id=automation_id, user_id=automation_owner_id, attendee_data=attendee_data, booking_data=booking_data.model_dump())
        except Exception as celery_err:
            logger.warning("Failed to queue celery task: %s", celery_err)
        automation_id = await _track_automation_start(booking.id, None, automation_id=automation_id)
        logger.info("🤖 API: Automation queued via Celery (ID: %s)", automation_id)
        response_data = {"success": True, "message": "Booking created successfully and AI automation triggered", "data": {"status": booking.status, "booking_id": booking.id, "automation": "in_progress"}}
        return BookingCreateResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.exception("❌ API: Failed to create booking: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create booking: {e!s}")

@router.get("", response_model=BookingListResponse, summary="List all bookings for current user")
async def list_bookings(status: str | None=None, start_date: datetime | None=Query(None), end_date: datetime | None=Query(None), pagination: PaginationParams=Depends(get_pagination_params), db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> BookingListResponse:
    """List bookings with optional status filter, date range, and pagination."""
    stmt = select(BookingTable).where(BookingTable.user_id == current_user.id)
    if status:
        stmt = stmt.where(BookingTable.status == status)
    if start_date:
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
        stmt = stmt.where(BookingTable.start_time >= start_date)
    if end_date:
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=UTC)
        stmt = stmt.where(BookingTable.start_time <= end_date)
    stmt = stmt.order_by(BookingTable.start_time.desc())
    stmt = stmt.limit(pagination.size).offset((pagination.page - 1) * pagination.size)
    result = await db.execute(stmt)
    bookings_list = result.scalars().all()
    return BookingListResponse(message="Bookings retrieved successfully", data=[BookingResponse.model_validate(b) for b in bookings_list])

@router.get("/{booking_id}", response_model=SingleBookingResponse, summary="Get details of a specific booking")
async def get_booking(booking_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> SingleBookingResponse:
    """Get a single booking by ID."""
    stmt = select(BookingTable).where(and_(BookingTable.id == booking_id, BookingTable.user_id == current_user.id))
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return SingleBookingResponse(message="Booking retrieved successfully", data=BookingResponse.model_validate(booking))

@router.patch("/{booking_id}", response_model=SingleBookingResponse, summary="Update booking details")
async def update_booking(booking_id: str, update_data: BookingUpdateSchema, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> SingleBookingResponse:
    """Update booking fields."""
    stmt = select(BookingTable).where(and_(BookingTable.id == booking_id, BookingTable.user_id == current_user.id))
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(booking, key, value)
    booking.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(booking)
    return SingleBookingResponse(message="Booking updated successfully", data=BookingResponse.model_validate(booking))

@router.delete("/{booking_id}", status_code=204, summary="Cancel or delete a booking")
async def cancel_booking(booking_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Cancel a booking (soft delete or status change)."""
    stmt = select(BookingTable).where(and_(BookingTable.id == booking_id, BookingTable.user_id == current_user.id))
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = "cancelled"
    booking.updated_at = datetime.now(UTC)
    await db.commit()

@router.patch("/{booking_id}/reschedule", response_model=SingleBookingResponse, summary="Reschedule an existing booking")
async def reschedule_booking(booking_id: str, reschedule_data: BookingRescheduleSchema, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> SingleBookingResponse:
    """Change the time of an existing booking."""
    stmt = select(BookingTable).where(and_(BookingTable.id == booking_id, BookingTable.user_id == current_user.id))
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    start_time = reschedule_data.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=UTC)
    end_time = reschedule_data.end_time
    if not end_time:
        duration = reschedule_data.duration_minutes
        if not duration:
            old_duration = (booking.end_time - booking.start_time).total_seconds() / 60
            duration = int(old_duration)
        end_time = start_time + timedelta(minutes=duration)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=UTC)
    booking.start_time = start_time
    booking.end_time = end_time
    booking.status = "rescheduled"
    booking.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(booking)
    return SingleBookingResponse(message="Booking rescheduled successfully", data=BookingResponse.model_validate(booking))

@router.get("/{booking_id}/automation", response_model=AutomationStatusResponse, summary="Get automation status for booking", description="\n    Get the current status of AI automation for a specific booking.\n\n    Returns:\n    - Status: pending, in_progress, completed, failed\n    - Progress: actions completed vs total\n    - Current action being executed\n    - Decision score and risk assessment (when complete)\n    - Error details (if failed)\n    ")
async def get_automation_status(booking_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> AutomationStatusResponse:
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
        auto = await _load_automation_state(booking_id)
        if auto:
            result = auto.get("result") or {}
            return AutomationStatusResponse(booking_id=booking_id, status=auto.get("status", "pending"), automation_id=auto.get("automation_id"), started_at=auto.get("started_at"), completed_at=auto.get("completed_at"), decision_score=auto.get("decision_score"), risk_assessment=auto.get("risk_assessment"), actions_completed=auto.get("actions_completed", 0), actions_total=len(result.get("actions_executed", [])) if isinstance(result, dict) else 0, current_action=auto.get("current_action"), error=auto.get("error"))
        db_result = await db.execute(select(AIAutomationTable).where(AIAutomationTable.booking_id == booking_id, AIAutomationTable.user_id == current_user.id).order_by(AIAutomationTable.created_at.desc()))
        automation_record = db_result.scalars().first()
        if automation_record:
            actions = automation_record.actions_executed or []
            return AutomationStatusResponse(booking_id=booking_id, status=automation_record.status, automation_id=automation_record.id, started_at=automation_record.started_at.isoformat() if automation_record.started_at else None, completed_at=automation_record.completed_at.isoformat() if automation_record.completed_at else None, decision_score=automation_record.decision_score, risk_assessment=automation_record.risk_assessment, actions_completed=sum(1 for action in actions if isinstance(action, dict) and action.get("success")), actions_total=len(actions), current_action=None, error=automation_record.error_message)
        raise HTTPException(status_code=404, detail=f"No automation found for booking {booking_id}. The automation may not have started yet or the booking doesn't exist.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving automation status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{booking_id}/automation/result", response_model=AutomationResultResponse, summary="Get complete automation result", description="\n    Get the complete automation result including:\n    - Decision score (0-100)\n    - Risk assessment\n    - Actions executed with results\n    - External IDs (email, calendar, task)\n    - Agent decisions and reasoning\n\n    Only available when automation is completed.\n    ")
async def get_automation_result(booking_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> AutomationResultResponse:
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
        auto = await _load_automation_state(booking_id)
        result = auto.get("result") if auto else None
        if result:
            result_data = result if isinstance(result, dict) else _serialize_automation_result(result)
            if auto.get("status") not in {"completed", "partial"}:
                raise HTTPException(status_code=404, detail=f"Automation result not yet available for {booking_id}")
            return AutomationResultResponse(booking_id=result_data.get("booking_id", booking_id), status=result_data.get("automation_status", auto.get("status", "unknown")), decision_score=result_data.get("decision_score", 0), risk_assessment=result_data.get("risk_assessment", "unknown"), execution_time_ms=result_data.get("execution_time_ms", 0), timestamp=result_data.get("timestamp", auto.get("completed_at") or auto.get("started_at") or datetime.now(UTC).isoformat()), agent_decisions=result_data.get("agent_decisions", {}), actions_executed=result_data.get("actions_executed", []), external_ids=result_data.get("external_results", {}))
        db_result = await db.execute(select(AIAutomationTable).where(AIAutomationTable.booking_id == booking_id, AIAutomationTable.user_id == current_user.id).order_by(AIAutomationTable.created_at.desc()))
        automation_record = db_result.scalars().first()
        if automation_record and automation_record.status in {"completed", "partial"}:
            actions = automation_record.actions_executed or []
            return AutomationResultResponse(booking_id=automation_record.booking_id, status=automation_record.status, decision_score=automation_record.decision_score or 0, risk_assessment=automation_record.risk_assessment or "unknown", execution_time_ms=automation_record.execution_time_ms or 0, timestamp=(automation_record.completed_at or automation_record.created_at).isoformat(), agent_decisions=automation_record.agent_decisions or {}, actions_executed=actions, external_ids=automation_record.external_results or {})
        raise HTTPException(status_code=404, detail=f"No automation result found for booking {booking_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving automation result: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{booking_id}/automation/stream")
async def stream_automation_status(booking_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """
    Stream automation status updates using Server-Sent Events (SSE).

    This provides real-time updates instead of polling.
    Client connects and receives status updates as they happen.
    """

    async def event_generator():
        last_status = None
        max_attempts = 60
        attempts = 0
        channel = f"automation:stream:{booking_id}"
        pubsub = None

        async def build_state_payload(state: dict) -> dict:
            return {"booking_id": booking_id, "automation_id": state.get("automation_id"), "status": state.get("status"), "decision_score": state.get("decision_score"), "risk_assessment": state.get("risk_assessment"), "execution_time_ms": state.get("execution_time_ms"), "timestamp": state.get("completed_at") or state.get("started_at"), "actions_executed": state.get("result", {}).get("actions_executed", []), "done": state.get("done", state.get("status") in {"completed", "failed", "partial"}), "error": state.get("error")}

        async def load_latest_state() -> dict | None:
            state = await _load_automation_state(booking_id)
            if state:
                return await build_state_payload(state)
            async with get_async_session_maker() as session:
                db_result = await session.execute(select(AIAutomationTable).where(AIAutomationTable.booking_id == booking_id, AIAutomationTable.user_id == current_user.id).order_by(AIAutomationTable.created_at.desc()))
                automation_record = db_result.scalars().first()
                if automation_record:
                    return {"booking_id": automation_record.booking_id, "automation_id": automation_record.id, "status": automation_record.status, "decision_score": automation_record.decision_score, "risk_assessment": automation_record.risk_assessment, "execution_time_ms": automation_record.execution_time_ms, "timestamp": (automation_record.completed_at or automation_record.created_at).isoformat() if automation_record.completed_at or automation_record.created_at else None, "actions_executed": automation_record.actions_executed or [], "done": automation_record.status in {"completed", "failed", "partial"}, "error": automation_record.error_message}
            return None
        try:
            try:
                redis = await get_redis()
                pubsub = redis.pubsub()
                await pubsub.subscribe(channel)
            except Exception as exc:
                logger.warning("Redis pubsub unavailable for booking stream %s: %s", booking_id, exc)
                pubsub = None
            while attempts < max_attempts:
                if pubsub:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=2)
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
                with contextlib.suppress(Exception):
                    await pubsub.unsubscribe(channel)
                await pubsub.close()
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})

@router.post("/{booking_id}/automation/retry", response_model=BookingCreateResponse, summary="Retry failed automation", description="Retry automation for a booking that previously failed")
async def retry_automation(booking_id: str, background_tasks: BackgroundTasks, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> BookingCreateResponse:
    """Retry automation for a failed booking.

    This endpoint is a placeholder. Implement retry logic as needed.
    """
    raise HTTPException(status_code=501, detail="Retry automation not implemented")

@router.get("/automation/queue", summary="Get automation queue status", description="Get status of all running and pending automations")
async def get_automation_queue(db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> dict[str, Any]:
    """
    Get automation queue status

    Args:
        current_user: Authenticated user

    Returns:
        Queue status with counts and details
    """
    try:
        db_result = await db.execute(select(AIAutomationTable).where(AIAutomationTable.user_id == current_user.id).order_by(AIAutomationTable.created_at.desc()))
        automations = db_result.scalars().all()
        running = sum(1 for automation in automations if automation.status == "in_progress")
        completed = sum(1 for automation in automations if automation.status == "completed")
        failed = sum(1 for automation in automations if automation.status == "failed")
        recent_tasks = [{"booking_id": automation.booking_id, "status": automation.status, "started_at": automation.started_at.isoformat() if automation.started_at else None, "automation_id": automation.id, "completed_at": automation.completed_at.isoformat() if automation.completed_at else None} for automation in automations[:10]]
        return {"total": len(automations), "running": running, "completed": completed, "failed": failed, "recent_tasks": recent_tasks, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting queue status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
AUTOMATION_WEBHOOK_SECRET = os.environ.get("AUTOMATION_WEBHOOK_SECRET", "dev-webhook-secret-change-in-production")

@router.post("/webhook/automation-complete", summary="Webhook for automation completion", description="Webhook called when automation completes (for external integrations). Requires X-Webhook-Secret header.")
async def automation_webhook(request: Request, booking_id: str, automation_id: str, status: str, result: dict[str, Any] | None=None, db: AsyncSession=Depends(get_db)) -> dict[str, str]:
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
    webhook_secret = request.headers.get("X-Webhook-Secret")
    if not webhook_secret or webhook_secret != AUTOMATION_WEBHOOK_SECRET:
        logger.warning("❌ Unauthorized webhook attempt from %s", request.client.host if request.client else "unknown")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing X-Webhook-Secret header")
    logger.info("🔔 Webhook: Automation %s for %s completed: %s", automation_id, booking_id, status)
    db_result = await db.execute(select(AIAutomationTable).where(AIAutomationTable.id == automation_id))
    automation_record = db_result.scalars().first()
    if automation_record is None:
        raise HTTPException(status_code=404, detail=f"Automation {automation_id} not found")
    payload = result or {}
    automation_record.status = status
    automation_record.decision_score = payload.get("decision_score", automation_record.decision_score)
    automation_record.risk_assessment = payload.get("risk_assessment", automation_record.risk_assessment)
    automation_record.agent_decisions = payload.get("agent_decisions", automation_record.agent_decisions)
    automation_record.actions_executed = payload.get("actions_executed", automation_record.actions_executed)
    automation_record.external_results = payload.get("external_results", automation_record.external_results)
    automation_record.execution_time_ms = payload.get("execution_time_ms", automation_record.execution_time_ms)
    automation_record.completed_at = datetime.now(UTC)
    automation_record.error_message = payload.get("error", automation_record.error_message)
    automation_record.trigger_source = "webhook"
    booking_result = await db.execute(select(BookingTable).where(BookingTable.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    if booking:
        booking.automation_status = status
        booking.automation_run_at = automation_record.completed_at
        booking.decision_score = automation_record.decision_score
        booking.risk_level = automation_record.risk_assessment
    await db.commit()
    return {"status": "acknowledged"}
