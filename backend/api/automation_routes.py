"""API routes for automation rules management."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable
from backend.models.automation import AutomationRule, AutomationExecution, AutomationTemplate

router = APIRouter(prefix="/automation", tags=["automation"])


# Pydantic Models

class AutomationRuleCreate(BaseModel):
    """Create automation rule request."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    rule_type: str = Field(..., regex="^(auto_accept|auto_decline|auto_reschedule|smart_scheduling|conflict_resolution|team_coordination|reminder_scheduling|resource_allocation)$")
    conditions: dict = Field(default=dict)
    actions: dict = Field(default=dict)
    confidence_threshold: float = Field(default=70.0, ge=0, le=100)
    require_confirmation: bool = Field(default=False)
    max_executions_per_day: Optional[int] = Field(None, ge=1)
    priority: int = Field(default=50, ge=0, le=100)
    team_id: Optional[str] = None


class AutomationRuleUpdate(BaseModel):
    """Update automation rule request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    conditions: Optional[dict] = None
    actions: Optional[dict] = None
    confidence_threshold: Optional[float] = Field(None, ge=0, le=100)
    require_confirmation: Optional[bool] = None
    max_executions_per_day: Optional[int] = Field(None, ge=1)
    priority: Optional[int] = Field(None, ge=0, le=100)


class AutomationRuleResponse(BaseModel):
    """Automation rule response."""
    id: str
    name: str
    description: Optional[str]
    rule_type: str
    conditions: dict
    actions: dict
    is_enabled: bool
    confidence_threshold: float
    require_confirmation: bool
    max_executions_per_day: Optional[int]
    execution_count_today: int
    priority: int
    created_at: datetime


class AutomationExecutionResponse(BaseModel):
    """Automation execution response."""
    id: str
    rule_id: str
    rule_name: str
    trigger_type: str
    status: str
    confidence_score: float
    automation_tier: str
    action_taken: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]


class AutomationTemplateResponse(BaseModel):
    """Automation template response."""
    id: str
    name: str
    description: str
    category: str
    rule_type: str
    template_conditions: dict
    template_actions: dict
    default_confidence_threshold: float
    default_require_confirmation: bool


# Routes

@router.post("/rules", response_model=AutomationRuleResponse)
async def create_automation_rule(
    rule: AutomationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Create a new automation rule."""
    # If team_id provided, verify membership
    if rule.team_id:
        from backend.models.team import TeamMember, TeamRole
        stmt = select(TeamMember).where(
            and_(
                TeamMember.team_id == rule.team_id,
                TeamMember.user_id == current_user.id,
                TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN])
            )
        )
        team_member = (await db.execute(stmt)).scalars().first()
        if not team_member:
            raise HTTPException(status_code=403, detail="Not authorized to add automation rules to this team")
    
    new_rule = AutomationRule(
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type,
        user_id=current_user.id,
        team_id=rule.team_id,
        conditions=rule.conditions,
        actions=rule.actions,
        confidence_threshold=rule.confidence_threshold,
        require_confirmation=rule.require_confirmation,
        max_executions_per_day=rule.max_executions_per_day,
        priority=rule.priority,
    )
    
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    
    return AutomationRuleResponse(
        id=new_rule.id,
        name=new_rule.name,
        description=new_rule.description,
        rule_type=new_rule.rule_type,
        conditions=new_rule.conditions,
        actions=new_rule.actions,
        is_enabled=new_rule.is_enabled,
        confidence_threshold=new_rule.confidence_threshold,
        require_confirmation=new_rule.require_confirmation,
        max_executions_per_day=new_rule.max_executions_per_day,
        execution_count_today=new_rule.execution_count_today,
        priority=new_rule.priority,
        created_at=new_rule.created_at,
    )


@router.get("/rules", response_model=List[AutomationRuleResponse])
async def list_automation_rules(
    rule_type: Optional[str] = None,
    team_id: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """List automation rules."""
    stmt = select(AutomationRule).where(
        AutomationRule.user_id == current_user.id
    ).order_by(desc(AutomationRule.priority), desc(AutomationRule.created_at)).limit(limit)
    
    if rule_type:
        stmt = stmt.where(AutomationRule.rule_type == rule_type)
    
    if team_id:
        stmt = stmt.where(AutomationRule.team_id == team_id)
    
    if is_enabled is not None:
        stmt = stmt.where(AutomationRule.is_enabled == is_enabled)
    
    rules = (await db.execute(stmt)).scalars().all()
    
    return [
        AutomationRuleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            rule_type=r.rule_type,
            conditions=r.conditions,
            actions=r.actions,
            is_enabled=r.is_enabled,
            confidence_threshold=r.confidence_threshold,
            require_confirmation=r.require_confirmation,
            max_executions_per_day=r.max_executions_per_day,
            execution_count_today=r.execution_count_today,
            priority=r.priority,
            created_at=r.created_at,
        )
        for r in rules
    ]


