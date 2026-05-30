"""Email template system for customizable notifications."""
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from backend.models.tables import UserTable

class EmailTemplate(Base):
    """Customizable email templates for notifications."""
    __tablename__ = "email_templates"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    html_body: Mapped[str] = mapped_column(Text, nullable=False)
    text_body: Mapped[str] = mapped_column(Text, nullable=False)
    available_variables: Mapped[list] = mapped_column(JSON, default=list)
    primary_color: Mapped[str] = mapped_column(String(7), default="#6366f1")
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    user: Mapped[Optional["UserTable"]] = relationship("UserTable", back_populates="email_templates")
    __table_args__ = (Index("ix_email_templates_user_slug", "user_id", "slug", unique=True), Index("ix_email_templates_system", "is_system"))

class EmailLog(Base):
    """Log of sent emails for analytics and debugging."""
    __tablename__ = "email_logs"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    template_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("email_templates.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    to_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cc_emails: Mapped[list | None] = mapped_column(JSON, nullable=True)
    bcc_emails: Mapped[list | None] = mapped_column(JSON, nullable=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="resend")
    provider_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    __table_args__ = (Index("ix_email_logs_user_status", "user_id", "status"), Index("ix_email_logs_sent_at", "sent_at"))
