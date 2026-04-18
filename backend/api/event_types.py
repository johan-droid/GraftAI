from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable
from backend.services.bookings import (
    delete_event_type,
    list_event_types,
    create_event_type,
    update_event_type,
)

router = APIRouter(tags=["EventTypes"])
SINGLE_ASSIGNMENT_METHOD = "host_only"


class EventTypePayload(BaseModel):
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    color: Optional[str] = Field(default="#3b82f6", pattern=r"^#[0-9A-Fa-f]{6}$")
    duration_minutes: int = Field(default=60, ge=1)
    meeting_provider: Optional[str] = None
    is_public: Optional[bool] = True
    buffer_before_minutes: Optional[int] = None
    buffer_after_minutes: Optional[int] = None
    minimum_notice_minutes: Optional[int] = None
    availability: Optional[Dict[str, List[str]]] = None
    exceptions: Optional[List[Dict[str, Any]]] = None
    recurrence_rule: Optional[str] = None
    custom_questions: Optional[List[Dict[str, Any]]] = None
    requires_attendee_confirmation: Optional[bool] = False
    travel_time_before_minutes: Optional[int] = None
    travel_time_after_minutes: Optional[int] = None
    requires_payment: Optional[bool] = False
    payment_amount: Optional[float] = None
    payment_currency: Optional[str] = None
    team_assignment_method: Optional[str] = None


class TeamMemberPayload(BaseModel):
    username: str
    assignment_method: Optional[str] = None
    priority: Optional[int] = None


class TeamMemberEditPayload(BaseModel):
    assignment_method: Optional[str] = None
    priority: Optional[int] = None


class TeamMemberResponse(BaseModel):
    id: str
    user_id: str
    username: Optional[str] = None
    assignment_method: str
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventTypeResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    slug: str
    color: str
    duration_minutes: int
    meeting_provider: Optional[str] = None
    is_public: bool
    buffer_before_minutes: Optional[int] = None
    buffer_after_minutes: Optional[int] = None
    minimum_notice_minutes: Optional[int] = None
    availability: Optional[Dict[str, List[str]]] = None
    exceptions: Optional[List[Dict[str, Any]]] = None
    recurrence_rule: Optional[str] = None
    custom_questions: Optional[List[Dict[str, Any]]] = None
    requires_attendee_confirmation: bool
    travel_time_before_minutes: Optional[int] = None
    travel_time_after_minutes: Optional[int] = None
    requires_payment: bool
    payment_amount: Optional[float] = None
    payment_currency: Optional[str] = None
    team_assignment_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/event-types", response_model=List[EventTypeResponse])
async def get_event_types(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    types = await list_event_types(db, current_user.id)
    return types


@router.post("/event-types", response_model=EventTypeResponse)
async def create_event_type_route(
    payload: EventTypePayload,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload_dict = payload.model_dump()
    payload_dict["team_assignment_method"] = SINGLE_ASSIGNMENT_METHOD
    try:
        event_type = await create_event_type(db, current_user.id, payload_dict)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return event_type


@router.patch("/event-types/{event_type_id}", response_model=EventTypeResponse)
async def update_event_type_route(
    event_type_id: str,
    payload: EventTypePayload,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload_dict = payload.model_dump()
    payload_dict["team_assignment_method"] = SINGLE_ASSIGNMENT_METHOD
    try:
        event_type = await update_event_type(
            db, current_user.id, event_type_id, payload_dict
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not event_type:
        raise HTTPException(status_code=404, detail="Event type not found")
    return event_type


@router.delete("/event-types/{event_type_id}")
async def delete_event_type_route(
    event_type_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_event_type(db, current_user.id, event_type_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event type not found")
    return {"status": "deleted"}


@router.get(
    "/event-types/{event_type_id}/team-members", response_model=List[TeamMemberResponse]
)
async def get_event_type_team_members(
    event_type_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return []


@router.post(
    "/event-types/{event_type_id}/team-members", response_model=TeamMemberResponse
)
async def add_event_type_team_member_route(
    event_type_id: str,
    payload: TeamMemberPayload,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Team scheduling is disabled. Only one-to-one host-only booking is supported.",
    )


@router.patch(
    "/event-types/{event_type_id}/team-members/{member_id}",
    response_model=TeamMemberResponse,
)
async def update_event_type_team_member_route(
    event_type_id: str,
    member_id: str,
    payload: TeamMemberEditPayload,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Team scheduling is disabled. Only one-to-one host-only booking is supported.",
    )


@router.delete("/event-types/{event_type_id}/team-members/{member_id}")
async def delete_event_type_team_member_route(
    event_type_id: str,
    member_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Team scheduling is disabled. Only one-to-one host-only booking is supported.",
    )
