"""API routes for advanced analytics (team metrics, trends, resource utilization)."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable
from backend.services.advanced_analytics_service import AdvancedAnalyticsService

router = APIRouter(prefix="/analytics/advanced", tags=["analytics-advanced"])


# Pydantic Models


class TeamMetricsResponse(BaseModel):
    """Team metrics response."""

    period: dict
    bookings: dict
    duration: dict
    revenue: dict
    team: dict


class BookingTrendItem(BaseModel):
    """Booking trend data point."""

    date: str
    total: int
    confirmed: int
    cancelled: int
    net: int


class MemberPerformanceItem(BaseModel):
    """Member performance data."""

    member_id: str
    user_id: str
    name: str
    role: str
    is_active: bool
    metrics: dict


class ResourceUtilizationItem(BaseModel):
    """Resource utilization data."""

    resource_id: str
    name: str
    type: str
    location: str
    metrics: dict


class RevenueAnalyticsResponse(BaseModel):
    """Revenue analytics response."""

    period: dict
    summary: dict
    daily_trend: List[dict]


class PeakHoursResponse(BaseModel):
    """Peak hours analysis response."""

    period: str
    hourly_distribution: List[dict]
    peak_hours: List[dict]


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary response."""

    generated_at: str
    summary: dict


# Routes


@router.get("/team/{team_id}/metrics", response_model=TeamMetricsResponse)
async def get_team_metrics(
    team_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get comprehensive metrics for a team."""
    # Verify user is a member of the team
    from backend.models.team import TeamMember
    from sqlalchemy import select, and_

    stmt = select(TeamMember).where(
        and_(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
    )
    member = (await db.execute(stmt)).scalars().first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    service = AdvancedAnalyticsService(db)
    metrics = await service.get_team_metrics(team_id, start_date, end_date)

    return TeamMetricsResponse(**metrics)


@router.get("/team/{team_id}/booking-trends", response_model=List[BookingTrendItem])
async def get_booking_trends(
    team_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get daily booking trends for a team."""
    from backend.models.team import TeamMember
    from sqlalchemy import select, and_

    stmt = select(TeamMember).where(
        and_(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
    )
    member = (await db.execute(stmt)).scalars().first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    service = AdvancedAnalyticsService(db)
    trends = await service.get_booking_trends(team_id, days)

    return [BookingTrendItem(**t) for t in trends]


@router.get(
    "/team/{team_id}/member-performance", response_model=List[MemberPerformanceItem]
)
async def get_member_performance(
    team_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get performance metrics for each team member."""
    from backend.models.team import TeamMember
    from sqlalchemy import select, and_

    stmt = select(TeamMember).where(
        and_(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
    )
    member = (await db.execute(stmt)).scalars().first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    service = AdvancedAnalyticsService(db)
    performance = await service.get_member_performance(team_id, days)

    return [MemberPerformanceItem(**p) for p in performance]


@router.get(
    "/team/{team_id}/resource-utilization", response_model=List[ResourceUtilizationItem]
)
async def get_resource_utilization(
    team_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get utilization metrics for team resources."""
    from backend.models.team import TeamMember
    from sqlalchemy import select, and_

    stmt = select(TeamMember).where(
        and_(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
    )
    member = (await db.execute(stmt)).scalars().first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    service = AdvancedAnalyticsService(db)
    utilization = await service.get_resource_utilization(team_id, days)

    return [ResourceUtilizationItem(**u) for u in utilization]


@router.get("/revenue", response_model=RevenueAnalyticsResponse)
async def get_revenue_analytics(
    team_id: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get revenue analytics."""
    service = AdvancedAnalyticsService(db)
    analytics = await service.get_revenue_analytics(team_id, current_user.id, days)

    return RevenueAnalyticsResponse(**analytics)


@router.get("/team/{team_id}/peak-hours", response_model=PeakHoursResponse)
async def get_peak_hours(
    team_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Analyze peak booking hours for a team."""
    from backend.models.team import TeamMember
    from sqlalchemy import select, and_

    stmt = select(TeamMember).where(
        and_(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
    )
    member = (await db.execute(stmt)).scalars().first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    service = AdvancedAnalyticsService(db)
    analysis = await service.get_peak_hours_analysis(team_id, days)

    return PeakHoursResponse(**analysis)


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    team_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get comprehensive dashboard summary."""
    service = AdvancedAnalyticsService(db)
    summary = await service.get_dashboard_summary(team_id, current_user.id)

    return DashboardSummaryResponse(**summary)
