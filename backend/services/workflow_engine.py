"""
Workflow Engine - Fully Functional Automation System

Executes workflow steps based on booking triggers.
Supports: EMAIL, SMS, WEBHOOK, SLACK actions.
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.models.tables import (
    WorkflowTable, WorkflowStepTable
)
from backend.services.messaging import send_message
from backend.utils.logger import get_logger
from backend.utils.db import AsyncSessionLocal

logger = get_logger(__name__)


class WorkflowEngine:
    """Executes workflows with booking triggers."""
    
    # Trigger types
    TRIGGERS = {
        "BOOKING_CREATED": "When a new booking is created",
        "BOOKING_CONFIRMED": "When a booking is confirmed",
        "BOOKING_CANCELLED": "When a booking is cancelled",
        "BOOKING_RESCHEDULED": "When a booking is rescheduled",
        "BOOKING_REMINDER": "Before a booking starts",
        "BOOKING_FOLLOWUP": "After a booking ends",
    }
    
    # Action types
    ACTIONS = {
        "EMAIL": "Send Email",
        "SMS": "Send SMS",
        "WEBHOOK": "Send Webhook",
        "SLACK": "Send Slack Message",
        "TEAMS": "Send Teams Message",
        "CALENDAR": "Add to Calendar",
    }
    
    async def trigger_workflows(
        self,
        trigger_type: str,
        booking_id: str,
        user_id: str,
        event_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Trigger all active workflows for a booking event.
        
        Args:
            trigger_type: Type of trigger (BOOKING_CREATED, etc.)
            booking_id: The booking that triggered the workflow
            user_id: User who owns the booking
            event_data: Data about the event
            
        Returns:
            List of execution results
        """
        async with AsyncSessionLocal() as db:
            # Find active workflows for this user/trigger
            stmt = select(WorkflowTable).where(
                and_(
                    WorkflowTable.user_id == user_id,
                    WorkflowTable.trigger == trigger_type,
                    WorkflowTable.is_active == True,
                )
            )
            result = await db.execute(stmt)
            workflows = result.scalars().all()
            
            if not workflows:
                logger.debug(f"No workflows found for trigger {trigger_type}")
                return []
            
            logger.info(f"Found {len(workflows)} workflows for trigger {trigger_type}")
            
            results = []
            for workflow in workflows:
                try:
                    result = await self.execute_workflow(
                        db, workflow, booking_id, event_data
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Workflow {workflow.id} execution failed: {e}")
                    results.append({
                        "workflow_id": workflow.id,
                        "success": False,
                        "error": str(e),
                    })
            
            return results
    
    async def execute_workflow(
        self,
        db: AsyncSession,
        workflow: WorkflowTable,
        booking_id: str,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single workflow's steps."""
        logger.info(f"Executing workflow {workflow.id}: {workflow.name}")
        
        # Load steps
        stmt = select(WorkflowStepTable).where(
            WorkflowStepTable.workflow_id == workflow.id,
            WorkflowStepTable.is_active == True,
        ).order_by(WorkflowStepTable.step_number)
        
        result = await db.execute(stmt)
        steps = result.scalars().all()
        
        executed_steps = []
        
        for step in steps:
            try:
                # Handle delay
                if step.delay_minutes > 0:
                    logger.info(f"Delaying step {step.id} for {step.delay_minutes} minutes")
                    await asyncio.sleep(step.delay_minutes * 60)
                
                result = await self.execute_step(step, event_data)
                executed_steps.append({
                    "step_id": step.id,
                    "action": step.action_type,
                    "success": True,
                    "result": result,
                })
                
            except Exception as e:
                logger.error(f"Step {step.id} failed: {e}")
                executed_steps.append({
                    "step_id": step.id,
                    "action": step.action_type,
                    "success": False,
                    "error": str(e),
                })
        
        return {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "booking_id": booking_id,
            "success": all(s["success"] for s in executed_steps),
            "steps_executed": len(executed_steps),
            "steps": executed_steps,
        }
    
    async def execute_step(
        self,
        step: WorkflowStepTable,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        action_type = step.action_type
        config = step.action_config
        
        # Replace template variables in config
        config = self._replace_template_vars(config, event_data)
        
        if action_type == "EMAIL":
            return await self._send_email(config, event_data)
        elif action_type == "SMS":
            return await self._send_sms(config, event_data)
        elif action_type == "WEBHOOK":
            return await self._send_webhook(config, event_data)
        elif action_type == "SLACK":
            return await self._send_slack(config, event_data)
        elif action_type == "TEAMS":
            return await self._send_teams(config, event_data)
        elif action_type == "CALENDAR":
            return await self._add_to_calendar(config, event_data)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _replace_template_vars(
        self,
        config: Dict[str, Any],
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Replace {{variable}} templates with actual values."""
        result = {}
        for key, value in config.items():
            if isinstance(value, str):
                for var_key, var_value in event_data.items():
                    placeholder = f"{{{{{var_key}}}}}"
                    if placeholder in value:
                        value = value.replace(placeholder, str(var_value))
                result[key] = value
            else:
                result[key] = value
        return result
    
    async def _send_email(
        self,
        config: Dict[str, Any],
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send email action."""
        recipient = config.get("recipient", event_data.get("attendee_email"))
        subject = config.get("subject", "Booking Notification")
        body = config.get("body", "Your booking has been updated.")
        
        if not recipient:
            raise ValueError("No recipient specified for email")
        
        # Send via messaging service
        await send_message(
            to=recipient,
            subject=subject,
            body=body,
            message_type="email",
        )
        
        logger.info(f"Email sent to {recipient}")
        return {"recipient": recipient, "subject": subject}
    
    async def _send_sms(
        self,
        config: Dict[str, Any],
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send SMS action."""
        phone = config.get("phone", event_data.get("attendee_phone"))
        message = config.get("message", "Your booking has been updated.")
        
        if not phone:
            raise ValueError("No phone number specified for SMS")
        
        # Send via messaging service (implement SMS provider)
        await send_message(
            to=phone,
            body=message,
            message_type="sms",
        )
        
        logger.info(f"SMS sent to {phone}")
        return {"phone": phone, "message": message}
    
    async def _send_webhook(
        self,
        config: Dict[str, Any],
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send webhook action."""
        import httpx
        
        url = config.get("url")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        
        if not url:
            raise ValueError("No webhook URL specified")
        
        payload = {
            "event": event_data.get("trigger_type"),
            "booking_id": event_data.get("booking_id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": event_data,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={**headers, "Content-Type": "application/json"},
            )
            response.raise_for_status()
        
        logger.info(f"Webhook sent to {url}")
        return {"url": url, "status_code": response.status_code}
    
    async def _send_slack(
        self,
        config: Dict[str, Any],
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send Slack message action."""
        import httpx
        
        webhook_url = config.get("webhook_url")
        message = config.get("message", "Booking notification")
        
        if not webhook_url:
            raise ValueError("No Slack webhook URL specified")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json={"text": message},
                timeout=30.0,
            )
            response.raise_for_status()
        
        logger.info("Slack message sent")
        return {"webhook": webhook_url[:50]}  # Truncate for logging
    
    async def _send_teams(
        self,
        config: Dict[str, Any],
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send Teams message action."""
        import httpx
        
        webhook_url = config.get("webhook_url")
        message = config.get("message", "Booking notification")
        
        if not webhook_url:
            raise ValueError("No Teams webhook URL specified")
        
        # Microsoft Teams adaptive card format
        card = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": "Booking Notification",
            "sections": [{
                "activityTitle": "Booking Notification",
                "activitySubtitle": event_data.get("booking_title", ""),
                "facts": [
                    {"name": "Attendee:", "value": event_data.get("attendee_email", "")},
                    {"name": "Time:", "value": event_data.get("booking_time", "")},
                ],
                "text": message,
            }],
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=card,
                timeout=30.0,
            )
            response.raise_for_status()
        
        logger.info("Teams message sent")
        return {"webhook": webhook_url[:50]}
    
    async def _add_to_calendar(
        self,
        config: Dict[str, Any],
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Add to calendar action."""
        # This would integrate with calendar APIs
        logger.info("Calendar action placeholder - integrate with calendar API")
        return {"action": "calendar_add", "status": "placeholder"}


# Global engine instance
_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get or create workflow engine."""
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine


# Convenience function for booking triggers
async def trigger_booking_workflows(
    trigger_type: str,
    booking_id: str,
    user_id: str,
    **event_data,
) -> List[Dict[str, Any]]:
    """
    Trigger workflows for a booking event.
    
    Usage:
        await trigger_booking_workflows(
            "BOOKING_CREATED",
            booking_id="abc123",
            user_id="user456",
            attendee_email="john@example.com",
            booking_title="Team Meeting",
            booking_time="2024-01-15 14:00",
        )
    """
    engine = get_workflow_engine()
    return await engine.trigger_workflows(
        trigger_type=trigger_type,
        booking_id=booking_id,
        user_id=user_id,
        event_data=event_data,
    )
