import html
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.tables import UserTable
from backend.services.bookings import (
    create_event_type,
    delete_event_type,
    list_event_types,
    update_event_type,
)

router = APIRouter(tags=["EventTypes"])
SINGLE_ASSIGNMENT_METHOD = "host_only"

class EventTypePayload(BaseModel):
    name: str
    description: str | None = None
    slug: str | None = None
    model_config = ConfigDict(extra="forbid")

    @field_validator("name", "description", mode="before")
    @classmethod
    def sanitize_html(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return html.escape(v.strip())
    color: str | None = Field(default="#3b82f6", pattern="^#[0-9A-Fa-f]{6}$")
    duration_minutes: int = Field(default=60, ge=1)
    meeting_provider: str | None = None
    is_public: bool | None = True
    buffer_before_minutes: int | None = None
    buffer_after_minutes: int | None = None
    minimum_notice_minutes: int | None = None
    availability: dict[str, list[str]] | None = None
    exceptions: list[dict[str, Any]] | None = None
    recurrence_rule: str | None = None
    custom_questions: list[dict[str, Any]] | None = None
    requires_attendee_confirmation: bool | None = False
    travel_time_before_minutes: int | None = None
    travel_time_after_minutes: int | None = None
    requires_payment: bool | None = False
    payment_amount: float | None = None
    payment_currency: str | None = None
    team_assignment_method: str | None = None

class TeamMemberPayload(BaseModel):
    username: str
    assignment_method: str | None = None
    priority: int | None = None

class TeamMemberEditPayload(BaseModel):
    assignment_method: str | None = None
    priority: int | None = None

class TeamMemberResponse(BaseModel):
    id: str
    user_id: str
    username: str | None = None
    assignment_method: str
    priority: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EventTypeResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    slug: str
    color: str
    duration_minutes: int
    meeting_provider: str | None = None
    is_public: bool
    buffer_before_minutes: int | None = None
    buffer_after_minutes: int | None = None
    minimum_notice_minutes: int | None = None
    availability: dict[str, list[str]] | None = None
    exceptions: list[dict[str, Any]] | None = None
    recurrence_rule: str | None = None
    custom_questions: list[dict[str, Any]] | None = None
    requires_attendee_confirmation: bool
    travel_time_before_minutes: int | None = None
    travel_time_after_minutes: int | None = None
    requires_payment: bool
    payment_amount: float | None = None
    payment_currency: str | None = None
    team_assignment_method: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

@router.get("/event-types", response_model=list[EventTypeResponse])
async def get_event_types(current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await list_event_types(db, current_user.id)

@router.post("/event-types", response_model=EventTypeResponse)
async def create_event_type_route(payload: EventTypePayload, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    payload_dict = payload.model_dump()
    payload_dict["team_assignment_method"] = SINGLE_ASSIGNMENT_METHOD
    try:
        event_type = await create_event_type(db, current_user.id, payload_dict)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return event_type

@router.patch("/event-types/{event_type_id}", response_model=EventTypeResponse)
async def update_event_type_route(event_type_id: str, payload: EventTypePayload, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    payload_dict = payload.model_dump()
    payload_dict["team_assignment_method"] = SINGLE_ASSIGNMENT_METHOD
    try:
        event_type = await update_event_type(db, current_user.id, event_type_id, payload_dict)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not event_type:
        raise HTTPException(status_code=404, detail="Event type not found")
    return event_type

@router.delete("/event-types/{event_type_id}")
async def delete_event_type_route(event_type_id: str, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    deleted = await delete_event_type(db, current_user.id, event_type_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event type not found")
    return {"status": "deleted"}

@router.get("/event-types/{event_type_id}/team-members", response_model=list[TeamMemberResponse])
async def get_event_type_team_members(event_type_id: str, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return []

@router.post("/event-types/{event_type_id}/team-members", response_model=TeamMemberResponse)
async def add_event_type_team_member_route(event_type_id: str, payload: TeamMemberPayload, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Team scheduling is disabled. Only one-to-one host-only booking is supported.")

@router.patch("/event-types/{event_type_id}/team-members/{member_id}", response_model=TeamMemberResponse)
async def update_event_type_team_member_route(event_type_id: str, member_id: str, payload: TeamMemberEditPayload, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Team scheduling is disabled. Only one-to-one host-only booking is supported.")

@router.delete("/event-types/{event_type_id}/team-members/{member_id}")
async def delete_event_type_team_member_route(event_type_id: str, member_id: str, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Team scheduling is disabled. Only one-to-one host-only booking is supported.")
