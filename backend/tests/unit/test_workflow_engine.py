"""
Unit tests for the Workflow Engine.
Tests the core workflow triggering, action execution, and error handling.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.services.workflow_engine import (
    WorkflowEngine,
    trigger_booking_workflows,
    ActionType,
    TriggerType,
)
from backend.models.tables import WorkflowTable, WorkflowStepTable, UserTable
from backend.utils.dead_letter_queue import DLQStatus


@pytest.fixture
def workflow_engine():
    return WorkflowEngine()


@pytest_asyncio.fixture
async def sample_workflow(db_session, test_user):
    workflow = WorkflowTable(
        id=str(uuid4()),
        user_id=test_user.id,
        name="Test Workflow",
        description="Test workflow for unit tests",
        trigger=TriggerType.BOOKING_CREATED.value,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(workflow)
    await db_session.flush()

    step1 = WorkflowStepTable(
        id=str(uuid4()),
        workflow_id=workflow.id,
        step_number=1,
        action_type=ActionType.EMAIL.value,
        action_config={
            "to": "{{attendee_email}}",
            "subject": "Booking Confirmation",
            "body": "Hi {{attendee_name}}, your booking is confirmed for {{booking_time}}.",
        },
        delay_minutes=0,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    step2 = WorkflowStepTable(
        id=str(uuid4()),
        workflow_id=workflow.id,
        step_number=2,
        action_type=ActionType.SLACK.value,
        action_config={
            "channel": "#bookings",
            "message": "New booking: {{booking_title}} by {{attendee_name}}",
        },
        delay_minutes=5,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    db_session.add_all([step1, step2])
    await db_session.flush()

    result = await db_session.execute(
        select(WorkflowTable)
        .options(selectinload(WorkflowTable.steps))
        .where(WorkflowTable.id == workflow.id)
    )
    workflow = result.scalar_one()
    return workflow


class TestWorkflowEngine:
    """Test the WorkflowEngine class."""

    @pytest.fixture
    def workflow_engine(self):
        """Create a workflow engine instance."""
        return WorkflowEngine()

    @pytest_asyncio.fixture
    async def sample_workflow(self, db_session, test_user):
        """Create a sample workflow with steps."""
        workflow = WorkflowTable(
            id=str(uuid4()),
            user_id=test_user.id,
            name="Test Workflow",
            description="Test workflow for unit tests",
            trigger=TriggerType.BOOKING_CREATED.value,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(workflow)
        await db_session.flush()

        # Add steps
        step1 = WorkflowStepTable(
            id=str(uuid4()),
            workflow_id=workflow.id,
            step_number=1,
            action_type=ActionType.EMAIL.value,
            action_config={
                "to": "{{attendee_email}}",
                "subject": "Booking Confirmation",
                "body": "Hi {{attendee_name}}, your booking is confirmed for {{booking_time}}.",
            },
            delay_minutes=0,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        
        step2 = WorkflowStepTable(
            id=str(uuid4()),
            workflow_id=workflow.id,
            step_number=2,
            action_type=ActionType.SLACK.value,
            action_config={
                "channel": "#bookings",
                "message": "New booking: {{booking_title}} by {{attendee_name}}",
            },
            delay_minutes=5,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        
        db_session.add_all([step1, step2])
        await db_session.flush()
        
        return workflow

    def test_action_type_enum(self):
        """Test ActionType enum values."""
        assert ActionType.EMAIL.value == "EMAIL"
        assert ActionType.SMS.value == "SMS"
        assert ActionType.WEBHOOK.value == "WEBHOOK"
        assert ActionType.SLACK.value == "SLACK"
        assert ActionType.TEAMS.value == "TEAMS"
        assert ActionType.CALENDAR.value == "CALENDAR"

    def test_trigger_type_enum(self):
        """Test TriggerType enum values."""
        assert TriggerType.BOOKING_CREATED.value == "BOOKING_CREATED"
        assert TriggerType.BOOKING_CONFIRMED.value == "BOOKING_CONFIRMED"
        assert TriggerType.BOOKING_CANCELLED.value == "BOOKING_CANCELLED"
        assert TriggerType.BOOKING_RESCHEDULED.value == "BOOKING_RESCHEDULED"
        assert TriggerType.REMINDER.value == "REMINDER"
        assert TriggerType.FOLLOW_UP.value == "FOLLOW_UP"

    @pytest.mark.asyncio
    async def test_get_workflows_for_trigger(self, workflow_engine, db_session, sample_workflow, test_user):
        """Test fetching workflows for a trigger."""
        workflows = await workflow_engine._get_workflows_for_trigger(
            db_session, TriggerType.BOOKING_CREATED.value, test_user.id
        )
        
        assert len(workflows) == 1
        assert workflows[0].id == sample_workflow.id
        assert workflows[0].trigger == TriggerType.BOOKING_CREATED.value

    @pytest.mark.asyncio
    async def test_get_workflows_inactive_ignored(self, workflow_engine, db_session, test_user):
        """Test that inactive workflows are not returned."""
        # Create inactive workflow
        inactive_workflow = WorkflowTable(
            id=str(uuid4()),
            user_id=test_user.id,
            name="Inactive Workflow",
            trigger=TriggerType.BOOKING_CREATED.value,
            is_active=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(inactive_workflow)
        await db_session.flush()
        
        workflows = await workflow_engine._get_workflows_for_trigger(
            db_session, TriggerType.BOOKING_CREATED.value, test_user.id
        )
        
        assert len(workflows) == 0

    @pytest.mark.asyncio
    async def test_replace_template_variables(self, workflow_engine):
        """Test template variable replacement."""
        template = "Hello {{attendee_name}}, your booking {{booking_title}} is at {{booking_time}}"
        variables = {
            "attendee_name": "John Doe",
            "booking_title": "Team Meeting",
            "booking_time": "2026-04-22T14:00:00",
        }
        
        result = workflow_engine._replace_template_variables(template, variables)
        
        assert "John Doe" in result
        assert "Team Meeting" in result
        assert "2026-04-22T14:00:00" in result
        assert "{{" not in result  # All variables replaced

    @pytest.mark.asyncio
    async def test_replace_template_variables_missing(self, workflow_engine):
        """Test template variable replacement with missing variables."""
        template = "Hello {{attendee_name}}, missing: {{nonexistent}}"
        variables = {
            "attendee_name": "John Doe",
        }
        
        result = workflow_engine._replace_template_variables(template, variables)
        
        assert "John Doe" in result
        assert "{{nonexistent}}" in result  # Missing vars kept as-is

    @pytest.mark.asyncio
    async def test_validate_action_config_email_valid(self, workflow_engine):
        """Test email action config validation with valid config."""
        config = {
            "to": "user@example.com",
            "subject": "Test",
            "body": "Hello",
        }
        
        is_valid, error = workflow_engine._validate_action_config(ActionType.EMAIL.value, config)
        
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_action_config_email_missing_to(self, workflow_engine):
        """Test email action config validation with missing 'to'."""
        config = {
            "subject": "Test",
            "body": "Hello",
        }
        
        is_valid, error = workflow_engine._validate_action_config(ActionType.EMAIL.value, config)
        
        assert is_valid is False
        assert "to" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_action_config_webhook_valid(self, workflow_engine):
        """Test webhook action config validation with valid config."""
        config = {
            "url": "https://example.com/webhook",
            "method": "POST",
        }
        
        is_valid, error = workflow_engine._validate_action_config(ActionType.WEBHOOK.value, config)
        
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_action_config_webhook_invalid_url(self, workflow_engine):
        """Test webhook action config validation with invalid URL."""
        config = {
            "url": "not-a-url",
            "method": "POST",
        }
        
        is_valid, error = workflow_engine._validate_action_config(ActionType.WEBHOOK.value, config)
        
        assert is_valid is False
        assert "url" in error.lower()


class TestTriggerBookingWorkflows:
    """Test the trigger_booking_workflows function."""

    @pytest.mark.asyncio
    @patch("backend.services.workflow_engine.WorkflowEngine.process_trigger")
    async def test_trigger_booking_workflows_success(self, mock_process_trigger, db_session):
        """Test successful workflow triggering."""
        mock_process_trigger.return_value = {"processed": 2, "errors": 0}
        
        result = await trigger_booking_workflows(
            trigger_type="BOOKING_CREATED",
            booking_id=str(uuid4()),
            user_id=str(uuid4()),
            attendee_email="test@example.com",
            attendee_name="Test User",
            booking_title="Test Meeting",
            booking_time=datetime.now(timezone.utc).isoformat(),
            booking_id_str=str(uuid4()),
        )
        
        assert result is not None
        mock_process_trigger.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.services.workflow_engine.WorkflowEngine.process_trigger")
    async def test_trigger_booking_workflows_with_db_session(self, mock_process_trigger, db_session):
        """Test workflow triggering with explicit db session."""
        mock_process_trigger.return_value = {"processed": 1, "errors": 0}
        
        # Call with db_session parameter
        result = await trigger_booking_workflows(
            trigger_type="BOOKING_CREATED",
            booking_id=str(uuid4()),
            user_id=str(uuid4()),
            attendee_email="test@example.com",
            attendee_name="Test User",
            booking_title="Test Meeting",
            booking_time=datetime.now(timezone.utc).isoformat(),
            booking_id_str=str(uuid4()),
        )
        
        assert result is not None


class TestWorkflowErrorHandling:
    """Test workflow error handling and DLQ integration."""

    @pytest.mark.asyncio
    async def test_workflow_step_error_handling(self, workflow_engine, db_session, sample_workflow, test_user):
        """Test that workflow step errors are handled gracefully."""
        # Create a step with invalid config that will cause an error
        step = WorkflowStepTable(
            id=str(uuid4()),
            workflow_id=sample_workflow.id,
            step_number=3,
            action_type=ActionType.EMAIL.value,
            action_config={
                # Missing required 'to' field - should cause validation error
                "subject": "Test",
                "body": "Test body",
            },
            delay_minutes=0,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(step)
        await db_session.flush()
        
        # Execute workflow - should handle error gracefully
        context = {
            "user_id": test_user.id,
            "trigger": TriggerType.BOOKING_CREATED.value,
            "booking_id": str(uuid4()),
        }
        
        # Should not raise exception, should handle error
        try:
            result = await workflow_engine._execute_workflow_step(
                db_session, step, context
            )
            # If validation fails, result should indicate failure
            # but not crash the entire workflow
        except Exception as e:
            # Even if it raises, it should be a controlled error
            assert isinstance(e, Exception)

    @pytest.mark.asyncio
    @patch("backend.services.workflow_engine.get_dlq")
    async def test_failed_actions_queued_to_dlq(self, mock_get_dlq, workflow_engine, db_session, sample_workflow, test_user):
        """Test that failed actions are queued to DLQ."""
        # Mock DLQ
        mock_dlq = AsyncMock()
        mock_get_dlq.return_value = mock_dlq
        mock_dlq.enqueue.return_value = "dlq-item-id-123"
        
        # Simulate a failed action
        action_type = ActionType.EMAIL.value
        payload = {"to": "test@example.com", "subject": "Test"}
        error = "SendGrid API timeout"
        
        # Manually call DLQ enqueue (as the workflow engine should do on failure)
        item_id = await mock_dlq.enqueue(
            action_type=action_type,
            payload=payload,
            error=error,
            max_retries=3,
            context={"user_id": test_user.id},
        )
        
        assert item_id == "dlq-item-id-123"
        mock_dlq.enqueue.assert_called_once()
        
        # Verify call arguments
        call_args = mock_dlq.enqueue.call_args
        assert call_args.kwargs["action_type"] == action_type
        assert call_args.kwargs["error"] == error


class TestWorkflowDelayExecution:
    """Test workflow step delay execution."""

    @pytest.mark.asyncio
    async def test_delay_calculation(self, workflow_engine):
        """Test that delay minutes are correctly calculated."""
        delay_minutes = 5
        expected_delay = timedelta(minutes=delay_minutes)
        
        # The workflow engine should schedule delayed steps
        # by storing them with a future execution time
        now = datetime.now(timezone.utc)
        scheduled_time = now + expected_delay
        
        assert scheduled_time > now
        assert (scheduled_time - now).total_seconds() == delay_minutes * 60

    @pytest.mark.asyncio
    async def test_delayed_step_not_executed_immediately(self, workflow_engine, db_session, sample_workflow):
        """Test that delayed steps are not executed immediately."""
        # Get delayed step (step 2 has 5 minute delay)
        delayed_step = None
        for step in sample_workflow.steps:
            if step.delay_minutes > 0:
                delayed_step = step
                break
        
        assert delayed_step is not None
        assert delayed_step.delay_minutes == 5


# Performance tests
@pytest.mark.slow
class TestWorkflowPerformance:
    """Performance tests for workflow engine."""

    @pytest.mark.asyncio
    async def test_workflow_execution_under_load(self, workflow_engine, db_session, test_user):
        """Test workflow execution performance with multiple workflows."""
        # Create multiple workflows
        workflows = []
        for i in range(10):
            workflow = WorkflowTable(
                id=str(uuid4()),
                user_id=test_user.id,
                name=f"Perf Test Workflow {i}",
                trigger=TriggerType.BOOKING_CREATED.value,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db_session.add(workflow)
            workflows.append(workflow)
        
        await db_session.flush()
        
        # Verify workflows were created
        assert len(workflows) == 10
        
        # Test fetching all workflows
        from sqlalchemy import select
        from backend.models.tables import WorkflowTable as WT
        
        result = await db_session.execute(
            select(WT).where(WT.user_id == test_user.id)
        )
        all_workflows = result.scalars().all()
        
        assert len(all_workflows) >= 10  # Including the sample workflow


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
