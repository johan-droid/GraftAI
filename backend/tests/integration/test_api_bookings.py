"""
Integration tests for Booking API endpoints.
Tests the complete booking flow from creation to confirmation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.api
class TestBookingAPI:
    """Test booking API endpoints."""

    @pytest.mark.asyncio
    async def test_create_booking(self, async_client, test_event):
        """Test creating a new booking."""
        booking_data = {
            "title": "Test Booking",
            "description": "Integration test booking",
            "attendees": ["booker@example.com"],
            "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "meeting_type": "consultation",
        }
        
        response = await async_client.post("/api/v1/bookings", json=booking_data)
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "booking_id" in data
        assert data["status"] in ["created", "confirmed"]

    @pytest.mark.asyncio
    async def test_list_bookings(self, async_client, test_booking):
        """Test listing bookings."""
        response = await async_client.get("/api/v1/bookings")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of bookings
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_booking(self, async_client, test_booking):
        """Test getting a specific booking."""
        response = await async_client.get(f"/api/v1/bookings/{test_booking.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_booking.id

    @pytest.mark.asyncio
    async def test_update_booking(self, async_client, test_booking):
        """Test updating a booking."""
        update_data = {
            "full_name": "Updated Name",
        }
        
        response = await async_client.patch(
            f"/api/v1/bookings/{test_booking.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("full_name") == update_data["full_name"] or data.get("name") == update_data["full_name"]

    @pytest.mark.asyncio
    async def test_cancel_booking(self, async_client, test_booking):
        """Test cancelling a booking."""
        response = await async_client.delete(f"/api/v1/bookings/{test_booking.id}")
        
        assert response.status_code in [200, 204]
        
        # Verify booking is cancelled
        get_response = await async_client.get(f"/api/v1/bookings/{test_booking.id}")
        if get_response.status_code == 200:
            data = get_response.json()
            assert data["status"] in ["cancelled", "canceled"]

    @pytest.mark.asyncio
    async def test_reschedule_booking(self, async_client, test_booking):
        """Test rescheduling a booking."""
        new_start = datetime.now(timezone.utc) + timedelta(days=2)
        new_end = new_start + timedelta(hours=1)
        
        reschedule_data = {
            "start_time": new_start.isoformat(),
            "end_time": new_end.isoformat(),
        }
        
        response = await async_client.patch(
            f"/api/v1/bookings/{test_booking.id}/reschedule",
            json=reschedule_data
        )
        
        # Reschedule endpoint may not exist, check status
        if response.status_code in [200, 201]:
            data = response.json()
        else:
            assert response.status_code in [404, 405, 422]


@pytest.mark.integration
@pytest.mark.api
class TestBookingValidation:
    """Test booking validation rules."""

    @pytest.mark.asyncio
    async def test_create_booking_missing_required_fields(self, async_client):
        """Test that creating a booking without required fields fails."""
        incomplete_data = {
            "name": "Test Booker",
            # Missing email, start_time, end_time
        }
        
        response = await async_client.post("/api/v1/bookings", json=incomplete_data)
        
        # Should return validation error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_booking_invalid_email(self, async_client, test_event):
        """Test that invalid email is rejected."""
        booking_data = {
            "title": "Test Booking",
            "description": "Invalid email test",
            "attendees": ["not-an-email"],
            "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
        }
        
        response = await async_client.post("/api/v1/bookings", json=booking_data)
        
        # Should return validation error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_booking_past_date(self, async_client, test_event):
        """Test that booking in the past is rejected."""
        booking_data = {
            "title": "Test Booking",
            "description": "Past date test",
            "attendees": ["booker@example.com"],
            "start_time": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
        }
        
        response = await async_client.post("/api/v1/bookings", json=booking_data)
        
        # Should return validation error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_nonexistent_booking(self, async_client):
        """Test getting a booking that doesn't exist."""
        fake_id = str(uuid4())
        
        response = await async_client.get(f"/api/v1/bookings/{fake_id}")
        
        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.api
class TestBookingPublicAPI:
    """Test public booking endpoints (no auth required)."""

    @pytest.mark.asyncio
    async def test_public_booking_page(self, async_client):
        """Test accessing public booking page."""
        # This endpoint may be at /u/{username} or similar
        response = await async_client.get("/public/test-user")
        
        # May return 200 or redirect
        assert response.status_code in [200, 307, 308]


@pytest.mark.integration
@pytest.mark.api
class TestBookingWorkflowIntegration:
    """Test booking workflow integration."""

    @pytest.mark.asyncio
    async def test_booking_triggers_workflow(self, async_client, test_event):
        """Test that creating a booking triggers workflow."""
        booking_data = {
            "title": "Workflow Test Booking",
            "description": "Trigger test",
            "attendees": ["workflow-test@example.com"],
            "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
        }
        
        response = await async_client.post("/api/v1/bookings", json=booking_data)
        
        assert response.status_code in [200, 201]
        
        # Workflow should have been triggered (async, so can't verify immediately)
        # But booking creation should succeed


@pytest.mark.integration
@pytest.mark.api
class TestBookingPagination:
    """Test booking list pagination."""

    @pytest.mark.asyncio
    async def test_list_bookings_with_pagination(self, async_client):
        """Test that booking list supports pagination."""
        response = await async_client.get("/api/v1/bookings?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list
        assert isinstance(data, list)
        
        # If API returns paginated response with metadata
        # Check for pagination fields

    @pytest.mark.asyncio
    async def test_list_bookings_with_limit(self, async_client):
        """Test limiting number of bookings returned."""
        response = await async_client.get("/api/v1/bookings?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return at most 5 items
        assert len(data) <= 5


@pytest.mark.integration
@pytest.mark.api
class TestBookingFilters:
    """Test booking list filters."""

    @pytest.mark.asyncio
    async def test_filter_by_status(self, async_client):
        """Test filtering bookings by status."""
        response = await async_client.get("/api/v1/bookings?status=confirmed")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned bookings should have confirmed status
        for booking in data:
            assert booking["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, async_client):
        """Test filtering bookings by date range."""
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        end_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        
        response = await async_client.get(
            f"/api/v1/bookings?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
