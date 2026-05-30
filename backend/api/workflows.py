"""
Workflows API Routes

Fully functional workflow management for automation.
"""
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.models.tables import (
    UserTable,
    WorkflowStepTable,
    WorkflowTable,
    generate_uuid,
)
from backend.services.workflow_engine import get_workflow_engine
from backend.utils.db import get_db
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])

class WorkflowStepCreate(BaseModel):
    """Create a workflow step."""
    step_number: int = Field(..., ge=1)
    action_type: str = Field(..., pattern="^(EMAIL|SMS|WEBHOOK|SLACK|TEAMS|CALENDAR)$")
    action_config: dict[str, Any] = Field(default_factory=dict)
    delay_minutes: int = Field(default=0, ge=0)
    is_active: bool = True

class WorkflowCreate(BaseModel):
    """Create a new workflow."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    trigger: str = Field(..., pattern="^(BOOKING_CREATED|BOOKING_CONFIRMED|BOOKING_CANCELLED|BOOKING_RESCHEDULED|BOOKING_REMINDER|BOOKING_FOLLOWUP)$")
    is_active: bool = True
    steps: list[WorkflowStepCreate] = Field(default_factory=list)

class WorkflowUpdate(BaseModel):
    """Update an existing workflow."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    trigger: str | None = Field(None, pattern="^(BOOKING_CREATED|BOOKING_CONFIRMED|BOOKING_CANCELLED|BOOKING_RESCHEDULED|BOOKING_REMINDER|BOOKING_FOLLOWUP)$")
    is_active: bool | None = None

class WorkflowStepResponse(BaseModel):
    """Workflow step response."""
    id: str
    workflow_id: str
    step_number: int
    action_type: str
    action_config: dict[str, Any]
    delay_minutes: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WorkflowStepListResponse(BaseModel):
    """List workflow steps response."""
    success: bool
    message: str
    data: list[WorkflowStepResponse]

