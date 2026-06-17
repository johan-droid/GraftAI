import json
import os

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.auth.config import SECRET_KEY
from backend.services.auth_service import create_access_token, create_refresh_token, decode_jwt_token


client = TestClient(app)


def test_jwks_rotate_and_fetch():
    os.environ["ADMIN_API_KEY"] = "test-admin-key-123"
    headers = {"X-ADMIN-API-KEY": "test-admin-key-123"}
    resp = client.post("/api/v1/auth/jwks/rotate", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "kid" in data
    kid = data["kid"]

    resp = client.get("/api/v1/auth/jwks")
    assert resp.status_code == 200
    ks = resp.json().get("keys", [])
    assert any(k.get("kid") == kid for k in ks)


def test_token_create_and_decode_roundtrip():
    import asyncio

    user_id = "test-user-123"
    access = asyncio.get_event_loop().run_until_complete(create_access_token(user_id))
    refresh = asyncio.get_event_loop().run_until_complete(create_refresh_token(user_id))
    # decode and validate payloads
    payload = asyncio.get_event_loop().run_until_complete(decode_jwt_token(access, expected_type="access"))
    assert payload["sub"] == user_id
    payload2 = asyncio.get_event_loop().run_until_complete(decode_jwt_token(refresh, expected_type="refresh"))
    assert payload2["sub"] == user_id
