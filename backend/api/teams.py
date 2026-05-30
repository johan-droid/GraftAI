from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.models.tables import generate_uuid
from backend.models.team import Team, TeamMember
from backend.utils.db import get_db
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/teams", tags=["teams"])

class TeamCreateRequest(BaseModel):
    name: str
    rotation_strategy: str | None = "round_robin"

class TeamResponse(BaseModel):
    id: str
    name: str
    rotation_strategy: str
    owner_user_id: str
    created_at: datetime

class TeamMemberRequest(BaseModel):
    user_id: str
    weight: int | None = 1
    max_daily_bookings: int | None = None

class TeamMemberResponse(BaseModel):
    id: str
    user_id: str
    weight: int | None
    is_active: bool

@router.post("", response_model=TeamResponse)
async def create_team(req: TeamCreateRequest, db: AsyncSession=Depends(get_db), current_user=Depends(get_current_user)):
    team = Team(id=generate_uuid(), owner_user_id=current_user.id, name=req.name, rotation_strategy=req.rotation_strategy or "round_robin", created_at=datetime.now(UTC))
    db.add(team)
    await db.flush()
    return TeamResponse(id=team.id, name=team.name, rotation_strategy=team.rotation_strategy, owner_user_id=team.owner_user_id, created_at=team.created_at)

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, db: AsyncSession=Depends(get_db), current_user=Depends(get_current_user)):
    stmt = select(Team).where(Team.id == team_id)
    result = await db.execute(stmt)
    team = result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse(id=team.id, name=team.name, rotation_strategy=team.rotation_strategy, owner_user_id=team.owner_user_id, created_at=team.created_at)

@router.post("/{team_id}/members", response_model=TeamMemberResponse)
async def add_team_member(team_id: str, req: TeamMemberRequest, db: AsyncSession=Depends(get_db), current_user=Depends(get_current_user)):
    stmt = select(Team).where(Team.id == team_id)
    res = await db.execute(stmt)
    team = res.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    member = TeamMember(id=generate_uuid(), team_id=team_id, user_id=req.user_id, weight=req.weight or 1, max_daily_bookings=req.max_daily_bookings, is_active=True, joined_at=datetime.now(UTC))
    db.add(member)
    await db.flush()
    return TeamMemberResponse(id=member.id, user_id=member.user_id, weight=member.weight, is_active=member.is_active)

@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_team_members(team_id: str, db: AsyncSession=Depends(get_db), current_user=Depends(get_current_user)):
    stmt = select(TeamMember).where(TeamMember.team_id == team_id)
    res = await db.execute(stmt)
    members = res.scalars().all()
    return [TeamMemberResponse(id=m.id, user_id=m.user_id, weight=m.weight, is_active=m.is_active) for m in members]
