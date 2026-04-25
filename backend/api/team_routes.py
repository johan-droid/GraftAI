"""Team scheduling API routes for collaborative scheduling."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

logger = logging.getLogger(__name__)

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable
from backend.models.team import Team, TeamMember, TeamRole, TeamEventType, TeamBooking

router = APIRouter(prefix="/teams", tags=["teams"])


# Pydantic Models


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    round_robin_enabled: Optional[bool] = None
    require_approval: Optional[bool] = None


class TeamMemberInvite(BaseModel):
    email: EmailStr
    role: TeamRole = TeamRole.MEMBER


class TeamEventTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    duration: int = Field(30, ge=15, le=120)
    assigned_members: Optional[List[str]] = None
    assignment_type: str = "all"  # all, specific, round_robin


class TeamBookingCreate(BaseModel):
    event_type_id: str
    title: str
    description: Optional[str] = None
    start_time: str  # ISO datetime
    attendee_name: str
    attendee_email: EmailStr
    attendee_phone: Optional[str] = None


# Team Routes


@router.post("/")
async def create_team(
    team: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Create a new team."""
    # Check if slug is unique
    stmt = select(Team).where(Team.slug == team.slug)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Team slug already exists")

    new_team = Team(
        name=team.name,
        slug=team.slug,
        description=team.description,
        owner_id=current_user.id,
    )

    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)

    # Add owner as team member
    owner_member = TeamMember(
        team_id=new_team.id, user_id=current_user.id, role=TeamRole.OWNER
    )
    db.add(owner_member)
    await db.commit()

    return {"id": new_team.id, "name": new_team.name, "slug": new_team.slug}


@router.get("/")
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """List all teams the user is a member of."""
    stmt = select(TeamMember).where(TeamMember.user_id == current_user.id)
    memberships = (await db.execute(stmt)).scalars().all()

    team_ids = [m.team_id for m in memberships]

    if not team_ids:
        return []

    stmt = select(Team).where(Team.id.in_(team_ids))
    teams = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "slug": t.slug,
            "description": t.description,
            "round_robin_enabled": t.round_robin_enabled,
            "require_approval": t.require_approval,
        }
        for t in teams
    ]


@router.get("/{team_id}")
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get team details."""
    stmt = select(Team).where(Team.id == team_id)
    team = (await db.execute(stmt)).scalars().first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if user is a member
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == current_user.id
    )
    membership = (await db.execute(stmt)).scalars().first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    return {
        "id": team.id,
        "name": team.name,
        "slug": team.slug,
        "description": team.description,
        "owner_id": team.owner_id,
        "round_robin_enabled": team.round_robin_enabled,
        "require_approval": team.require_approval,
        "default_booking_duration": team.default_booking_duration,
        "timezone": team.timezone,
        "business_hours": team.business_hours,
    }


@router.put("/{team_id}")
async def update_team(
    team_id: str,
    team_update: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Update team details (owner/admin only)."""
    stmt = select(Team).where(Team.id == team_id)
    team = (await db.execute(stmt)).scalars().first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if user is owner or admin
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == current_user.id
    )
    membership = (await db.execute(stmt)).scalars().first()

    if not membership or membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
        raise HTTPException(
            status_code=403, detail="Only owner or admin can update team"
        )

    if team_update.name is not None:
        team.name = team_update.name
    if team_update.description is not None:
        team.description = team_update.description
    if team_update.round_robin_enabled is not None:
        team.round_robin_enabled = team_update.round_robin_enabled
    if team_update.require_approval is not None:
        team.require_approval = team_update.require_approval

    await db.commit()
    await db.refresh(team)

    return {"id": team.id, "name": team.name, "slug": team.slug}


# Team Member Routes


