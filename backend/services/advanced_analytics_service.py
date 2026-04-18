"""Advanced analytics service for team metrics and trends.

Provides comprehensive analytics including:
- Team performance metrics
- Booking trends over time
- Resource utilization
- Revenue analytics
- User engagement metrics

Example Usage:
    service = AdvancedAnalyticsService(db)

    # Get team metrics
    metrics = await service.get_team_metrics(
        team_id="team_123",
        start_date="2024-01-01",
        end_date="2024-01-31"
    )

    # Get booking trends
    trends = await service.get_booking_trends(
        team_id="team_123",
        days=30
    )
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, desc, Float

from backend.models.team import TeamMember, TeamBooking
from backend.models.resource import Resource, ResourceBooking
from backend.models.tables import UserTable


class AdvancedAnalyticsService:
    """Service for generating advanced team and resource analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_team_metrics(
        self,
        team_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive metrics for a team.

        Args:
            team_id: Team ID
            start_date: Start of analysis period (default: 30 days ago)
            end_date: End of analysis period (default: now)

        Returns:
            Dictionary with team metrics
        """
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get team bookings
        stmt = select(TeamBooking).where(
            and_(
                TeamBooking.team_id == team_id,
                TeamBooking.created_at >= start_date,
                TeamBooking.created_at <= end_date,
            )
        )
        bookings = (await self.db.execute(stmt)).scalars().all()

        # Get team members
        stmt = select(TeamMember).where(TeamMember.team_id == team_id)
        members = (await self.db.execute(stmt)).scalars().all()

        # Calculate metrics
        total_bookings = len(bookings)
        confirmed = len([b for b in bookings if b.status == "confirmed"])
        cancelled = len([b for b in bookings if b.status == "cancelled"])
        pending = len([b for b in bookings if b.status == "pending"])

        # Duration statistics
        durations = []
        for b in bookings:
            if b.end_time and b.start_time:
                duration = (b.end_time - b.start_time).total_seconds() / 60
                durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0
        total_hours = sum(durations) / 60 if durations else 0

        # Revenue (if applicable)
        total_revenue = sum(
            [
                b.metadata.get("revenue", 0)
                for b in bookings
                if hasattr(b, "metadata") and b.metadata
            ]
        )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days,
            },
            "bookings": {
                "total": total_bookings,
                "confirmed": confirmed,
                "cancelled": cancelled,
                "pending": pending,
                "completion_rate": round(confirmed / total_bookings * 100, 2)
                if total_bookings
                else 0,
                "cancellation_rate": round(cancelled / total_bookings * 100, 2)
                if total_bookings
                else 0,
            },
            "duration": {
                "total_hours": round(total_hours, 2),
                "avg_minutes": round(avg_duration, 2),
                "avg_hours": round(avg_duration / 60, 2),
            },
            "revenue": {
                "total": round(total_revenue, 2),
                "avg_per_booking": round(total_revenue / total_bookings, 2)
                if total_bookings
                else 0,
            },
            "team": {
                "member_count": len(members),
                "active_members": len([m for m in members if m.is_active]),
            },
        }

    async def get_booking_trends(
        self, team_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily booking trends for a team.

        Args:
            team_id: Team ID
            days: Number of days to analyze

        Returns:
            List of daily trend data
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        stmt = (
            select(
                func.date(TeamBooking.created_at).label("date"),
                func.count(TeamBooking.id).label("total_bookings"),
                func.count(func.case([(TeamBooking.status == "confirmed", 1)])).label(
                    "confirmed"
                ),
                func.count(func.case([(TeamBooking.status == "cancelled", 1)])).label(
                    "cancelled"
                ),
            )
            .where(
                and_(
                    TeamBooking.team_id == team_id,
                    TeamBooking.created_at >= start_date,
                    TeamBooking.created_at <= end_date,
                )
            )
            .group_by(func.date(TeamBooking.created_at))
            .order_by(func.date(TeamBooking.created_at))
        )

        results = (await self.db.execute(stmt)).all()

        trends = []
        for row in results:
            trends.append(
                {
                    "date": str(row.date),
                    "total": row.total_bookings,
                    "confirmed": row.confirmed,
                    "cancelled": row.cancelled,
                    "net": row.confirmed - row.cancelled,
                }
            )

        return trends

    async def get_member_performance(
        self, team_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance metrics for each team member.

        Args:
            team_id: Team ID
            days: Analysis period

        Returns:
            List of member performance data
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get all members
        stmt = (
            select(TeamMember, UserTable)
            .join(UserTable, TeamMember.user_id == UserTable.id)
            .where(TeamMember.team_id == team_id)
        )

        members = (await self.db.execute(stmt)).all()

        performance = []
        for member, user in members:
            # Get bookings assigned to this member
            stmt = select(TeamBooking).where(
                and_(
                    TeamBooking.team_id == team_id,
                    TeamBooking.assigned_to == member.user_id,
                    TeamBooking.created_at >= start_date,
                    TeamBooking.created_at <= end_date,
                )
            )
            bookings = (await self.db.execute(stmt)).scalars().all()

            confirmed = [b for b in bookings if b.status == "confirmed"]

            performance.append(
                {
                    "member_id": member.id,
                    "user_id": member.user_id,
                    "name": user.full_name or user.email,
                    "role": member.role,
                    "is_active": member.is_active,
                    "metrics": {
                        "total_bookings": len(bookings),
                        "confirmed": len(confirmed),
                        "completion_rate": round(
                            len(confirmed) / len(bookings) * 100, 2
                        )
                        if bookings
                        else 0,
                        "total_duration_hours": sum(
                            [
                                (b.end_time - b.start_time).total_seconds() / 3600
                                for b in confirmed
                                if b.end_time and b.start_time
                            ]
                        ),
                    },
                }
            )

        # Sort by completion rate
        performance.sort(key=lambda x: x["metrics"]["completion_rate"], reverse=True)

        return performance

    async def get_resource_utilization(
        self, team_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get utilization metrics for team resources.

        Args:
            team_id: Team ID
            days: Analysis period

        Returns:
            List of resource utilization data
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get team resources
        stmt = select(Resource).where(
            and_(Resource.team_id == team_id, Resource.is_active == True)
        )
        resources = (await self.db.execute(stmt)).scalars().all()

        utilization = []
        for resource in resources:
            # Get bookings for this resource
            stmt = select(ResourceBooking).where(
                and_(
                    ResourceBooking.resource_id == resource.id,
                    ResourceBooking.status == "approved",
                    ResourceBooking.start_time >= start_date,
                    ResourceBooking.start_time <= end_date,
                )
            )
            bookings = (await self.db.execute(stmt)).scalars().all()

            # Calculate total booked hours
            booked_hours = sum(
                [
                    (b.end_time - b.start_time).total_seconds() / 3600
                    for b in bookings
                    if b.end_time and b.start_time
                ]
            )

            # Calculate available hours (assuming 8 hours/day, business days only)
            total_days = days
            business_days = sum(
                1
                for i in range(total_days)
                if (start_date + timedelta(days=i)).weekday() < 5
            )
            available_hours = business_days * 8  # 8 hours per business day

            utilization_rate = (
                (booked_hours / available_hours * 100) if available_hours else 0
            )

            utilization.append(
                {
                    "resource_id": resource.id,
                    "name": resource.name,
                    "type": resource.resource_type,
                    "location": resource.location,
                    "metrics": {
                        "total_bookings": len(bookings),
                        "booked_hours": round(booked_hours, 2),
                        "available_hours": available_hours,
                        "utilization_rate": round(utilization_rate, 2),
                        "revenue": sum([b.total_cost for b in bookings if b.total_cost])
                        or 0,
                    },
                }
            )

        # Sort by utilization rate
        utilization.sort(key=lambda x: x["metrics"]["utilization_rate"], reverse=True)

        return utilization

    async def get_revenue_analytics(
        self,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get revenue analytics.

        Args:
            team_id: Optional team filter
            user_id: Optional user filter
            days: Analysis period

        Returns:
            Revenue analytics data
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Base query conditions
        conditions = [
            TeamBooking.created_at >= start_date,
            TeamBooking.created_at <= end_date,
            TeamBooking.status == "confirmed",
        ]

        if team_id:
            conditions.append(TeamBooking.team_id == team_id)

        # Get total revenue
        stmt = select(
            func.count(TeamBooking.id).label("total_bookings"),
            func.sum(
                func.coalesce(
                    TeamBooking.metadata_json["revenue"].astext.cast(Float), 0
                )
            ).label("total_revenue"),
        ).where(and_(*conditions))

        result = (await self.db.execute(stmt)).first()

        # Get daily revenue trend
        stmt = (
            select(
                func.date(TeamBooking.created_at).label("date"),
                func.sum(
                    func.coalesce(
                        TeamBooking.metadata_json["revenue"].astext.cast(Float), 0
                    )
                ).label("revenue"),
                func.count(TeamBooking.id).label("bookings"),
            )
            .where(and_(*conditions))
            .group_by(func.date(TeamBooking.created_at))
            .order_by(func.date(TeamBooking.created_at))
        )

        daily_results = (await self.db.execute(stmt)).all()

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "summary": {
                "total_revenue": round(float(result.total_revenue or 0), 2),
                "total_bookings": result.total_bookings,
                "avg_revenue_per_booking": round(
                    float(result.total_revenue or 0) / result.total_bookings, 2
                )
                if result.total_bookings
                else 0,
            },
            "daily_trend": [
                {
                    "date": str(row.date),
                    "revenue": round(float(row.revenue or 0), 2),
                    "bookings": row.bookings,
                }
                for row in daily_results
            ],
        }

    async def get_peak_hours_analysis(
        self, team_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Analyze peak booking hours.

        Args:
            team_id: Team ID
            days: Analysis period

        Returns:
            Peak hours analysis
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        stmt = (
            select(
                extract("hour", TeamBooking.start_time).label("hour"),
                func.count(TeamBooking.id).label("bookings"),
            )
            .where(
                and_(
                    TeamBooking.team_id == team_id,
                    TeamBooking.status == "confirmed",
                    TeamBooking.created_at >= start_date,
                    TeamBooking.created_at <= end_date,
                )
            )
            .group_by(extract("hour", TeamBooking.start_time))
            .order_by(desc("bookings"))
        )

        results = (await self.db.execute(stmt)).all()

        hours_data = {int(row.hour): row.bookings for row in results}

        # Fill in missing hours
        for hour in range(24):
            if hour not in hours_data:
                hours_data[hour] = 0

        return {
            "period": f"Last {days} days",
            "hourly_distribution": [
                {
                    "hour": h,
                    "bookings": c,
                    "period": f"{h:02d}:00-{(h + 1) % 24:02d}:00",
                }
                for h, c in sorted(hours_data.items())
            ],
            "peak_hours": [
                {"hour": int(row.hour), "bookings": row.bookings}
                for row in results[:3]  # Top 3 hours
            ],
        }

    async def get_dashboard_summary(
        self, team_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a comprehensive dashboard summary.

        Args:
            team_id: Optional team filter
            user_id: Optional user filter

        Returns:
            Dashboard summary data
        """
        # Get various time periods
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        periods = {
            "today": (today, now),
            "this_week": (week_start, now),
            "this_month": (month_start, now),
        }

        summary = {}

        for period_name, (start, end) in periods.items():
            # Build conditions
            conditions = [
                TeamBooking.created_at >= start,
                TeamBooking.created_at <= end,
            ]

            if team_id:
                conditions.append(TeamBooking.team_id == team_id)

            # Get bookings for this period
            stmt = select(TeamBooking).where(and_(*conditions))
            bookings = (await self.db.execute(stmt)).scalars().all()

            confirmed = [b for b in bookings if b.status == "confirmed"]
            cancelled = [b for b in bookings if b.status == "cancelled"]

            summary[period_name] = {
                "total": len(bookings),
                "confirmed": len(confirmed),
                "cancelled": len(cancelled),
                "completion_rate": round(len(confirmed) / len(bookings) * 100, 2)
                if bookings
                else 0,
            }

        # Add team-specific data if applicable
        if team_id:
            team_metrics = await self.get_team_metrics(team_id)
            summary["team_metrics"] = team_metrics

            # Upcoming bookings
            stmt = (
                select(TeamBooking)
                .where(
                    and_(
                        TeamBooking.team_id == team_id,
                        TeamBooking.start_time >= now,
                        TeamBooking.status == "confirmed",
                    )
                )
                .order_by(TeamBooking.start_time)
                .limit(5)
            )

            upcoming = (await self.db.execute(stmt)).scalars().all()
            summary["upcoming_bookings"] = [
                {
                    "id": b.id,
                    "title": b.title,
                    "start_time": b.start_time.isoformat(),
                    "attendee_name": b.attendee_name,
                }
                for b in upcoming
            ]

        return {"generated_at": now.isoformat(), "summary": summary}
