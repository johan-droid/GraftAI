"""Automation rules models for AI-driven scheduling automation."""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, Text, Integer, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
import secrets

from .base import Base

if TYPE_CHECKING:
    from backend.models.tables import UserTable
    from backend.models.team import Team


class AutomationRuleType(str):
    """Types of automation rules."""
    AUTO_ACCEPT = "auto_accept"
    AUTO_DECLINE = "auto_decline"
    AUTO_RESCHEDULE = "auto_reschedule"
    SMART_SCHEDULING = "smart_scheduling"
    CONFLICT_RESOLUTION = "conflict_resolution"
    TEAM_COORDINATION = "team_coordination"
    REMINDER_SCHEDULING = "reminder_scheduling"
    RESOURCE_ALLOCATION = "resource_allocation"


class AutomationRule(Base):
    """Automation rule configuration."""
    __tablename__ = "automation_rules"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Ownership
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Rule conditions (when to trigger)
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    # Example: {"event_type": "1:1", "organizer": "team_member", "min_notice_hours": 2}
    
    # Rule actions (what to do)
    actions: Mapped[dict] = mapped_column(JSON, default=dict)
    # Example: {"action": "accept", "add_to_calendar": true, "send_confirmation": true}
    
    # Automation settings
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=70.0)  # Min confidence to auto-execute
    require_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Execution limits
    max_executions_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_count_today: Mapped[int] = mapped_column(Integer, default=0)
    last_execution_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Priority (higher = checked first)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="automation_rules")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="automation_rules")
    executions: Mapped[List["AutomationExecution"]] = relationship("AutomationExecution", back_populates="rule", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_automation_rules_user_enabled', 'user_id', 'is_enabled'),
        Index('ix_automation_rules_team_enabled', 'team_id', 'is_enabled'),
        Index('ix_automation_rules_type_priority', 'rule_type', 'priority'),
    )


class AutomationExecution(Base):
    """Log of automation rule executions."""
    __tablename__ = "automation_executions"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    rule_id: Mapped[str] = mapped_column(String(100), ForeignKey("automation_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Execution context
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)  # booking_created, conflict_detected, etc.
    trigger_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Execution result
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, success, failed, skipped
    action_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Confidence and decision
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    automation_tier: Mapped[str] = mapped_column(String(20), default="draft")  # draft, trusted, full_auto
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # User interaction
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    rule: Mapped["AutomationRule"] = relationship("AutomationRule", back_populates="executions")
    
    __table_args__ = (
        Index('ix_automation_executions_rule', 'rule_id'),
        Index('ix_automation_executions_status', 'status'),
        Index('ix_automation_executions_started', 'started_at'),
    )


class AutomationTemplate(Base):
    """Pre-built automation rule templates for users to use."""
    __tablename__ = "automation_templates"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # scheduling, conflict, team, resource
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Template conditions and actions
    template_conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    template_actions: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Template settings
    default_confidence_threshold: Mapped[float] = mapped_column(Float, default=70.0)
    default_require_confirmation: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Usage stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_automation_templates_category', 'category'),
        Index('ix_automation_templates_featured', 'is_featured', 'is_active'),
    )
