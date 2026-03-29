from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from backend.api.main import app
from backend.auth.routes import _create_jwt_token


from backend.utils.tenant import get_current_org_id, get_current_workspace_id

import pytest

@pytest.mark.asyncio
async def test_send_notification_route(monkeypatch):
    fake_send = AsyncMock()
    monkeypatch.setattr("backend.api.notifications.send_custom_notification", fake_send)

    token_data = await _create_jwt_token("1", email="user@example.com")
    authorization_header = {"Authorization": f"Bearer {token_data['access_token']}"}

    app.dependency_overrides[get_current_org_id] = lambda: 1
    app.dependency_overrides[get_current_workspace_id] = lambda: 1

    client = TestClient(app)
    payload = {
        "to_email": "user@example.com",
        "subject": "Test Notification",
        "message": "This is a test notification from GraftAI.",
    }

    response = client.post(
        "/api/v1/notifications/test",
        json=payload,
        headers=authorization_header,
    )

    assert response.status_code == 202
    assert response.json().get("status") == "queued"
    fake_send.assert_awaited_once()
