"""
SSO (OAuth2, OIDC) authentication implementation with Redis-backed state storage.
"""

from datetime import datetime, timedelta, timezone
import os
import json
from typing import Any
from fastapi import HTTPException, Request, status
from authlib.integrations.httpx_client import AsyncOAuth2Client
from backend.utils.redis_singleton import safe_delete, safe_get, safe_set
import hmac
import hashlib
import logging

# Initialize logger
logger = logging.getLogger(__name__)


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Fallback for dev only; production should raise error (already done in routes.py)
    SECRET_KEY = "insecure-dev-fallback"


def _sign_state(state: str) -> str:
    """Sign a state string with HMAC-SHA256."""
    key = SECRET_KEY or "insecure-dev-fallback"
    return hmac.new(key.encode(), state.encode(), hashlib.sha256).hexdigest()


def _verify_state(signed_state: str) -> str | None:
    """Verify a signed state and return the original state string."""
    if "." not in signed_state:
        return None
    state, signature = signed_state.split(".", 1)
    expected = _sign_state(state)
    if hmac.compare_digest(expected, signature):
        return state
    return None


# SSRF protection: only allow these domains for userinfo_url
ALLOWED_SSO_DOMAINS = [
    "www.googleapis.com",
    "graph.microsoft.com",
]


def _store_oauth_state(state: str, data: dict, ttl_seconds: int = 300):
    """Store OAuth state in Redis with TTL."""
    # Serialize session object separately - we need to reconstruct it later
    session = data.pop("session", None)
    state_data = {
        "data": json.dumps(data),
        "session_state": getattr(session, "state", None),
        "session_scope": getattr(session, "scope", None),
    }
    safe_set(f"oauth:state:{state}", json.dumps(state_data), ttl_seconds=ttl_seconds)


def _get_oauth_state(state: str) -> dict | None:
    """Retrieve OAuth state from Redis (no immediate deletion)."""
    key = f"oauth:state:{state}"
    raw_data = safe_get(key)
    if not raw_data:
        return None

    if isinstance(raw_data, bytes):
        raw_data = raw_data.decode("utf-8")
    elif not isinstance(raw_data, str):
        raw_data = str(raw_data)

    state_data = json.loads(raw_data)
    data = json.loads(state_data["data"])
    return data


def _delete_oauth_state(state: str):
    """Delete OAuth state from Redis after successful login."""
    safe_delete(f"oauth:state:{state}")


def get_provider_config(provider: str) -> dict | None:
    """Get provider configuration dynamically, allowing for late env loading."""
    provider = provider.lower()
    
    if provider == "google":
        return {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
            "scope": "openid profile email https://www.googleapis.com/auth/calendar.events",
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
            "revoke_url": "https://oauth2.googleapis.com/revoke",
            "access_type": "offline",
            "prompt": "select_account",
        }
    elif provider == "microsoft":
        return {
            "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
            "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "scope": "openid profile email User.Read Calendars.ReadWrite OnlineMeetings.ReadWrite",
            "redirect_uri": os.getenv("MICROSOFT_REDIRECT_URI"),
        }
    return None


# During OAuth2 login the provider should return to the frontend callback endpoint.
# This matches the existing Next.js `/auth-callback` page flow in frontend/src/app/auth-callback/page.tsx
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
OAUTH2_REDIRECT_URI = os.getenv(
    "OAUTH2_REDIRECT_URI", f"{APP_BASE_URL}/api/v1/auth/sso/callback"
)


def start_oauth2_flow(provider: str = "microsoft", redirect_to: str = "/dashboard"):
    config = get_provider_config(provider)
    if not config:
        raise HTTPException(
            status_code=400, detail=f"Provider {provider} not supported"
        )

    client_id = config["client_id"]
    client_secret = config["client_secret"]

    if not all([client_id, client_secret]):
        missing = []
        if not client_id: missing.append("client_id")
        if not client_secret: missing.append("client_secret")
        logger.error(f"SSO provider '{provider}' missing: {', '.join(missing)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SSO provider '{provider}' is currently unavailable (missing configuration)",
        )

    # Using sync discovery/init; create_authorization_url is local computation
    from authlib.integrations.requests_client import OAuth2Session

    # Use provider-specific redirect URI if available, otherwise global default
    redirect_uri = config.get("redirect_uri") or OAUTH2_REDIRECT_URI
    
    session = OAuth2Session(
        client_id=client_id,
        client_secret=client_secret,
        scope=config["scope"],
        redirect_uri=redirect_uri,
    )

    extra_params = {}
    if config.get("access_type"):
        extra_params["access_type"] = config["access_type"]
    if config.get("prompt"):
        extra_params["prompt"] = config["prompt"]
    if config.get("response_mode"):
        extra_params["response_mode"] = config["response_mode"]

    authorization_url, state = session.create_authorization_url(
        config["auth_url"], **extra_params
    )

    # Sign the state to prevent tampering (SSRF/CSRF hardening)
    signature = _sign_state(state)
    signed_state = f"{state}.{signature}"

    _store_oauth_state(
        state,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "redirect_to": redirect_to,
            "provider": provider.lower(),
        },
        ttl_seconds=300,
    )

    return {
        "authorization_url": authorization_url.replace(
            f"state={state}", f"state={signed_state}"
        ),
        "state": signed_state,
        "expires_in_seconds": 300,
        "redirect_to": redirect_to,
        "provider": provider,
    }


