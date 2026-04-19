from fastapi import HTTPException, status
from starlette.requests import Request
from typing import Callable
from collections import defaultdict
import hashlib
import hmac
import os
import time

_rate_limit_state: dict[str, dict[str, list[float]]] = defaultdict(
    lambda: defaultdict(list)
)


def _current_window_timestamps(key: str, window_seconds: int) -> list[float]:
    now = time.time()
    timestamps = _rate_limit_state[key]
    valid = [ts for ts in timestamps["calls"] if ts > now - window_seconds]
    _rate_limit_state[key]["calls"] = valid
    return valid


def get_rate_limiter(max_requests: int = 10, window_seconds: int = 60) -> Callable:
    def dependency(request: Request):
        client_ip = request.client.host if request.client else "anonymous"
        window = _current_window_timestamps(client_ip, window_seconds)
        if len(window) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please slow down.",
            )
        window.append(time.time())
        _rate_limit_state[client_ip]["calls"] = window
        return True

    return dependency


def _booking_action_secret() -> str:
    secret = os.getenv("BOOKING_ACTION_SECRET", "").strip()
    if secret:
        return secret

    jwt_secret = os.getenv("JWT_SECRET", "").strip()
    if jwt_secret:
        return jwt_secret

    secret_key = os.getenv("SECRET_KEY", "").strip()
    if secret_key:
        return secret_key

    raise ValueError(
        "BOOKING_ACTION_SECRET, JWT_SECRET, or SECRET_KEY must be configured for booking action tokens."
    )


def create_public_action_token(booking_id: str, email: str) -> str:
    payload = f"{booking_id}:{email.strip().lower()}".encode("utf-8")
    return hmac.new(
        _booking_action_secret().encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def verify_public_action_token(booking_id: str, email: str, token: str) -> bool:
    if not token:
        return False
    expected = create_public_action_token(booking_id, email)
    return hmac.compare_digest(expected, token.strip())
