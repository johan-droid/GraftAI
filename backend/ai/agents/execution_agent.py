"""
Execution Agent - Executes actions with retry logic and failure handling
Handles actual operations like sending emails, creating calendar events, etc.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio
import re
import uuid
from sqlalchemy import inspect
from backend.ai.agents.base import BaseAgent, AgentContext
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ActionResult:
    """Result of executing an action"""

    success: bool
    action_type: str
    result: Any
    error: Optional[str] = None
    attempts: int = 1
    execution_time_ms: float = 0.0


class ExecutionAgent(BaseAgent):
    """
    Specialized agent for executing operations and handling failures

    Responsibilities:
    - Execute actions (send emails, create events, API calls)
    - Handle failures with retry logic
    - Manage rollback for failed operations
    - Track execution state
    - Ensure atomicity where possible
    """

    def __init__(self):
        super().__init__(
            name="ExecutionAgent",
            description="Executes actions with retry logic and failure handling",
        )

        # Action registry
        self.actions: Dict[str, Callable] = {}
        self._register_default_actions()

        # Execution history
        self.execution_history: List[Dict[str, Any]] = []

    def _get_available_tools(self) -> list:
        return [
            "execute_action",
            "batch_execute",
            "retry_failed",
            "rollback",
            "compensate",
        ]

    def _register_default_actions(self):
        """Register default action handlers"""
        self.register_action("send_email", self._action_send_email)
        self.register_action(
            "create_calendar_event", self._action_create_calendar_event
        )
        self.register_action("send_notification", self._action_send_notification)
        self.register_action("webhook_call", self._action_webhook_call)
        self.register_action("database_insert", self._action_database_insert)
        self.register_action("database_update", self._action_database_update)

    def register_action(self, action_type: str, handler: Callable):
        """Register a new action handler"""
        self.actions[action_type] = handler
        logger.info(f"Registered action handler: {action_type}")

    async def _execute(self, context: AgentContext) -> Dict[str, Any]:
        """
        Execute actions with retry and failure handling

        Args:
            context: Contains actions to execute (single or batch)

        Returns:
            Execution results with status for each action
        """
        data = context.data
        user_id = context.user_id

        # Determine execution mode
        if "actions" in data:
            # Batch execution
            return await self._execute_batch(data["actions"], user_id, context)
        else:
            # Single action
            action_type = data.get("action_type")
            action_params = data.get("params", {})

            result = await self._execute_single(
                action_type=action_type,
                params=action_params,
                user_id=user_id,
                max_retries=data.get("max_retries", 3),
                rollback_on_failure=data.get("rollback_on_failure", False),
            )

            return {
                "success": result.success,
                "action_type": result.action_type,
                "result": result.result,
                "error": result.error,
                "attempts": result.attempts,
                "execution_time_ms": result.execution_time_ms,
            }

    async def _execute_single(
        self,
        action_type: str,
        params: Dict[str, Any],
        user_id: str,
        max_retries: int = 3,
        rollback_on_failure: bool = False,
    ) -> ActionResult:
        """Execute a single action with retry logic"""
        start_time = datetime.utcnow()

        # Get action handler
        handler = self.actions.get(action_type)
        if not handler:
            return ActionResult(
                success=False,
                action_type=action_type,
                result=None,
                error=f"Unknown action type: {action_type}",
                execution_time_ms=0.0,
            )

        # Execute with retry
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"Executing {action_type} (attempt {attempt}/{max_retries})"
                )

                # Execute the action
                result = await handler(params, user_id)

                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Log success
                self._log_execution(
                    action_type=action_type,
                    success=True,
                    user_id=user_id,
                    execution_time_ms=execution_time,
                    attempt=attempt,
                )

                return ActionResult(
                    success=True,
                    action_type=action_type,
                    result=result,
                    attempts=attempt,
                    execution_time_ms=execution_time,
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(f"{action_type} attempt {attempt} failed: {e}")

                # Don't retry on certain errors
                if self._is_non_retryable_error(e):
                    break

                # Exponential backoff
                if attempt < max_retries:
                    wait_time = min(2**attempt, 30)  # Max 30 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

        # All retries failed
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        self._log_execution(
            action_type=action_type,
            success=False,
            user_id=user_id,
            execution_time_ms=execution_time,
            attempt=max_retries,
            error=last_error,
        )

        # Attempt rollback if requested
        if rollback_on_failure:
            await self._rollback_action(action_type, params, user_id)

        return ActionResult(
            success=False,
            action_type=action_type,
            result=None,
            error=last_error,
            attempts=max_retries,
            execution_time_ms=execution_time,
        )

    async def _execute_batch(
        self, actions: List[Dict[str, Any]], user_id: str, context: AgentContext
    ) -> Dict[str, Any]:
        """Execute multiple actions in batch with transaction-like behavior"""
        results = []
        completed_actions = []
        all_success = True

        # Execution strategy
        strategy = context.data.get("strategy", "sequential")  # sequential or parallel

        if strategy == "parallel":
            # Execute all in parallel
            tasks = [
                self._execute_single(
                    action["action_type"],
                    action.get("params", {}),
                    user_id,
                    action.get("max_retries", 3),
                    action.get("rollback_on_failure", False),
                )
                for action in actions
            ]

            action_results = await asyncio.gather(*tasks, return_exceptions=True)

            for action, result in zip(actions, action_results):
                if isinstance(result, Exception):
                    results.append(
                        {
                            "action_type": action["action_type"],
                            "success": False,
                            "error": str(result),
                        }
                    )
                    all_success = False
                    continue

                results.append(
                    {
                        "action_type": result.action_type,
                        "success": result.success,
                        "result": result.result,
                        "error": result.error,
                        "attempts": result.attempts,
                    }
                )

                if result.success:
                    completed_actions.append(
                        {
                            "action_type": action["action_type"],
                            "params": action.get("params", {}),
                            "result": result.result,
                        }
                    )
                else:
                    all_success = False

        else:
            # Execute sequentially
            for action in actions:
                result = await self._execute_single(
                    action["action_type"],
                    action.get("params", {}),
                    user_id,
                    action.get("max_retries", 3),
                    action.get("rollback_on_failure", False),
                )

                results.append(
                    {
                        "action_type": result.action_type,
                        "success": result.success,
                        "result": result.result,
                        "error": result.error,
                        "attempts": result.attempts,
                    }
                )

                if result.success:
                    completed_actions.append(
                        {
                            "action_type": action["action_type"],
                            "params": action.get("params", {}),
                            "result": result.result,
                        }
                    )
                else:
                    all_success = False

                    # Stop on first failure if transaction mode
                    if context.data.get("transactional", False):
                        logger.error("Transaction failed, initiating rollback")
                        await self._rollback_batch(completed_actions, user_id)
                        break

        return {
            "success": all_success,
            "strategy": strategy,
            "results": results,
            "completed_count": len(completed_actions),
            "failed_count": len(actions) - len(completed_actions),
        }

    def _is_non_retryable_error(self, error: Exception) -> bool:
        """Determine if an error should not be retried"""
        error_str = str(error).lower()

        non_retryable = [
            "authentication failed",
            "permission denied",
            "not found",
            "invalid parameter",
            "bad request",
            "validation failed",
        ]

        return any(keyword in error_str for keyword in non_retryable)

    async def _rollback_action(self, action_type: str, params: Dict, user_id: str):
        """Rollback a failed action"""
        logger.info(f"Rolling back action: {action_type}")

        # Implement rollback logic for each action type
        rollback_handlers = {
            "create_calendar_event": self._rollback_calendar_event,
            "database_insert": self._rollback_database_insert,
            "send_email": None,  # Can't unsend email
        }

        handler = rollback_handlers.get(action_type)
        if handler:
            try:
                await handler(params, user_id)
            except Exception as e:
                logger.error(f"Rollback failed for {action_type}: {e}")

    async def _rollback_batch(self, completed_actions: List[Dict], user_id: str):
        """Rollback a batch of completed actions"""
        logger.info(f"Rolling back {len(completed_actions)} actions")

        # Rollback in reverse order
        for action in reversed(completed_actions):
            await self._rollback_action(
                action["action_type"],
                {
                    **action.get("params", {}),
                    "_result": action.get("result", {}),
                },
                user_id,
            )

    def _log_execution(self, **kwargs):
        """Log execution details"""
        self.execution_history.append(
            {**kwargs, "timestamp": datetime.utcnow().isoformat()}
        )

        # Keep only last 1000 entries
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    # ===== Action Handlers =====

    async def _action_send_email(self, params: Dict, user_id: str) -> Dict:
        """Send email action"""
        from backend.tasks.email_tasks import send_email

        result = send_email.delay(
            to_email=params["to"],
            subject=params["subject"],
            body=params["body"],
            template=params.get("template"),
        )

        return {"task_id": result.id, "status": "queued"}

    async def _action_create_calendar_event(self, params: Dict, user_id: str) -> Dict:
        """Create calendar event action"""
        from backend.ai.tools.scheduling_tools_real import (
            create_calendar_event as create_calendar_event_real,
        )

        result = await create_calendar_event_real(
            title=params["title"],
            start_time=params["start_time"],
            duration_minutes=params.get("duration_minutes", 30),
            attendees=params.get("attendees", []),
            description=params.get("description"),
            location=params.get("location"),
            timezone=params.get("timezone", "UTC"),
            organizer_email=params.get("organizer_email") or params.get("user_email"),
            calendar_provider=params.get("calendar_provider", "google"),
        )

        if not result.get("success"):
            raise RuntimeError(result.get("error", "Calendar event creation failed"))

        return result

    async def _action_send_notification(self, params: Dict, user_id: str) -> Dict:
        """Send notification action"""
        # Could be push, SMS, in-app, etc.
        notification_type = params.get("type", "in_app")

        if notification_type == "push":
            logger.warning("Push notifications are not implemented")
            raise NotImplementedError("Push notifications are not implemented")
        elif notification_type == "sms":
            from backend.ai.tools.communication_tools import send_sms

            sms_result = await send_sms(to=params["to"], message=params["message"])
            if not sms_result.get("success"):
                raise RuntimeError(sms_result.get("error", "SMS delivery failed"))
            notification_id = sms_result.get("sms_id")
        else:
            logger.warning("In-app notifications are not implemented")
            raise NotImplementedError("In-app notifications are not implemented")

        return {"notification_id": notification_id, "type": notification_type}

    async def _action_webhook_call(self, params: Dict, user_id: str) -> Dict:
        """Make webhook call action"""
        from backend.tasks.webhook_tasks import deliver_webhook

        result = deliver_webhook.delay(
            webhook_id=params["webhook_id"],
            subscriber_url=params["url"],
            payload=params["payload"],
            secret=params.get("secret"),
        )

        return {"task_id": result.id, "status": "queued"}

    async def _action_database_insert(self, params: Dict, user_id: str) -> Dict:
        """Database insert action"""
        from sqlalchemy import text
        from backend.utils.db import get_async_session_maker

        table = params.get("table")
        values = dict(params.get("values") or {})

        if not table or not values:
            raise ValueError("database_insert requires table and values")

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
            raise ValueError("Invalid table name for database_insert")

        safe_columns = []
        for column in values.keys():
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(column)):
                raise ValueError(f"Invalid column name: {column}")
            safe_columns.append(column)

        if "id" not in values:
            try:
                inspect_session_maker = get_async_session_maker()
                async with inspect_session_maker() as inspect_session:
                    bind = inspect_session.get_bind()
                    sync_bind = getattr(bind, "sync_engine", bind)
                    inspector = inspect(sync_bind)
                    if table in inspector.get_table_names():
                        columns_info = {
                            c["name"]: c for c in inspector.get_columns(table)
                        }
                        id_column = columns_info.get("id")
                        if id_column and not id_column.get("autoincrement", False):
                            values["id"] = str(uuid.uuid4())
                            safe_columns.append("id")
            except Exception as exc:
                logger.warning(
                    "Unable to inspect database schema for table %s: %s", table, exc
                )

        if "id" in values and "id" not in safe_columns:
            safe_columns.append("id")

        placeholders = ", ".join(f":{col}" for col in safe_columns)
        columns_sql = ", ".join(f'"{col}"' for col in safe_columns)

        session_maker = get_async_session_maker()
        async with session_maker() as session:
            await session.execute(
                text(f'INSERT INTO "{table}" ({columns_sql}) VALUES ({placeholders})'),
                {k: values[k] for k in safe_columns},
            )
            await session.commit()

        return {"inserted_id": values["id"], "table": table}

    async def _action_database_update(self, params: Dict, user_id: str) -> Dict:
        """Database update action"""
        return {"updated_count": 1, "table": params.get("table")}

    # ===== Rollback Handlers =====

    async def _rollback_calendar_event(self, params: Dict, user_id: str):
        """Rollback calendar event creation"""
        result = params.get("_result") or {}
        event_id = (
            params.get("event_id")
            or params.get("created_event_id")
            or result.get("event_id")
        )
        if event_id:
            from backend.ai.tools.scheduling_tools_real import GoogleCalendarService

            organizer_email = (
                params.get("organizer_email")
                or params.get("user_email")
                or "default@graftai.com"
            )
            calendar = GoogleCalendarService()

            if not await calendar.authenticate(organizer_email):
                raise RuntimeError("Calendar rollback failed: authentication required")

            delete_result = await calendar.delete_event(event_id)
            if not delete_result.get("success"):
                raise RuntimeError(
                    delete_result.get("error", "Calendar event deletion failed")
                )

            logger.info(f"Deleted calendar event during rollback: {event_id}")

    async def _rollback_database_insert(self, params: Dict, user_id: str):
        """Rollback database insert"""
        from sqlalchemy import text
        from backend.utils.db import get_async_session_maker

        result = params.get("_result") or {}
        inserted_id = params.get("inserted_id") or result.get("inserted_id")
        table = params.get("table") or result.get("table")

        if not inserted_id or not table:
            return

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
            raise ValueError("Invalid table name for rollback")

        session_maker = get_async_session_maker()
        async with session_maker() as session:
            await session.execute(
                text(f'DELETE FROM "{table}" WHERE id = :id'),
                {"id": inserted_id},
            )
            await session.commit()

        logger.info(f"Deleted database record during rollback: {table}/{inserted_id}")
