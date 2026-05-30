from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from backend.models.automation import AutomationRule
    from backend.models.resource import Resource
    from backend.models.tables import UserTable
import uuid


def generate_uuid():
    return str(uuid.uuid4())
"Team scheduling models for collaborative scheduling."
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.automation import AutomationRule
    from backend.models.resource import Resource
    from backend.models.tables import UserTable

def generate_uuid():
    return str(uuid.uuid4())

class TeamRole(StrEnum):
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
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    round_robin_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    collective_availability_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    require_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    default_booking_duration: Mapped[int] = mapped_column(Integer, default=30)
    min_booking_notice: Mapped[int] = mapped_column(Integer, default=4)
    max_booking_notice: Mapped[int] = mapped_column(Integer, default=168)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    business_hours: Mapped[dict] = mapped_column(JSON, default=lambda: {"monday": {"start": "09:00", "end": "17:00", "enabled": True}, "tuesday": {"start": "09:00", "end": "17:00", "enabled": True}, "wednesday": {"start": "09:00", "end": "17:00", "enabled": True}, "thursday": {"start": "09:00", "end": "17:00", "enabled": True}, "friday": {"start": "09:00", "end": "17:00", "enabled": True}, "saturday": {"start": None, "end": None, "enabled": False}, "sunday": {"start": None, "end": None, "enabled": False}})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    members: Mapped[list["TeamMember"]] = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    event_types: Mapped[list["TeamEventType"]] = relationship("TeamEventType", back_populates="team", cascade="all, delete-orphan")
    bookings: Mapped[list["TeamBooking"]] = relationship("TeamBooking", back_populates="team", cascade="all, delete-orphan")
    resources: Mapped[list["Resource"]] = relationship("Resource", back_populates="team")
    automation_rules: Mapped[list["AutomationRule"]] = relationship("AutomationRule", back_populates="team", cascade="all, delete-orphan")

class TeamMember(Base):
    """Team membership with roles and permissions."""
    __tablename__ = "team_members"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[TeamRole] = mapped_column(SQLEnum(TeamRole), default=TeamRole.MEMBER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    round_robin_weight: Mapped[int] = mapped_column(Integer, default=1)
    max_daily_bookings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="team_memberships")
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"), Index("ix_team_members_team_user", "team_id", "user_id"))

class TeamEventType(Base):
    """Team event types for booking links."""
    __tablename__ = "team_event_types"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[int] = mapped_column(Integer, default=30)
    min_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    available_days: Mapped[list] = mapped_column(JSON, default=lambda: [0, 1, 2, 3, 4])
    available_hours: Mapped[dict] = mapped_column(JSON, default=lambda: {"start": "09:00", "end": "17:00"})
    buffer_before: Mapped[int] = mapped_column(Integer, default=0)
    buffer_after: Mapped[int] = mapped_column(Integer, default=0)
    max_bookings_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_bookings_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assigned_members: Mapped[list] = mapped_column(JSON, default=list)
    assignment_type: Mapped[str] = mapped_column(String(50), default="all")
    booking_link_slug: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    team: Mapped["Team"] = relationship("Team", back_populates="event_types")
    bookings: Mapped[list["TeamBooking"]] = relationship("TeamBooking", back_populates="event_type", cascade="all, delete-orphan")

class TeamBooking(Base):
    """Team bookings for collaborative scheduling."""
    __tablename__ = "team_bookings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type_id: Mapped[str] = mapped_column(String, ForeignKey("team_event_types.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attendee_name: Mapped[str] = mapped_column(String(100), nullable=False)
    attendee_email: Mapped[str] = mapped_column(String(255), nullable=False)
    attendee_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", name="fk_team_bookings_assigned_to_users"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="confirmed")
    confirmation_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meeting_password: Mapped[str | None] = mapped_column(String(50), nullable=True)
    synced_to_google: Mapped[bool] = mapped_column(Boolean, default=False)
    synced_to_outlook: Mapped[bool] = mapped_column(Boolean, default=False)
    synced_to_apple: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    team: Mapped["Team"] = relationship("Team", back_populates="bookings")
    event_type: Mapped["TeamEventType"] = relationship("TeamEventType", back_populates="bookings")
