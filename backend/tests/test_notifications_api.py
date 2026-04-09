import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock

from backend.api.main import app
from backend.auth.schemes import get_current_user_id


@pytest.mark.asyncio
async def test_send_notification_route(monkeypatch):
    fake_send = AsyncMock()
    monkeypatch.setattr("backend.api.notifications.send_custom_notification", fake_send)

    app.dependency_overrides[get_current_user_id] = lambda: "1"

    payload = {
        "to_email": "user@example.com",
        "subject": "Test Notification",
        "message": "This is a test notification from GraftAI.",
    }

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/notifications/test",
                json=payload,
            )
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)

    assert response.status_code == 202
    assert response.json().get("status") == "queued"
    fake_send.assert_awaited_once()
