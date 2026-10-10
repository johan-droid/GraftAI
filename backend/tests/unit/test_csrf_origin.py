"""
Unit tests for origin-based CSRF protection.

Auth cookies are SameSite=None, so any cross-site page can make the browser
attach them. These tests pin the one thing an attacker cannot forge: Origin.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from backend.utils.csrf import CSRFMiddleware

SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]


def build_client(allowed_origins=None, allowed_origin_regex=None, exempt_paths=()):
    app = FastAPI()
    app.add_middleware(
        CSRFMiddleware,
        allowed_origins=allowed_origins or [],
        allowed_origin_regex=allowed_origin_regex,
        exempt_paths=exempt_paths,
    )

    @app.post("/api/v1/bookings")
    async def create():
        return {"ok": True}

    @app.post("/api/v1/webhooks/stripe")
    async def webhook():
        return {"ok": True}

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("method", SAFE_METHODS)
def test_safe_methods_skip_origin_check(method: str):
    client = build_client(allowed_origins=["https://graftai.tech"])
    response = client.request(
        method, "/api/v1/bookings", headers={"origin": "https://evil.com"}
    )
    assert response.status_code in (200, 405)


def test_trusted_origin_allowed():
    client = build_client(allowed_origins=["https://graftai.tech"])
    response = client.post(
        "/api/v1/bookings", headers={"origin": "https://graftai.tech"}
    )
    assert response.status_code == 200


def test_untrusted_origin_rejected():
    client = build_client(allowed_origins=["https://graftai.tech"])
    response = client.post("/api/v1/bookings", headers={"origin": "https://evil.com"})
    assert response.status_code == 403


def test_untrusted_referer_rejected():
    client = build_client(allowed_origins=["https://graftai.tech"])
    response = client.post(
        "/api/v1/bookings", headers={"referer": "https://evil.com/attack.html"}
    )
    assert response.status_code == 403


def test_referer_fallback_accepts_trusted_origin():
    client = build_client(allowed_origins=["https://graftai.tech"])
    response = client.post(
        "/api/v1/bookings", headers={"referer": "https://graftai.tech/bookings/new"}
    )
    assert response.status_code == 200


def test_trailing_slash_and_regex_origins():
    client = build_client(
        allowed_origins=["https://graftai.tech/"],
        allowed_origin_regex=r"^https?://(?:localhost|127\.0\.0\.1)(?::\d+)?$",
    )
    assert (
        client.post(
            "/api/v1/bookings", headers={"origin": "https://graftai.tech"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/bookings", headers={"origin": "http://localhost:3000"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/bookings", headers={"origin": "http://evil.localhost"}
        ).status_code
        == 403
    )


def test_non_browser_client_without_origin_allowed():
    client = build_client(allowed_origins=["https://graftai.tech"])
    assert client.post("/api/v1/bookings").status_code == 200


def test_exempt_paths_skipped():
    client = build_client(
        allowed_origins=["https://graftai.tech"], exempt_paths=("/api/v1/webhooks",)
    )
    response = client.post(
        "/api/v1/webhooks/stripe", headers={"origin": "https://evil.com"}
    )
    assert response.status_code == 200


def test_middleware_runs_before_existing_middleware_and_returns_response():
    # The 403 must be a real response object, not a bare raise, so CORS can label it.
    app = FastAPI()
    app.add_middleware(CSRFMiddleware, allowed_origins=["https://graftai.tech"])

    class MarkerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Marker"] = "1"
            return response

    app.add_middleware(MarkerMiddleware)

    @app.post("/x")
    async def x():
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/x", headers={"origin": "https://evil.com"})
    assert response.status_code == 403
    assert response.headers["X-Marker"] == "1"
