"""
Bookings API Routes with AI Automation

Provides endpoints for creating bookings and triggering AI agent automation.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json
from sqlalchemy import select

from backend.utils.db import get_db, get_async_session_maker
from backend.api.deps import get_current_user
from backend.models.tables import (
    UserTable,
    BookingTable,
    AIAutomationTable,
    generate_uuid,
)
from backend.services.booking_automation import AutomationResult
from backend.utils.logger import get_logger
from backend.utils.idempotency import (
    check_idempotency_key,
    store_idempotency_key,
    idempotency_key_header,
)
from dateutil import parser as date_parser

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
    estimated_value: Optional[float] = Field(
        None, description="Estimated business value"
    )


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


def _track_automation_start(
    booking_id: str, task: asyncio.Task, automation_id: Optional[str] = None
) -> str:
    """Track the start of an automation task"""
    automation_id = (
        automation_id or f"auto_{booking_id}_{datetime.utcnow().timestamp()}"
    )

    _automation_tasks[booking_id] = {
        "automation_id": automation_id,
        "task": task,
        "status": "in_progress",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    return automation_id


def _update_automation_result(booking_id: str, result: AutomationResult):
    """Update automation with result"""
    if booking_id in _automation_tasks:
        _automation_tasks[booking_id].update(
            {
                "status": result.automation_status,
                "completed_at": datetime.utcnow().isoformat(),
                "result": result,
                "decision_score": result.decision_score,
                "risk_assessment": result.risk_assessment,
                "actions_completed": len(result.actions_executed),
            }
        )


def _update_automation_error(booking_id: str, error: str):
    """Update automation with error"""
    if booking_id in _automation_tasks:
        _automation_tasks[booking_id].update(
            {
                "status": "failed",
                "completed_at": datetime.utcnow().isoformat(),
                "error": error,
            }
        )


async def _persist_automation_result(
    booking_id: str,
    user_id: str,
    result: Optional[AutomationResult] = None,
    automation_id: Optional[str] = None,
    error: Optional[str] = None,
    trigger_source: str = "api",
) -> None:
    session_factory = get_async_session_maker()
    async with session_factory() as session:
        async with session.begin():
            booking_result = await session.execute(
                select(BookingTable)
                .where(BookingTable.id == booking_id)
                .with_for_update()
            )
            booking = booking_result.scalar_one_or_none()

            now = datetime.utcnow()
            if booking:
                booking.automation_status = (
                    result.automation_status if result else "failed"
                )
                booking.automation_run_at = now
                booking.decision_score = result.decision_score if result else 0
                booking.risk_level = result.risk_assessment if result else "unknown"
                session.add(booking)

            automation_query = select(AIAutomationTable).where(
                AIAutomationTable.booking_id == booking_id,
                AIAutomationTable.user_id == user_id,
            )
            if automation_id:
                automation_query = automation_query.where(
                    AIAutomationTable.id == automation_id
                )
            automation_query = automation_query.order_by(
                AIAutomationTable.created_at.desc()
            )
            automation_result = await session.execute(automation_query)
            automation_record = automation_result.scalars().first()

            actions = result.actions_executed if result else []
            agent_decisions = (
                result.agent_decisions if result else {"error": error or "unknown"}
            )
            fallback_mode = None
            if isinstance(agent_decisions, dict):
                fallback_mode = agent_decisions.get("mode")

            if automation_record is None:
                automation_record = AIAutomationTable(
                    id=automation_id or generate_uuid(),
                    booking_id=booking_id,
                    user_id=user_id,
                    status=result.automation_status if result else "failed",
                    decision_score=result.decision_score if result else 0,
                    risk_assessment=result.risk_assessment if result else "unknown",
                    agent_decisions=agent_decisions,
                    actions_executed=actions,
                    external_results=result.external_results if result else {},
                    execution_time_ms=result.execution_time_ms if result else 0,
                    started_at=now,
                    completed_at=now,
                    error_message=error,
                    fallback_mode=fallback_mode,
                    trigger_source=trigger_source,
                )
                session.add(automation_record)
            else:
                automation_record.status = (
                    result.automation_status if result else "failed"
                )
                automation_record.decision_score = (
                    result.decision_score if result else 0
                )
                automation_record.risk_assessment = (
                    result.risk_assessment if result else "unknown"
                )
                automation_record.agent_decisions = agent_decisions
                automation_record.actions_executed = actions
                automation_record.external_results = (
                    result.external_results if result else {}
                )
                automation_record.execution_time_ms = (
                    result.execution_time_ms if result else 0
                )
                automation_record.completed_at = now
                automation_record.error_message = error
                automation_record.fallback_mode = fallback_mode
                automation_record.trigger_source = trigger_source
                if automation_record.started_at is None:
                    automation_record.started_at = now

            await session.flush()


async def _update_automation_result(
    booking_id: str,
    result: AutomationResult,
    automation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trigger_source: str = "api",
) -> None:
    if user_id is None:
        return

    await _persist_automation_result(
        booking_id=booking_id,
        user_id=user_id,
        result=result,
        automation_id=automation_id,
        trigger_source=trigger_source,
    )


async def _update_automation_error(
    booking_id: str,
    error: str,
    automation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trigger_source: str = "api",
) -> None:
    if user_id is None:
        return

    await _persist_automation_result(
        booking_id=booking_id,
        user_id=user_id,
        automation_id=automation_id,
        error=error,
        trigger_source=trigger_source,
    )


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
    """,
)
async def create_booking(
    request: Request,
    booking_data: BookingCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
    idempotency_key: Optional[str] = Depends(idempotency_key_header),
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
        logger.info(
            f"📅 API: Creating booking '{booking_data.title}' for user {current_user.id}"
        )

        # Parse start_time and calculate end_time
        start_time = date_parser.parse(booking_data.start_time)
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        end_time = start_time + timedelta(minutes=booking_data.duration_minutes)

        # Get first attendee info for the booking record
        attendee_email = (
            booking_data.attendees[0] if booking_data.attendees else current_user.email
        )
        attendee_name = attendee_email.split("@")[
            0
        ]  # Use email prefix as name fallback

        # Create booking in database with proper persistence
        booking = BookingTable(
            id=generate_uuid(),
            user_id=booking_data.organizer_id or current_user.id,
            full_name=attendee_name,
            email=attendee_email,
            time_zone="UTC",  # Default, could be enhanced to detect from user prefs
            start_time=start_time,
            end_time=end_time,
            status="confirmed",
            is_reminder_sent=False,
            metadata_payload={
                "title": booking_data.title,
                "description": booking_data.description,
                "attendees": booking_data.attendees,
                "location": booking_data.location,
                "meeting_type": booking_data.meeting_type,
                "estimated_value": booking_data.estimated_value,
                "duration_minutes": booking_data.duration_minutes,
            },
        )

        # Check idempotency key for duplicate request prevention
        if idempotency_key:
            cached_response = await check_idempotency_key(
                db, idempotency_key, current_user.id, booking_data.model_dump()
            )
            if cached_response:
                logger.info(
                    f"🔄 Returning cached response for idempotency key: {idempotency_key[:16]}..."
                )
                return BookingCreateResponse(**cached_response)

        # Persist to database
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        automation_owner_id = booking.user_id

        automation_record = AIAutomationTable(
            booking_id=booking.id,
            user_id=automation_owner_id,
            status="in_progress",
            started_at=datetime.utcnow(),
            trigger_source="api",
        )
        db.add(automation_record)
        await db.commit()
        await db.refresh(automation_record)
        automation_id = automation_record.id

        logger.info(f"✅ API: Booking created with ID: {booking.id}")

        # Trigger AI automation asynchronously with fallback
        # This runs in the background and doesn't block the response
        async def run_automation():
            """Background task for automation with intelligent fallback"""
            try:
                from backend.ai.fallback import automate_booking_with_fallback
                from backend.services.booking_automation import AutomationResult
                from backend.services.workflow_engine import trigger_booking_workflows

                # Build attendee data from booking metadata
                attendee_data = None
                if booking.metadata_payload and booking.metadata_payload.get(
                    "attendees"
                ):
                    attendees = booking.metadata_payload["attendees"]
                    attendee_data = {
                        "email": attendees[0] if attendees else booking.email,
                        "name": booking.full_name,
                    }

                # Run with full fallback support:
                # Level 1: AI Agent → Level 2: Rule-based → Level 3: Manual review
                fallback_result = await automate_booking_with_fallback(
                    booking=booking, attendee=attendee_data
                )

                # Convert FallbackResult to AutomationResult for tracking
                from backend.services.booking_automation import AutomationResult

                result = AutomationResult(
                    booking_id=booking.id,
                    automation_status=fallback_result.status,
                    actions_executed=fallback_result.actions,
                    agent_decisions={"mode": fallback_result.mode.value},
                    external_results={},
                    risk_assessment="unknown",
                    decision_score=70
                    if fallback_result.mode.value == "rule_based"
                    else 85,
                    execution_time_ms=fallback_result.execution_time_ms,
                    timestamp=fallback_result.timestamp,
                )

                # Update tracking with result
                await _update_automation_result(
                    booking.id,
                    result,
                    automation_id=automation_id,
                    user_id=automation_owner_id,
                    trigger_source="api",
                )

                logger.info(
                    f"✅ Automation completed for {booking.id}: "
                    f"Mode={fallback_result.mode.value}, Status={fallback_result.status}"
                )
                
                # Trigger user-defined workflows (confirmation emails, slack, etc.)
                try:
                    await trigger_booking_workflows(
                        trigger_type="BOOKING_CREATED",
                        booking_id=booking.id,
                        user_id=automation_owner_id,
                        attendee_email=attendee_data.get("email") if attendee_data else booking.email,
                        attendee_name=attendee_data.get("name") if attendee_data else booking.full_name,
                        booking_title=booking_data.title,
                        booking_time=booking.start_time.isoformat(),
                        booking_id_str=booking.id,
                    )
                    logger.info(f"🔄 Workflows triggered for booking {booking.id}")
                except Exception as wf_error:
                    logger.error(f"Workflow trigger failed (non-blocking): {wf_error}")

            except Exception as e:
                logger.error(f"❌ Automation failed for {booking.id}: {e}")
                await _update_automation_error(
                    booking.id,
                    str(e),
                    automation_id=automation_id,
                    user_id=automation_owner_id,
                    trigger_source="api",
                )

        # Create background task
        task = asyncio.create_task(run_automation())

        # Track the automation
        automation_id = _track_automation_start(
            booking.id, task, automation_id=automation_id
        )

        logger.info(f"🤖 API: Automation triggered (ID: {automation_id})")

        # Return immediately - automation runs in background
        response_data = {
            "status": "created",
            "booking_id": booking.id,
            "automation": "in_progress",
            "message": "Booking created successfully. AI automation is running in the background.",
        }

        # Store idempotency key with response for future deduplication
        if idempotency_key:
            await store_idempotency_key(
                db,
                idempotency_key,
                current_user.id,
                booking_data.model_dump(),
                response_data,
                201,
            )

        return BookingCreateResponse(**response_data)

    except Exception as e:
        logger.error(f"❌ API: Failed to create booking: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create booking: {str(e)}"
        )


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
    """,
)
async def get_automation_status(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
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
                error=auto.get("error"),
            )

        # Check database for completed automations
        db_result = await db.execute(
            select(AIAutomationTable)
            .where(
                AIAutomationTable.booking_id == booking_id,
                AIAutomationTable.user_id == current_user.id,
            )
            .order_by(AIAutomationTable.created_at.desc())
        )
        automation_record = db_result.scalars().first()
        if automation_record:
            actions = automation_record.actions_executed or []
            return AutomationStatusResponse(
                booking_id=booking_id,
                status=automation_record.status,
                automation_id=automation_record.id,
                started_at=automation_record.started_at.isoformat()
                if automation_record.started_at
                else None,
                completed_at=automation_record.completed_at.isoformat()
                if automation_record.completed_at
                else None,
                decision_score=automation_record.decision_score,
                risk_assessment=automation_record.risk_assessment,
                actions_completed=sum(
                    1
                    for action in actions
                    if isinstance(action, dict) and action.get("success")
                ),
                actions_total=len(actions),
                current_action=None,
                error=automation_record.error_message,
            )

        # If not found, return not found
        raise HTTPException(
            status_code=404,
            detail=f"No automation found for booking {booking_id}. "
            f"The automation may not have started yet or the booking doesn't exist.",
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
    """,
)
async def get_automation_result(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
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
                    detail=f"Automation result not yet available for {booking_id}",
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
                        "task_id": a.get("task_id"),
                    }
                    for a in result.actions_executed
                ],
                external_ids=result.external_results,
            )

        db_result = await db.execute(
            select(AIAutomationTable)
            .where(
                AIAutomationTable.booking_id == booking_id,
                AIAutomationTable.user_id == current_user.id,
            )
            .order_by(AIAutomationTable.created_at.desc())
        )
        automation_record = db_result.scalars().first()

        if automation_record and automation_record.status in {"completed", "partial"}:
            actions = automation_record.actions_executed or []
            return AutomationResultResponse(
                booking_id=automation_record.booking_id,
                status=automation_record.status,
                decision_score=automation_record.decision_score or 0,
                risk_assessment=automation_record.risk_assessment or "unknown",
                execution_time_ms=automation_record.execution_time_ms or 0,
                timestamp=(
                    automation_record.completed_at or automation_record.created_at
                ).isoformat(),
                agent_decisions=automation_record.agent_decisions or {},
                actions_executed=actions,
                external_ids=automation_record.external_results or {},
            )

        raise HTTPException(
            status_code=404,
            detail=f"No automation result found for booking {booking_id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving automation result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{booking_id}/automation/stream")
