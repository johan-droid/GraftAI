from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    func,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


class OrganizationTable(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    workspaces = relationship(
        "WorkspaceTable", back_populates="organization", cascade="all, delete-orphan"
    )
    users = relationship("UserOrganizationTable", back_populates="organization")
    events = relationship("EventTable", back_populates="organization")
    todos = relationship("TodoTable", back_populates="organization")


class UserOrganizationTable(Base):
    """Many-to-Many mapping for Users and Organizations."""
    __tablename__ = "user_organizations"

    user_id = Column(
        String(100), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    org_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True
    )
    role = Column(String(50), default="member")  # admin, member, guest

    # Relationships
    user = relationship("UserTable", back_populates="organizations")
    organization = relationship("OrganizationTable", back_populates="users")


class WorkspaceTable(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    slug = Column(String(100), index=True, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    organization = relationship("OrganizationTable", back_populates="workspaces")
    events = relationship(
        "EventTable", back_populates="workspace", cascade="all, delete-orphan"
    )
    todos = relationship("TodoTable", back_populates="workspace")


class UserTable(Base):
    __tablename__ = "users"

    id = Column(String(100), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255)) # Restoration of 'name' for Better Auth compatibility
    full_name = Column(String(255))
    image = Column(Text) # Restoration for Better Auth
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String(512))
    password = Column(Text) # Fallback legacy field
    email_verified = Column(Boolean, default=False)
    timezone = Column(String(100), default="UTC")
    tenant_id = Column(Integer, index=True)
    
    # Consent Preferences
    consent_analytics = Column(Boolean, default=True, nullable=False)
    consent_notifications = Column(Boolean, default=True, nullable=False)
    consent_ai_training = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    events = relationship(
        "EventTable", back_populates="user", cascade="all, delete-orphan"
    )
    organizations = relationship("UserOrganizationTable", back_populates="user")
    todos = relationship("TodoTable", back_populates="user")
    notifications = relationship("NotificationTable", back_populates="user")

    # Integrations
    zoom_access_token = Column(Text)
    zoom_refresh_token = Column(Text)
    zoom_token_expires_at = Column(DateTime(timezone=True))
    zoom_account_id = Column(String(100))

    google_access_token = Column(Text)
    google_refresh_token = Column(Text)
    google_token_expires_at = Column(DateTime(timezone=True))
    google_id = Column(String(100))

    microsoft_access_token = Column(Text)
    microsoft_refresh_token = Column(Text)
    microsoft_token_expires_at = Column(DateTime(timezone=True))
    microsoft_id = Column(String(100))


class EventTable(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    org_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    workspace_id = Column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )

    title = Column(String(512), nullable=False)
    description = Column(Text)
    category = Column(String(50), default="meeting", index=True)
    color = Column(String(20), default="#8A2BE2")

    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    metadata_payload = Column(JSONB, default={}, nullable=False)

    is_remote = Column(Boolean, default=True)
    status = Column(String(50), default="confirmed")
    is_reminded = Column(Boolean, default=False, nullable=False)
    
    is_meeting = Column(Boolean, default=False, nullable=False)
    meeting_platform = Column(String(50))
    meeting_link = Column(String(1024))
    attendees = Column(JSONB, default=[], nullable=False)
    agenda = Column(Text)
    
    last_synced_hash = Column(String(64))
    provider_id = Column(String(255), index=True)
    provider_source = Column(String(50), index=True)
    is_busy = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_events_user_availability", "user_id", "start_time", "end_time", postgresql_where="is_busy = true"),
    )

    user = relationship("UserTable", back_populates="events")
    workspace = relationship("WorkspaceTable", back_populates="events")
    organization = relationship("OrganizationTable", back_populates="events")


class TodoTable(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    
    title = Column(String(512), nullable=False)
    description = Column(Text)
    is_completed = Column(Boolean, default=False, nullable=False)
    priority = Column(String(20), default="medium")
    due_date = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("UserTable", back_populates="todos")
    workspace = relationship("WorkspaceTable", back_populates="todos")
    organization = relationship("OrganizationTable", back_populates="todos")


class NotificationTable(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), default="email")
    recipient = Column(String(255), nullable=False)
    subject = Column(String(512))
    body = Column(Text)
    status = Column(String(20), default="pending")  # pending, sent, failed
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("UserTable", back_populates="notifications")


# --- Better Auth Integration Tables (Preserved for SSO/Session Stability) ---

class AccountTable(Base):
    __tablename__ = "account"
    id = Column(String(100), primary_key=True)
    userId = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"))
    accountId = Column(Text)
    providerId = Column(Text)
    accessToken = Column(Text)
    refreshToken = Column(Text)
    idToken = Column(Text)
    expiresAt = Column(DateTime(timezone=True))
    password = Column(Text)


class SessionTable(Base):
    __tablename__ = "session"
    id = Column(String(100), primary_key=True)
    userId = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(Text, unique=True, nullable=False)
    expiresAt = Column(DateTime(timezone=True))
    ipAddress = Column(Text)
    userAgent = Column(Text)


class VerificationTable(Base):
    __tablename__ = "verification"
    id = Column(String(100), primary_key=True)
    identifier = Column(Text, nullable=False)
    value = Column(Text, nullable=False)
    expiresAt = Column(DateTime(timezone=True))


class AuditLogTable(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"))
    action = Column(String(255), nullable=False)
    ip_address = Column(String(64))
    user_agent = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())


class BookingTable(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PreferenceTable(Base):
    __tablename__ = "preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"))
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AuthSessionTable(Base):
    """Legacy session table from prototype."""
    __tablename__ = "auth_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"))
    session_token = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
