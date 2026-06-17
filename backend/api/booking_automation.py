"""
Booking Automation API Routes

Provides endpoints for triggering and monitoring AI agent automation
for bookings created in the scheduler.
"""
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.models.tables import AIAutomationTable, UserTable
from backend.services.booking_automation import BookingAutomationService
from backend.services.notifications import send_custom_notification
from backend.utils.db import get_async_session_maker, get_db
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/bookings", tags=["booking-automation"])

class TriggerAutomationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    """Request to trigger automation for a booking"""
    booking_id: str = Field(..., description="ID of the booking to automate")
    user_id: str | None = Field(None, description="User ID (defaults to current user)")
    trigger_source: str = Field("api", description="Source of trigger (scheduler, api, webhook)")

class AutomationActionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    """Result of a single automation action"""
    tool_name: str
    success: bool
    status: str
    timestamp: str
    email_id: str | None = None
    event_id: str | None = None
    task_id: str | None = None
    error: str | None = None

class AgentDecisionInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    """Information about agent decisions"""
    actions: list[str]
    reasoning: str
    risk_assessment: str
    confidence: str
    vip_level: str | None = None
    requires_human_review: bool = False
    human_review_reason: str | None = None

class AutomationStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    """Response for automation status"""
    booking_id: str
    status: str
    decision_score: int = Field(..., ge=0, le=100, description="AI decision quality score 0-100")
    risk_assessment: str
    execution_time_ms: float
    timestamp: str
    agent_decisions: AgentDecisionInfo
    actions_executed: list[AutomationActionResult]
    external_ids: dict[str, str | None]
    automation_summary: str

class AutomationHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    """Response for automation history"""
    booking_id: str
    automation_count: int
    history: list[dict[str, Any]]

def _build_actions(actions: list[dict[str, Any]] | None) -> list[AutomationActionResult]:
    normalized: list[AutomationActionResult] = []
    for action in actions or []:
        normalized.append(AutomationActionResult(tool_name=action.get("tool_name", "unknown"), success=bool(action.get("success", False)), status=action.get("status", "unknown"), timestamp=str(action.get("timestamp") or datetime.now(UTC).isoformat()), email_id=action.get("email_id"), event_id=action.get("event_id"), task_id=action.get("task_id"), error=action.get("error")))
    return normalized

def _build_agent_decisions(agent_decisions: dict[str, Any] | None, risk_assessment: str, actions: list[dict[str, Any]]) -> AgentDecisionInfo:
    decisions = agent_decisions or {}
    action_names = decisions.get("actions") or [action.get("tool_name", "unknown") for action in actions]
    confidence = decisions.get("confidence", "MEDIUM")
    return AgentDecisionInfo(actions=action_names, reasoning=str(decisions.get("reasoning", ""))[:500], risk_assessment=str(decisions.get("risk_assessment", risk_assessment)), confidence=str(confidence), vip_level=decisions.get("vip_level"), requires_human_review=bool(decisions.get("requires_human_review", False)), human_review_reason=decisions.get("human_review_reason"))

def _build_summary(status: str, decision_score: int, risk_assessment: str, actions: list[dict[str, Any]]) -> str:
    if status == "in_progress":
        return "Automation is currently running."
    successful_actions = sum(1 for action in actions if action.get("success"))
    total_actions = len(actions)
    summary = f"AI Agent executed {successful_actions}/{total_actions} actions with decision score {decision_score}/100. Risk assessment: {risk_assessment.upper()}. "
    if decision_score >= 90:
        summary += "Excellent automation performance."
    elif decision_score >= 70:
        summary += "Good automation performance."
    else:
        summary += "Some issues encountered."
    return summary

