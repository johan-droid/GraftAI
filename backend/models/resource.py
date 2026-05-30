"""Resource booking models for rooms, equipment, and facilities."""
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from backend.models.resource import Resource
    from backend.models.tables import UserTable
    from backend.models.team import Team

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
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    room_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    owner_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    team_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("teams.id"), nullable=True, index=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    features: Mapped[list] = mapped_column(JSON, default=list)
    amenities: Mapped[list] = mapped_column(JSON, default=list)
    images: Mapped[list] = mapped_column(JSON, default=list)
    min_booking_duration: Mapped[int] = mapped_column(Integer, default=15)
    max_booking_duration: Mapped[int] = mapped_column(Integer, default=480)
    min_notice_hours: Mapped[int] = mapped_column(Integer, default=0)
    max_booking_days_ahead: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    business_hours: Mapped[dict] = mapped_column(JSON, default=lambda: {"monday": {"start": "09:00", "end": "17:00", "enabled": True}, "tuesday": {"start": "09:00", "end": "17:00", "enabled": True}, "wednesday": {"start": "09:00", "end": "17:00", "enabled": True}, "thursday": {"start": "09:00", "end": "17:00", "enabled": True}, "friday": {"start": "09:00", "end": "17:00", "enabled": True}, "saturday": {"start": None, "end": None, "enabled": False}, "sunday": {"start": None, "end": None, "enabled": False}})
    hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approver_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    owner: Mapped["UserTable"] = relationship("UserTable", back_populates="owned_resources")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="resources")
    bookings: Mapped[list["ResourceBooking"]] = relationship("ResourceBooking", back_populates="resource", cascade="all, delete-orphan")
    __table_args__ = (Index("ix_resources_type_location", "resource_type", "location"), Index("ix_resources_team_active", "team_id", "is_active"))

class ResourceBooking(Base):
    """Bookings for resources."""
    __tablename__ = "resource_bookings"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    resource_id: Mapped[str] = mapped_column(String(100), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    booking_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    team_booking_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("team_bookings.id", ondelete="SET NULL"), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attendees: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hourly_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    resource: Mapped["Resource"] = relationship("Resource", back_populates="bookings")
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="resource_bookings")
    __table_args__ = (Index("ix_resource_bookings_resource_time", "resource_id", "start_time", "end_time"), Index("ix_resource_bookings_user", "user_id", "status"), Index("ix_resource_bookings_status", "status"))

class ResourceMaintenance(Base):
    """Maintenance records for resources."""
    __tablename__ = "resource_maintenance"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    resource_id: Mapped[str] = mapped_column(String(100), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
