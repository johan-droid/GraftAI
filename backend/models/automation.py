"""Automation rules models for AI-driven scheduling automation."""
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
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    actions: Mapped[dict] = mapped_column(JSON, default=dict)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=70.0)
    require_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    max_executions_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_count_today: Mapped[int] = mapped_column(Integer, default=0)
    last_execution_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="automation_rules")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="automation_rules")
    executions: Mapped[list["AutomationExecution"]] = relationship("AutomationExecution", back_populates="rule", cascade="all, delete-orphan")
    __table_args__ = (Index("ix_automation_rules_user_enabled", "user_id", "is_enabled"), Index("ix_automation_rules_team_enabled", "team_id", "is_enabled"), Index("ix_automation_rules_type_priority", "rule_type", "priority"))

class AutomationExecution(Base):
    """Log of automation rule executions."""
    __tablename__ = "automation_executions"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    rule_id: Mapped[str] = mapped_column(String(100), ForeignKey("automation_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_data: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_data: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    automation_tier: Mapped[str] = mapped_column(String(20), default="draft")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rule: Mapped["AutomationRule"] = relationship("AutomationRule", back_populates="executions")
    __table_args__ = (Index("ix_automation_executions_rule", "rule_id"), Index("ix_automation_executions_status", "status"), Index("ix_automation_executions_started", "started_at"))

class AutomationTemplate(Base):
    """Pre-built automation rule templates for users to use."""
    __tablename__ = "automation_templates"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    template_conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    template_actions: Mapped[dict] = mapped_column(JSON, default=dict)
    default_confidence_threshold: Mapped[float] = mapped_column(Float, default=70.0)
    default_require_confirmation: Mapped[bool] = mapped_column(Boolean, default=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    __table_args__ = (Index("ix_automation_templates_category", "category"), Index("ix_automation_templates_featured", "is_featured", "is_active"))
