import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.auth.routes import _create_jwt_token
from backend.auth.schemes import decode_token

client = TestClient(app)


def test_create_and_decode_jwt():
    token_data = _create_jwt_token("123")
    assert "access_token" in token_data
    token = token_data["access_token"]

    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == "123"


def test_sso_callback_browser_redirects_to_frontend():
    response = client.get(
        "/auth/sso/callback?code=test_code&state=test_state",
        headers={"Accept": "*/*"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "auth-callback" in response.headers["location"]


def test_sso_callback_json_invalid_state_returns_400():
    response = client.get(
        "/auth/sso/callback?code=test_code&state=test_state",
        headers={"Accept": "application/json"},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "Invalid or expired state" in response.json().get("detail")


def test_auth_check_without_token_returns_401():
    response = client.get("/auth/check")
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__])
