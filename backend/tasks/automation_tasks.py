"""
Celery tasks for booking automation.
Replaces asyncio.create_task() for distributed, durable execution.
"""
from datetime import UTC
from typing import Any

from sqlalchemy import select

from backend.ai.fallback import automate_booking_with_fallback
from backend.core.celery_app import celery_app
from backend.models.tables import AIAutomationTable, BookingTable
from backend.services.workflow_engine import trigger_booking_workflows
from backend.utils.db import AsyncSessionLocal
from backend.utils.logger import get_logger

logger = get_logger(__name__)

@celery_app.task(name="backend.tasks.automation_tasks.run_booking_automation_task", bind=True)
def run_booking_automation_task(self, booking_id: str, automation_id: str, user_id: str, attendee_data: dict[str, Any] | None=None, booking_data: dict[str, Any] | None=None) -> dict[str, Any]:
    """
    Celery task to run booking automation with fallback support.

    This replaces asyncio.create_task() for distributed execution that
    survives worker restarts and provides retry capability.
    """
    import asyncio

    async def _execute():
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(BookingTable).where(BookingTable.id == booking_id)
                result = await db.execute(stmt)
                booking = result.scalar_one_or_none()
                if not booking:
                    logger.error("Booking %s not found for automation", booking_id)
                    return {"success": False, "error": "Booking not found"}
                fallback_result = await automate_booking_with_fallback(booking=booking, attendee=attendee_data)
                stmt = select(AIAutomationTable).where(AIAutomationTable.id == automation_id)
                result = await db.execute(stmt)
                auto_record = result.scalar_one_or_none()
                if auto_record:
                    auto_record.status = fallback_result.status
                    auto_record.completed_at = datetime.now(UTC)
                    auto_record.agent_decisions = {"mode": fallback_result.mode.value}
                    auto_record.actions_executed = fallback_result.actions
                    await db.commit()
                try:
                    await trigger_booking_workflows(trigger_type="BOOKING_CREATED", booking_id=booking.id, user_id=user_id, attendee_email=attendee_data.get("email") if attendee_data else booking.email, attendee_name=attendee_data.get("name") if attendee_data else booking.full_name, booking_title=booking_data.get("title") if booking_data else "Booking", booking_time=booking.start_time.isoformat())
                except Exception as wf_error:
                    logger.exception("Workflow trigger failed: %s", wf_error)
                logger.info("✅ Celery automation completed for %s: Mode=%s, Status=%s", booking_id, fallback_result.mode.value, fallback_result.status)
                return {"success": True, "booking_id": booking_id, "status": fallback_result.status, "mode": fallback_result.mode.value}
            except Exception as e:
                logger.exception("❌ Celery automation failed for %s: %s", booking_id, e)
                stmt = select(AIAutomationTable).where(AIAutomationTable.id == automation_id)
                result = await db.execute(stmt)
                auto_record = result.scalar_one_or_none()
                if auto_record:
                    auto_record.status = "failed"
                    auto_record.completed_at = datetime.now(UTC)
                    auto_record.error = str(e)
                    await db.commit()
                retry_count = self.request.retries
                if retry_count < 3:
                    logger.info("Retrying automation for %s (attempt %s)", booking_id, retry_count + 1)
                    raise self.retry(countdown=60 * (retry_count + 1), exc=e)
                return {"success": False, "error": str(e), "booking_id": booking_id}
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            loop.create_task(_execute())
            return {"success": True, "message": "Task scheduled in existing loop"}
    except RuntimeError:
        pass
    return asyncio.run(_execute())

@celery_app.task(name="backend.tasks.automation_tasks.log_agent_interaction_task")
def log_agent_interaction_task(request_data: dict[str, Any], response_data: dict[str, Any]) -> bool:
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
            await vector_store.add_document(collection="agent_interactions", document={**request_data, **response_data, "logged_at": datetime.now(UTC).isoformat()})
            logger.info("Interaction logged to vector store for request %s", request_data.get("id"))
            return True
        except Exception as e:
            logger.exception("Failed to log interaction to vector store: %s", e)
            return False
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            loop.create_task(_execute())
            return True
    except RuntimeError:
        pass
    return asyncio.run(_execute())
from datetime import datetime
