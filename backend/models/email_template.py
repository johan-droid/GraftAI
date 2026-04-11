"""Email template system for customizable notifications."""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
import secrets

from .base import Base

if TYPE_CHECKING:
    from backend.models.tables import UserTable


class EmailTemplate(Base):
    """Customizable email templates for notifications."""
    __tablename__ = "email_templates"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    # Template metadata
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., "booking_confirmation"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Ownership - system templates have no owner
    user_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # System templates cannot be deleted
    
    # Template content
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    html_body: Mapped[str] = mapped_column(Text, nullable=False)
    text_body: Mapped[str] = mapped_column(Text, nullable=False)  # Plain text fallback
    
    # Template variables (documented for users)
    available_variables: Mapped[list] = mapped_column(JSON, default=list)  # ["{{user_name}}", "{{booking_title}}", ...]
    
    # Styling
    primary_color: Mapped[str] = mapped_column(String(7), default="#6366f1")  # Hex color
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Locale
    language: Mapped[str] = mapped_column(String(10), default="en")  # ISO 639-1 code
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Mapped[Optional["UserTable"]] = relationship("UserTable", back_populates="email_templates")
    
    __table_args__ = (
        Index('ix_email_templates_user_slug', 'user_id', 'slug', unique=True),
        Index('ix_email_templates_system', 'is_system'),
    )


class EmailLog(Base):
    """Log of sent emails for analytics and debugging."""
    __tablename__ = "email_logs"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    # Reference
    template_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("email_templates.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Recipients
    to_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cc_emails: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    bcc_emails: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Content
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # sent, delivered, opened, bounced, failed
    
    # Provider info
    provider: Mapped[str] = mapped_column(String(50), default="resend")  # resend, sendgrid, etc.
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Tracking
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    email_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)  # IP, user agent, etc.
    
    __table_args__ = (
        Index('ix_email_logs_user_status', 'user_id', 'status'),
        Index('ix_email_logs_sent_at', 'sent_at'),
    )
