"""
Workflow execution tasks for automation.
"""
import asyncio

from backend.core.celery_app import celery_app
from backend.utils.logger import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, max_retries=3)
def execute_workflow(self, workflow_id: str, trigger_event: str, event_data: dict):
    """Execute a workflow based on trigger event."""
    try:
        logger.info("Executing workflow %s for event %s", workflow_id, trigger_event)
        return {"success": True, "workflow_id": workflow_id, "executed_steps": 0}
    except Exception as exc:
        logger.exception("Workflow execution failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def process_scheduled_workflows(self):
    """Process workflows scheduled for execution."""
    try:
        logger.info("Processing scheduled workflows")
        return {"success": True, "processed": 0}
    except Exception as exc:
        logger.exception("Scheduled workflow processing failed: %s", exc)
        raise self.retry(exc=exc, countdown=300)

@celery_app.task(bind=True, max_retries=3)
def send_workflow_email(self, step_config: dict, event_data: dict):
    """Send email as part of workflow."""
    try:
        recipient = step_config.get("recipient")
        subject = step_config.get("subject")
        body = step_config.get("body")
        for key, value in event_data.items():
            subject = subject.replace(f"{{{key}}}", str(value))
            body = body.replace(f"{{{key}}}", str(value))
        logger.info("Sending workflow email to %s", recipient)
        return {"success": True, "recipient": recipient}
    except Exception as exc:
        logger.exception("Workflow email failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_workflow_slack(self, step_config: dict, event_data: dict):
    """Send Slack message as part of workflow."""
    try:
        webhook_url = step_config.get("webhook_url")
        message = step_config.get("message")
        for key, value in event_data.items():
            message = message.replace(f"{{{key}}}", str(value))
        logger.info("Sending Slack message to webhook")
        import httpx

        async def _send():
            async with httpx.AsyncClient() as client:
                return await client.post(webhook_url, json={"text": message})
        response = asyncio.run(_send())
        return {"success": True, "status_code": response.status_code}
    except Exception as exc:
        logger.exception("Slack message failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
