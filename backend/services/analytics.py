from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from backend.auth.schemes import get_current_user_id
from backend.models.tables import EventTable
from backend.utils.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


class AnalyticsRequest(BaseModel):
    organization_id: Optional[int] = None
    range: Optional[str] = "7d"


class AnalyticsResponse(BaseModel):
    summary: str
    details: Optional[dict] = None


@router.post("/summary", response_model=AnalyticsResponse)
async def analytics_summary(
    request: AnalyticsRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    High-Fidelity Analytics Engine.
    Aggregates real-time data from the EventTable to provide actionable insights.
    """
    logger.info(f"Analytics summary requested by user: {user_id}")

    # Calculate time range
    now = datetime.now()
    if request.range == "7d":
        start_date = now - timedelta(days=7)
    elif request.range == "30d":
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

        summary_text = f"You have {meetings_count} meetings scheduled for the last {request.range}. Total value delivered: {total_hours:.1f} hours."

        return AnalyticsResponse(
            summary=summary_text,
            details={
                "meetings": meetings_count,
                "hours": round(total_hours, 1),
                "growth": growth,
            },
        )
    except Exception as e:
        logger.error(f"Analytics engine failure: {e}")
        return AnalyticsResponse(
            summary="Analytics temporarily unavailable due to a processing error.",
            details={"meetings": 0, "hours": 0, "growth": 0},
        )
