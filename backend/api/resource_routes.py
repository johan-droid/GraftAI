"""API routes for resource booking (rooms, equipment, etc.)."""

from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable
from backend.models.resource import Resource, ResourceBooking
from backend.models.team import TeamMember, TeamRole

router = APIRouter(prefix="/resources", tags=["resources"])


# Pydantic Models


class ResourceCreate(BaseModel):
    """Create resource request."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    resource_type: str = Field(..., pattern="^(room|equipment|vehicle|desk|other)$")
    location: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    floor: Optional[str] = None
    room_number: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=1)
    features: List[str] = Field(default=[])
    amenities: List[str] = Field(default=[])
    team_id: Optional[str] = None
    min_booking_duration: int = Field(default=15, ge=5)
    max_booking_duration: int = Field(default=480, ge=15)
    min_notice_hours: int = Field(default=0, ge=0)
    max_booking_days_ahead: int = Field(default=30, ge=1)
    hourly_rate: Optional[float] = None
    requires_approval: bool = False
    approver_ids: List[str] = Field(default=[])


class ResourceUpdate(BaseModel):
    """Update resource request."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    features: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    is_active: Optional[bool] = None
    min_booking_duration: Optional[int] = None
    max_booking_duration: Optional[int] = None
    requires_approval: Optional[bool] = None
    hourly_rate: Optional[float] = None


class ResourceResponse(BaseModel):
    """Resource response."""

    id: str
    name: str
    description: Optional[str]
    resource_type: str
    location: str
    capacity: Optional[int]
    features: List[str]
    amenities: List[str]
    is_active: bool
    min_booking_duration: int
    max_booking_duration: int
    hourly_rate: Optional[float]
    requires_approval: bool


class ResourceBookingRequest(BaseModel):
    """Book resource request."""

    resource_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    attendees: int = Field(default=1, ge=1)
    booking_id: Optional[str] = None  # Associated booking


class ResourceBookingResponse(BaseModel):
    """Resource booking response."""

    id: str
    resource_id: str
    resource_name: str
    user_id: str
    title: str
    start_time: datetime
    end_time: datetime
    status: str
    total_cost: Optional[float]


class ResourceAvailabilityRequest(BaseModel):
    """Check resource availability."""

    start_date: datetime
    end_date: datetime


# Routes


