"""
Workflows API Routes

Fully functional workflow management for automation.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete

from backend.utils.db import get_db
from backend.api.deps import get_current_user
from backend.models.tables import (
    UserTable, WorkflowTable, WorkflowStepTable, generate_uuid
)
from backend.services.workflow_engine import get_workflow_engine
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


# ═══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class WorkflowStepCreate(BaseModel):
    """Create a workflow step."""
    step_number: int = Field(..., ge=1)
    action_type: str = Field(..., pattern="^(EMAIL|SMS|WEBHOOK|SLACK|TEAMS|CALENDAR)$")
    action_config: Dict[str, Any] = Field(default_factory=dict)
    delay_minutes: int = Field(default=0, ge=0)
    is_active: bool = True


class WorkflowCreate(BaseModel):
    """Create a new workflow."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    trigger: str = Field(..., pattern="^(BOOKING_CREATED|BOOKING_CONFIRMED|BOOKING_CANCELLED|BOOKING_RESCHEDULED|BOOKING_REMINDER|BOOKING_FOLLOWUP)$")
    is_active: bool = True
    steps: List[WorkflowStepCreate] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    """Update an existing workflow."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    trigger: Optional[str] = Field(None, pattern="^(BOOKING_CREATED|BOOKING_CONFIRMED|BOOKING_CANCELLED|BOOKING_RESCHEDULED|BOOKING_REMINDER|BOOKING_FOLLOWUP)$")
    is_active: Optional[bool] = None


class WorkflowStepResponse(BaseModel):
    """Workflow step response."""
    id: str
    workflow_id: str
    step_number: int
    action_type: str
    action_config: Dict[str, Any]
    delay_minutes: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowStepListResponse(BaseModel):
    """List workflow steps response."""
    success: bool
    message: str
    data: List[WorkflowStepResponse]


class WorkflowResponse(BaseModel):
    """Workflow response."""
    id: str
    name: str
    description: Optional[str]
    trigger: str
    is_active: bool
    steps: List[WorkflowStepResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowListResponse(BaseModel):
    """List workflows response."""
    success: bool
    message: str
    data: List[WorkflowResponse]


class WorkflowTestRequest(BaseModel):
    """Test a workflow with sample data."""
    event_data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "attendee_email": "test@example.com",
            "attendee_name": "Test User",
            "booking_title": "Test Meeting",
            "booking_time": datetime.now(timezone.utc).isoformat(),
            "booking_id": "test-booking-123",
        }
    )


class WorkflowTestResponse(BaseModel):
    """Workflow test response."""
    success: bool
    message: str
    data: Dict[str, Any]


class TriggerTypeResponse(BaseModel):
    """Available trigger types."""
    triggers: Dict[str, str]


class ActionTypeResponse(BaseModel):
    """Available action types."""
    actions: Dict[str, str]


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _serialize_step(step: WorkflowStepTable) -> Dict[str, Any]:
    """Serialize workflow step to dict."""
    return {
        "id": step.id,
        "step_number": step.step_number,
        "action_type": step.action_type,
        "action_config": step.action_config,
        "delay_minutes": step.delay_minutes,
        "is_active": step.is_active,
        "created_at": step.created_at.isoformat() if step.created_at else None,
    }


def _serialize_workflow(workflow: WorkflowTable) -> Dict[str, Any]:
    """Serialize workflow to dict."""
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "trigger": workflow.trigger,
        "is_active": workflow.is_active,
        "steps": [_serialize_step(s) for s in (workflow.steps or [])],
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
    }


# ═══════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/triggers", response_model=TriggerTypeResponse)
async def get_trigger_types():
    """Get available workflow trigger types."""
    engine = get_workflow_engine()
    return {"triggers": engine.TRIGGERS}


@router.get("/actions", response_model=ActionTypeResponse)
async def get_action_types():
    """Get available workflow action types."""
    engine = get_workflow_engine()
    return {"actions": engine.ACTIONS}


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all workflows for the current user."""
    stmt = select(WorkflowTable).where(
        WorkflowTable.user_id == current_user.id
    ).order_by(WorkflowTable.created_at.desc())
    
    result = await db.execute(stmt)
    workflows = result.scalars().all()
    
    # Eager load steps
    for workflow in workflows:
        workflow.steps  # This triggers the relationship loading
    
    return {
        "success": True,
        "message": f"Found {len(workflows)} workflows",
        "data": [_serialize_workflow(w) for w in workflows],
    }


