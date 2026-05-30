"""Analytics API routes for usage metrics and insights."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.tables import BookingTable, EventTypeTable, UserTable

router = APIRouter(prefix="/analytics", tags=["analytics"])

def _is_admin(user: UserTable) -> bool:
    tier = (getattr(user, "tier", "") or "").strip().lower()
    if tier in {"admin", "elite"}:
        return True
    preferences = getattr(user, "preferences", None)
    if isinstance(preferences, dict):
        role = str(preferences.get("role", "")).strip().lower()
        if role in {"admin", "elite", "owner"}:
            return True
    return False

class AnalyticsOverview(BaseModel):
    total_bookings: int
    total_revenue: float
    active_users: int
    avg_booking_duration: float
    conversion_rate: float

class BookingMetrics(BaseModel):
    date: str
    bookings: int
    revenue: float
    unique_users: int

class EventTypeMetrics(BaseModel):
    event_type_id: str
    event_type_name: str
    total_bookings: int
    total_revenue: float
    avg_duration: float

@router.get("/overview")
async def get_analytics_overview(db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Get overall analytics overview."""
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    stmt = select(func.count(BookingTable.id))
    total_bookings = (await db.execute(stmt)).scalar() or 0
    total_revenue = total_bookings * 19.0
    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    stmt = select(func.count(func.distinct(BookingTable.user_id))).where(BookingTable.created_at >= thirty_days_ago)
    active_users = (await db.execute(stmt)).scalar() or 0
    stmt = select(BookingTable)
    bookings = (await db.execute(stmt)).scalars().all()
    total_duration = sum((b.end_time - b.start_time).total_seconds() / 60 for b in bookings if b.end_time and b.start_time)
    avg_booking_duration = total_duration / len(bookings) if bookings else 0
    conversion_rate = 0.15
    return AnalyticsOverview(total_bookings=total_bookings, total_revenue=total_revenue, active_users=active_users, avg_booking_duration=round(avg_booking_duration, 2), conversion_rate=conversion_rate)

@router.get("/bookings/timeline")
async def get_booking_timeline(days: int=Query(30, ge=1, le=365), db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Get booking metrics over time."""
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    start_date = datetime.now(UTC) - timedelta(days=days)
    stmt = select(func.date(BookingTable.created_at).label("date"), func.count(BookingTable.id).label("bookings"), func.count(func.distinct(BookingTable.user_id)).label("unique_users")).where(BookingTable.created_at >= start_date).group_by(func.date(BookingTable.created_at)).order_by(func.date(BookingTable.created_at))
    results = (await db.execute(stmt)).all()
    return [BookingMetrics(date=str(result.date), bookings=result.bookings, revenue=result.bookings * 19.0, unique_users=result.unique_users) for result in results]

@router.get("/event-types")
async def get_event_type_metrics(db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Get metrics by event type."""
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    stmt = select(EventTypeTable.id, EventTypeTable.name, func.count(BookingTable.id).label("total_bookings")).outerjoin(BookingTable, EventTypeTable.id == BookingTable.event_type_id).group_by(EventTypeTable.id, EventTypeTable.name)
    results = (await db.execute(stmt)).all()
    return [EventTypeMetrics(event_type_id=result.id, event_type_name=result.name, total_bookings=result.total_bookings, total_revenue=result.total_bookings * 19.0, avg_duration=30.0) for result in results]

@router.get("/user/{user_id}")
async def get_user_analytics(user_id: str, days: int=Query(30, ge=1, le=365), db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Get analytics for a specific user."""
    if current_user.id != user_id and (not _is_admin(current_user)):
        raise HTTPException(status_code=403, detail="Access denied")
    start_date = datetime.now(UTC) - timedelta(days=days)
    stmt = select(BookingTable).where(and_(BookingTable.user_id == user_id, BookingTable.created_at >= start_date))
    bookings = (await db.execute(stmt)).scalars().all()
    stmt = select(EventTypeTable).where(EventTypeTable.user_id == user_id)
    event_types = (await db.execute(stmt)).scalars().all()
    return {"user_id": user_id, "period_days": days, "total_bookings": len(bookings), "total_event_types": len(event_types), "bookings": [{"id": b.id, "title": b.title, "start_time": b.start_time.isoformat() if b.start_time else None, "end_time": b.end_time.isoformat() if b.end_time else None, "status": b.status} for b in bookings]}

@router.get("/realtime")
async def get_realtime_metrics(db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Get real-time metrics for dashboard."""
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    stmt = select(func.count(BookingTable.id)).where(BookingTable.created_at >= one_hour_ago)
    bookings_last_hour = (await db.execute(stmt)).scalar() or 0
    stmt = select(func.count(func.distinct(BookingTable.user_id))).where(BookingTable.created_at >= one_hour_ago)
    active_users_last_hour = (await db.execute(stmt)).scalar() or 0
    stmt = select(func.count(UserTable.id))
    total_users = (await db.execute(stmt)).scalar() or 0
    stmt = select(func.count(EventTypeTable.id))
    total_event_types = (await db.execute(stmt)).scalar() or 0
    return {"bookings_last_hour": bookings_last_hour, "active_users_last_hour": active_users_last_hour, "total_users": total_users, "total_event_types": total_event_types, "timestamp": datetime.now(UTC).isoformat()}

@router.get("/summary")
async def get_user_dashboard_summary(db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Get dashboard summary for current user (non-admin endpoint)."""
    from backend.models.tables import EventTable
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    week_end = week_start + timedelta(days=7)
    week_start_naive = week_start.replace(tzinfo=None)
    week_end_naive = week_end.replace(tzinfo=None)
    now_naive = now.replace(tzinfo=None)
    tomorrow_naive = (now + timedelta(days=1)).replace(tzinfo=None)
    stmt = select(BookingTable).where(and_(BookingTable.user_id == current_user.id, BookingTable.start_time >= week_start_naive, BookingTable.start_time < week_end_naive, BookingTable.status != "cancelled"))
    bookings = (await db.execute(stmt)).scalars().all()
    total_hours = 0.0
    for b in bookings:
        if b.end_time and b.start_time:
            duration = (b.end_time - b.start_time).total_seconds() / 3600
            total_hours += duration
    prev_week_start_naive = (week_start - timedelta(days=7)).replace(tzinfo=None)
    prev_week_end_naive = week_start.replace(tzinfo=None)
    stmt = select(func.count(BookingTable.id)).where(and_(BookingTable.user_id == current_user.id, BookingTable.start_time >= prev_week_start_naive, BookingTable.start_time < prev_week_end_naive, BookingTable.status != "cancelled"))
    prev_week_count = (await db.execute(stmt)).scalar() or 0
    current_week_count = len(bookings)
    if prev_week_count > 0:
        growth = round((current_week_count - prev_week_count) / prev_week_count * 100)
    else:
        growth = 100 if current_week_count > 0 else 0
    stmt = select(func.count(EventTable.id)).where(and_(EventTable.user_id == current_user.id, EventTable.start_time >= now_naive, EventTable.start_time <= tomorrow_naive, EventTable.source != "deleted"))
    upcoming_today = (await db.execute(stmt)).scalar() or 0
    suggestions_count = 0
    if current_user.preferences and isinstance(current_user.preferences, dict):
        suggestions_count = current_user.preferences.get("pending_suggestions", 0)
    return {"summary": f"You have {current_week_count} meetings this week with {upcoming_today} events today.", "details": {"meetings": current_week_count, "hours": round(total_hours, 1), "growth": growth, "previousWeekMeetings": prev_week_count, "upcomingToday": upcoming_today, "suggestions": suggestions_count}}
