import hmac
import hashlib
import os
import secrets
import time
from urllib.parse import quote_plus, unquote_plus, quote, unquote
from typing import Optional

from fastapi import HTTPException, status, Request

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", os.getenv("FRONTEND_URL", "http://localhost:3000")).rstrip("/")
OAUTH_STATE_EXPIRY_SECONDS = 600
ALLOWED_REDIRECT_PATHS = {"/dashboard", "/settings", "/calendar", "/profile", "/auth-callback"}

from backend.auth.config import SECRET_KEY


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def frontend_redirect_token(
    access_token: str,
    redirect_to: str = "/dashboard",
    frontend_url: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> str:
    base_url = (frontend_url or FRONTEND_BASE_URL).rstrip("/")
    url = f"{base_url}/auth-callback?access_token={quote_plus(access_token)}&redirect={quote_plus(redirect_to)}"
    if refresh_token:
        url += f"&refresh_token={quote_plus(refresh_token)}"
    return url


def build_oauth_state(
    user_id: Optional[str],
    redirect_to: Optional[str] = "/dashboard",
    provider: Optional[str] = None,
    frontend_url: Optional[str] = None,
) -> str:
    safe_redirect = sanitize_redirect(redirect_to or "/dashboard")
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(16)
    user_id_str = user_id or ""
    provider_str = provider or ""
    frontend_url_str = quote(frontend_url or "", safe='')
    payload = f"{timestamp}:{nonce}:{user_id_str}:{safe_redirect}:{provider_str}:{frontend_url_str}"
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{timestamp}:{nonce}:{user_id_str}:{safe_redirect}:{provider_str}:{frontend_url_str}:{signature}"


def parse_oauth_state(state: str) -> tuple[Optional[str], str, Optional[str], Optional[str]]:
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state: missing state",
        )

    parts = state.split(":", 6)
    if len(parts) not in (5, 6, 7):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state: malformed",
        )

    if len(parts) == 7:
        timestamp_str, nonce, user_id, redirect_to, provider, frontend_url, signature = parts
    elif len(parts) == 6:
        timestamp_str, nonce, user_id, redirect_to, provider, signature = parts
        frontend_url = ""
    else:
        timestamp_str, nonce, user_id, redirect_to, signature = parts
        provider = ""
        frontend_url = ""

    payload = f"{timestamp_str}:{nonce}:{user_id}:{redirect_to}:{provider}:{frontend_url}"
    expected_signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state: signature verification failed",
        )

    try:
        state_time = int(timestamp_str)
        current_time = int(time.time())
        if current_time - state_time > OAUTH_STATE_EXPIRY_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth state: expired",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state: invalid timestamp",
        )

    decoded_redirect = unquote_plus(redirect_to)
    safe_redirect = sanitize_redirect(decoded_redirect)
    decoded_frontend_url = unquote(frontend_url) if frontend_url else None
    return user_id or None, safe_redirect, provider or None, decoded_frontend_url


def sanitize_redirect(redirect: str) -> str:
    if not redirect:
        return "/dashboard"

    decoded = unquote_plus(redirect)
    if decoded.startswith(("http://", "https://", "//")):
        return "/dashboard"

    if not decoded.startswith("/"):
        decoded = "/" + decoded

    base_path = decoded.split("?")[0].split("#")[0]
    for allowed in ALLOWED_REDIRECT_PATHS:
        if base_path == allowed or base_path.startswith(allowed + "/"):
            return decoded
    return "/dashboard"
