import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.tables import UserTable, UserTokenTable
from backend.services.scheduler import (
    create_event,
    delete_event,
    get_events_for_range,
    update_event,
)
from backend.services.sync_engine import sync_user_calendar
from backend.services.usage import check_usage_limit, increment_usage
from backend.utils.audit_logger import (
    Action,
    AuditLogger,
    EventCategory,
    EventType,
    Result,
)
from backend.utils.errors import TimezoneError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calendar", tags=["Calendar"])

class EventCreateSchema(BaseModel):
    title: str = Field(..., json_schema_extra={"example": "Quarterly business review"})
    start_time: datetime = Field(..., json_schema_extra={"example": "2026-05-01T14:00:00Z"}, description="ISO 8601 formatted UTC start time")
    end_time: datetime = Field(..., json_schema_extra={"example": "2026-05-01T15:00:00Z"}, description="ISO 8601 formatted UTC end time")
    description: str | None = Field(None, json_schema_extra={"example": "Discuss roadmap and action items."})
    location: str | None = Field(None, json_schema_extra={"example": "Conference Room A"})
    is_meeting: bool | None = Field(False, json_schema_extra={"example": True})
    meeting_provider: str | None = Field(None, json_schema_extra={"example": "microsoft"}, description="Preferred external calendar/video provider, e.g. google, microsoft, zoom")
    meeting_type: str | None = Field(None, json_schema_extra={"example": "consultation"})
    attendees: list[str] | None = Field(default_factory=list, json_schema_extra={"example": ["alice@example.com", "bob@example.com"]})
    model_config = ConfigDict(json_schema_extra={"example": {"title": "Quarterly business review", "start_time": "2026-05-01T14:00:00Z", "end_time": "2026-05-01T15:00:00Z", "description": "Discuss roadmap and action items.", "location": "Conference Room A", "is_meeting": True, "meeting_provider": "microsoft", "meeting_type": "strategy", "attendees": ["alice@example.com", "bob@example.com"]}})

