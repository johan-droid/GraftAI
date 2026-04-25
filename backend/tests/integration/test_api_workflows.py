"""
Integration tests for Workflow API endpoints.
Tests the complete flow from HTTP request to database persistence.
"""

import pytest
from datetime import datetime, timezone


@pytest.mark.integration
@pytest.mark.api
class TestWorkflowAPI:
    """Test workflow API endpoints."""

    @pytest.mark.asyncio
    async def test_list_triggers(self, async_client):
        """Test listing available workflow triggers."""
        response = await async_client.get("/api/v1/workflows/triggers")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of triggers
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check for known triggers
        trigger_values = [t["value"] for t in data]
        assert "BOOKING_CREATED" in trigger_values
        assert "BOOKING_CONFIRMED" in trigger_values
        assert "BOOKING_CANCELLED" in trigger_values

    @pytest.mark.asyncio
    async def test_list_actions(self, async_client):
        """Test listing available workflow actions."""
        response = await async_client.get("/api/v1/workflows/actions")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of actions
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check for known actions
        action_values = [a["value"] for a in data]
        assert "EMAIL" in action_values
        assert "SMS" in action_values
        assert "SLACK" in action_values
        assert "WEBHOOK" in action_values

    @pytest.mark.asyncio
    async def test_create_workflow(self, async_client):
        """Test creating a new workflow."""
        workflow_data = {
            "name": "Test Workflow",
            "description": "Test workflow for integration tests",
            "trigger": "BOOKING_CREATED",
            "is_active": True,
        }
        
        response = await async_client.post("/api/v1/workflows", json=workflow_data)
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        # Should return created workflow
        assert "id" in data
        assert data["name"] == workflow_data["name"]
        assert data["trigger"] == workflow_data["trigger"]

    @pytest.mark.asyncio
    async def test_list_workflows(self, async_client):
        """Test listing user's workflows."""
        # First create a workflow
        workflow_data = {
            "name": "List Test Workflow",
            "trigger": "BOOKING_CREATED",
            "is_active": True,
        }
        create_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        assert create_response.status_code in [200, 201]
        
        # Now list workflows
        response = await async_client.get("/api/v1/workflows")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_workflow(self, async_client):
        """Test getting a specific workflow."""
        # First create a workflow
        workflow_data = {
            "name": "Get Test Workflow",
            "trigger": "BOOKING_CREATED",
            "is_active": True,
        }
        create_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["id"]
        
        # Now get the workflow
        response = await async_client.get(f"/api/v1/workflows/{workflow_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == workflow_id
        assert data["name"] == workflow_data["name"]

    @pytest.mark.asyncio
    async def test_update_workflow(self, async_client):
        """Test updating a workflow."""
        # First create a workflow
        workflow_data = {
            "name": "Update Test Workflow",
            "trigger": "BOOKING_CREATED",
            "is_active": True,
        }
        create_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["id"]
        
        # Update the workflow
        update_data = {
            "name": "Updated Workflow Name",
            "is_active": False,
        }
        response = await async_client.patch(f"/api/v1/workflows/{workflow_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["is_active"] == update_data["is_active"]

    @pytest.mark.asyncio
    async def test_delete_workflow(self, async_client):
        """Test deleting a workflow."""
        # First create a workflow
        workflow_data = {
            "name": "Delete Test Workflow",
            "trigger": "BOOKING_CREATED",
            "is_active": True,
        }
        create_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["id"]
        
        # Delete the workflow
        response = await async_client.delete(f"/api/v1/workflows/{workflow_id}")
        
        assert response.status_code in [200, 204]
        
        # Verify it's deleted
        get_response = await async_client.get(f"/api/v1/workflows/{workflow_id}")
        assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.api
class TestWorkflowStepsAPI:
    """Test workflow steps API endpoints."""

    @pytest.fixture
    async def created_workflow(self, async_client):
        """Create a workflow and return its ID."""
        workflow_data = {
            "name": "Steps Test Workflow",
            "trigger": "BOOKING_CREATED",
            "is_active": True,
        }
        response = await async_client.post("/api/v1/workflows", json=workflow_data)
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_add_workflow_step(self, async_client, created_workflow):
        """Test adding a step to a workflow."""
        step_data = {
            "action_type": "EMAIL",
            "action_config": {
                "to": "{{attendee_email}}",
                "subject": "Booking Confirmation",
                "body": "Your booking is confirmed!",
            },
            "delay_minutes": 0,
            "step_number": 1,
        }
        
        response = await async_client.post(
            f"/api/v1/workflows/{created_workflow}/steps",
            json=step_data
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "id" in data
        assert data["action_type"] == step_data["action_type"]
        assert data["step_number"] == step_data["step_number"]

    @pytest.mark.asyncio
    async def test_list_workflow_steps(self, async_client, created_workflow):
        """Test listing steps of a workflow."""
        # First add a step
        step_data = {
            "action_type": "SLACK",
            "action_config": {"channel": "#bookings", "message": "New booking!"},
            "delay_minutes": 5,
            "step_number": 1,
        }
        await async_client.post(f"/api/v1/workflows/{created_workflow}/steps", json=step_data)
        
        # List steps
        response = await async_client.get(f"/api/v1/workflows/{created_workflow}/steps")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_delete_workflow_step(self, async_client, created_workflow):
        """Test deleting a workflow step."""
        # First add a step
        step_data = {
            "action_type": "SMS",
            "action_config": {"to": "{{attendee_phone}}", "body": "Reminder!"},
            "step_number": 1,
        }
        create_response = await async_client.post(
            f"/api/v1/workflows/{created_workflow}/steps",
            json=step_data
        )
        step_id = create_response.json()["id"]
        
        # Delete the step
        response = await async_client.delete(
            f"/api/v1/workflows/{created_workflow}/steps/{step_id}"
        )
        
        assert response.status_code in [200, 204]


@pytest.mark.integration
@pytest.mark.api
class TestWorkflowTestAPI:
    """Test workflow testing endpoint."""

    @pytest.fixture
    async def workflow_with_step(self, async_client):
        """Create a workflow with a step for testing."""
        # Create workflow
        workflow_data = {
            "name": "Test Workflow with Step",
            "trigger": "BOOKING_CREATED",
            "is_active": True,
        }
        wf_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = wf_response.json()["id"]
        
        # Add step
        step_data = {
            "action_type": "EMAIL",
            "action_config": {
                "to": "{{attendee_email}}",
                "subject": "Test",
                "body": "Test",
            },
            "delay_minutes": 0,
            "step_number": 1,
        }
        await async_client.post(f"/api/v1/workflows/{workflow_id}/steps", json=step_data)
        
        return workflow_id

    @pytest.mark.asyncio
    async def test_workflow_test_endpoint(self, async_client, workflow_with_step):
        """Test the workflow test endpoint."""
        response = await async_client.post(f"/api/v1/workflows/{workflow_with_step}/test")
        
        # Should return test results
        assert response.status_code in [200, 202]
        data = response.json()
        
        # Response structure may vary, but should indicate success
        assert "success" in data or "message" in data or "results" in data


@pytest.mark.integration
@pytest.mark.api
class TestWorkflowTriggerAPI:
    """Test workflow manual trigger endpoint."""

    @pytest.fixture
    async def active_workflow(self, async_client):
        """Create an active workflow with steps."""
        # Create workflow
        workflow_data = {
            "name": "Trigger Test Workflow",
            "trigger": "BOOKING_CREATED",
            "is_active": True,
        }
        wf_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = wf_response.json()["id"]
        
        # Add step
        step_data = {
            "action_type": "SLACK",
            "action_config": {"channel": "#test", "message": "Test"},
            "delay_minutes": 0,
            "step_number": 1,
        }
        await async_client.post(f"/api/v1/workflows/{workflow_id}/steps", json=step_data)
        
        return workflow_id

    @pytest.mark.asyncio
    async def test_manual_trigger_workflow(self, async_client, active_workflow):
        """Test manually triggering a workflow."""
        trigger_data = {
            "test_variables": {
                "attendee_email": "test@example.com",
                "attendee_name": "Test User",
                "booking_title": "Test Meeting",
                "booking_time": datetime.now(timezone.utc).isoformat(),
            }
        }
        
        response = await async_client.post(
            f"/api/v1/workflows/{active_workflow}/trigger",
            json=trigger_data
        )
        
        # Should accept the trigger request
        assert response.status_code in [200, 202]
        data = response.json()
        
        # Should indicate workflow was triggered
        assert "message" in data or "success" in data or "workflow_id" in data


@pytest.mark.integration
@pytest.mark.api
class TestWorkflowAuthorization:
    """Test workflow API authorization."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_users_workflow(
        self, async_client, async_client_for_other_user
    ):
        """Test that users cannot access other users' workflows."""

        workflow_data = {
            "name": "Auth Test Workflow",
            "trigger": "BOOKING_CREATED",
            "is_active": True,
        }
        response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = response.json()["id"]

        get_response = await async_client_for_other_user.get(
            f"/api/v1/workflows/{workflow_id}"
        )

        assert get_response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_unauthorized_access_returns_401(self, async_client_unauthenticated):
        """Test that unauthenticated requests return 401."""
        response = await async_client_unauthenticated.get("/api/v1/workflows")
        
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