def _build_status_response(automation: AIAutomationTable) -> AutomationStatusResponse:
    actions = automation.actions_executed or []
    decision_score = automation.decision_score or 0
    risk_assessment = automation.risk_assessment or "unknown"
    started_at = automation.started_at.isoformat() if automation.started_at else automation.created_at.isoformat() if automation.created_at else None
    completed_at = automation.completed_at.isoformat() if automation.completed_at else None
    return AutomationStatusResponse(booking_id=automation.booking_id, status=automation.status, decision_score=decision_score, risk_assessment=risk_assessment, execution_time_ms=automation.execution_time_ms or 0, timestamp=completed_at or started_at or datetime.now(UTC).isoformat(), agent_decisions=_build_agent_decisions(automation.agent_decisions, risk_assessment, actions), actions_executed=_build_actions(actions), external_ids=automation.external_results or {}, automation_summary=_build_summary(automation.status, decision_score, risk_assessment, actions))

def _build_result_response(automation: AIAutomationTable) -> AutomationStatusResponse:
    actions = automation.actions_executed or []
    decision_score = automation.decision_score or 0
    risk_assessment = automation.risk_assessment or "unknown"
    timestamp = automation.completed_at.isoformat() if automation.completed_at else automation.created_at.isoformat() if automation.created_at else datetime.now(UTC).isoformat()
    return AutomationStatusResponse(booking_id=automation.booking_id, status=automation.status, decision_score=decision_score, risk_assessment=risk_assessment, execution_time_ms=automation.execution_time_ms or 0, timestamp=timestamp, agent_decisions=_build_agent_decisions(automation.agent_decisions, risk_assessment, actions), actions_executed=_build_actions(actions), external_ids=automation.external_results or {}, automation_summary=_build_summary(automation.status, decision_score, risk_assessment, actions))

