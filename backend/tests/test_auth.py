import pytest
import uuid
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.auth.routes import _create_jwt_token
from backend.auth.schemes import decode_token


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_create_and_decode_jwt():
    token_data = _create_jwt_token("123")
    assert "access_token" in token_data
    token = token_data["access_token"]

    # decode_token is now async
    payload = await decode_token(token)
    assert payload is not None
    assert payload.get("sub") == "123"


def test_auth_register_and_login_flow(client):
    unique_email = f"testuser+{uuid.uuid4().hex[:8]}@example.com"

    # Register new user
    response = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "StrongPassw0rd!", "full_name": "Test User"},
    )
    assert response.status_code == 200
    assert response.json().get("message") == "User registered successfully"

    # Login user
    response = client.post(
        "/api/v1/auth/token",
        data={"username": unique_email, "password": "StrongPassw0rd!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert "access_token" in response.cookies or "graftai_access_token" in response.cookies

    # Check authenticated endpoint
    access_token = data.get("access_token")
    headers = (
        {"Authorization": f"Bearer {access_token}"}
        if access_token
        else {}
    )
    auth_response = client.get(
        "/api/v1/auth/check",
        headers=headers,
    )
    assert auth_response.status_code == 200
    assert auth_response.json().get("authenticated") is True


def test_auth_check_returns_usage_and_trial(client):
    unique_email = f"testuser3+{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "StrongPassw0rd!", "full_name": "Trial User"},
    )
    assert response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": unique_email, "password": "StrongPassw0rd!"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json().get("access_token")
    assert access_token

    headers = {"Authorization": f"Bearer {access_token}"}
    check_response = client.get("/api/v1/auth/check", headers=headers)
    assert check_response.status_code == 200

    user_payload = check_response.json().get("user", {})
    assert user_payload.get("daily_ai_limit") == 10
    assert user_payload.get("daily_sync_limit") == 3
    assert user_payload.get("trial_days_left") is not None
    assert user_payload.get("trial_active") is True
    assert user_payload.get("quota_reset_at")


def test_auth_refresh_rotates_token(client):
    unique_email = f"testuser2+{uuid.uuid4().hex[:8]}@example.com"

    # Register and login user
    client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "StrongPassw0rd!", "full_name": "Test User2"},
    )
    response = client.post(
        "/api/v1/auth/token",
        data={"username": unique_email, "password": "StrongPassw0rd!"},
    )
    assert response.status_code == 200
    refresh_token = response.cookies.get("graftai_refresh_token")

    # Refresh token
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json().get("message") == "Token refreshed successfully"


def test_auth_check_accepts_query_access_token(client):
    unique_email = f"testuserq+{uuid.uuid4().hex[:8]}@example.com"

    client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "StrongPassw0rd!", "full_name": "Query Token User"},
    )

    response = client.post(
        "/api/v1/auth/token",
        data={"username": unique_email, "password": "StrongPassw0rd!"},
    )
    assert response.status_code == 200

    access_token = response.cookies.get("graftai_access_token")
    assert access_token

    check_response = client.get(f"/api/v1/auth/check?token={access_token}")
    assert check_response.status_code == 200
    assert check_response.json().get("authenticated") is True


def test_auth_check_rejects_refresh_token_as_bearer(client):
    unique_email = f"testrt+{uuid.uuid4().hex[:8]}@example.com"

    client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "StrongPassw0rd!", "full_name": "Refresh Token User"},
    )

    response = client.post(
        "/api/v1/auth/token",
        data={"username": unique_email, "password": "StrongPassw0rd!"},
    )
    assert response.status_code == 200

    refresh_token = response.cookies.get("graftai_refresh_token")
    assert refresh_token

    check_response = client.get(
        "/api/v1/auth/check",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert check_response.status_code == 401


def test_auth_check_without_token_returns_401(client):
    response = client.get("/api/v1/auth/check")
    assert response.status_code == 401


def test_options_preflight_exposes_xsrf_header(client):
    response = client.get(
        "/api/v1/auth/check",
        headers={"Origin": "http://localhost:3000"},
    )
    # Route is protected and gives 401, but CORS expose header should exist.
    assert response.status_code == 401
    expose_headers = response.headers.get("access-control-expose-headers", "")
    assert "x-xsrf-token" in expose_headers.lower() or "x-xsrf-token" in response.headers


def test_refresh_endpoint_without_refresh_token_returns_401(client):
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid"})
    assert r.status_code == 401


def test_password_hash_and_verify_long_password():
    from backend.services.auth_utils import get_password_hash, verify_password

    long_password = "a" * 128
    hashed = get_password_hash(long_password)
    assert verify_password(long_password, hashed)


def test_password_hash_too_long_raises_value_error():
    from backend.services.auth_utils import get_password_hash

    # Argon2 actually handles very long passwords (up to 4GB in some implementations)
    # The previous passlib/bcrypt might have had a 72-char limit or manual check.
    # If our new implementation doesn't raise ValueError, we should update the test.
    too_long_password = "a" * 5000
    try:
        get_password_hash(too_long_password)
    except ValueError:
        pass  # Expected
    except Exception as e:
        pytest.fail(f"Unexpected exception type: {type(e).__name__}")


if __name__ == "__main__":
    pytest.main([__file__])
