from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel
from backend.api.deps import get_db
from backend.auth.schemes import get_current_user_id
from backend.services import scheduler
from backend.utils.sanitization import sanitize_recursive
import logging
from backend.utils.tenant import get_current_org_id, get_current_workspace_id

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "meeting"  # meeting, event, birthday, task
    color: Optional[str] = None
    start_time: datetime
    end_time: datetime
    metadata_payload: dict = {}
    is_remote: bool = True
    status: str = "confirmed"


class EventCreate(EventBase):
    google_access_token: Optional[str] = None
    microsoft_access_token: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata_payload: Optional[dict] = None
    status: Optional[str] = None
    google_access_token: Optional[str] = None
    microsoft_access_token: Optional[str] = None


class EventResponse(EventBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/events", response_model=List[EventResponse])
async def get_events(
    start: datetime,
    end: datetime,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    org_id: int = Depends(get_current_org_id),
    workspace_id: Optional[int] = Depends(get_current_workspace_id),
):
    """Fetch events for a user within a time range, scoped by organization/workspace."""
    return await scheduler.get_events_for_range(db, user_id, start, end, org_id=org_id, workspace_id=workspace_id)


@router.post("/events", response_model=EventResponse)
async def create_event(
    event_in: EventCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    org_id: int = Depends(get_current_org_id),
    workspace_id: Optional[int] = Depends(get_current_workspace_id),
):
    """Create a new event and sync to AI."""
    # Sanitize incoming data to prevent XSS in description/metadata
    event_dict = sanitize_recursive(event_in.model_dump())
    event_dict["user_id"] = user_id
    event_dict["org_id"] = org_id
    event_dict["workspace_id"] = workspace_id

    try:
        return await scheduler.create_event(db, event_dict, background_tasks=background_tasks)
    except ValueError as ve:
        # Business logic errors (e.g. conflicts)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Event creation failed: {e}")
        raise HTTPException(status_code=500, detail="Could not create event")


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_in: EventUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    org_id: int = Depends(get_current_org_id),
):
    """Update event and trigger real-time AI context update."""
    # Sanitize incoming update data
    update_data = sanitize_recursive(event_in.model_dump(exclude_unset=True))
    
    try:
        event = await scheduler.update_event(
            db, event_id, user_id, update_data, background_tasks=background_tasks, org_id=org_id
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Event update failed: {e}")
        raise HTTPException(status_code=500, detail="Could not update event")


@router.get("/slots")
async def get_available_slots(
    date: datetime,
    duration: int = 30,
    target_timezone: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    org_id: int = Depends(get_current_org_id),
):
    """Detect available time slots for scheduling (Smart Pipeline)."""
    return await scheduler.find_available_slots(
        db, user_id, date, duration, target_timezone=target_timezone, org_id=org_id
    )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    org_id: int = Depends(get_current_org_id),
    workspace_id: Optional[int] = Depends(get_current_workspace_id),
):
    """Delete event and purge from AI memory."""
    success = await scheduler.delete_event(
        db, event_id, user_id, background_tasks=background_tasks, org_id=org_id, workspace_id=workspace_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return None
