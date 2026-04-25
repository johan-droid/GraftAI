import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable
from backend.services.scheduler import get_events_for_range

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


def _parse_range_window(range_str: str) -> int:
    if range_str.endswith("d") and range_str[:-1].isdigit():
        return int(range_str[:-1])
    return 30


@router.get("/summary")
@router.post("/summary")
async def analytics_summary(
    range: str = Query("30d", description="Time range, e.g. 7d, 30d, 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    days = _parse_range_window(range)
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    end = now + timedelta(days=days)
    events = await get_events_for_range(db, str(current_user.id), start, end)

    meetings = len(events)
    hours = sum(
        max(0, (event["end_time"] - event["start_time"]).total_seconds() / 3600)
        for event in events
        if event.get("end_time") and event.get("start_time")
    )

    sorted_events = sorted(events, key=lambda e: e["start_time"], reverse=True)
    recent_events = [
        {
            "id": event["id"],
            "title": event["title"],
            "start_time": event["start_time"].isoformat(),
            "category": event.get("source", "event"),
            "is_upcoming": event["start_time"] > now,
        }
        for event in sorted_events[:5]
    ]

    upcoming = [e for e in events if e["start_time"] and e["start_time"] > now]
    next_event = None
    if upcoming:
        next_one = min(upcoming, key=lambda event: event["start_time"])
        next_event = {
            "id": next_one["id"],
            "title": next_one["title"],
            "start_time": next_one["start_time"].isoformat(),
            "category": next_one.get("source", "event"),
            "is_upcoming": True,
        }

    return {
        "summary": f"You have {meetings} meetings over the past {days} days.",
        "details": {
            "meetings": meetings,
            "hours": round(hours, 1),
            "growth": 0,
            "cancellations": 0,
            "recent_events": recent_events,
            "next_event": next_event,
        },
    }


@router.get("/realtime")
async def analytics_realtime(
    range: str = Query("30d", description="Time range, e.g. 7d, 30d, 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    days = _parse_range_window(range)
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    end = now + timedelta(days=days)
    events = await get_events_for_range(db, str(current_user.id), start, end)

    meetings = len(events)
    hours = sum(
        max(0, (event["end_time"] - event["start_time"]).total_seconds() / 3600)
        for event in events
        if event.get("end_time") and event.get("start_time")
    )

    recent_events = [
        {
            "id": event["id"],
            "title": event["title"],
            "start_time": event["start_time"].isoformat(),
            "category": event.get("source", "event"),
            "is_upcoming": event["start_time"] > now,
        }
        for event in sorted(events, key=lambda e: e["start_time"], reverse=True)[:5]
    ]

    return {
        "summary": f"Realtime summary for the last {days} days.",
        "range": range,
        "generated_at": now.isoformat(),
        "totals": {
            "meetings": meetings,
            "hours": round(hours, 1),
            "growth": 0,
            "unique_attendees": 0,
            "cancellations": 0,
        },
        "series": [],
        "meeting_types": [],
        "peak_hours": [],
        "recent_events": recent_events,
        "next_event": recent_events[0] if recent_events else None,
    }
