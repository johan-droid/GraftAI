"""
Celery tasks for booking automation.
Replaces asyncio.create_task() for distributed, durable execution.
"""
from typing import Dict, Any, Optional
from backend.core.celery_app import celery_app
from backend.utils.logger import get_logger
from backend.utils.db import AsyncSessionLocal
from backend.models.tables import BookingTable, AIAutomationTable
from backend.ai.fallback import automate_booking_with_fallback
from backend.services.workflow_engine import trigger_booking_workflows
from sqlalchemy import select

logger = get_logger(__name__)


@celery_app.task(name="backend.tasks.automation_tasks.run_booking_automation_task", bind=True)
def run_booking_automation_task(
    self,
    booking_id: str,
    automation_id: str,
    user_id: str,
    attendee_data: Optional[Dict[str, Any]] = None,
    booking_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Celery task to run booking automation with fallback support.
    
    This replaces asyncio.create_task() for distributed execution that
    survives worker restarts and provides retry capability.
    """
    import asyncio
    
    async def _execute():
        async with AsyncSessionLocal() as db:
            try:
                # Load booking
                stmt = select(BookingTable).where(BookingTable.id == booking_id)
                result = await db.execute(stmt)
                booking = result.scalar_one_or_none()
                
                if not booking:
                    logger.error(f"Booking {booking_id} not found for automation")
                    return {"success": False, "error": "Booking not found"}
                
                # Run automation with fallback
                fallback_result = await automate_booking_with_fallback(
                    booking=booking,
                    attendee=attendee_data
                )
                
                # Update automation record
                stmt = select(AIAutomationTable).where(AIAutomationTable.id == automation_id)
                result = await db.execute(stmt)
                auto_record = result.scalar_one_or_none()
                
                if auto_record:
                    auto_record.status = fallback_result.status
                    auto_record.completed_at = datetime.now(timezone.utc)
                    auto_record.agent_decisions = {"mode": fallback_result.mode.value}
                    auto_record.actions_executed = fallback_result.actions
                    await db.commit()
                
                # Trigger workflows
                try:
                    await trigger_booking_workflows(
                        trigger_type="BOOKING_CREATED",
                        booking_id=booking.id,
                        user_id=user_id,
                        attendee_email=attendee_data.get("email") if attendee_data else booking.email,
                        attendee_name=attendee_data.get("name") if attendee_data else booking.full_name,
                        booking_title=booking_data.get("title") if booking_data else "Booking",
                        booking_time=booking.start_time.isoformat(),
                    )
                except Exception as wf_error:
                    logger.error(f"Workflow trigger failed: {wf_error}")
                
                logger.info(
                    f"✅ Celery automation completed for {booking_id}: "
                    f"Mode={fallback_result.mode.value}, Status={fallback_result.status}"
                )
                
                return {
                    "success": True,
                    "booking_id": booking_id,
                    "status": fallback_result.status,
                    "mode": fallback_result.mode.value,
                }
                
            except Exception as e:
                logger.error(f"❌ Celery automation failed for {booking_id}: {e}")
                
                # Update automation record with error
                stmt = select(AIAutomationTable).where(AIAutomationTable.id == automation_id)
                result = await db.execute(stmt)
                auto_record = result.scalar_one_or_none()
                
                if auto_record:
                    auto_record.status = "failed"
                    auto_record.completed_at = datetime.now(timezone.utc)
                    auto_record.error = str(e)
                    await db.commit()
                
                # Retry with exponential backoff
                retry_count = self.request.retries
                if retry_count < 3:
                    logger.info(f"Retrying automation for {booking_id} (attempt {retry_count + 1})")
                    raise self.retry(countdown=60 * (retry_count + 1), exc=e)
                
                return {"success": False, "error": str(e), "booking_id": booking_id}
    
    return asyncio.run(_execute())


@celery_app.task(name="backend.tasks.automation_tasks.log_agent_interaction_task")
def log_agent_interaction_task(
    request_data: Dict[str, Any],
    response_data: Dict[str, Any]
) -> bool:
    """
    Celery task to log agent interactions to the vector store.
    This ensures that logging doesn't block the AI orchestrator
    and is persistent even if the API worker restarts.
    """
    import asyncio
    from backend.ai.memory.vector_store import VectorStore
    
    async def _execute():
        try:
            vector_store = VectorStore()
            await vector_store.add_document(
                collection="agent_interactions",
                document={
                    **request_data,
                    **response_data,
                    "logged_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            logger.info(f"Interaction logged to vector store for request {request_data.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to log interaction to vector store: {e}")
            return False
            
    return asyncio.run(_execute())


# Import datetime here to avoid circular import issues
from datetime import datetime, timezone
