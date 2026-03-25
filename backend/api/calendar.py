from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel
from backend.api.deps import get_db
from backend.auth.schemes import get_current_user_id
from backend.services import scheduler
import logging

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "meeting" # meeting, event, birthday, task
    color: Optional[str] = None
    start_time: datetime
    end_time: datetime
    metadata_payload: dict = {}
    is_remote: bool = True
    status: str = "confirmed"

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata_payload: Optional[dict] = None
    status: Optional[str] = None

class EventResponse(EventBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/events", response_model=List[EventResponse])
async def get_events(
    start: datetime,
    end: datetime,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Fetch events for a user within a time range."""
    return await scheduler.get_events_for_range(db, user_id, start, end)

@router.post("/events", response_model=EventResponse)
async def create_event(
    event_in: EventCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Create a new event and sync to AI."""
    event_dict = event_in.model_dump()
    event_dict["user_id"] = user_id
    
    try:
        return await scheduler.create_event(db, event_dict)
    except Exception as e:
        logger.error(f"Event creation failed: {e}")
        raise HTTPException(status_code=500, detail="Could not create event")

@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_in: EventUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update event and trigger real-time AI context update."""
    update_data = event_in.model_dump(exclude_unset=True)
    event = await scheduler.update_event(db, event_id, user_id, update_data)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event

@router.get("/slots")
async def get_available_slots(
    date: datetime,
    duration: int = 30,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Detect available time slots for scheduling (Smart Pipeline)."""
    return await scheduler.find_available_slots(db, user_id, date, duration)

@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Delete event and purge from AI memory."""
    success = await scheduler.delete_event(db, event_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return None
