"""API Key model for developer access management."""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
import secrets
import hashlib

from .base import Base


def generate_api_key():
    """Generate a secure API key."""
    return f"graft_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


class APIKey(Base):
    """API keys for developer access to the platform."""
    __tablename__ = "api_keys"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    # Key details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # First 8 chars for display
    
    # Ownership
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Permissions
    scopes: Mapped[list] = mapped_column(JSON, default=lambda: ["read", "write"])  # read, write, admin
    
    # Rate limiting
    rate_limit: Mapped[int] = mapped_column(default=1000)  # requests per hour
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Usage tracking
    request_count: Mapped[int] = mapped_column(default=0)
    
    # Relationships
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="api_keys")
    
    __table_args__ = (
        Index('ix_api_keys_user_active', 'user_id', 'is_active'),
    )


class APIKeyUsage(Base):
    """Track API key usage for analytics and rate limiting."""
    __tablename__ = "api_key_usage"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    api_key_id: Mapped[str] = mapped_column(String(100), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Request details
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(default=200)
    
    # Timing
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    response_time_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Client info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
