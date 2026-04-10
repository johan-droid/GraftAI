"""Resource booking models for rooms, equipment, and facilities."""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, Text, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
import secrets

from .base import Base


class ResourceType(str):
    """Types of bookable resources."""
    ROOM = "room"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    DESK = "desk"
    OTHER = "other"


class Resource(Base):
    """Bookable resources (rooms, equipment, etc.)."""
    __tablename__ = "resources"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # room, equipment, vehicle, desk
    
    # Location
    location: Mapped[str] = mapped_column(String(200), nullable=False)  # Building name, floor, etc.
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    floor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Ownership
    owner_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    team_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("teams.id"), nullable=True, index=True)
    
    # Capacity (for rooms, vehicles)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Features/Capabilities
    features: Mapped[list] = mapped_column(JSON, default=list)  # ["projector", "whiteboard", "video_conference"]
    amenities: Mapped[list] = mapped_column(JSON, default=list)  # ["wifi", "coffee", "parking"]
    
    # Images
    images: Mapped[list] = mapped_column(JSON, default=list)  # ["https://...", "https://..."]
    
    # Booking rules
    min_booking_duration: Mapped[int] = mapped_column(Integer, default=15)  # minutes
    max_booking_duration: Mapped[int] = mapped_column(Integer, default=480)  # minutes (8 hours)
    min_notice_hours: Mapped[int] = mapped_column(Integer, default=0)
    max_booking_days_ahead: Mapped[int] = mapped_column(Integer, default=30)
    
    # Availability
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    business_hours: Mapped[dict] = mapped_column(JSON, default=lambda: {
        "monday": {"start": "09:00", "end": "17:00", "enabled": True},
        "tuesday": {"start": "09:00", "end": "17:00", "enabled": True},
        "wednesday": {"start": "09:00", "end": "17:00", "enabled": True},
        "thursday": {"start": "09:00", "end": "17:00", "enabled": True},
        "friday": {"start": "09:00", "end": "17:00", "enabled": True},
        "saturday": {"start": None, "end": None, "enabled": False},
        "sunday": {"start": None, "end": None, "enabled": False},
    })
    
    # Pricing (if applicable)
    hourly_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # For paid resources
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Approval
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approver_ids: Mapped[list] = mapped_column(JSON, default=list)  # List of user IDs who can approve
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    owner: Mapped["UserTable"] = relationship("UserTable", back_populates="owned_resources")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="resources")
    bookings: Mapped[List["ResourceBooking"]] = relationship("ResourceBooking", back_populates="resource", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_resources_type_location', 'resource_type', 'location'),
        Index('ix_resources_team_active', 'team_id', 'is_active'),
    )


class ResourceBooking(Base):
    """Bookings for resources."""
    __tablename__ = "resource_bookings"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    # References
    resource_id: Mapped[str] = mapped_column(String(100), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    
    # Event reference (if associated with a meeting/booking)
    booking_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    team_booking_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("team_bookings.id", ondelete="SET NULL"), nullable=True)
    
    # Schedule
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Purpose
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attendees: Mapped[int] = mapped_column(Integer, default=1)  # Number of people using resource
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected, cancelled, completed
    
    # Approval
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Check-in/out
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Cost (if applicable)
    hourly_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    resource: Mapped["Resource"] = relationship("Resource", back_populates="bookings")
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="resource_bookings")
    
    __table_args__ = (
        Index('ix_resource_bookings_resource_time', 'resource_id', 'start_time', 'end_time'),
        Index('ix_resource_bookings_user', 'user_id', 'status'),
        Index('ix_resource_bookings_status', 'status'),
    )


class ResourceMaintenance(Base):
    """Maintenance records for resources."""
    __tablename__ = "resource_maintenance"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    resource_id: Mapped[str] = mapped_column(String(100), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Maintenance details
    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)  # routine, repair, cleaning, inspection
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Schedule
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled, in_progress, completed, cancelled
    
    # Cost
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