@router.get("/rules/{rule_id}", response_model=AutomationRuleResponse)
async def get_automation_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Get automation rule details."""
    stmt = select(AutomationRule).where(
        and_(
            AutomationRule.id == rule_id,
            AutomationRule.user_id == current_user.id
        )
    )
    rule = (await db.execute(stmt)).scalars().first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    
    return AutomationRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type,
        conditions=rule.conditions,
        actions=rule.actions,
        is_enabled=rule.is_enabled,
        confidence_threshold=rule.confidence_threshold,
        require_confirmation=rule.require_confirmation,
        max_executions_per_day=rule.max_executions_per_day,
        execution_count_today=rule.execution_count_today,
        priority=rule.priority,
        created_at=rule.created_at,
    )


@router.put("/rules/{rule_id}", response_model=AutomationRuleResponse)
async def update_automation_rule(
    rule_id: str,
    update: AutomationRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Update an automation rule."""
    stmt = select(AutomationRule).where(
        and_(
            AutomationRule.id == rule_id,
            AutomationRule.user_id == current_user.id
        )
    )
    rule = (await db.execute(stmt)).scalars().first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    
    # Update fields
    if update.name is not None:
        rule.name = update.name
    if update.description is not None:
        rule.description = update.description
    if update.is_enabled is not None:
        rule.is_enabled = update.is_enabled
    if update.conditions is not None:
        rule.conditions = update.conditions
    if update.actions is not None:
        rule.actions = update.actions
    if update.confidence_threshold is not None:
        rule.confidence_threshold = update.confidence_threshold
    if update.require_confirmation is not None:
        rule.require_confirmation = update.require_confirmation
    if update.max_executions_per_day is not None:
        rule.max_executions_per_day = update.max_executions_per_day
    if update.priority is not None:
        rule.priority = update.priority
    
    await db.commit()
    await db.refresh(rule)
    
    return AutomationRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type,
        conditions=rule.conditions,
        actions=rule.actions,
        is_enabled=rule.is_enabled,
        confidence_threshold=rule.confidence_threshold,
        require_confirmation=rule.require_confirmation,
        max_executions_per_day=rule.max_executions_per_day,
        execution_count_today=rule.execution_count_today,
        priority=rule.priority,
        created_at=rule.created_at,
    )


@router.delete("/rules/{rule_id}")
async def delete_automation_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Delete an automation rule."""
    stmt = select(AutomationRule).where(
        and_(
            AutomationRule.id == rule_id,
            AutomationRule.user_id == current_user.id
        )
    )
    rule = (await db.execute(stmt)).scalars().first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    
    await db.delete(rule)
    await db.commit()
    
    return {"status": "success", "message": "Automation rule deleted"}


@router.get("/executions", response_model=List[AutomationExecutionResponse])
async def list_automation_executions(
    rule_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """List automation executions."""
    stmt = select(AutomationExecution, AutomationRule).join(
        AutomationRule, AutomationExecution.rule_id == AutomationRule.id
    ).where(
        AutomationRule.user_id == current_user.id
    ).order_by(desc(AutomationExecution.started_at)).limit(limit)
    
    if rule_id:
        stmt = stmt.where(AutomationExecution.rule_id == rule_id)
    
    if status:
        stmt = stmt.where(AutomationExecution.status == status)
    
    results = (await db.execute(stmt)).all()
    
    return [
        AutomationExecutionResponse(
            id=execution.id,
            rule_id=execution.rule_id,
            rule_name=rule.name,
            trigger_type=execution.trigger_type,
            status=execution.status,
            confidence_score=execution.confidence_score,
            automation_tier=execution.automation_tier,
            action_taken=execution.action_taken,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
        )
        for execution, rule in results
    ]


@router.get("/templates", response_model=List[AutomationTemplateResponse])
async def list_automation_templates(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """List available automation templates."""
    stmt = select(AutomationTemplate).where(
        AutomationTemplate.is_active == True
    ).order_by(desc(AutomationTemplate.is_featured), AutomationTemplate.name)
    
    if category:
        stmt = stmt.where(AutomationTemplate.category == category)
    
    templates = (await db.execute(stmt)).scalars().all()
    
    return [
        AutomationTemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            category=t.category,
            rule_type=t.rule_type,
            template_conditions=t.template_conditions,
            template_actions=t.template_actions,
            default_confidence_threshold=t.default_confidence_threshold,
            default_require_confirmation=t.default_require_confirmation,
        )
        for t in templates
    ]


@router.post("/templates/{template_id}/use", response_model=AutomationRuleResponse)
async def use_automation_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Create a rule from a template."""
    stmt = select(AutomationTemplate).where(
        and_(
            AutomationTemplate.id == template_id,
            AutomationTemplate.is_active == True
        )
    )
    template = (await db.execute(stmt)).scalars().first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create rule from template
    new_rule = AutomationRule(
        name=template.name,
        description=template.description,
        rule_type=template.rule_type,
        user_id=current_user.id,
        conditions=template.template_conditions.copy(),
        actions=template.template_actions.copy(),
        confidence_threshold=template.default_confidence_threshold,
        require_confirmation=template.default_require_confirmation,
    )
    
    db.add(new_rule)
    
    # Increment template usage count
    template.usage_count += 1
    
    await db.commit()
    await db.refresh(new_rule)
    
    return AutomationRuleResponse(
        id=new_rule.id,
        name=new_rule.name,
        description=new_rule.description,
        rule_type=new_rule.rule_type,
        conditions=new_rule.conditions,
        actions=new_rule.actions,
        is_enabled=new_rule.is_enabled,
        confidence_threshold=new_rule.confidence_threshold,
        require_confirmation=new_rule.require_confirmation,
        max_executions_per_day=new_rule.max_executions_per_day,
        execution_count_today=new_rule.execution_count_today,
        priority=new_rule.priority,
        created_at=new_rule.created_at,
    )
