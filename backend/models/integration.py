"""Integration settings for third-party services."""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
import secrets

from .base import Base

if TYPE_CHECKING:
    from backend.models.tables import UserTable
    from backend.models.integration import IntegrationLog


class Integration(Base):
    """Third-party service integrations."""

    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16)
    )

    # User ownership
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Integration type
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # zapier, slack, teams, custom
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Configuration
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Event subscriptions
    events: Mapped[list] = mapped_column(
        JSON,
        default=lambda: ["booking.created", "booking.updated", "booking.cancelled"],
    )

    # Provider-specific settings
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_message: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="integrations")
    logs: Mapped[List["IntegrationLog"]] = relationship(
        "IntegrationLog", back_populates="integration", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_integrations_user_provider", "user_id", "provider"),
        Index("ix_integrations_active", "is_active"),
    )


class IntegrationLog(Base):
    """Log of integration webhook deliveries."""

    __tablename__ = "integration_logs"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16)
    )
    integration_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Delivery status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # success, failed, pending
    status_code: Mapped[Optional[int]] = mapped_column(nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timing
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    response_time_ms: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration", back_populates="logs"
    )

    __table_args__ = (
        Index("ix_integration_logs_integration", "integration_id", "sent_at"),
        Index("ix_integration_logs_status", "status"),
    )
