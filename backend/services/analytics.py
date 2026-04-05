from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes import get_current_user_id
from backend.models.tables import EventTable
from backend.utils.db import get_db

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


class AnalyticsRequest(BaseModel):
    organization_id: Optional[int] = None
    range: Optional[str] = "7d"


class AnalyticsResponse(BaseModel):
    summary: str
    details: Optional[dict] = None


class AnalyticsSeriesPoint(BaseModel):
    bucket: str
    meetings: int
    hours: float
    categories: Optional[Dict[str, int]] = None
    dominant_category: Optional[str] = None


class AnalyticsDistributionPoint(BaseModel):
    label: str
    count: int
    pct: int


class AnalyticsPeakHourPoint(BaseModel):
    hour: str
    count: int


class AnalyticsRealtimeResponse(BaseModel):
    summary: str
    range: str
    generated_at: str
    totals: Dict[str, Any]
    series: List[AnalyticsSeriesPoint]
    meeting_types: List[AnalyticsDistributionPoint]
    peak_hours: List[AnalyticsPeakHourPoint]
    recent_events: List[Dict[str, Any]]
    next_event: Optional[Dict[str, Any]] = None


def _resolve_range_days(range_value: str) -> int:
    value = (range_value or "7d").strip().lower()
    if value == "7d":
        return 7
    if value == "30d":
        return 30
    if value == "90d":
        return 90
    return 7


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _extract_attendee_emails(attendees: Any) -> set[str]:
    emails: set[str] = set()
    if not isinstance(attendees, list):
        return emails

    for item in attendees:
        if isinstance(item, dict):
            email = item.get("email")
            if isinstance(email, str) and email.strip():
                emails.add(email.strip().lower())
        elif isinstance(item, str) and item.strip():
            emails.add(item.strip().lower())

    return emails


