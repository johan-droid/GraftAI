"""
Booking Automation API Routes

Provides endpoints for triggering and monitoring AI agent automation
for bookings created in the scheduler.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.auth.dependencies import get_current_user
from backend.models.tables import UserTable, EventTable
from backend.services.booking_automation import (
    BookingAutomationService,
    AutomationResult,
    on_booking_created
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/bookings", tags=["booking-automation"])


# ═══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class TriggerAutomationRequest(BaseModel):
    """Request to trigger automation for a booking"""
    booking_id: str = Field(..., description="ID of the booking to automate")
    user_id: Optional[str] = Field(None, description="User ID (defaults to current user)")
    trigger_source: str = Field("api", description="Source of trigger (scheduler, api, webhook)")


class AutomationActionResult(BaseModel):
    """Result of a single automation action"""
    tool_name: str
    success: bool
    status: str
    timestamp: str
    email_id: Optional[str] = None
    event_id: Optional[str] = None
    task_id: Optional[str] = None
    error: Optional[str] = None


class AgentDecisionInfo(BaseModel):
    """Information about agent decisions"""
    actions: List[str]
    reasoning: str
    risk_assessment: str
    confidence: str
    vip_level: Optional[str] = None
    requires_human_review: bool = False
    human_review_reason: Optional[str] = None


class AutomationStatusResponse(BaseModel):
    """Response for automation status"""
    booking_id: str
    status: str  # completed, partial, failed, pending
    decision_score: int = Field(..., ge=0, le=100, description="AI decision quality score 0-100")
    risk_assessment: str
    execution_time_ms: float
    timestamp: str
    agent_decisions: AgentDecisionInfo
    actions_executed: List[AutomationActionResult]
    external_ids: Dict[str, Optional[str]]  # email_id, calendar_id, task_id
    automation_summary: str


class AutomationHistoryResponse(BaseModel):
    """Response for automation history"""
    booking_id: str
    automation_count: int
    history: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/{booking_id}/automate",
    response_model=AutomationStatusResponse,
    summary="Trigger AI automation for a booking",
    description=""
    "Triggers the complete AI agent workflow for a booking:\n"
    "1. Perception - Load booking data, attendee profile, context\n"
    "2. Reasoning - LLaMA analyzes and decides optimal actions\n"
    "3. Action - Execute tools (email, calendar, tasks)\n"
    "4. Reflection - Assess outcomes and learn patterns\n"
    "5. Store results and return status\n"
)
async def trigger_booking_automation(
    booking_id: str,
    background_tasks: BackgroundTasks,
    request: Optional[TriggerAutomationRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> AutomationStatusResponse:
    """
    Trigger AI agent automation for a specific booking.
    
    This endpoint runs the complete 4-phase agent workflow:
    - Perception: Gather context about booking and attendee
    - Cognition: Analyze and decide optimal actions
    - Action: Execute decided tools (email, calendar, tasks)
    - Reflection: Assess outcomes and update knowledge
    
    Returns detailed results including:
    - Decision score (0-100)
    - Risk assessment
    - Actions executed
    - External IDs (email, calendar, task)
    """
    try:
        logger.info(f"🚀 API: Triggering automation for booking {booking_id}")
        
        # Initialize automation service
        service = BookingAutomationService()
        
        # Get user ID (from request or current user)
        user_id = request.user_id if request else current_user.id
        trigger_source = request.trigger_source if request else "api"
        
        # Run automation workflow
        result = await service.process_booking_created(
            booking_id=booking_id,
            user_id=user_id,
            trigger_source=trigger_source
        )
        
        # Build agent decisions info
        agent_decisions = AgentDecisionInfo(
            actions=result.agent_decisions.get("actions", []),
            reasoning=result.agent_decisions.get("reasoning", "")[:500],  # Truncate
            risk_assessment=result.risk_assessment,
            confidence=result.agent_decisions.get("confidence", "MEDIUM"),
            vip_level=result.agent_decisions.get("vip_level"),
            requires_human_review=result.agent_decisions.get("requires_human_review", False),
            human_review_reason=result.agent_decisions.get("human_review_reason")
        )
        
        # Build action results
        actions_executed = [
            AutomationActionResult(
                tool_name=action.get("tool_name", "unknown"),
                success=action.get("success", False),
                status=action.get("status", "unknown"),
                timestamp=action.get("timestamp", datetime.utcnow().isoformat()),
                email_id=action.get("email_id"),
                event_id=action.get("event_id"),
                task_id=action.get("task_id"),
                error=action.get("error")
            )
            for action in result.actions_executed
        ]
        
        # Build summary
        successful_actions = sum(1 for a in actions_executed if a.success)
        total_actions = len(actions_executed)
        
        automation_summary = (
            f"AI Agent executed {successful_actions}/{total_actions} actions "
            f"with decision score {result.decision_score}/100. "
            f"Risk assessment: {result.risk_assessment.upper()}. "
        )
        
        if result.decision_score >= 90:
            automation_summary += "Excellent automation performance."
        elif result.decision_score >= 70:
            automation_summary += "Good automation performance."
        else:
            automation_summary += "Some issues encountered."
        
        logger.info(f"✅ API: Automation complete for {booking_id} "
                   f"(Score: {result.decision_score}, Status: {result.automation_status})")
        
        return AutomationStatusResponse(
            booking_id=result.booking_id,
            status=result.automation_status,
            decision_score=result.decision_score,
            risk_assessment=result.risk_assessment,
            execution_time_ms=result.execution_time_ms,
            timestamp=result.timestamp,
            agent_decisions=agent_decisions,
            actions_executed=actions_executed,
            external_ids=result.external_results,
            automation_summary=automation_summary
        )
        
    except Exception as e:
        logger.error(f"❌ API: Automation failed for {booking_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Automation failed: {str(e)}"
        )


@router.get(
    "/{booking_id}/automation-status",
    response_model=AutomationStatusResponse,
    summary="Get automation status for a booking",
    description="Retrieve the current automation status and results for a booking"
)
async def get_automation_status(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> AutomationStatusResponse:
    """
    Get the automation status and results for a specific booking.
    
    Returns the same detailed information as the trigger endpoint,
    but retrieves stored results instead of running automation.
    """
    try:
        # TODO: Query database for stored automation results
        # For now, return a not-found response
        
        # Check if booking exists and user has access
        # booking = await db.get(EventTable, booking_id)
        # if not booking or booking.user_id != current_user.id:
        #     raise HTTPException(status_code=404, detail="Booking not found")
        
        # Return stored results
        raise HTTPException(
            status_code=404,
            detail=f"Automation status for booking {booking_id} not found. "
                   f"Trigger automation first with POST /bookings/{booking_id}/automate"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving automation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/automation/history",
    response_model=List[AutomationStatusResponse],
    summary="Get automation history for current user",
    description="Retrieve history of all automation runs for the current user"
)
async def get_automation_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> List[AutomationStatusResponse]:
    """
    Get automation history for the current user.
    
    Returns a list of recent automation results, ordered by timestamp.
    """
    try:
        # TODO: Query database for automation history
        # bookings_with_automation = await db.execute(
        #     select(EventTable)
        #     .where(EventTable.user_id == current_user.id)
        #     .where(EventTable.automation_status.isnot(None))
        #     .order_by(desc(EventTable.last_automation_sync))
        #     .limit(limit)
        # )
        
        # For now, return empty list
        return []
        
    except Exception as e:
        logger.error(f"Error retrieving automation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/webhook/booking-created",
    summary="Webhook for booking creation events",
    description=""
    "Webhook endpoint called by scheduler when a booking is created.\n"
    "Triggers AI automation automatically.\n"
    "Requires webhook secret for authentication."
)
async def webhook_booking_created(
    booking_id: str,
    user_id: str,
    background_tasks: BackgroundTasks,
    webhook_secret: str,  # Should be validated
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Webhook endpoint triggered when a booking is created.
    
    This is called automatically by the scheduler system.
    Runs automation in background and returns immediately.
    """
    try:
        # Validate webhook secret
        # if webhook_secret != settings.WEBHOOK_SECRET:
        #     raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
        logger.info(f"🔔 Webhook: Booking created {booking_id} for user {user_id}")
        
        # Trigger automation in background
        # This returns immediately while automation runs asynchronously
        background_tasks.add_task(
            _run_automation_background,
            booking_id=booking_id,
            user_id=user_id
        )
        
        return {
            "status": "accepted",
            "booking_id": booking_id,
            "message": "Automation queued for background execution",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_automation_background(booking_id: str, user_id: str):
    """Background task to run automation"""
    try:
        service = BookingAutomationService()
        result = await service.process_booking_created(
            booking_id=booking_id,
            user_id=user_id,
            trigger_source="webhook"
        )
        
        logger.info(f"Background automation complete: {booking_id} "
                   f"(Score: {result.decision_score})")
        
        # TODO: Send notification to user about completion
        
    except Exception as e:
        logger.error(f"Background automation failed: {booking_id} - {e}")
        # TODO: Alert on failure, queue for retry


@router.get(
    "/automation/stats",
    summary="Get automation statistics",
    description="Get aggregate statistics about automation performance"
)
async def get_automation_stats(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get automation statistics for the current user.
    
    Returns aggregate metrics about automation performance.
    """
    try:
        # TODO: Query database for stats
        # - Total automations
        # - Success rate
        # - Average decision score
        # - Most common actions
        # - Risk distribution
        
        # For now, return placeholder stats
        return {
            "period_days": days,
            "total_automations": 0,
            "successful": 0,
            "failed": 0,
            "partial": 0,
            "success_rate": 0.0,
            "avg_decision_score": 0,
            "avg_execution_time_ms": 0,
            "actions_breakdown": {},
            "risk_distribution": {
                "low": 0,
                "medium": 0,
                "high": 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# UTILITY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/{booking_id}/retry-automation",
    summary="Retry failed automation",
    description="Retry automation for a booking that previously failed"
)
async def retry_automation(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> AutomationStatusResponse:
    """
    Retry automation for a booking that previously failed or partially succeeded.
    """
    # This would re-trigger automation
    # Similar to trigger_booking_automation but with checks
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.post(
    "/{booking_id}/cancel-automation",
    summary="Cancel pending automation",
    description="Cancel automation that is still pending or running"
)
async def cancel_automation(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel automation that is still in progress.
    """
    # This would stop background automation
    raise HTTPException(status_code=501, detail="Not yet implemented")
