"""
Bookings API Routes with AI Automation

Provides endpoints for creating bookings and triggering AI agent automation.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from backend.utils.db import get_db
from backend.api.deps import get_current_user
from backend.models.tables import UserTable
from backend.services.booking_automation import BookingAutomationService, AutomationResult
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/bookings", tags=["bookings"])


# ═══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class BookingCreateRequest(BaseModel):
    """Request to create a new booking"""
    title: str = Field(..., description="Meeting title")
    description: Optional[str] = Field(None, description="Meeting description")
    start_time: str = Field(..., description="Start time (ISO format)")
    duration_minutes: int = Field(30, description="Duration in minutes")
    attendees: list[str] = Field(..., description="List of attendee emails")
    organizer_id: Optional[str] = Field(None, description="Organizer user ID")
    location: Optional[str] = Field(None, description="Meeting location")
    meeting_type: str = Field("consultation", description="Type of meeting")
    estimated_value: Optional[float] = Field(None, description="Estimated business value")


class BookingCreateResponse(BaseModel):
    """Response after creating booking"""
    status: str
    booking_id: str
    automation: str
    message: str


class AutomationStatusResponse(BaseModel):
    """Automation status for a booking"""
    booking_id: str
    status: str  # pending, in_progress, completed, failed
    automation_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    decision_score: Optional[int] = None
    risk_assessment: Optional[str] = None
    actions_completed: int = 0
    actions_total: int = 0
    current_action: Optional[str] = None
    error: Optional[str] = None


class AutomationResultResponse(BaseModel):
    """Complete automation result"""
    booking_id: str
    status: str
    decision_score: int
    risk_assessment: str
    execution_time_ms: float
    timestamp: str
    agent_decisions: Dict[str, Any]
    actions_executed: list[Dict[str, Any]]
    external_ids: Dict[str, Optional[str]]


# ═══════════════════════════════════════════════════════════════════
# IN-MEMORY AUTOMATION TRACKING (Replace with Redis in production)
# ═══════════════════════════════════════════════════════════════════

_automation_tasks: Dict[str, Dict[str, Any]] = {}


def _track_automation_start(booking_id: str, task: asyncio.Task) -> str:
    """Track the start of an automation task"""
    automation_id = f"auto_{booking_id}_{datetime.utcnow().timestamp()}"
    
    _automation_tasks[booking_id] = {
        "automation_id": automation_id,
        "task": task,
        "status": "in_progress",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None
    }
    
    return automation_id


def _update_automation_result(booking_id: str, result: AutomationResult):
    """Update automation with result"""
    if booking_id in _automation_tasks:
        _automation_tasks[booking_id].update({
            "status": result.automation_status,
            "completed_at": datetime.utcnow().isoformat(),
            "result": result,
            "decision_score": result.decision_score,
            "risk_assessment": result.risk_assessment,
            "actions_completed": len(result.actions_executed)
        })


def _update_automation_error(booking_id: str, error: str):
    """Update automation with error"""
    if booking_id in _automation_tasks:
        _automation_tasks[booking_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error": error
        })


# ═══════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=BookingCreateResponse,
    summary="Create booking and trigger AI automation",
    description="""
    Creates a new booking in the database and triggers AI agent automation asynchronously.
    
    The automation runs in the background and the API returns immediately with
    "automation": "in_progress". Use the /automation endpoint to check status.
    
    The AI agent will:
    1. Analyze attendee reliability and booking characteristics
    2. Decide optimal actions (email, calendar, reminders, tasks)
    3. Execute actions automatically
    4. Store results for tracking
    """
)
async def create_booking(
    booking_data: BookingCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> BookingCreateResponse:
    """
    Create booking and trigger AI automation
    
    Args:
        booking_data: Booking details
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Booking creation status with automation tracking
    """
    try:
        logger.info(f"📅 API: Creating booking '{booking_data.title}' for user {current_user.id}")
        
        # Create booking in database
        # TODO: Replace with actual database insert
        booking = {
            "id": f"booking_{datetime.utcnow().timestamp()}",
            "title": booking_data.title,
            "description": booking_data.description,
            "start_time": booking_data.start_time,
            "duration_minutes": booking_data.duration_minutes,
            "attendees": booking_data.attendees,
            "organizer_id": booking_data.organizer_id or current_user.id,
            "location": booking_data.location,
            "meeting_type": booking_data.meeting_type,
            "estimated_value": booking_data.estimated_value,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ API: Booking created with ID: {booking['id']}")
        
        # Trigger AI automation asynchronously with fallback
        # This runs in the background and doesn't block the response
        async def run_automation():
            """Background task for automation with intelligent fallback"""
            try:
                from backend.ai.fallback import automate_booking_with_fallback
                
                # Build attendee data from booking
                attendee_data = None
                if booking.get("attendees"):
                    attendee_data = {
                        "email": booking["attendees"][0],
                        "name": booking.get("attendee_name", ""),
                    }
                
                # Run with full fallback support:
                # Level 1: AI Agent → Level 2: Rule-based → Level 3: Manual review
                fallback_result = await automate_booking_with_fallback(
                    booking=booking,
                    attendee=attendee_data
                )
                
                # Convert FallbackResult to AutomationResult for tracking
                from backend.services.booking_automation import AutomationResult
                result = AutomationResult(
                    booking_id=booking["id"],
                    automation_status=fallback_result.status,
                    actions_executed=fallback_result.actions,
                    agent_decisions={"mode": fallback_result.mode.value},
                    external_results={},
                    risk_assessment="unknown",
                    decision_score=70 if fallback_result.mode.value == "rule_based" else 85,
                    execution_time_ms=fallback_result.execution_time_ms,
                    timestamp=fallback_result.timestamp
                )
                
                # Update tracking with result
                _update_automation_result(booking["id"], result)
                
                logger.info(
                    f"✅ Automation completed for {booking['id']}: "
                    f"Mode={fallback_result.mode.value}, Status={fallback_result.status}"
                )
                
            except Exception as e:
                logger.error(f"❌ Automation failed for {booking['id']}: {e}")
                _update_automation_error(booking["id"], str(e))
        
        # Create background task
        task = asyncio.create_task(run_automation())
        
        # Track the automation
        automation_id = _track_automation_start(booking["id"], task)
        
        logger.info(f"🤖 API: Automation triggered (ID: {automation_id})")
        
        # Return immediately - automation runs in background
        return BookingCreateResponse(
            status="created",
            booking_id=booking["id"],
            automation="in_progress",
            message="Booking created successfully. AI automation is running in the background."
        )
        
    except Exception as e:
        logger.error(f"❌ API: Failed to create booking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create booking: {str(e)}")


@router.get(
    "/{booking_id}/automation",
    response_model=AutomationStatusResponse,
    summary="Get automation status for booking",
    description="""
    Get the current status of AI automation for a specific booking.
    
    Returns:
    - Status: pending, in_progress, completed, failed
    - Progress: actions completed vs total
    - Current action being executed
    - Decision score and risk assessment (when complete)
    - Error details (if failed)
    """
)
async def get_automation_status(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> AutomationStatusResponse:
    """
    Get automation status for a booking
    
    Args:
        booking_id: Booking ID to check
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Current automation status and progress
    """
    try:
        # Check in-memory tracking
        if booking_id in _automation_tasks:
            auto = _automation_tasks[booking_id]
            
            # Get result if available
            result = auto.get("result")
            
            return AutomationStatusResponse(
                booking_id=booking_id,
                status=auto["status"],
                automation_id=auto.get("automation_id"),
                started_at=auto.get("started_at"),
                completed_at=auto.get("completed_at"),
                decision_score=auto.get("decision_score"),
                risk_assessment=auto.get("risk_assessment"),
                actions_completed=auto.get("actions_completed", 0),
                actions_total=len(result.actions_executed) if result else 0,
                current_action=None,  # Could track current action in service
                error=auto.get("error")
            )
        
        # Check database for completed automations
        # TODO: Query database for stored results
        # automation_record = await db.query(AutomationTable).filter(...).first()
        
        # If not found, return not found
        raise HTTPException(
            status_code=404,
            detail=f"No automation found for booking {booking_id}. "
                   f"The automation may not have started yet or the booking doesn't exist."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving automation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{booking_id}/automation/result",
    response_model=AutomationResultResponse,
    summary="Get complete automation result",
    description="""
    Get the complete automation result including:
    - Decision score (0-100)
    - Risk assessment
    - Actions executed with results
    - External IDs (email, calendar, task)
    - Agent decisions and reasoning
    
    Only available when automation is completed.
    """
)
async def get_automation_result(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> AutomationResultResponse:
    """
    Get complete automation result
    
    Args:
        booking_id: Booking ID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Complete automation result
    """
    try:
        # Check in-memory tracking
        if booking_id in _automation_tasks:
            auto = _automation_tasks[booking_id]
            result = auto.get("result")
            
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Automation result not yet available for {booking_id}"
                )
            
            return AutomationResultResponse(
                booking_id=result.booking_id,
                status=result.automation_status,
                decision_score=result.decision_score,
                risk_assessment=result.risk_assessment,
                execution_time_ms=result.execution_time_ms,
                timestamp=result.timestamp,
                agent_decisions=result.agent_decisions,
                actions_executed=[
                    {
                        "tool_name": a.get("tool_name"),
                        "success": a.get("success"),
                        "status": a.get("status"),
                        "email_id": a.get("email_id"),
                        "event_id": a.get("event_id"),
                        "task_id": a.get("task_id")
                    }
                    for a in result.actions_executed
                ],
                external_ids=result.external_results
            )
        
        # TODO: Check database for stored results
        
        raise HTTPException(
            status_code=404,
            detail=f"No automation result found for booking {booking_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving automation result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{booking_id}/automation/retry",
    response_model=BookingCreateResponse,
    summary="Retry failed automation",
    description="Retry automation for a booking that previously failed"
)
async def retry_automation(
    booking_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> BookingCreateResponse:
    """
    Retry automation for a failed booking
    
    Args:
        booking_id: Booking ID to retry
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Retry status
    """
    try:
        # Check if booking exists and belongs to user
        # TODO: Query database
        
        # Check current automation status
        if booking_id in _automation_tasks:
            auto = _automation_tasks[booking_id]
            if auto["status"] == "in_progress":
                raise HTTPException(
                    status_code=400,
                    detail=f"Automation already in progress for {booking_id}"
                )
        
        # Trigger new automation
        async def run_retry():
            try:
                service = BookingAutomationService()
                result = await service.process_booking_created(
                    booking_id=booking_id,
                    user_id=current_user.id,
                    trigger_source="api_retry"
                )
                _update_automation_result(booking_id, result)
            except Exception as e:
                _update_automation_error(booking_id, str(e))
        
        task = asyncio.create_task(run_retry())
        automation_id = _track_automation_start(booking_id, task)
        
        return BookingCreateResponse(
            status="retrying",
            booking_id=booking_id,
            automation="in_progress",
            message="Automation retry started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/automation/queue",
    summary="Get automation queue status",
    description="Get status of all running and pending automations"
)
async def get_automation_queue(
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get automation queue status
    
    Args:
        current_user: Authenticated user
    
    Returns:
        Queue status with counts and details
    """
    try:
        running = sum(1 for a in _automation_tasks.values() if a["status"] == "in_progress")
        completed = sum(1 for a in _automation_tasks.values() if a["status"] == "completed")
        failed = sum(1 for a in _automation_tasks.values() if a["status"] == "failed")
        
        recent_tasks = [
            {
                "booking_id": bid,
                "status": auto["status"],
                "started_at": auto.get("started_at"),
                "automation_id": auto.get("automation_id")
            }
            for bid, auto in list(_automation_tasks.items())[-10:]  # Last 10
        ]
        
        return {
            "total": len(_automation_tasks),
            "running": running,
            "completed": completed,
            "failed": failed,
            "recent_tasks": recent_tasks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# WEBHOOK ENDPOINT
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/webhook/automation-complete",
    summary="Webhook for automation completion",
    description="Webhook called when automation completes (for external integrations)"
)
async def automation_webhook(
    booking_id: str,
    automation_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Webhook for automation completion
    
    Args:
        booking_id: Booking ID
        automation_id: Automation ID
        status: Completion status
        result: Optional result data
    
    Returns:
        Acknowledgment
    """
    logger.info(f"🔔 Webhook: Automation {automation_id} for {booking_id} completed: {status}")
    
    # Could trigger notifications, analytics, etc.
    
    return {"status": "acknowledged"}