class WorkflowResponse(BaseModel):
    """Workflow response."""
    id: str
    name: str
    description: str | None
    trigger: str
    is_active: bool
    steps: list[WorkflowStepResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WorkflowListResponse(BaseModel):
    """List workflows response."""
    success: bool
    message: str
    data: list[WorkflowResponse]

class WorkflowSingleResponse(BaseModel):
    """Single workflow response."""
    success: bool
    message: str
    data: WorkflowResponse

class WorkflowTestRequest(BaseModel):
    """Test a workflow with sample data."""
    event_data: dict[str, Any] = Field(default_factory=lambda: {"attendee_email": "test@example.com", "attendee_name": "Test User", "booking_title": "Test Meeting", "booking_time": datetime.now(UTC).isoformat(), "booking_id": "test-booking-123"})

class WorkflowTestResponse(BaseModel):
    """Workflow test response."""
    success: bool
    message: str
    data: dict[str, Any]

class ActionTypeResponse(BaseModel):
    """Available action types."""
    success: bool
    message: str
    data: list[dict[str, str]]

class TriggerTypeResponse(BaseModel):
    """Available trigger types."""
    success: bool
    message: str
    data: list[dict[str, str]]

def _serialize_step(step: WorkflowStepTable) -> dict[str, Any]:
    """Serialize workflow step to dict."""
    return {"id": step.id, "step_number": step.step_number, "action_type": step.action_type, "action_config": step.action_config, "delay_minutes": step.delay_minutes, "is_active": step.is_active, "created_at": step.created_at.isoformat() if step.created_at else None}

def _serialize_workflow(workflow: WorkflowTable) -> dict[str, Any]:
    """Serialize workflow to dict."""
    return {"id": workflow.id, "name": workflow.name, "description": workflow.description, "trigger": workflow.trigger, "is_active": workflow.is_active, "steps": [_serialize_step(s) for s in workflow.steps or []], "created_at": workflow.created_at.isoformat() if workflow.created_at else None, "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None}

@router.get("/triggers", response_model=TriggerTypeResponse)
async def get_trigger_types():
    """Get available workflow trigger types."""
    engine = get_workflow_engine()
    return {"success": True, "message": "Triggers retrieved", "data": [{"value": k, "label": v} for k, v in engine.TRIGGERS.items()]}

@router.get("/actions", response_model=ActionTypeResponse)
async def get_action_types():
    """Get available workflow action types."""
    engine = get_workflow_engine()
    return {"success": True, "message": "Actions retrieved", "data": [{"value": k, "label": v} for k, v in engine.ACTIONS.items()]}

@router.get("", response_model=WorkflowListResponse)
async def list_workflows(current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """List all workflows for the current user."""
    stmt = select(WorkflowTable).where(WorkflowTable.user_id == current_user.id).order_by(WorkflowTable.created_at.desc())
    result = await db.execute(stmt)
    workflows = result.scalars().all()
    for workflow in workflows:
        workflow.steps
    return {"success": True, "message": f"Found {len(workflows)} workflows", "data": [_serialize_workflow(w) for w in workflows]}

@router.post("", response_model=WorkflowSingleResponse)
async def create_workflow(payload: WorkflowCreate, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """Create a new workflow with steps."""
    try:
        workflow = WorkflowTable(id=generate_uuid(), user_id=current_user.id, name=payload.name, description=payload.description, trigger=payload.trigger, is_active=payload.is_active)
        db.add(workflow)
        await db.flush()
        for step_data in payload.steps:
            step = WorkflowStepTable(id=generate_uuid(), workflow_id=workflow.id, step_number=step_data.step_number, action_type=step_data.action_type, action_config=step_data.action_config, delay_minutes=step_data.delay_minutes, is_active=step_data.is_active)
            db.add(step)
        await db.commit()
        await db.refresh(workflow)
        logger.info("Created workflow %s for user %s...", workflow.id, current_user.id[:8])
        return {"success": True, "message": "Workflow created successfully", "data": _serialize_workflow(workflow)}
    except Exception as e:
        logger.exception("Failed to create workflow: %s", e)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {e!s}")

@router.get("/{workflow_id}", response_model=WorkflowSingleResponse)
async def get_workflow(workflow_id: str, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """Get a specific workflow."""
    stmt = select(WorkflowTable).where(and_(WorkflowTable.id == workflow_id, WorkflowTable.user_id == current_user.id))
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"success": True, "message": "Workflow retrieved successfully", "data": _serialize_workflow(workflow)}

@router.patch("/{workflow_id}", response_model=WorkflowSingleResponse)
async def update_workflow(workflow_id: str, payload: WorkflowUpdate, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """Update a workflow."""
    stmt = select(WorkflowTable).where(and_(WorkflowTable.id == workflow_id, WorkflowTable.user_id == current_user.id))
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if payload.name is not None:
        workflow.name = payload.name
    if payload.description is not None:
        workflow.description = payload.description
    if payload.trigger is not None:
        workflow.trigger = payload.trigger
    if payload.is_active is not None:
        workflow.is_active = payload.is_active
    workflow.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(workflow)
    logger.info("Updated workflow %s", workflow.id)
    return {"success": True, "message": "Workflow updated successfully", "data": _serialize_workflow(workflow)}

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """Delete a workflow."""
    stmt = select(WorkflowTable).where(and_(WorkflowTable.id == workflow_id, WorkflowTable.user_id == current_user.id))
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(workflow)
    await db.commit()
    logger.info("Deleted workflow %s", workflow_id)
    return {"success": True, "message": "Workflow deleted successfully"}

@router.post("/{workflow_id}/steps")
async def add_workflow_step(workflow_id: str, step: WorkflowStepCreate, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """Add a step to a workflow."""
    stmt = select(WorkflowTable).where(and_(WorkflowTable.id == workflow_id, WorkflowTable.user_id == current_user.id))
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    new_step = WorkflowStepTable(id=generate_uuid(), workflow_id=workflow_id, step_number=step.step_number, action_type=step.action_type, action_config=step.action_config, delay_minutes=step.delay_minutes, is_active=step.is_active)
    db.add(new_step)
    await db.commit()
    await db.refresh(new_step)
    return {"success": True, "message": "Step added successfully", "data": _serialize_step(new_step)}

@router.get("/{workflow_id}/steps", response_model=WorkflowStepListResponse)
async def list_workflow_steps(workflow_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """List all steps for a specific workflow."""
    stmt = select(WorkflowTable).where(and_(WorkflowTable.id == workflow_id, WorkflowTable.user_id == current_user.id))
    workflow = (await db.execute(stmt)).scalars().first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    stmt = select(WorkflowStepTable).where(WorkflowStepTable.workflow_id == workflow_id).order_by(WorkflowStepTable.step_number)
    steps = (await db.execute(stmt)).scalars().all()
    return WorkflowStepListResponse(success=True, message=f"Retrieved {len(steps)} steps", data=[WorkflowStepResponse.model_validate(s) for s in steps])

@router.delete("/{workflow_id}/steps/{step_id}")
async def delete_workflow_step(workflow_id: str, step_id: str, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """Delete a workflow step."""
    stmt = select(WorkflowTable).where(and_(WorkflowTable.id == workflow_id, WorkflowTable.user_id == current_user.id))
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    stmt = delete(WorkflowStepTable).where(and_(WorkflowStepTable.id == step_id, WorkflowStepTable.workflow_id == workflow_id))
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Step not found")
    return {"success": True, "message": "Step deleted successfully"}

@router.post("/{workflow_id}/test", response_model=WorkflowTestResponse)
async def test_workflow(workflow_id: str, payload: WorkflowTestRequest, current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """Test a workflow with sample data."""
    stmt = select(WorkflowTable).where(and_(WorkflowTable.id == workflow_id, WorkflowTable.user_id == current_user.id))
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    engine = get_workflow_engine()
    try:
        result_data = await engine.execute_workflow(db=db, workflow=workflow, booking_id="test-booking-id", event_data=payload.event_data)
        return {"success": True, "message": "Workflow test completed", "data": result_data}
    except Exception as e:
        logger.exception("Workflow test failed: %s", e)
        return {"success": False, "message": f"Workflow test failed: {e!s}", "data": {"error": str(e)}}

@router.post("/{workflow_id}/trigger")
async def manually_trigger_workflow(workflow_id: str, event_data: dict[str, Any], current_user: UserTable=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    """Manually trigger a workflow for testing."""
    stmt = select(WorkflowTable).where(and_(WorkflowTable.id == workflow_id, WorkflowTable.user_id == current_user.id))
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    engine = get_workflow_engine()
    try:
        result_data = await engine.execute_workflow(db=db, workflow=workflow, booking_id=event_data.get("booking_id", "manual-trigger"), event_data=event_data)
        return {"success": True, "message": "Workflow triggered successfully", "data": result_data}
    except Exception as e:
        logger.exception("Manual workflow trigger failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