async def stream_automation_status(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    Stream automation status updates using Server-Sent Events (SSE).

    This provides real-time updates instead of polling.
    Client connects and receives status updates as they happen.
    """

    async def event_generator():
        last_status = None
        max_attempts = 60  # 2 minutes max (2s intervals)
        attempts = 0

        while attempts < max_attempts:
            # Use a fresh DB session for each poll to avoid stale/closed connections
            session_factory = get_async_session_maker()
            async with session_factory() as session:
                db_result = await session.execute(
                    select(AIAutomationTable)
                    .where(
                        AIAutomationTable.booking_id == booking_id,
                        AIAutomationTable.user_id == current_user.id,
                    )
                    .order_by(AIAutomationTable.created_at.desc())
                )
                automation_record = db_result.scalars().first()

            if automation_record:
                current_status = {
                    "booking_id": automation_record.booking_id,
                    "status": automation_record.status,
                    "decision_score": automation_record.decision_score,
                    "risk_assessment": automation_record.risk_assessment,
                    "execution_time_ms": automation_record.execution_time_ms,
                    "timestamp": (
                        automation_record.completed_at or automation_record.created_at
                    ).isoformat()
                    if automation_record.completed_at or automation_record.created_at
                    else None,
                    "actions_executed": automation_record.actions_executed or [],
                }

                # Only send if status changed
                if current_status != last_status:
                    last_status = current_status
                    yield f"data: {json.dumps(current_status)}\n\n"

                # End stream if completed or failed
                if automation_record.status in {"completed", "failed", "partial"}:
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    break
            else:
                # No automation record yet
                yield f"data: {json.dumps({'status': 'pending', 'booking_id': booking_id})}\n\n"

            attempts += 1
            await asyncio.sleep(2)  # Poll every 2 seconds

        # Timeout reached
        if attempts >= max_attempts:
            yield f"data: {json.dumps({'error': 'Stream timeout', 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post(
    "/{booking_id}/automation/retry",
    response_model=BookingCreateResponse,
    summary="Retry failed automation",
    description="Retry automation for a booking that previously failed",
)
async def retry_automation(
    booking_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> BookingCreateResponse:
    """Retry automation for a failed booking.

    This endpoint is a placeholder. Implement retry logic as needed.
    """
    raise HTTPException(status_code=501, detail="Retry automation not implemented")


@router.get(
    "/automation/queue",
    summary="Get automation queue status",
    description="Get status of all running and pending automations",
)
async def get_automation_queue(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get automation queue status

    Args:
        current_user: Authenticated user

    Returns:
        Queue status with counts and details
    """
    try:
        db_result = await db.execute(
            select(AIAutomationTable)
            .where(AIAutomationTable.user_id == current_user.id)
            .order_by(AIAutomationTable.created_at.desc())
        )
        automations = db_result.scalars().all()

        running = sum(
            1 for automation in automations if automation.status == "in_progress"
        )
        completed = sum(
            1 for automation in automations if automation.status == "completed"
        )
        failed = sum(1 for automation in automations if automation.status == "failed")

        recent_tasks = [
            {
                "booking_id": automation.booking_id,
                "status": automation.status,
                "started_at": automation.started_at.isoformat()
                if automation.started_at
                else None,
                "automation_id": automation.id,
                "completed_at": automation.completed_at.isoformat()
                if automation.completed_at
                else None,
            }
            for automation in automations[:10]
        ]

        return {
            "total": len(automations),
            "running": running,
            "completed": completed,
            "failed": failed,
            "recent_tasks": recent_tasks,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# WEBHOOK ENDPOINT
# ═══════════════════════════════════════════════════════════════════

# Webhook secret - should be set via environment variable in production
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
AUTOMATION_WEBHOOK_SECRET = os.environ.get(
    "AUTOMATION_WEBHOOK_SECRET", "dev-webhook-secret-change-in-production"
)


@router.post(
    "/webhook/automation-complete",
    summary="Webhook for automation completion",
    description="Webhook called when automation completes (for external integrations). Requires X-Webhook-Secret header.",
)
async def automation_webhook(
    request: Request,
    booking_id: str,
    automation_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Webhook for automation completion

    Args:
        request: FastAPI request object (for header validation)
        booking_id: Booking ID
        automation_id: Automation ID
        status: Completion status
        result: Optional result data

    Returns:
        Acknowledgment
    """
    # Validate webhook secret from header
    webhook_secret = request.headers.get("X-Webhook-Secret")
    if not webhook_secret or webhook_secret != AUTOMATION_WEBHOOK_SECRET:
        logger.warning(
            f"❌ Unauthorized webhook attempt from {request.client.host if request.client else 'unknown'}"
        )
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing X-Webhook-Secret header",
        )

    logger.info(
        f"🔔 Webhook: Automation {automation_id} for {booking_id} completed: {status}"
    )

    db_result = await db.execute(
        select(AIAutomationTable).where(AIAutomationTable.id == automation_id)
    )
    automation_record = db_result.scalars().first()
    if automation_record is None:
        raise HTTPException(
            status_code=404, detail=f"Automation {automation_id} not found"
        )

    payload = result or {}
    automation_record.status = status
    automation_record.decision_score = payload.get(
        "decision_score", automation_record.decision_score
    )
    automation_record.risk_assessment = payload.get(
        "risk_assessment", automation_record.risk_assessment
    )
    automation_record.agent_decisions = payload.get(
        "agent_decisions", automation_record.agent_decisions
    )
    automation_record.actions_executed = payload.get(
        "actions_executed", automation_record.actions_executed
    )
    automation_record.external_results = payload.get(
        "external_results", automation_record.external_results
    )
    automation_record.execution_time_ms = payload.get(
        "execution_time_ms", automation_record.execution_time_ms
    )
    automation_record.completed_at = datetime.utcnow()
    automation_record.error_message = payload.get(
        "error", automation_record.error_message
    )
    automation_record.trigger_source = "webhook"

    booking_result = await db.execute(
        select(BookingTable).where(BookingTable.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()
    if booking:
        booking.automation_status = status
        booking.automation_run_at = automation_record.completed_at
        booking.decision_score = automation_record.decision_score
        booking.risk_level = automation_record.risk_assessment

    await db.commit()

    return {"status": "acknowledged"}