async def _fetch_events_for_range(
    db: AsyncSession,
    user_id: str,
    start_date: datetime,
    end_date: datetime,
) -> List[EventTable]:
    stmt = (
        select(EventTable)
        .where(
            and_(
                EventTable.user_id == user_id,
                EventTable.start_time >= start_date,
                EventTable.start_time <= end_date,
            )
        )
        .order_by(EventTable.start_time.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _build_analytics_payload(
    events: List[EventTable],
    start_date: datetime,
    end_date: datetime,
    now: datetime,
) -> Dict[str, Any]:
    meeting_count = len(events)
    total_hours = 0.0

    category_counter: Counter[str] = Counter()
    hour_counter: Counter[int] = Counter()
    unique_attendees: set[str] = set()
    cancelled_count = 0

    per_day_meetings: Dict[str, int] = {}
    per_day_hours: Dict[str, float] = {}
    per_day_category: Dict[str, Counter[str]] = {}

    cursor = start_date.date()
    while cursor <= end_date.date():
        key = cursor.isoformat()
        per_day_meetings[key] = 0
        per_day_hours[key] = 0.0
        per_day_category[key] = Counter()
        cursor += timedelta(days=1)

    upcoming_events = sorted(
        events,
        key=lambda x: _as_utc(getattr(x, "start_time")),
    )

    recent_events = upcoming_events[:5]

    next_event = None
    if upcoming_events:
        candidate = upcoming_events[0]
        next_event = {
            "id": int(getattr(candidate, "id")),
            "title": str(getattr(candidate, "title")),
            "start_time": _as_utc(getattr(candidate, "start_time")).isoformat(),
            "category": str(getattr(candidate, "category")),
            "is_upcoming": True,
        }

    for event in events:
        start_utc = _as_utc(getattr(event, "start_time"))
        end_utc = _as_utc(getattr(event, "end_time"))
        duration_hours = max(0.0, (end_utc - start_utc).total_seconds() / 3600)

        total_hours += duration_hours
        event_category = str(getattr(event, "category") or "other")
        category_counter[event_category] += 1
        hour_counter[start_utc.hour] += 1
        unique_attendees |= _extract_attendee_emails(getattr(event, "attendees"))

        if str(getattr(event, "status") or "").lower() in {"canceled", "cancelled"}:
            cancelled_count += 1

        day_key = start_utc.date().isoformat()
        if day_key in per_day_meetings:
            per_day_meetings[day_key] += 1
            per_day_hours[day_key] += duration_hours
            per_day_category[day_key][event_category] += 1

    growth = 0

    total_days = max(1, (end_date.date() - start_date.date()).days + 1)
    use_short_label = total_days <= 14

    series: List[Dict[str, Any]] = []
    for day_key in sorted(per_day_meetings.keys()):
        dt = datetime.fromisoformat(day_key).replace(tzinfo=timezone.utc)
        bucket = dt.strftime("%a") if use_short_label else dt.strftime("%m-%d")
        categories_counter = per_day_category.get(day_key, Counter())
        dominant = None
        if categories_counter:
            dominant = categories_counter.most_common(1)[0][0]
        series.append(
            {
                "bucket": bucket,
                "meetings": per_day_meetings[day_key],
                "hours": round(per_day_hours[day_key], 2),
                "categories": dict(categories_counter),
                "dominant_category": dominant,
            }
        )

    total_for_pct = max(1, meeting_count)
    meeting_types = [
        {
            "label": label,
            "count": count,
            "pct": int((count / total_for_pct) * 100),
        }
        for label, count in category_counter.most_common()
    ]

    peak_hours = [
        {
            "hour": f"{hour:02d}:00",
            "count": count,
        }
        for hour, count in hour_counter.most_common(4)
    ]

    recent_events_payload = [
        {
            "id": int(getattr(item, "id")),
            "title": str(getattr(item, "title")),
            "start_time": _as_utc(getattr(item, "start_time")).isoformat(),
            "category": str(getattr(item, "category") or "other"),
            "is_upcoming": _as_utc(getattr(item, "start_time")) >= now,
        }
        for item in recent_events
    ]

    if meeting_count == 0:
        summary = "No current or upcoming meetings found in this window."
    else:
        summary = (
            f"{meeting_count} current/upcoming meetings across {round(total_hours, 1)}h "
            f"in the next {max(1, (end_date.date() - start_date.date()).days + 1)} days."
        )

    return {
        "summary": summary,
        "totals": {
            "meetings": meeting_count,
            "hours": round(total_hours, 1),
            "growth": growth,
            "unique_attendees": len(unique_attendees),
            "cancellations": cancelled_count,
        },
        "series": series,
        "meeting_types": meeting_types,
        "peak_hours": peak_hours,
        "recent_events": recent_events_payload,
        "next_event": next_event,
    }


@router.get("/summary", response_model=AnalyticsResponse)
async def analytics_summary(
    range: str = "7d",
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Real-time summary metrics backed directly by current event records."""
    now = datetime.now(timezone.utc)
    days = _resolve_range_days(range)
    start_date = now
    end_date = now + timedelta(days=days)

    try:
        events = await _fetch_events_for_range(db, user_id, start_date, end_date)

        payload = _build_analytics_payload(
            events=events,
            start_date=start_date,
            end_date=end_date,
            now=now,
        )

        details = {
            "meetings": payload["totals"]["meetings"],
            "hours": payload["totals"]["hours"],
            "growth": payload["totals"]["growth"],
            "recent_events": payload["recent_events"],
            "next_event": payload["next_event"],
            "unique_attendees": payload["totals"]["unique_attendees"],
            "cancellations": payload["totals"]["cancellations"],
        }
        return AnalyticsResponse(summary=payload["summary"], details=details)
    except Exception as exc:
        logger.exception(f"Analytics summary failure for user {user_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to compute analytics summary")


@router.get("/realtime", response_model=AnalyticsRealtimeResponse)
async def analytics_realtime(
    range: str = "30d",
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Returns graph-ready real-time analytics for dashboard charts."""
    now = datetime.now(timezone.utc)
    days = _resolve_range_days(range)
    start_date = now
    end_date = now + timedelta(days=days)

    try:
        events = await _fetch_events_for_range(db, user_id, start_date, end_date)

        payload = _build_analytics_payload(
            events=events,
            start_date=start_date,
            end_date=end_date,
            now=now,
        )

        return AnalyticsRealtimeResponse(
            summary=payload["summary"],
            range=range,
            generated_at=now.isoformat(),
            totals=payload["totals"],
            series=payload["series"],
            meeting_types=payload["meeting_types"],
            peak_hours=payload["peak_hours"],
            recent_events=payload["recent_events"],
            next_event=payload["next_event"],
        )
    except Exception as exc:
        logger.exception(f"Analytics realtime failure for user {user_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to compute realtime analytics")
