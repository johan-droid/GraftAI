"""
Integration tests for Workflow API endpoints.
Tests the complete flow from HTTP request to database persistence.
"""
from datetime import UTC, datetime

import pytest
import pytest_asyncio


@pytest.mark.integration
@pytest.mark.api
class TestWorkflowAPI:
    """Test workflow API endpoints."""

    @pytest.mark.asyncio
    async def test_list_triggers(self, async_client):
        """Test listing available workflow triggers."""
        response = await async_client.get("/api/v1/workflows/triggers")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0
        trigger_values = [t["value"] for t in data]
        assert "BOOKING_CREATED" in trigger_values
        assert "BOOKING_CONFIRMED" in trigger_values
        assert "BOOKING_CANCELLED" in trigger_values

    @pytest.mark.asyncio
    async def test_list_actions(self, async_client):
        """Test listing available workflow actions."""
        response = await async_client.get("/api/v1/workflows/actions")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0
        action_values = [a["value"] for a in data]
        assert "EMAIL" in action_values
        assert "SMS" in action_values
        assert "SLACK" in action_values
        assert "WEBHOOK" in action_values

    @pytest.mark.asyncio
    async def test_create_workflow(self, async_client):
        """Test creating a new workflow."""
        workflow_data = {"name": "Test Workflow", "description": "Test workflow for integration tests", "trigger": "BOOKING_CREATED", "is_active": True}
        response = await async_client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code in [200, 201]
        data = response.json()["data"]
        assert "id" in data
        assert data["name"] == workflow_data["name"]
        assert data["trigger"] == workflow_data["trigger"]

    @pytest.mark.asyncio
    async def test_list_workflows(self, async_client):
        """Test listing user's workflows."""
        workflow_data = {"name": "List Test Workflow", "trigger": "BOOKING_CREATED", "is_active": True}
        create_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        assert create_response.status_code in [200, 201]
        response = await async_client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_workflow(self, async_client):
        """Test getting a specific workflow."""
        workflow_data = {"name": "Get Test Workflow", "trigger": "BOOKING_CREATED", "is_active": True}
        create_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["data"]["id"]
        response = await async_client.get(f"/api/v1/workflows/{workflow_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == workflow_id
        assert data["name"] == workflow_data["name"]

    @pytest.mark.asyncio
    async def test_update_workflow(self, async_client):
        """Test updating a workflow."""
        workflow_data = {"name": "Update Test Workflow", "trigger": "BOOKING_CREATED", "is_active": True}
        create_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["data"]["id"]
        update_data = {"name": "Updated Workflow Name", "is_active": False}
        response = await async_client.patch(f"/api/v1/workflows/{workflow_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == update_data["name"]
        assert data["is_active"] == update_data["is_active"]

    @pytest.mark.asyncio
    async def test_delete_workflow(self, async_client):
        """Test deleting a workflow."""
        workflow_data = {"name": "Delete Test Workflow", "trigger": "BOOKING_CREATED", "is_active": True}
        create_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["data"]["id"]
        response = await async_client.delete(f"/api/v1/workflows/{workflow_id}")
        assert response.status_code in [200, 204]
        get_response = await async_client.get(f"/api/v1/workflows/{workflow_id}")
        assert get_response.status_code == 404

@pytest.mark.integration
@pytest.mark.api
class TestWorkflowStepsAPI:
    """Test workflow steps API endpoints."""

    @pytest_asyncio.fixture
    async def created_workflow(self, async_client):
        """Create a workflow and return its ID."""
        workflow_data = {"name": "Steps Test Workflow", "trigger": "BOOKING_CREATED", "is_active": True}
        response = await async_client.post("/api/v1/workflows", json=workflow_data)
        return response.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_add_workflow_step(self, async_client, created_workflow):
        """Test adding a step to a workflow."""
        step_data = {"action_type": "EMAIL", "action_config": {"to": "{{attendee_email}}", "subject": "Booking Confirmation", "body": "Your booking is confirmed!"}, "delay_minutes": 0, "step_number": 1}
        response = await async_client.post(f"/api/v1/workflows/{created_workflow}/steps", json=step_data)
        assert response.status_code in [200, 201]
        data = response.json()["data"]
        assert "id" in data
        assert data["action_type"] == step_data["action_type"]
        assert data["step_number"] == step_data["step_number"]

    @pytest.mark.asyncio
    async def test_list_workflow_steps(self, async_client, created_workflow):
        """Test listing steps of a workflow."""
        step_data = {"action_type": "SLACK", "action_config": {"channel": "#bookings", "message": "New booking!"}, "delay_minutes": 5, "step_number": 1}
        await async_client.post(f"/api/v1/workflows/{created_workflow}/steps", json=step_data)
        response = await async_client.get(f"/api/v1/workflows/{created_workflow}/steps")
        assert response.status_code == 200
        data = response.json()
        steps = data.get("data", [])
        assert isinstance(steps, list)
        assert len(steps) >= 1

    @pytest.mark.asyncio
    async def test_delete_workflow_step(self, async_client, created_workflow):
        """Test deleting a workflow step."""
        step_data = {"action_type": "SMS", "action_config": {"to": "{{attendee_phone}}", "body": "Reminder!"}, "step_number": 1}
        create_response = await async_client.post(f"/api/v1/workflows/{created_workflow}/steps", json=step_data)
        step_id = create_response.json()["data"]["id"]
        response = await async_client.delete(f"/api/v1/workflows/{created_workflow}/steps/{step_id}")
        assert response.status_code in [200, 204]

@pytest.mark.integration
@pytest.mark.api
class TestWorkflowTestAPI:
    """Test workflow testing endpoint."""

    @pytest_asyncio.fixture
    async def workflow_with_step(self, async_client):
        """Create a workflow with a step for testing."""
        workflow_data = {"name": "Test Workflow with Step", "trigger": "BOOKING_CREATED", "is_active": True}
        wf_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = wf_response.json()["data"]["id"]
        step_data = {"action_type": "EMAIL", "action_config": {"to": "{{attendee_email}}", "subject": "Test", "body": "Test"}, "delay_minutes": 0, "step_number": 1}
        await async_client.post(f"/api/v1/workflows/{workflow_id}/steps", json=step_data)
        return workflow_id

    @pytest.mark.asyncio
    async def test_workflow_test_endpoint(self, async_client, workflow_with_step):
        """Test the workflow test endpoint."""
        response = await async_client.post(f"/api/v1/workflows/{workflow_with_step}/test", json={})
        assert response.status_code in [200, 202]
        data = response.json()["data"]
        assert "success" in data or "message" in data or "results" in data

@pytest.mark.integration
@pytest.mark.api
class TestWorkflowTriggerAPI:
    """Test workflow manual trigger endpoint."""

    @pytest_asyncio.fixture
    async def active_workflow(self, async_client):
        """Create an active workflow with steps."""
        workflow_data = {"name": "Trigger Test Workflow", "trigger": "BOOKING_CREATED", "is_active": True}
        wf_response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = wf_response.json()["data"]["id"]
        step_data = {"action_type": "SLACK", "action_config": {"channel": "#test", "message": "Test"}, "delay_minutes": 0, "step_number": 1}
        await async_client.post(f"/api/v1/workflows/{workflow_id}/steps", json=step_data)
        return workflow_id

    @pytest.mark.asyncio
    async def test_manual_trigger_workflow(self, async_client, active_workflow):
        """Test manually triggering a workflow."""
        trigger_data = {"test_variables": {"attendee_email": "test@example.com", "attendee_name": "Test User", "booking_title": "Test Meeting", "booking_time": datetime.now(UTC).isoformat()}}
        response = await async_client.post(f"/api/v1/workflows/{active_workflow}/trigger", json=trigger_data)
        assert response.status_code in [200, 202]
        data = response.json()
        assert "message" in data or "success" in data or "workflow_id" in data

@pytest.mark.integration
@pytest.mark.api
class TestWorkflowAuthorization:
    """Test workflow API authorization."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_users_workflow(self, async_client, async_client_for_other_user):
        """Test that users cannot access other users' workflows."""
        workflow_data = {"name": "Auth Test Workflow", "trigger": "BOOKING_CREATED", "is_active": True}
        response = await async_client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = response.json()["data"]["id"]
        get_response = await async_client_for_other_user.get(f"/api/v1/workflows/{workflow_id}")
        assert get_response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_unauthorized_access_returns_401(self, async_client_unauthenticated):
        """Test that unauthenticated requests return 401."""
        response = await async_client_unauthenticated.get("/api/v1/workflows")
        assert response.status_code == 401
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
