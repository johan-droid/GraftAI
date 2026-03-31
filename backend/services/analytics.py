from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from backend.auth.schemes import get_current_user_id
from backend.models.tables import EventTable
from backend.utils.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta, timezone

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


class AnalyticsRequest(BaseModel):
    organization_id: Optional[int] = None
    range: Optional[str] = "7d"


class AnalyticsResponse(BaseModel):
    summary: str
    details: Optional[dict] = None


@router.get("/summary", response_model=AnalyticsResponse)
async def analytics_summary(
    range: str = "7d",
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    High-Fidelity Analytics Engine.
    Aggregates real-time data from the EventTable to provide actionable insights.
    """
    logger.info(f"Analytics summary requested by user: {user_id}")

    # Calculate time range using aware UTC datetime
    now = datetime.now(timezone.utc)
    if range == "7d":
        start_date = now - timedelta(days=7)
    elif range == "30d":
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)

    try:
        # 1. Total Meetings Count
        count_stmt = select(func.count(EventTable.id)).where(
            and_(EventTable.user_id == user_id, EventTable.start_time >= start_date)
        )
        count_result = await db.execute(count_stmt)
        meetings_count = count_result.scalar() or 0

        # 2. Total Hours Scheduled
        # Using a direct select to sum durations (end_time - start_time)
        duration_stmt = select(EventTable.start_time, EventTable.end_time).where(
            and_(EventTable.user_id == user_id, EventTable.start_time >= start_date)
        )
        duration_result = await db.execute(duration_stmt)
        total_hours = 0.0
        for start, end in duration_result:
            total_hours += (end - start).total_seconds() / 3600

        # 3. Growth Calculation (Comparison with previous period)
        prev_start = start_date - (now - start_date)
        prev_count_stmt = select(func.count(EventTable.id)).where(
            and_(
                EventTable.user_id == user_id,
                EventTable.start_time >= prev_start,
                EventTable.start_time < start_date,
            )
        )
        prev_count_result = await db.execute(prev_count_stmt)
        prev_meetings = prev_count_result.scalar() or 0

        growth = 0
        if prev_meetings > 0:
            growth = int(((meetings_count - prev_meetings) / prev_meetings) * 100)
        elif meetings_count > 0:
            growth = 100  # First week growth

        # 4. Next/Recent Activity List
        activity_stmt = select(EventTable).where(
            EventTable.user_id == user_id
        ).order_by(EventTable.start_time.desc()).limit(5)
        activity_result = await db.execute(activity_stmt)
        activity_list = []
        for event in activity_result.scalars():
            activity_list.append({
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time.isoformat(),
                "category": event.category,
                "is_upcoming": event.start_time >= now
            })

        if meetings_count > 0:
            summary_text = f"You've got {meetings_count} meetings on the books for the last {range}. That's about {total_hours:.1f} hours of focused time coordinated by your AI Copilot."
        else:
            summary_text = f"Your calendar is clear! No meetings scheduled in the last {range}. Perfect time for some deep work."

        return AnalyticsResponse(
            summary=summary_text,
            details={
                "meetings": meetings_count,
                "hours": round(total_hours, 1),
                "growth": growth,
                "recent_events": activity_list,
                "next_event": activity_list[0] if activity_list and activity_list[0]["is_upcoming"] else None
            },
        )
    except Exception as e:
        logger.error(f"Analytics engine failure: {e}")
        return AnalyticsResponse(
            summary="We're having a bit of trouble crunching your latest numbers, but we'll have them back up shortly.",
            details={"meetings": 0, "hours": 0, "growth": 0, "next_event": None},
        )