@router.post("/", response_model=ResourceResponse)
async def create_resource(
    resource: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Create a new resource (room, equipment, etc.)."""
    # If team_id provided, verify membership
    if resource.team_id:
        stmt = select(TeamMember).where(
            and_(
                TeamMember.team_id == resource.team_id,
                TeamMember.user_id == current_user.id,
                TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN]),
            )
        )
        team_member = (await db.execute(stmt)).scalars().first()
        if not team_member:
            raise HTTPException(
                status_code=403, detail="Not authorized to add resources to this team"
            )

    new_resource = Resource(
        name=resource.name,
        description=resource.description,
        resource_type=resource.resource_type,
        location=resource.location,
        address=resource.address,
        floor=resource.floor,
        room_number=resource.room_number,
        capacity=resource.capacity,
        features=resource.features,
        amenities=resource.amenities,
        owner_id=current_user.id,
        team_id=resource.team_id,
        min_booking_duration=resource.min_booking_duration,
        max_booking_duration=resource.max_booking_duration,
        min_notice_hours=resource.min_notice_hours,
        max_booking_days_ahead=resource.max_booking_days_ahead,
        hourly_rate=resource.hourly_rate,
        requires_approval=resource.requires_approval,
        approver_ids=resource.approver_ids if resource.requires_approval else [],
    )

    db.add(new_resource)
    await db.commit()
    await db.refresh(new_resource)

    return ResourceResponse(
        id=new_resource.id,
        name=new_resource.name,
        description=new_resource.description,
        resource_type=new_resource.resource_type,
        location=new_resource.location,
        capacity=new_resource.capacity,
        features=new_resource.features,
        amenities=new_resource.amenities,
        is_active=new_resource.is_active,
        min_booking_duration=new_resource.min_booking_duration,
        max_booking_duration=new_resource.max_booking_duration,
        hourly_rate=new_resource.hourly_rate,
        requires_approval=new_resource.requires_approval,
    )


@router.get("/", response_model=List[ResourceResponse])
async def list_resources(
    resource_type: Optional[str] = None,
    location: Optional[str] = None,
    team_id: Optional[str] = None,
    available_from: Optional[datetime] = None,
    available_to: Optional[datetime] = None,
    min_capacity: Optional[int] = None,
    features: Optional[List[str]] = Query(default=None),
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """List available resources."""
    stmt = select(Resource).where(Resource.is_active == True).limit(limit)

    # Filter by type
    if resource_type:
        stmt = stmt.where(Resource.resource_type == resource_type)

    # Filter by location
    if location:
        stmt = stmt.where(Resource.location.ilike(f"%{location}%"))

    # Filter by team
    if team_id:
        stmt = stmt.where(Resource.team_id == team_id)
    else:
        # Show user's own resources and team resources
        stmt = stmt.where(
            or_(
                Resource.owner_id == current_user.id,
                Resource.team_id.in_(
                    select(TeamMember.team_id).where(
                        TeamMember.user_id == current_user.id
                    )
                ),
            )
        )

    # Filter by capacity
    if min_capacity:
        stmt = stmt.where(Resource.capacity >= min_capacity)

    # Filter by features
    if features:
        for feature in features:
            stmt = stmt.where(Resource.features.contains([feature]))

    resources = (await db.execute(stmt)).scalars().all()

    # Filter by availability if requested
    if available_from and available_to:
        available_resources = []
        for resource in resources:
            # Check for conflicting bookings
            stmt = select(ResourceBooking).where(
                and_(
                    ResourceBooking.resource_id == resource.id,
                    ResourceBooking.status.in_(["approved", "pending"]),
                    or_(
                        and_(
                            ResourceBooking.start_time <= available_from,
                            ResourceBooking.end_time > available_from,
                        ),
                        and_(
                            ResourceBooking.start_time < available_to,
                            ResourceBooking.end_time >= available_to,
                        ),
                        and_(
                            ResourceBooking.start_time >= available_from,
                            ResourceBooking.end_time <= available_to,
                        ),
                    ),
                )
            )
            conflicting = (await db.execute(stmt)).scalars().first()
            if not conflicting:
                available_resources.append(resource)
        resources = available_resources

    return [
        ResourceResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            resource_type=r.resource_type,
            location=r.location,
            capacity=r.capacity,
            features=r.features,
            amenities=r.amenities,
            is_active=r.is_active,
            min_booking_duration=r.min_booking_duration,
            max_booking_duration=r.max_booking_duration,
            hourly_rate=r.hourly_rate,
            requires_approval=r.requires_approval,
        )
        for r in resources
    ]


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get resource details."""
    stmt = select(Resource).where(
        and_(
            Resource.id == resource_id,
            or_(
                Resource.owner_id == current_user.id,
                Resource.team_id.in_(
                    select(TeamMember.team_id).where(
                        TeamMember.user_id == current_user.id
                    )
                ),
            ),
        )
    )
    resource = (await db.execute(stmt)).scalars().first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    return ResourceResponse(
        id=resource.id,
        name=resource.name,
        description=resource.description,
        resource_type=resource.resource_type,
        location=resource.location,
        capacity=resource.capacity,
        features=resource.features,
        amenities=resource.amenities,
        is_active=resource.is_active,
        min_booking_duration=resource.min_booking_duration,
        max_booking_duration=resource.max_booking_duration,
        hourly_rate=resource.hourly_rate,
        requires_approval=resource.requires_approval,
    )


@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    update: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Update a resource."""
    stmt = select(Resource).where(
        and_(Resource.id == resource_id, Resource.owner_id == current_user.id)
    )
    resource = (await db.execute(stmt)).scalars().first()

    if not resource:
        # Check if team admin
        stmt = select(Resource).where(
            and_(
                Resource.id == resource_id,
                Resource.team_id.in_(
                    select(TeamMember.team_id).where(
                        and_(
                            TeamMember.user_id == current_user.id,
                            TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN]),
                        )
                    )
                ),
            )
        )
        resource = (await db.execute(stmt)).scalars().first()

    if not resource:
        raise HTTPException(
            status_code=404, detail="Resource not found or access denied"
        )

    # Update fields
    if update.name is not None:
        resource.name = update.name
    if update.description is not None:
        resource.description = update.description
    if update.location is not None:
        resource.location = update.location
    if update.capacity is not None:
        resource.capacity = update.capacity
    if update.features is not None:
        resource.features = update.features
    if update.amenities is not None:
        resource.amenities = update.amenities
    if update.is_active is not None:
        resource.is_active = update.is_active
    if update.min_booking_duration is not None:
        resource.min_booking_duration = update.min_booking_duration
    if update.max_booking_duration is not None:
        resource.max_booking_duration = update.max_booking_duration
    if update.requires_approval is not None:
        resource.requires_approval = update.requires_approval
    if update.hourly_rate is not None:
        resource.hourly_rate = update.hourly_rate

    await db.commit()
    await db.refresh(resource)

    return ResourceResponse(
        id=resource.id,
        name=resource.name,
        description=resource.description,
        resource_type=resource.resource_type,
        location=resource.location,
        capacity=resource.capacity,
        features=resource.features,
        amenities=resource.amenities,
        is_active=resource.is_active,
        min_booking_duration=resource.min_booking_duration,
        max_booking_duration=resource.max_booking_duration,
        hourly_rate=resource.hourly_rate,
        requires_approval=resource.requires_approval,
    )


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Delete a resource."""
    stmt = select(Resource).where(
        and_(Resource.id == resource_id, Resource.owner_id == current_user.id)
    )
    resource = (await db.execute(stmt)).scalars().first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    await db.delete(resource)
    await db.commit()

    return {"status": "success", "message": "Resource deleted"}


@router.post("/bookings", response_model=ResourceBookingResponse)
async def book_resource(
    request: ResourceBookingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Book a resource."""
    # Get resource
    stmt = select(Resource).where(
        and_(Resource.id == request.resource_id, Resource.is_active == True)
    )
    resource = (await db.execute(stmt)).scalars().first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Check availability
    stmt = select(ResourceBooking).where(
        and_(
            ResourceBooking.resource_id == request.resource_id,
            ResourceBooking.status.in_(["approved", "pending"]),
            or_(
                and_(
                    ResourceBooking.start_time <= request.start_time,
                    ResourceBooking.end_time > request.start_time,
                ),
                and_(
                    ResourceBooking.start_time < request.end_time,
                    ResourceBooking.end_time >= request.end_time,
                ),
                and_(
                    ResourceBooking.start_time >= request.start_time,
                    ResourceBooking.end_time <= request.end_time,
                ),
            ),
        )
    )
    conflicting = (await db.execute(stmt)).scalars().first()
    if conflicting:
        raise HTTPException(
            status_code=409, detail="Resource not available for requested time"
        )

    # Check capacity
    if resource.capacity and request.attendees > resource.capacity:
        raise HTTPException(
            status_code=400, detail=f"Exceeds capacity of {resource.capacity}"
        )

    # Check duration limits
    duration = (request.end_time - request.start_time).total_seconds() / 60
    if duration < resource.min_booking_duration:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum booking duration is {resource.min_booking_duration} minutes",
        )
    if duration > resource.max_booking_duration:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum booking duration is {resource.max_booking_duration} minutes",
        )

    # Check notice requirement
    if resource.min_notice_hours > 0:
        min_start = datetime.now(timezone.utc) + timedelta(
            hours=resource.min_notice_hours
        )
        if request.start_time < min_start:
            raise HTTPException(
                status_code=400,
                detail=f"Must book at least {resource.min_notice_hours} hours in advance",
            )

    # Calculate cost
    total_cost = None
    if resource.hourly_rate:
        hours = duration / 60
        total_cost = hours * resource.hourly_rate

    # Create booking
    booking = ResourceBooking(
        resource_id=request.resource_id,
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        start_time=request.start_time,
        end_time=request.end_time,
        attendees=request.attendees,
        booking_id=request.booking_id,
        status="pending" if resource.requires_approval else "approved",
        hourly_cost=resource.hourly_rate,
        total_cost=total_cost,
    )

    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    return ResourceBookingResponse(
        id=booking.id,
        resource_id=resource.id,
        resource_name=resource.name,
        user_id=booking.user_id,
        title=booking.title,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        total_cost=booking.total_cost,
    )


@router.get("/bookings/my", response_model=List[ResourceBookingResponse])
async def get_my_resource_bookings(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get current user's resource bookings."""
    stmt = (
        select(ResourceBooking, Resource)
        .join(Resource, ResourceBooking.resource_id == Resource.id)
        .options(selectinload(ResourceBooking.user))  # Eager load user to prevent N+1
        .where(ResourceBooking.user_id == current_user.id)
        .order_by(desc(ResourceBooking.start_time))
        .limit(limit)
    )

    if status:
        stmt = stmt.where(ResourceBooking.status == status)

    results = (await db.execute(stmt)).all()

    return [
        ResourceBookingResponse(
            id=booking.id,
            resource_id=resource.id,
            resource_name=resource.name,
            user_id=booking.user_id,
            title=booking.title,
            start_time=booking.start_time,
            end_time=booking.end_time,
            status=booking.status,
            total_cost=booking.total_cost,
        )
        for booking, resource in results
    ]


@router.post("/bookings/{booking_id}/cancel")
async def cancel_resource_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Cancel a resource booking."""
    stmt = select(ResourceBooking).where(
        and_(
            ResourceBooking.id == booking_id, ResourceBooking.user_id == current_user.id
        )
    )
    booking = (await db.execute(stmt)).scalars().first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking already cancelled")

    booking.status = "cancelled"
    await db.commit()

    return {"status": "success", "message": "Booking cancelled"}


@router.get("/{resource_id}/availability")
async def get_resource_availability(
    resource_id: str,
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get resource availability for a date range."""
    stmt = select(Resource).where(
        and_(Resource.id == resource_id, Resource.is_active == True)
    )
    resource = (await db.execute(stmt)).scalars().first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Get existing bookings
    stmt = (
        select(ResourceBooking)
        .where(
            and_(
                ResourceBooking.resource_id == resource_id,
                ResourceBooking.status.in_(["approved", "pending"]),
                ResourceBooking.start_time >= start_date,
                ResourceBooking.end_time <= end_date,
            )
        )
        .order_by(ResourceBooking.start_time)
    )

    bookings = (await db.execute(stmt)).scalars().all()

    return {
        "resource_id": resource_id,
        "resource_name": resource.name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "bookings": [
            {
                "start": b.start_time.isoformat(),
                "end": b.end_time.isoformat(),
                "status": b.status,
                "title": b.title,
            }
            for b in bookings
        ],
    }
