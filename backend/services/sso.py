"""
SSO (OAuth2, OIDC) authentication implementation with Redis-backed state storage.
"""
from datetime import datetime, timedelta, timezone
import os
import uuid
import json
from fastapi import HTTPException
from authlib.integrations.httpx_client import AsyncOAuth2Client
import redis
import hmac
import hashlib
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Redis client for state storage (shared across workers)
_redis_client = None

def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


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
    if ":" not in signed_state:
        return None
    state, signature = signed_state.split(":", 1)
    expected = _sign_state(state)
    if hmac.compare_digest(expected, signature):
        return state
    return None

# SSRF protection: only allow these domains for userinfo_url
ALLOWED_SSO_DOMAINS = [
    "api.github.com",
    "www.googleapis.com",
    "graph.microsoft.com",
    "appleid.apple.com"
]


def _store_oauth_state(state: str, data: dict, ttl_seconds: int = 300):
    """Store OAuth state in Redis with TTL."""
    client = _get_redis_client()
    # Serialize session object separately - we need to reconstruct it later
    session = data.pop("session", None)
    state_data = {
        "data": json.dumps(data),
        "session_state": getattr(session, "state", None),
        "session_scope": getattr(session, "scope", None),
    }
    client.setex(f"oauth:state:{state}", ttl_seconds, json.dumps(state_data))


def _get_oauth_state(state: str) -> dict | None:
    """Retrieve and delete OAuth state from Redis."""
    client = _get_redis_client()
    key = f"oauth:state:{state}"
    raw_data = client.get(key)
    if not raw_data:
        return None
    client.delete(key)
    state_data = json.loads(raw_data)
    data = json.loads(state_data["data"])
    return data

# Multi-provider configuration
PROVIDERS = {
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID") or os.getenv("OAUTH2_CLIENT_ID"),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET") or os.getenv("OAUTH2_CLIENT_SECRET"),
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "read:user user:email",
    },
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid profile email",
    },
    "microsoft": {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid profile email User.Read",
    },
    "apple": {
        "client_id": os.getenv("APPLE_CLIENT_ID"),
        "client_secret": os.getenv("APPLE_CLIENT_SECRET"),
        "auth_url": "https://appleid.apple.com/auth/authorize",
        "token_url": "https://appleid.apple.com/auth/token",
        "userinfo_url": None,  # Apple returns user info in the ID token
        "scope": "name email",
        "response_mode": "form_post",  # Apple requires form_post
    },
}

# During OAuth2 login the provider should return to the frontend callback endpoint.
# This matches the existing Next.js `/auth-callback` page flow in frontend/src/app/auth-callback/page.tsx
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
OAUTH2_REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI", f"{APP_BASE_URL}/auth/sso/callback")


def start_oauth2_flow(provider: str = "github", redirect_to: str = "/dashboard"):
    config = PROVIDERS.get(provider.lower())
    if not config:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not supported")

    client_id = config["client_id"]
    client_secret = config["client_secret"]

    if not all([client_id, client_secret]):
        raise RuntimeError(f"OAuth2 credentials for {provider} are not configured")

    # Using sync discovery/init; create_authorization_url is local computation
    from authlib.integrations.requests_client import OAuth2Session
    session = OAuth2Session(
        client_id=client_id,
        client_secret=client_secret,
        scope=config["scope"],
        redirect_uri=OAUTH2_REDIRECT_URI,
    )

    # Apple requires response_mode=form_post
    extra_params = {}
    if config.get("response_mode"):
        extra_params["response_mode"] = config["response_mode"]

    authorization_url, state = session.create_authorization_url(
        config["auth_url"], **extra_params
    )
    
    # Sign the state to prevent tampering (SSRF/CSRF hardening)
    signature = _sign_state(state)
    signed_state = f"{state}:{signature}"
    
    _store_oauth_state(state, {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "redirect_to": redirect_to,
        "provider": provider.lower(),
    }, ttl_seconds=300)

    return {
        "authorization_url": authorization_url.replace(f"state={state}", f"state={signed_state}"),
        "state": signed_state,
        "expires_in_seconds": 300,
        "redirect_to": redirect_to,
        "provider": provider,
    }


async def complete_oauth2_flow(code: str, signed_state: str):
    # Verify HMAC signature first
    state = _verify_state(signed_state)
    if not state:
        raise HTTPException(status_code=403, detail="OAuth state signature verification failed")

    data = _get_oauth_state(state)
    if not data:
        raise RuntimeError("Invalid or expired state")

    created_at = datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat()))
    if datetime.now(timezone.utc) - created_at > timedelta(minutes=5):
        raise RuntimeError("OAuth2 state expired")

    provider_name = data.get("provider", "github")
    config = PROVIDERS.get(provider_name)
    if not config:
        raise RuntimeError(f"Provider config for {provider_name} not found")

    # Reconstruct Async Client
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    
    async with AsyncOAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        scope=config["scope"],
        redirect_uri=OAUTH2_REDIRECT_URI,
        state=state,
    ) as session:
        token = await session.fetch_token(
            config.get("token_url"),
            code=code,
            authorization_response=f"?code={code}&state={state}",
        )

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
    email = profile.get("email") or profile.get("mail") or profile.get("userPrincipalName")

    return {
        "provider": provider_name,
        "profile": {
            "id": user_id,
            "name": name,
            "email": email,
        },
        "token": token,
        "redirect_to": redirect_to,
    }