async def complete_oauth2_flow(request: Request, code: str, state: str):
    # Verify HMAC signature first
    original_state = _verify_state(state)
    if not original_state:
        raise HTTPException(
            status_code=403, detail="OAuth state signature verification failed"
        )

    data = _get_oauth_state(original_state)
    if not data:
        logger.error(f"State not found in Redis for: {original_state}")
        raise RuntimeError("Invalid or expired state")
    
    # Enforce one-time use semantics
    _delete_oauth_state(original_state)

    created_at = datetime.fromisoformat(
        data.get("created_at", datetime.now(timezone.utc).isoformat())
    )
    if datetime.now(timezone.utc) - created_at > timedelta(minutes=5):
        raise RuntimeError("OAuth2 state expired")

    provider_name = data.get("provider", "google")
    config = get_provider_config(provider_name)
    if not config:
        raise RuntimeError(f"Provider config for {provider_name} not found")

    # Reconstruct Async Client
    client_id = config["client_id"]
    client_secret = config["client_secret"]

    # Use provider-specific redirect URI if available, 
    # otherwise dynamically determine it from the current request URL (stripping query/fragment)
    # to maintain consistency regardless of prefix (/api/v1/auth vs /auth)
    redirect_uri = config.get("redirect_uri")
    if not redirect_uri:
        # Reconstruct the redirect_uri from the incoming request to be prefix-agnostic
        redirect_uri = str(request.url.replace(query="", fragment=""))

    logger.info(f"Using redirect_uri for token exchange: {redirect_uri}")

    session: Any = AsyncOAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        scope=config["scope"],
        redirect_uri=redirect_uri,
        state=state,
    )
    try:
        # Pass the FULL URL from the request for robust parameter verification by authlib
        # This handles cases where scheme/host/port might be tricky behind proxies.
        token = await session.fetch_token(
            config.get("token_url"),
            code=code,
            authorization_response=str(request.url),
        )
    finally:
        if hasattr(session, "aclose"):
            await getattr(session, "aclose")()

    import httpx

    userinfo_url = config.get("userinfo_url")

    if userinfo_url:
        # SSRF Protection: validate userinfo_url against allowlist
        from urllib.parse import urlparse

        domain = urlparse(userinfo_url).netloc
        if domain not in ALLOWED_SSO_DOMAINS:
            logger.error(f"Potential SSRF blocked: {userinfo_url}")
            raise HTTPException(status_code=400, detail="Disallowed userinfo URL")

        # Standard OAuth2/OIDC: fetch user info via ASYNC client
        headers = {"Authorization": f"Bearer {token.get('access_token')}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            userinfo_resp = await client.get(userinfo_url, headers=headers)
            userinfo_resp.raise_for_status()
            profile = userinfo_resp.json()
    else:
        # Apple Sign In: user info is embedded in the ID token
        id_token = token.get("id_token", "")
        if id_token:
            try:
                # Decode without verification for extracting claims
                # (token was already validated by Apple during exchange)
                import base64
                import json as _json

                parts = id_token.split(".")
                payload_b64 = parts[1] + "==" if len(parts) > 1 else ""
                profile = _json.loads(base64.urlsafe_b64decode(payload_b64))
            except Exception:
                profile = {}
        else:
            profile = {}

    redirect_to = data.get("redirect_to", "/dashboard")

    # Normalize user profile across providers
    user_id = profile.get("id") or profile.get("sub")
    # Microsoft Graph returns displayName; Apple uses given_name
    name = (
        profile.get("name")
        or profile.get("displayName")
        or profile.get("login")
        or profile.get("given_name")
    )
    # Microsoft Graph returns mail or userPrincipalName
    email = (
        profile.get("email") or profile.get("mail") or profile.get("userPrincipalName")
    )

    # --- PHASE 3: RETURN TOKEN DATA ---
    # Database persistence is now handled by the caller (routes.py) 
    # to ensure the user record is committed first.

    return {
        "provider": provider_name,
        "profile": {
            "id": user_id,
            "name": name,
            "email": email,
        },
        "token": token,
        "redirect_to": redirect_to,
        "oauth_state": original_state,
    }


async def revoke_provider_token(provider: str, token: dict):
    """
    Revoke access on the provider's side (Google, GitHub, etc.)
    This ensures that the next login will require a fresh consent screen.
    """
    config = get_provider_config(provider)
    if not config or not config.get("revoke_url"):
        logger.info(f"No revocation URL for provider {provider}")
        return False

    import httpx

    # Google revocation
    if provider.lower() == "google":
        revoke_token = token.get("refresh_token") or token.get("access_token")
        if not revoke_token:
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Google revocation endpoint
                resp = await client.post(
                    config["revoke_url"], params={"token": revoke_token}
                )
                if resp.status_code == 200:
                    logger.info(f"Successfully revoked Google token for {provider}")
                    return True
            except Exception as e:
                logger.error(f"Failed to revoke Google token: {e}")
                return False

    # GitHub revocation (requires Basic Auth with client_id/secret)
    # Note: GitHub typically requires revoking the entire grant via API, 
    # which is more complex as it requires an admin token or a user delete.
    # For now, we focus on Google as per user request.

    return False