@router.post("/{booking_id}/automate", response_model=AutomationStatusResponse, summary="Trigger AI automation for a booking", description="Triggers the complete AI agent workflow for a booking:\n1. Perception - Load booking data, attendee profile, context\n2. Reasoning - LLaMA analyzes and decides optimal actions\n3. Action - Execute tools (email, calendar, tasks)\n4. Reflection - Assess outcomes and learn patterns\n5. Store results and return status\n")
async def trigger_booking_automation(booking_id: str, background_tasks: BackgroundTasks, request: TriggerAutomationRequest | None=None, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> AutomationStatusResponse:
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
        logger.info("🚀 API: Triggering automation for booking %s", booking_id)
        service = BookingAutomationService()
        user_id = request.user_id if request else current_user.id
        trigger_source = request.trigger_source if request else "api"
        result = await service.process_booking_created(booking_id=booking_id, user_id=user_id, trigger_source=trigger_source)
        agent_decisions = AgentDecisionInfo(actions=result.agent_decisions.get("actions", []), reasoning=result.agent_decisions.get("reasoning", "")[:500], risk_assessment=result.risk_assessment, confidence=result.agent_decisions.get("confidence", "MEDIUM"), vip_level=result.agent_decisions.get("vip_level"), requires_human_review=result.agent_decisions.get("requires_human_review", False), human_review_reason=result.agent_decisions.get("human_review_reason"))
        actions_executed = [AutomationActionResult(tool_name=action.get("tool_name", "unknown"), success=action.get("success", False), status=action.get("status", "unknown"), timestamp=action.get("timestamp", datetime.now(UTC).isoformat()), email_id=action.get("email_id"), event_id=action.get("event_id"), task_id=action.get("task_id"), error=action.get("error")) for action in result.actions_executed]
        successful_actions = sum(1 for a in actions_executed if a.success)
        total_actions = len(actions_executed)
        automation_summary = f"AI Agent executed {successful_actions}/{total_actions} actions with decision score {result.decision_score}/100. Risk assessment: {result.risk_assessment.upper()}. "
        if result.decision_score >= 90:
            automation_summary += "Excellent automation performance."
        elif result.decision_score >= 70:
            automation_summary += "Good automation performance."
        else:
            automation_summary += "Some issues encountered."
        logger.info("✅ API: Automation complete for %s (Score: %s, Status: %s)", booking_id, result.decision_score, result.automation_status)
        return AutomationStatusResponse(booking_id=result.booking_id, status=result.automation_status, decision_score=result.decision_score, risk_assessment=result.risk_assessment, execution_time_ms=result.execution_time_ms, timestamp=result.timestamp, agent_decisions=agent_decisions, actions_executed=actions_executed, external_ids=result.external_results, automation_summary=automation_summary)
    except Exception as e:
        logger.exception("❌ API: Automation failed for %s: %s", booking_id, e)
        raise HTTPException(status_code=500, detail=f"Automation failed: {e!s}")

@router.get("/{booking_id}/automation-status", response_model=AutomationStatusResponse, summary="Get automation status for a booking", description="Retrieve the current automation status and results for a booking")
async def get_automation_status(booking_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> AutomationStatusResponse:
    """
    Get the automation status and results for a specific booking.

    Returns the same detailed information as the trigger endpoint,
    but retrieves stored results instead of running automation.
    """
    try:
        db_result = await db.execute(select(AIAutomationTable).where(AIAutomationTable.booking_id == booking_id, AIAutomationTable.user_id == current_user.id).order_by(AIAutomationTable.created_at.desc()))
        automation = db_result.scalars().first()
        if automation:
            return _build_status_response(automation)
        raise HTTPException(status_code=404, detail=f"Automation status for booking {booking_id} not found. Trigger automation first with POST /bookings/{booking_id}/automate")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving automation status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/automation/history", response_model=list[AutomationStatusResponse], summary="Get automation history for current user", description="Retrieve history of all automation runs for the current user")
async def get_automation_history(limit: int=10, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> list[AutomationStatusResponse]:
    """
    Get automation history for the current user.

    Returns a list of recent automation results, ordered by timestamp.
    """
    try:
        db_result = await db.execute(select(AIAutomationTable).where(AIAutomationTable.user_id == current_user.id).order_by(AIAutomationTable.created_at.desc()).limit(max(limit, 1)))
        automations = db_result.scalars().all()
        return [_build_status_response(automation) for automation in automations]
    except Exception as e:
        logger.exception("Error retrieving automation history: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/booking-created", summary="Webhook for booking creation events", description="Webhook endpoint called by scheduler when a booking is created.\nTriggers AI automation automatically.\nRequires webhook secret for authentication.")
async def _verify_booking_webhook(request: Request, webhook_secret: str | None) -> bytes:
    secret = os.getenv("AUTOMATION_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Automation webhook secret not configured")
    header_signature = request.headers.get("X-GraftAI-Signature")
    payload = await request.body()
    if header_signature:
        expected_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, header_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")
        return payload
    if not webhook_secret or not hmac.compare_digest(webhook_secret, secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")
    return payload

async def webhook_booking_created(request: Request, booking_id: str, user_id: str, background_tasks: BackgroundTasks, webhook_secret: str | None=None, db: AsyncSession=Depends(get_db)) -> dict[str, Any]:
    """
    Webhook endpoint triggered when a booking is created.

    This is called automatically by the scheduler system.
    Runs automation in background and returns immediately.
    """
    try:
        await _verify_booking_webhook(request, webhook_secret)
        logger.info("🔔 Webhook: Booking created %s for user %s", booking_id, user_id)
        background_tasks.add_task(_run_automation_background, booking_id=booking_id, user_id=user_id)
        return {"status": "accepted", "booking_id": booking_id, "message": "Automation queued for background execution", "timestamp": datetime.now(UTC).isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Webhook error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

async def _run_automation_background(booking_id: str, user_id: str):
    """Background task to run automation"""
    try:
        service = BookingAutomationService()
        result = await service.process_booking_created(booking_id=booking_id, user_id=user_id, trigger_source="webhook")
        logger.info("Background automation complete: %s (Score: %s)", booking_id, result.decision_score)
        session_factory = get_async_session_maker()
        async with session_factory() as db:
            user_result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = user_result.scalars().first()
            user_email = user.email if user else None
            if user_email:
                try:
                    await send_custom_notification(user_email, subject=f"Booking automation finished for {booking_id}", message=f"Your booking automation for {booking_id} completed with a score of {result.decision_score}/100 and status {result.automation_status}.")
                except Exception as notification_error:
                    logger.warning("Background notification failed for %s: %s", booking_id, notification_error)
    except Exception as e:
        logger.exception("Background automation failed: %s - %s", booking_id, e)
        try:
            session_factory = get_async_session_maker()
            async with session_factory() as db:
                user_result = await db.execute(select(UserTable).where(UserTable.id == user_id))
                user = user_result.scalars().first()
                user_email = user.email if user else None
            if user_email:
                await send_custom_notification(user_email, subject=f"Booking automation failed for {booking_id}", message=f"The automation for booking {booking_id} failed and will need to be retried.")
        except Exception as notification_error:
            logger.warning("Failure notification could not be sent for %s: %s", booking_id, notification_error)

@router.get("/automation/stats", summary="Get automation statistics", description="Get aggregate statistics about automation performance")
async def get_automation_stats(days: int=30, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> dict[str, Any]:
    """
    Get automation statistics for the current user.

    Returns aggregate metrics about automation performance.
    """
    try:
        cutoff = datetime.now(UTC) - timedelta(days=max(days, 1))
        db_result = await db.execute(select(AIAutomationTable).where(AIAutomationTable.user_id == current_user.id, AIAutomationTable.created_at >= cutoff).order_by(AIAutomationTable.created_at.desc()))
        automations = db_result.scalars().all()
        total_automations = len(automations)
        successful = sum(1 for automation in automations if automation.status == "completed")
        failed = sum(1 for automation in automations if automation.status == "failed")
        partial = sum(1 for automation in automations if automation.status == "partial")
        decision_scores = [automation.decision_score for automation in automations if automation.decision_score is not None]
        execution_times = [automation.execution_time_ms for automation in automations if automation.execution_time_ms is not None]
        actions_breakdown: dict[str, int] = {}
        risk_distribution: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for automation in automations:
            for action in automation.actions_executed or []:
                tool_name = action.get("tool_name", "unknown")
                actions_breakdown[tool_name] = actions_breakdown.get(tool_name, 0) + 1
            raw_risk = automation.risk_assessment or "medium"
            try:
                risk_key = str(raw_risk).lower()
            except Exception:
                risk_key = "medium"
            allowed = {"low", "medium", "high", "critical"}
            if risk_key not in allowed:
                risk_key = "medium"
            risk_distribution[risk_key] = risk_distribution.get(risk_key, 0) + 1
        return {"period_days": days, "total_automations": total_automations, "successful": successful, "failed": failed, "partial": partial, "success_rate": round(successful / total_automations * 100, 2) if total_automations else 0.0, "avg_decision_score": round(sum(decision_scores) / len(decision_scores), 2) if decision_scores else 0, "avg_execution_time_ms": round(sum(execution_times) / len(execution_times), 2) if execution_times else 0, "actions_breakdown": actions_breakdown, "risk_distribution": risk_distribution, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error retrieving stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{booking_id}/retry-automation", summary="Retry failed automation", description="Retry automation for a booking that previously failed")
async def retry_automation(booking_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> AutomationStatusResponse:
    """
    Retry automation for a booking that previously failed or partially succeeded.
    """
    raise HTTPException(status_code=501, detail="Not yet implemented")

@router.post("/{booking_id}/cancel-automation", summary="Cancel pending automation", description="Cancel automation that is still pending or running")
async def cancel_automation(booking_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)) -> dict[str, Any]:
    """
    Cancel automation that is still in progress.
    """
    raise HTTPException(status_code=501, detail="Not yet implemented")