@router.post("", response_model=WorkflowResponse)
async def create_workflow(
    payload: WorkflowCreate,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow with steps."""
    try:
        # Create workflow
        workflow = WorkflowTable(
            id=generate_uuid(),
            user_id=current_user.id,
            name=payload.name,
            description=payload.description,
            trigger=payload.trigger,
            is_active=payload.is_active,
        )
        
        db.add(workflow)
        await db.flush()  # Get the workflow ID
        
        # Create steps
        for step_data in payload.steps:
            step = WorkflowStepTable(
                id=generate_uuid(),
                workflow_id=workflow.id,
                step_number=step_data.step_number,
                action_type=step_data.action_type,
                action_config=step_data.action_config,
                delay_minutes=step_data.delay_minutes,
                is_active=step_data.is_active,
            )
            db.add(step)
        
        await db.commit()
        await db.refresh(workflow)
        
        logger.info(f"Created workflow {workflow.id} for user {current_user.id[:8]}...")
        
        return _serialize_workflow(workflow)
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific workflow."""
    stmt = select(WorkflowTable).where(
        and_(
            WorkflowTable.id == workflow_id,
            WorkflowTable.user_id == current_user.id,
        )
    )
    
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return _serialize_workflow(workflow)


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdate,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a workflow."""
    stmt = select(WorkflowTable).where(
        and_(
            WorkflowTable.id == workflow_id,
            WorkflowTable.user_id == current_user.id,
        )
    )
    
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Update fields
    if payload.name is not None:
        workflow.name = payload.name
    if payload.description is not None:
        workflow.description = payload.description
    if payload.trigger is not None:
        workflow.trigger = payload.trigger
    if payload.is_active is not None:
        workflow.is_active = payload.is_active
    
    workflow.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(workflow)
    
    logger.info(f"Updated workflow {workflow.id}")
    
    return _serialize_workflow(workflow)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a workflow."""
    stmt = select(WorkflowTable).where(
        and_(
            WorkflowTable.id == workflow_id,
            WorkflowTable.user_id == current_user.id,
        )
    )
    
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Delete workflow (cascade will delete steps)
    await db.delete(workflow)
    await db.commit()
    
    logger.info(f"Deleted workflow {workflow_id}")
    
    return {
        "success": True,
        "message": "Workflow deleted successfully",
    }


@router.post("/{workflow_id}/steps")
async def add_workflow_step(
    workflow_id: str,
    step: WorkflowStepCreate,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a step to a workflow."""
    # Verify workflow exists and belongs to user
    stmt = select(WorkflowTable).where(
        and_(
            WorkflowTable.id == workflow_id,
            WorkflowTable.user_id == current_user.id,
        )
    )
    
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create step
    new_step = WorkflowStepTable(
        id=generate_uuid(),
        workflow_id=workflow_id,
        step_number=step.step_number,
        action_type=step.action_type,
        action_config=step.action_config,
        delay_minutes=step.delay_minutes,
        is_active=step.is_active,
    )
    
    db.add(new_step)
    await db.commit()
    await db.refresh(new_step)
    
    return {
        "success": True,
        "message": "Step added successfully",
        "data": _serialize_step(new_step),
    }


@router.get("/{workflow_id}/steps", response_model=WorkflowStepListResponse)
async def list_workflow_steps(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """List all steps for a specific workflow."""
    # Verify workflow ownership
    stmt = select(WorkflowTable).where(
        and_(WorkflowTable.id == workflow_id, WorkflowTable.user_id == current_user.id)
    )
    workflow = (await db.execute(stmt)).scalars().first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    stmt = (
        select(WorkflowStepTable)
        .where(WorkflowStepTable.workflow_id == workflow_id)
        .order_by(WorkflowStepTable.step_order)
    )
    steps = (await db.execute(stmt)).scalars().all()

    return WorkflowStepListResponse(
        success=True,
        message=f"Retrieved {len(steps)} steps",
        data=[WorkflowStepResponse.model_validate(s) for s in steps],
    )


@router.delete("/{workflow_id}/steps/{step_id}")
async def delete_workflow_step(
    workflow_id: str,
    step_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a workflow step."""
    # Verify workflow exists and belongs to user
    stmt = select(WorkflowTable).where(
        and_(
            WorkflowTable.id == workflow_id,
            WorkflowTable.user_id == current_user.id,
        )
    )
    
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Delete step
    stmt = delete(WorkflowStepTable).where(
        and_(
            WorkflowStepTable.id == step_id,
            WorkflowStepTable.workflow_id == workflow_id,
        )
    )
    
    result = await db.execute(stmt)
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Step not found")
    
    return {
        "success": True,
        "message": "Step deleted successfully",
    }


@router.post("/{workflow_id}/test", response_model=WorkflowTestResponse)
async def test_workflow(
    workflow_id: str,
    payload: WorkflowTestRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test a workflow with sample data."""
    # Verify workflow exists and belongs to user
    stmt = select(WorkflowTable).where(
        and_(
            WorkflowTable.id == workflow_id,
            WorkflowTable.user_id == current_user.id,
        )
    )
    
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Execute workflow with test data
    engine = get_workflow_engine()
    
    try:
        result_data = await engine.execute_workflow(
            db=db,
            workflow=workflow,
            booking_id="test-booking-id",
            event_data=payload.event_data,
        )
        
        return {
            "success": True,
            "message": "Workflow test completed",
            "data": result_data,
        }
        
    except Exception as e:
        logger.error(f"Workflow test failed: {e}")
        return {
            "success": False,
            "message": f"Workflow test failed: {str(e)}",
            "data": {"error": str(e)},
        }


@router.post("/{workflow_id}/trigger")
async def manually_trigger_workflow(
    workflow_id: str,
    event_data: Dict[str, Any],
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a workflow for testing."""
    # Verify workflow exists and belongs to user
    stmt = select(WorkflowTable).where(
        and_(
            WorkflowTable.id == workflow_id,
            WorkflowTable.user_id == current_user.id,
        )
    )
    
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Execute workflow
    engine = get_workflow_engine()
    
    try:
        result_data = await engine.execute_workflow(
            db=db,
            workflow=workflow,
            booking_id=event_data.get("booking_id", "manual-trigger"),
            event_data=event_data,
        )
        
        return {
            "success": True,
            "message": "Workflow triggered successfully",
            "data": result_data,
        }
        
    except Exception as e:
        logger.error(f"Manual workflow trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