@router.post("/{team_id}/members")
async def add_team_member(
    team_id: str,
    invite: TeamMemberInvite,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Add a member to the team (owner/admin only)."""
    # Check team exists and user has permission
    stmt = select(Team).where(Team.id == team_id)
    team = (await db.execute(stmt)).scalars().first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == current_user.id
    )
    membership = (await db.execute(stmt)).scalars().first()

    if not membership or membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
        raise HTTPException(
            status_code=403, detail="Only owner or admin can add members"
        )

    # Find user by email
    stmt = select(UserTable).where(UserTable.email == invite.email.lower())
    user = (await db.execute(stmt)).scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already a member
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == user.id
    )
    existing = (await db.execute(stmt)).scalars().first()

    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    try:
        new_member = TeamMember(team_id=team_id, user_id=user.id, role=invite.role)
        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)

        return {
            "id": new_member.id,
            "user_id": user.id,
            "email": getattr(user, "email", invite.email),
            "role": new_member.role,
            "is_active": getattr(new_member, "is_active", True),
            "joined_at": new_member.joined_at.isoformat() if hasattr(new_member, "joined_at") and new_member.joined_at else datetime.now().isoformat(),
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to add team member: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while adding team member: {str(e)}"
        )


@router.get("/{team_id}/members")
async def list_team_members(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """List all team members."""
    # Check if user is a member
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == current_user.id
    )
    membership = (await db.execute(stmt)).scalars().first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    stmt = select(TeamMember).where(TeamMember.team_id == team_id)
    members = (await db.execute(stmt)).scalars().all()

    # Get user details
    user_ids = [m.user_id for m in members]
    stmt = select(UserTable).where(UserTable.id.in_(user_ids))
    users = {u.id: u for u in (await db.execute(stmt)).scalars().all()}

    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "email": users.get(m.user_id, {}).email
            if users.get(m.user_id)
            else "Unknown",
            "role": m.role,
            "is_active": m.is_active,
            "joined_at": m.joined_at.isoformat(),
        }
        for m in members
    ]


@router.delete("/{team_id}/members/{member_id}")
async def remove_team_member(
    team_id: str,
    member_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Remove a member from the team (owner only)."""
    # Check if current user is owner
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == current_user.id
    )
    membership = (await db.execute(stmt)).scalars().first()

    if not membership or membership.role != TeamRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can remove members")

    # Get member to remove
    stmt = select(TeamMember).where(TeamMember.id == member_id)
    member = (await db.execute(stmt)).scalars().first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Cannot remove owner
    if member.role == TeamRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot remove team owner")

    await db.delete(member)
    await db.commit()

    return {"status": "success", "message": "Member removed"}


# Team Event Type Routes


@router.post("/{team_id}/event-types")
async def create_event_type(
    team_id: str,
    event_type: TeamEventTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Create a team event type (booking link)."""
    # Check if user is owner or admin
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == current_user.id
    )
    membership = (await db.execute(stmt)).scalars().first()

    if not membership or membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
        raise HTTPException(
            status_code=403, detail="Only owner or admin can create event types"
        )

    # Generate booking link slug
    booking_slug = f"{secrets.token_urlsafe(8)}"

    new_event_type = TeamEventType(
        team_id=team_id,
        name=event_type.name,
        slug=event_type.slug,
        description=event_type.description,
        duration=event_type.duration,
        assigned_members=event_type.assigned_members or [],
        assignment_type=event_type.assignment_type,
        booking_link_slug=booking_slug,
    )

    db.add(new_event_type)
    await db.commit()
    await db.refresh(new_event_type)

    return {
        "id": new_event_type.id,
        "name": new_event_type.name,
        "slug": new_event_type.slug,
        "booking_link": f"/book/{booking_slug}",
    }


@router.get("/{team_id}/event-types")
async def list_event_types(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """List all event types for a team."""
    # Check if user is a member
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == current_user.id
    )
    membership = (await db.execute(stmt)).scalars().first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    stmt = select(TeamEventType).where(TeamEventType.team_id == team_id)
    event_types = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": et.id,
            "name": et.name,
            "slug": et.slug,
            "description": et.description,
            "duration": et.duration,
            "assignment_type": et.assignment_type,
            "booking_link": f"/book/{et.booking_link_slug}"
            if et.booking_link_slug
            else None,
            "is_active": et.is_active,
        }
        for et in event_types
    ]


# Team Booking Routes


@router.post("/{team_id}/bookings")
async def create_team_booking(
    team_id: str, booking: TeamBookingCreate, db: AsyncSession = Depends(get_db)
):
    """Create a team booking (public endpoint for booking links)."""
    # Get event type
    stmt = select(TeamEventType).where(TeamEventType.id == booking.event_type_id)
    event_type = (await db.execute(stmt)).scalars().first()

    if not event_type:
        raise HTTPException(status_code=404, detail="Event type not found")

    if not event_type.is_active:
        raise HTTPException(status_code=400, detail="Event type is not active")

    # Generate confirmation code
    confirmation_code = secrets.token_urlsafe(8).upper()

    # Create booking
    start_time = datetime.fromisoformat(booking.start_time)
    end_time = start_time + timedelta(minutes=event_type.duration)

    new_booking = TeamBooking(
        team_id=team_id,
        event_type_id=booking.event_type_id,
        title=booking.title,
        description=booking.description,
        start_time=start_time,
        end_time=end_time,
        attendee_name=booking.attendee_name,
        attendee_email=booking.attendee_email,
        attendee_phone=booking.attendee_phone,
        confirmation_code=confirmation_code,
        status="pending",  # Will be confirmed if not require_approval
    )

    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)

    # Send confirmation email to attendee
    try:
        from backend.services.notifications import NotificationService

        notification_service = NotificationService(db)
        await notification_service.send_booking_confirmation(
            to_email=booking.attendee_email,
            booking_data={
                "id": new_booking.id,
                "title": booking.title,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "confirmation_code": confirmation_code,
                "attendee_name": booking.attendee_name,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")

    # TODO: Add to assigned member's calendar (requires team member assignment logic)

    return {
        "id": new_booking.id,
        "confirmation_code": confirmation_code,
        "status": new_booking.status,
    }