class EventResponseSchema(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    source: str
    description: str | None = None
    location: str | None = None
    meeting_url: str | None = None
    is_meeting: bool | None = False
    meeting_provider: str | None = None
    attendees: list[str] | None = None
    model_config = ConfigDict(from_attributes=True)

class AvailabilitySlot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    time: str
    available: bool
    reason: str | None = None

class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    date: str
    slots: list[AvailabilitySlot]
    timezone: str

async def _audit_calendar_event(db: AsyncSession, request: Request, current_user: UserTable, *, event_type: EventType, action: Action, result: Result, resource_id: str | None=None, failure_reason: str | None=None, metadata: dict | None=None) -> None:
    try:
        await AuditLogger.log(db=db, event_type=event_type, event_category=EventCategory.DATA_MODIFICATION if action != Action.READ else EventCategory.DATA_ACCESS, action=action, result=result, user_id=str(current_user.id), user_email=getattr(current_user, "email", None), ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"), resource_type="calendar_event", resource_id=resource_id, failure_reason=failure_reason, metadata=metadata or {}, compliance_standards=["SOC2", "GDPR"], data_categories=["calendar_metadata", "scheduling"])
    except Exception:
        logger.exception("Audit logging failed for user=%s event=%s", current_user.id, event_type.value)

@router.get("/events", response_model=list[EventResponseSchema])
async def list_events(request: Request, start: datetime=Query(..., description="Start of date range"), end: datetime=Query(..., description="End of date range"), limit: int=Query(50, ge=1, le=200, description="Maximum number of events to return"), offset: int=Query(0, ge=0, description="Pagination offset for event results"), db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """
    Fetch all calendar events (both local and synced from Google/MSFT)
    for the logged-in user within a specific timeframe.
    """
    events = await get_events_for_range(db, user_id=current_user.id, start=start, end=end, limit=limit, offset=offset)
    await _audit_calendar_event(db, request, current_user, event_type=EventType.CALENDAR_VIEW, action=Action.READ, result=Result.SUCCESS, metadata={"start": start.isoformat(), "end": end.isoformat(), "limit": limit, "offset": offset})
    return events

@router.post("/events", response_model=EventResponseSchema)
async def add_local_event(request: Request, payload: EventCreateSchema, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """
    Create a new schedule block locally.
    Includes built-in conflict detection to prevent double-booking.
    """
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time.")
    event_data = payload.model_dump()
    event_data["user_id"] = current_user.id
    event_data["source"] = "local"
    event_data["fingerprint"] = "local_creation"
    try:
        new_event = await create_event(db, event_data)
        await _audit_calendar_event(db, request, current_user, event_type=EventType.EVENT_CREATE, action=Action.CREATE, result=Result.SUCCESS, resource_id=str(new_event.id), metadata={"source": "local", "meeting_provider": payload.meeting_provider, "attendee_count": len(payload.attendees or [])})
        return new_event
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimezoneError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        await _audit_calendar_event(db, request, current_user, event_type=EventType.EVENT_CREATE, action=Action.CREATE, result=Result.FAILURE, failure_reason=str(e))
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        await _audit_calendar_event(db, request, current_user, event_type=EventType.EVENT_CREATE, action=Action.CREATE, result=Result.FAILURE, failure_reason=str(e))
        logger.error("Failed to create event: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/events/{event_id}", response_model=EventResponseSchema)
async def edit_event(request: Request, event_id: str, payload: EventCreateSchema, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    updated = await update_event(db, event_id, current_user.id, payload.model_dump())
    if not updated:
        await _audit_calendar_event(db, request, current_user, event_type=EventType.EVENT_UPDATE, action=Action.UPDATE, result=Result.FAILURE, resource_id=event_id, failure_reason="event_not_found")
        raise HTTPException(status_code=404, detail="Event not found")
    await _audit_calendar_event(db, request, current_user, event_type=EventType.EVENT_UPDATE, action=Action.UPDATE, result=Result.SUCCESS, resource_id=event_id)
    return updated

@router.delete("/events/{event_id}")
async def delete_event_route(request: Request, event_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    deleted = await delete_event(db, event_id, current_user.id)
    if not deleted:
        await _audit_calendar_event(db, request, current_user, event_type=EventType.EVENT_DELETE, action=Action.DELETE, result=Result.FAILURE, resource_id=event_id, failure_reason="event_not_found")
        raise HTTPException(status_code=404, detail="Event not found")
    await _audit_calendar_event(db, request, current_user, event_type=EventType.EVENT_DELETE, action=Action.DELETE, result=Result.SUCCESS, resource_id=event_id)
    return {"status": "deleted"}

@router.post("/sync")
async def trigger_calendar_sync(request: Request, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user), _usage_check: bool=Depends(check_usage_limit("calendar_syncs"))):
    """
    Triggers a sync with external calendars (Google/Microsoft).
    """
    provider_stmt = select(UserTokenTable.provider, UserTokenTable.is_active).where(and_(UserTokenTable.user_id == current_user.id, UserTokenTable.provider.in_(["google", "microsoft"])))
    provider_rows = (await db.execute(provider_stmt)).all()
    active_providers = [provider for provider, is_active in provider_rows if is_active]
    inactive_providers = [provider for provider, is_active in provider_rows if not is_active]
    if not active_providers:
        if inactive_providers:
            await _audit_calendar_event(db, request, current_user, event_type=EventType.CALENDAR_UPDATE, action=Action.UPDATE, result=Result.DENIED, failure_reason="inactive_calendar_integrations", metadata={"inactive_providers": sorted(set(inactive_providers))})
            raise HTTPException(status_code=400, detail=f"Your {', '.join(sorted(set(inactive_providers)))} connection(s) need reconnection. Please reconnect them under Settings > Integrations.")
        await _audit_calendar_event(db, request, current_user, event_type=EventType.CALENDAR_UPDATE, action=Action.UPDATE, result=Result.DENIED, failure_reason="no_calendar_integrations")
        raise HTTPException(status_code=400, detail="No active calendar integrations found. Connect Google or Microsoft under Settings > Integrations.")
    try:
        sync_summary = await sync_user_calendar(db, current_user.id)
        if sync_summary.get("successful_tokens", 0) == 0:
            await _audit_calendar_event(db, request, current_user, event_type=EventType.CALENDAR_UPDATE, action=Action.UPDATE, result=Result.FAILURE, failure_reason="all_calendar_providers_failed", metadata={"attempted_providers": active_providers, "sync_summary": sync_summary})
            raise HTTPException(status_code=502, detail="Calendar providers are connected but sync failed for all of them. Please reconnect Google/Microsoft integration and try again.")
        await increment_usage(db, current_user.id, "calendar_syncs")
        await _audit_calendar_event(db, request, current_user, event_type=EventType.CALENDAR_UPDATE, action=Action.UPDATE, result=Result.SUCCESS, metadata={"synced_providers": active_providers, "integration_style": "cal.com-compatible", "sync_summary": sync_summary})
        return {"status": "success", "message": "Calendar sync completed.", "synced_providers": active_providers, "sync_summary": sync_summary}
    except Exception as e:
        await _audit_calendar_event(db, request, current_user, event_type=EventType.CALENDAR_UPDATE, action=Action.UPDATE, result=Result.FAILURE, failure_reason=str(e), metadata={"attempted_providers": active_providers})
        logger.exception("Calendar sync failed for user %s: %s", current_user.id, e)
        raise HTTPException(status_code=500, detail="Calendar sync failed due to an integration error. Please reconnect your calendar providers or try again later.")

@router.get("/availability/free-slots", response_model=AvailabilityResponse)
async def get_free_slots(date: str=Query(..., description="Date in YYYY-MM-DD format"), duration: int=Query(30, description="Meeting duration in minutes"), db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """
    Get available time slots for a specific date based on user's calendar.
    Considers existing events and work hours preferences.
    """
    from dateutil import parser as date_parser
    from dateutil import tz as dateutil_tz

    from backend.models.tables import EventTable
    try:
        target_date = date_parser.parse(date).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    if duration <= 0 or duration > 480:
        raise HTTPException(status_code=400, detail="Duration must be between 1 and 480 minutes.")
    user_tz = "UTC"
    work_start = 9
    work_end = 18
    if current_user.preferences and isinstance(current_user.preferences, dict):
        user_tz = current_user.preferences.get("timezone", "UTC")
        work_start_str = current_user.preferences.get("work_hours_start", "09:00")
        work_end_str = current_user.preferences.get("work_hours_end", "18:00")
        try:
            work_start = int(work_start_str.split(":")[0])
            work_end = int(work_end_str.split(":")[0])
        except (ValueError, IndexError):
            pass
    user_tzinfo = dateutil_tz.gettz(user_tz) or dateutil_tz.tzutc()
    day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=user_tzinfo)
    day_end = datetime.combine(target_date, datetime.max.time().replace(microsecond=0)).replace(tzinfo=user_tzinfo)
    stmt = select(EventTable).where(and_(EventTable.user_id == current_user.id, not EventTable.is_deleted, EventTable.start_time <= day_end, EventTable.end_time >= day_start, EventTable.source != "deleted"))
    events = (await db.execute(stmt)).scalars().all()
    busy_intervals = []
    for event in events:
        if event.start_time and event.end_time:
            start = event.start_time
            end = event.end_time
            if start.tzinfo is None:
                start = start.replace(tzinfo=user_tzinfo)
            else:
                start = start.astimezone(user_tzinfo)
            if end.tzinfo is None:
                end = end.replace(tzinfo=user_tzinfo)
            else:
                end = end.astimezone(user_tzinfo)
            busy_intervals.append((start, end))
    slots = []
    work_start_minutes = work_start * 60
    work_end_minutes = work_end * 60
    day_work_end = day_start + timedelta(minutes=work_end_minutes)
    for minute_offset in range(work_start_minutes, work_end_minutes, duration):
        slot_time = day_start + timedelta(minutes=minute_offset)
        slot_end = slot_time + timedelta(minutes=duration)
        if slot_end > day_work_end:
            continue
        time_str = slot_time.strftime("%H:%M")
        is_available = True
        reason = None
        for busy_start, busy_end in busy_intervals:
            if slot_time < busy_end and slot_end > busy_start:
                is_available = False
                reason = "busy"
                break
        slots.append(AvailabilitySlot(time=time_str, available=is_available, reason=reason))
    return AvailabilityResponse(date=date, slots=slots, timezone=user_tz)
