"""Team scheduling models for collaborative scheduling."""

from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, DateTime,
    Text, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from .base import Base

if TYPE_CHECKING:
    from backend.models.resource import Resource
    from backend.models.automation import AutomationRule
    from backend.models.tables import UserTable

import uuid


def generate_uuid():
    return str(uuid.uuid4())


class TeamRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Team(Base):
    """Team organization for collaborative scheduling."""
    __tablename__ = "teams"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Team settings
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    round_robin_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    collective_availability_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    require_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Booking settings
    default_booking_duration: Mapped[int] = mapped_column(Integer, default=30)
    min_booking_notice: Mapped[int] = mapped_column(Integer, default=4)  # hours
    max_booking_notice: Mapped[int] = mapped_column(Integer, default=168)  # hours (1 week)
    
    # Timezone and hours
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
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    members: Mapped[List["TeamMember"]] = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    event_types: Mapped[List["TeamEventType"]] = relationship("TeamEventType", back_populates="team", cascade="all, delete-orphan")
    bookings: Mapped[List["TeamBooking"]] = relationship("TeamBooking", back_populates="team", cascade="all, delete-orphan")
    resources: Mapped[List["Resource"]] = relationship("Resource", back_populates="team")
    automation_rules: Mapped[List["AutomationRule"]] = relationship("AutomationRule", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """Team membership with roles and permissions."""
    __tablename__ = "team_members"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[TeamRole] = mapped_column(SQLEnum(TeamRole), default=TeamRole.MEMBER, nullable=False)
    
    # Member-specific settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    round_robin_weight: Mapped[int] = mapped_column(Integer, default=1)  # For weighted round-robin
    max_daily_bookings: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["UserTable"] = relationship("UserTable")  # Will need to add back_populates in UserTable
    
    # Indexes
    __table_args__ = (
        Index('ix_team_members_team_user', 'team_id', 'user_id', unique=True),
    )


class TeamEventType(Base):
    """Team event types for booking links."""
    __tablename__ = "team_event_types"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Scheduling settings
    duration: Mapped[int] = mapped_column(Integer, default=30)  # minutes
    min_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Availability
    available_days: Mapped[list] = mapped_column(JSON, default=lambda: [0, 1, 2, 3, 4])  # Mon-Fri
    available_hours: Mapped[dict] = mapped_column(JSON, default=lambda: {
        "start": "09:00",
        "end": "17:00"
    })
    
    # Buffer times
    buffer_before: Mapped[int] = mapped_column(Integer, default=0)  # minutes
    buffer_after: Mapped[int] = mapped_column(Integer, default=0)  # minutes
    
    # Limits
    max_bookings_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_bookings_per_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Assignment
    assigned_members: Mapped[list] = mapped_column(JSON, default=list)  # List of user IDs
    assignment_type: Mapped[str] = mapped_column(String(50), default="all")  # all, specific, round_robin
    
    # Booking link
    booking_link_slug: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="event_types")
    bookings: Mapped[List["TeamBooking"]] = relationship("TeamBooking", back_populates="event_type", cascade="all, delete-orphan")


class TeamBooking(Base):
    """Team bookings for collaborative scheduling."""
    __tablename__ = "team_bookings"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type_id: Mapped[str] = mapped_column(String, ForeignKey("team_event_types.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Booking details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Schedule
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Attendee information
    attendee_name: Mapped[str] = mapped_column(String(100), nullable=False)
    attendee_email: Mapped[str] = mapped_column(String(255), nullable=False)
    attendee_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Assignment
    assigned_to: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # User ID of assigned team member
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="confirmed")  # confirmed, pending, cancelled, completed
    confirmation_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    
    # Meeting details
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meeting_password: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Calendar sync
    synced_to_google: Mapped[bool] = mapped_column(Boolean, default=False)
    synced_to_outlook: Mapped[bool] = mapped_column(Boolean, default=False)
    synced_to_apple: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="bookings")
    event_type: Mapped["TeamEventType"] = relationship("TeamEventType", back_populates="bookings")
