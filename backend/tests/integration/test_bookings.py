"""
Core Booking Engine Integration Test

This is the "Canary in the Coal Mine." If this fails, the app is broken.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_booking_flow(client: AsyncClient, db_session):
    """
    Ensures the core booking endpoint returns the correct status and 
    triggers the AI automation without crashing.
    """
    # 1. Define the payload
    payload = {
        "event_type_id": "test-event-123",
        "attendee_name": "Jane Doe",
        "attendee_email": "jane@example.com",
        "start_time": "2026-04-22T14:00:00+00:00",
        "notes": "Looking forward to chatting about AI!"
    }

    # 2. Hit the endpoint
    response = await client.post("/api/v1/bookings", json=payload)

    # 3. Assertions
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
    data = response.json()
    assert "id" in data or "booking_id" in data, "Response should contain booking ID"
    assert data.get("attendee_email") == "jane@example.com", "Attendee email should match"
    
    # Ensure the AI pipeline picked it up (status should be pending or completed)
    automation_status = data.get("automation_status") or data.get("status")
    assert automation_status in ["pending", "completed", "in_progress"], \
        f"Expected valid automation status, got {automation_status}"
