import hmac
import hashlib
import ipaddress
import os
import secrets
import time
from functools import lru_cache
from urllib.parse import quote_plus, unquote_plus, quote, unquote, urlparse
from typing import Optional

from fastapi import HTTPException, status, Request

FRONTEND_BASE_URL = os.getenv(
    "FRONTEND_BASE_URL", os.getenv("FRONTEND_URL", "http://localhost:3000")
).rstrip("/")
OAUTH_STATE_EXPIRY_SECONDS = 600
ALLOWED_REDIRECT_PATHS = {
    "/dashboard",
    "/settings",
    "/calendar",
    "/profile",
    "/auth-callback",
}

from backend.auth.config import SECRET_KEY


@lru_cache(maxsize=1)
def _trusted_proxy_networks() -> tuple[ipaddress._BaseNetwork, ...]:
    raw = os.getenv("TRUSTED_PROXY_IPS", "")
    if not raw:
        return ()

    networks: list[ipaddress._BaseNetwork] = []
    for token in (value.strip() for value in raw.split(",") if value.strip()):
        try:
            if "/" in token:
                networks.append(ipaddress.ip_network(token, strict=False))
            else:
                suffix = "/128" if ":" in token else "/32"
                networks.append(ipaddress.ip_network(f"{token}{suffix}", strict=False))
        except ValueError:
            continue
    return tuple(networks)


def _is_trusted_proxy_host(host: Optional[str]) -> bool:
    if not host:
        return False

    if host in {"127.0.0.1", "::1", "localhost"}:
        return True

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False

    networks = _trusted_proxy_networks()
    if not networks:
        return False
    return any(ip in network for network in networks)


@lru_cache(maxsize=1)
def _allowed_frontend_origins() -> tuple[str, ...]:
    configured = os.getenv(
        "FRONTEND_URL", os.getenv("FRONTEND_BASE_URL", FRONTEND_BASE_URL)
    )
    origins: list[str] = []

    for candidate in (
        value.strip() for value in configured.split(",") if value.strip()
    ):
        try:
            parsed = urlparse(candidate)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                origins.append(f"{parsed.scheme}://{parsed.netloc}".rstrip("/"))
        except Exception:
            continue

    if not origins:
        origins = [FRONTEND_BASE_URL]

    # Preserve order while removing duplicates.
    return tuple(dict.fromkeys(origins))


def sanitize_frontend_url(frontend_url: Optional[str]) -> str:
    if not frontend_url:
        return _allowed_frontend_origins()[0]

    try:
        parsed = urlparse(frontend_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return _allowed_frontend_origins()[0]
        origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    except Exception:
        return _allowed_frontend_origins()[0]

    if origin in _allowed_frontend_origins():
        return origin
    return _allowed_frontend_origins()[0]


def get_client_ip(request: Request) -> str:
    direct_host = request.client.host if request.client else None

    if _is_trusted_proxy_host(direct_host):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
            if client_ip:
                return client_ip

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            real_ip = real_ip.strip()
            if real_ip:
                return real_ip

    return direct_host or "unknown"


def frontend_redirect_token(
    access_token: str,
    redirect_to: str = "/dashboard",
    frontend_url: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> str:
    base_url = sanitize_frontend_url(frontend_url).rstrip("/")
    # Use URL fragments so tokens never appear in intermediary HTTP logs.
    url = f"{base_url}/auth-callback#at={quote_plus(access_token)}&redirect={quote_plus(redirect_to)}"
    if refresh_token:
        url += f"&rt={quote_plus(refresh_token)}"
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
    frontend_url_str = quote(sanitize_frontend_url(frontend_url), safe="")
    payload = f"{timestamp}:{nonce}:{user_id_str}:{safe_redirect}:{provider_str}:{frontend_url_str}"
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{timestamp}:{nonce}:{user_id_str}:{safe_redirect}:{provider_str}:{frontend_url_str}:{signature}"


def parse_oauth_state(
    state: str,
) -> tuple[Optional[str], str, Optional[str], Optional[str]]:
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
        (
            timestamp_str,
            nonce,
            user_id,
            redirect_to,
            provider,
            frontend_url,
            signature,
        ) = parts
    elif len(parts) == 6:
        timestamp_str, nonce, user_id, redirect_to, provider, signature = parts
        frontend_url = ""
    else:
        timestamp_str, nonce, user_id, redirect_to, signature = parts
        provider = ""
        frontend_url = ""

    payload = (
        f"{timestamp_str}:{nonce}:{user_id}:{redirect_to}:{provider}:{frontend_url}"
    )
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
    decoded_frontend_url = sanitize_frontend_url(
        unquote(frontend_url) if frontend_url else None
    )
    return user_id or None, safe_redirect, provider or None, decoded_frontend_url


def sanitize_redirect(redirect: str) -> str:
    if not redirect:
        return "/dashboard"

    decoded = unquote_plus(redirect)

    parsed = urlparse(decoded)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in {"http", "https"}:
            return "/dashboard"

        origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        if origin not in _allowed_frontend_origins():
            return "/dashboard"

        path = parsed.path or "/"
        query = f"?{parsed.query}" if parsed.query else ""
        fragment = f"#{parsed.fragment}" if parsed.fragment else ""
        decoded = f"{path}{query}{fragment}"

    if not decoded.startswith("/"):
        decoded = "/" + decoded

    base_path = decoded.split("?")[0].split("#")[0]
    for allowed in ALLOWED_REDIRECT_PATHS:
        if base_path == allowed or base_path.startswith(allowed + "/"):
            return decoded
    return "/dashboard"
