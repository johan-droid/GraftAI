"""
Core Booking Engine Integration Test

This is the "Canary in the Coal Mine." If this fails, the app is broken.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_create_booking_flow(async_client: AsyncClient, db_session):
    """
    Ensures the core booking endpoint returns the correct status and 
    triggers the AI automation without crashing.
    """
    # 1. Define the payload matching BookingCreateRequest
    payload = {
        "title": "Jane Doe - Quarterly Sync",
        "description": "Discuss roadmap and action items.",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "duration_minutes": 30,
        "attendees": ["jane@example.com"],
        "meeting_type": "consultation",
        "location": "Zoom"
    }

    # 2. Hit the endpoint
    response = await async_client.post("/api/v1/bookings", json=payload)

    # 3. Assertions
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
    data = response.json()
    assert "booking_id" in data, "Response should contain booking_id"
    assert data["status"] == "created", "Status should be 'created'"
    
    # Ensure the AI pipeline picked it up
    assert data.get("automation") == "in_progress", \
        f"Expected automation in_progress, got {data.get('automation')}"
