"""Integration settings for third-party services."""
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.utils.soft_delete import SoftDeleteMixin

from .base import Base

if TYPE_CHECKING:
    from backend.models.integration import IntegrationLog
    from backend.models.tables import UserTable

class Integration(Base, SoftDeleteMixin):
    """Third-party service integrations."""
    __tablename__ = "integrations"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    webhook_secret: Mapped[str | None] = mapped_column(String(100), nullable=True)
    events: Mapped[list] = mapped_column(JSON, default=lambda: ["booking.created", "booking.updated", "booking.cancelled"])
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="integrations")
    logs: Mapped[list["IntegrationLog"]] = relationship("IntegrationLog", back_populates="integration", cascade="all, delete-orphan")
    __table_args__ = (Index("ix_integrations_user_provider", "user_id", "provider"), Index("ix_integrations_active", "is_active"))

class IntegrationLog(Base):
    """Log of integration webhook deliveries."""
    __tablename__ = "integration_logs"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    integration_id: Mapped[str] = mapped_column(String(100), ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    status_code: Mapped[int | None] = mapped_column(nullable=True)
    response_body: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    response_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    integration: Mapped["Integration"] = relationship("Integration", back_populates="logs")
    __table_args__ = (Index("ix_integration_logs_integration", "integration_id", "sent_at"), Index("ix_integration_logs_status", "status"))
