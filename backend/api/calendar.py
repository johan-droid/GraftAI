from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from backend.api.deps import get_db
from backend.auth.schemes import get_current_user_id
from backend.services import scheduler
from backend.utils.sanitization import sanitize_recursive
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "meeting"
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
):
    return await scheduler.get_events_for_range(db, user_id, start, end)


@router.post("/events", response_model=EventResponse)
async def create_event(
    event_in: EventCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    event_dict = sanitize_recursive(event_in.model_dump())
    event_dict["user_id"] = user_id
    try:
        return await scheduler.create_event(db, event_dict, background_tasks)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.error(f"Event creation failed: {exc}")
        raise HTTPException(status_code=500, detail="Could not create event")


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_in: EventUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    update_data = sanitize_recursive(event_in.model_dump(exclude_unset=True))
    try:
        event = await scheduler.update_event(db, event_id, user_id, update_data, background_tasks)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/slots")
async def get_available_slots(
    date: datetime,
    duration: int = 30,
    target_timezone: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await scheduler.find_available_slots(
        db, user_id, date, duration, target_timezone=target_timezone
    )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    success = await scheduler.delete_event(db, event_id, user_id, background_tasks)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return None
