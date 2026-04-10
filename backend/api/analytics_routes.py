"""Analytics API routes for usage metrics and insights."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable, BookingTable, EventTypeTable

router = APIRouter(prefix="/analytics", tags=["analytics"])


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
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Get overall analytics overview."""
    # Check if user is admin/owner
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Total bookings
    stmt = select(func.count(BookingTable.id))
    total_bookings = (await db.execute(stmt)).scalar() or 0
    
    # Total revenue (simulated - in production use actual payment data)
    total_revenue = total_bookings * 19.0  # Assuming $19 per booking
    
    # Active users (users with bookings in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    stmt = select(func.count(func.distinct(BookingTable.user_id))).where(
        BookingTable.created_at >= thirty_days_ago
    )
    active_users = (await db.execute(stmt)).scalar() or 0
    
    # Average booking duration
    stmt = select(BookingTable)
    bookings = (await db.execute(stmt)).scalars().all()
    
    total_duration = sum(
        (b.end_time - b.start_time).total_seconds() / 60
        for b in bookings if b.end_time and b.start_time
    )
    avg_booking_duration = total_duration / len(bookings) if bookings else 0
    
    # Conversion rate (bookings / unique visitors - simulated)
    conversion_rate = 0.15  # 15% conversion rate
    
    return AnalyticsOverview(
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        active_users=active_users,
        avg_booking_duration=round(avg_booking_duration, 2),
        conversion_rate=conversion_rate
    )


@router.get("/bookings/timeline")
async def get_booking_timeline(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Get booking metrics over time."""
    # Check if user is admin/owner
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get bookings grouped by day
    stmt = select(
        func.date(BookingTable.created_at).label('date'),
        func.count(BookingTable.id).label('bookings'),
        func.count(func.distinct(BookingTable.user_id)).label('unique_users')
    ).where(
        BookingTable.created_at >= start_date
    ).group_by(
        func.date(BookingTable.created_at)
    ).order_by(
        func.date(BookingTable.created_at)
    )
    
    results = (await db.execute(stmt)).all()
    
    timeline = [
        BookingMetrics(
            date=str(result.date),
            bookings=result.bookings,
            revenue=result.bookings * 19.0,
            unique_users=result.unique_users
        )
        for result in results
    ]
    
    return timeline


@router.get("/event-types")
async def get_event_type_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Get metrics by event type."""
    # Check if user is admin/owner
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get event types with booking counts
    stmt = select(
        EventTypeTable.id,
        EventTypeTable.name,
        func.count(BookingTable.id).label('total_bookings')
    ).outerjoin(
        BookingTable,
        EventTypeTable.id == BookingTable.event_type_id
    ).group_by(
        EventTypeTable.id,
        EventTypeTable.name
    )
    
    results = (await db.execute(stmt)).all()
    
    metrics = [
        EventTypeMetrics(
            event_type_id=result.id,
            event_type_name=result.name,
            total_bookings=result.total_bookings,
            total_revenue=result.total_bookings * 19.0,
            avg_duration=30.0  # Default duration
        )
        for result in results
    ]
    
    return metrics


@router.get("/user/{user_id}")
async def get_user_analytics(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Get analytics for a specific user."""
    # Users can only view their own analytics or if they're admin
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get user's bookings
    stmt = select(BookingTable).where(
        and_(
            BookingTable.user_id == user_id,
            BookingTable.created_at >= start_date
        )
    )
    bookings = (await db.execute(stmt)).scalars().all()
    
    # Get user's event types
    stmt = select(EventTypeTable).where(EventTypeTable.user_id == user_id)
    event_types = (await db.execute(stmt)).scalars().all()
    
    return {
        "user_id": user_id,
        "period_days": days,
        "total_bookings": len(bookings),
        "total_event_types": len(event_types),
        "bookings": [
            {
                "id": b.id,
                "title": b.title,
                "start_time": b.start_time.isoformat() if b.start_time else None,
                "end_time": b.end_time.isoformat() if b.end_time else None,
                "status": b.status,
            }
            for b in bookings
        ]
    }


@router.get("/realtime")
async def get_realtime_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Get real-time metrics for dashboard."""
    # Check if user is admin/owner
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Bookings in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    stmt = select(func.count(BookingTable.id)).where(
        BookingTable.created_at >= one_hour_ago
    )
    bookings_last_hour = (await db.execute(stmt)).scalar() or 0
    
    # Active users in last hour
    stmt = select(func.count(func.distinct(BookingTable.user_id))).where(
        BookingTable.created_at >= one_hour_ago
    )
    active_users_last_hour = (await db.execute(stmt)).scalar() or 0
    
    # Total users
    stmt = select(func.count(UserTable.id))
    total_users = (await db.execute(stmt)).scalar() or 0
    
    # Total event types
    stmt = select(func.count(EventTypeTable.id))
    total_event_types = (await db.execute(stmt)).scalar() or 0
    
    return {
        "bookings_last_hour": bookings_last_hour,
        "active_users_last_hour": active_users_last_hour,
        "total_users": total_users,
        "total_event_types": total_event_types,
        "timestamp": datetime.utcnow().isoformat()
    }
