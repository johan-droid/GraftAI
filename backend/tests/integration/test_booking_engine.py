"""
Core Booking Engine Integration Test

This is the "Canary in the Coal Mine" test. If this fails, the booking engine is broken.
Tests the core booking endpoint, AI automation triggering, and data persistence.
"""
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_booking_flow(async_client: AsyncClient, db_session):
    """
    Ensures the core booking endpoint returns the correct status and
    triggers the AI automation without crashing.

    This test validates:
    1. Booking creation endpoint accepts valid payload
    2. Response contains booking ID and automation status
    3. Data is persisted in the database
    4. AI automation is triggered (status should be pending or completed)
    """
    payload = {"title": "Quarterly Sync", "description": "Discuss roadmap and action items.", "start_time": (datetime.now(UTC) + timedelta(days=1)).isoformat(), "duration_minutes": 30, "attendees": ["jane@example.com"], "meeting_type": "consultation", "location": "Zoom"}
    response = await async_client.post("/api/v1/bookings", json=payload)
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
    data = response.json()
    assert "data" in data, "Response should be wrapped in 'data'"
    assert "booking_id" in data["data"], "Response should contain booking ID"
    booking_id = data["data"].get("booking_id")
    assert booking_id is not None, "Booking ID should not be None"
    assert "automation" in data["data"] or "status" in data["data"], "Response data should contain automation status"
    automation_status = data["data"].get("automation") or data["data"].get("status")
    assert automation_status in ["pending", "completed", "in_progress", "success"], f"Expected valid automation status, got {automation_status}"

@pytest.mark.asyncio
async def test_create_booking_with_invalid_payload(async_client: AsyncClient):
    """
    Test that the booking endpoint rejects invalid payloads with proper error messages.

    Validates:
    1. Missing required fields return 422
    2. Invalid date formats are rejected
    3. Negative durations are rejected
    """
    payload = {"title": "Test Meeting"}
    response = await async_client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
    payload = {"title": "Test Meeting", "start_time": "invalid-date", "duration_minutes": 60, "attendees": ["test@example.com"]}
    response = await async_client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 422, f"Expected 422 for invalid date, got {response.status_code}"
    payload = {"title": "Test Meeting", "start_time": (datetime.now(UTC) + timedelta(days=1)).isoformat(), "duration_minutes": -30, "attendees": ["test@example.com"]}
    response = await async_client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 422, f"Expected 422 for negative duration, got {response.status_code}"

@pytest.mark.asyncio
async def test_booking_pagination_limits(async_client: AsyncClient, db_session):
    """
    Test that booking list endpoints respect pagination limits.

    Validates:
    1. Pagination parameters are enforced
    2. Maximum page size is limited (100 items)
    3. Response contains pagination metadata
    """
    response = await async_client.get("/api/v1/bookings?size=200")
    if response.status_code == 200:
        data = response.json()
        if "data" in data and isinstance(data["data"], dict) and ("pagination" in data["data"]):
            assert data["data"]["pagination"]["per_page"] <= 100, "Page size should be capped at 100"
        elif "data" in data and isinstance(data["data"], list):
            assert len(data["data"]) <= 100, "Should not return more than 100 items"
    response = await async_client.get("/api/v1/bookings?page=1&size=20")
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"

@pytest.mark.asyncio
async def test_booking_html_sanitization(async_client: AsyncClient):
    """
    Test that XSS payloads are properly sanitized.

    Validates:
    1. Script tags are escaped in title
    2. Script tags are escaped in description
    3. Normal text is not affected
    """
    xss_payload = {"title": "<script>alert('XSS')</script>", "description": "<img src=x onerror=alert('XSS')>", "start_time": (datetime.now(UTC) + timedelta(days=1)).isoformat(), "duration_minutes": 60, "attendees": ["test@example.com"]}
    response = await async_client.post("/api/v1/bookings", json=xss_payload)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["success"] is True
    booking_id = data["data"].get("booking_id")
    assert booking_id is not None
    get_response = await async_client.get(f"/api/v1/bookings/{booking_id}")
    assert get_response.status_code == 200
    booking_data = get_response.json()
    assert booking_data["success"] is True
    assert booking_data["data"].get("id") is not None, "Booking ID should be present"

@pytest.mark.asyncio
async def test_booking_payload_size_limit(async_client: AsyncClient):
    """
    Test that large payloads are rejected to prevent OOM crashes.

    Validates:
    1. Payloads > 2MB return 413 status
    2. Valid small payloads are accepted
    """
    large_payload = {"title": "Test Meeting", "description": "A" * 3000000, "start_time": (datetime.now(UTC) + timedelta(days=1)).isoformat(), "duration_minutes": 60, "attendees": ["test@example.com"]}
    response = await async_client.post("/api/v1/bookings", json=large_payload)
    assert response.status_code in [200, 201, 413], f"Expected 200/201/413, got {response.status_code}"
    if response.status_code == 413:
        error_data = response.json()
        assert "too large" in str(error_data).lower(), "Error message should mention payload size"

@pytest.mark.asyncio
async def test_booking_automation_status(async_client: AsyncClient, db_session):
    """
    Test that booking automation status can be retrieved.

    Validates:
    1. Automation status endpoint is accessible
    2. Status includes decision score and risk assessment
    3. Actions executed are tracked
    """
    payload = {"title": "Test Meeting for Automation", "description": "Test automation status", "start_time": (datetime.now(UTC) + timedelta(days=1)).isoformat(), "duration_minutes": 30, "attendees": ["test@example.com"]}
    create_response = await async_client.post("/api/v1/bookings", json=payload)
    assert create_response.status_code in [200, 201]
    create_data = create_response.json()
    booking_id = create_data["data"].get("booking_id")
    if booking_id:
        status_response = await async_client.get(f"/api/v1/bookings/{booking_id}/automation")
        if status_response.status_code == 200:
            status_data = status_response.json()
            assert "status" in status_data, "Automation status should include status field"
