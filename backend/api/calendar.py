import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.utils.errors import ValidationError, TimezoneError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

# We import the simplified services and models we created earlier
from backend.api.deps import get_db, get_current_user 
from backend.models.tables import UserTable, UserTokenTable
from backend.services.scheduler import get_events_for_range, create_event, update_event, delete_event
from backend.services.sync_engine import sync_user_calendar
from backend.services.usage import check_usage_limit, increment_usage

logger = logging.getLogger(__name__)

# Adding the prefix here for monolithic consistency
router = APIRouter(prefix="/calendar", tags=["Calendar"])

# --- Pydantic Schemas for Input Validation ---
class EventCreateSchema(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    is_meeting: Optional[bool] = False
    meeting_provider: Optional[str] = None
    meeting_type: Optional[str] = None
    attendees: Optional[List[str]] = Field(default_factory=list)

class EventResponseSchema(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    source: str
    description: Optional[str] = None
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    is_meeting: Optional[bool] = False
    meeting_provider: Optional[str] = None
    attendees: Optional[List[str]] = None

    class Config:
        from_attributes = True


@router.get("/events", response_model=List[EventResponseSchema])
async def list_events(
    start: datetime = Query(..., description="Start of date range"),
    end: datetime = Query(..., description="End of date range"),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    Fetch all calendar events (both local and synced from Google/MSFT) 
    for the logged-in user within a specific timeframe.
    """
    events = await get_events_for_range(db, user_id=current_user.id, start=start, end=end)
    return events


@router.post("/events", response_model=EventResponseSchema)
async def add_local_event(
    payload: EventCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
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
        return new_event
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimezoneError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("Failed to create event: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/events/{event_id}", response_model=EventResponseSchema)
async def edit_event(
    event_id: str,
    payload: EventCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    updated = await update_event(db, event_id, current_user.id, payload.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated


@router.delete("/events/{event_id}")
async def delete_event_route(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    deleted = await delete_event(db, event_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "deleted"}


@router.post("/sync")
async def trigger_calendar_sync(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
    _usage_check: bool = Depends(check_usage_limit("calendar_syncs"))
):
    """
    Triggers a sync with external calendars (Google/Microsoft).
    """
    provider_stmt = select(UserTokenTable.provider, UserTokenTable.is_active).where(
        and_(
            UserTokenTable.user_id == current_user.id,
            UserTokenTable.provider.in_(["google", "microsoft"])
        )
    )
    provider_rows = (await db.execute(provider_stmt)).all()
    active_providers = [provider for provider, is_active in provider_rows if is_active]
    inactive_providers = [provider for provider, is_active in provider_rows if not is_active]

    if not active_providers:
        if inactive_providers:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Your {', '.join(sorted(set(inactive_providers)))} connection(s) need reconnection. "
                    "Please reconnect them under Settings > Integrations."
                )
            )
        raise HTTPException(
            status_code=400,
            detail="No active calendar integrations found. Connect Google or Microsoft under Settings > Integrations."
        )

    try:
        await sync_user_calendar(db, current_user.id)
        await increment_usage(db, current_user.id, "calendar_syncs")
        return {
            "status": "success",
            "message": "Calendar sync completed.",
            "synced_providers": active_providers,
        }
    except Exception as e:
        logger.error(f"Calendar sync failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=(
                "Calendar sync failed due to an integration error. "
                "Please reconnect your calendar providers or try again later."
            )
        )
