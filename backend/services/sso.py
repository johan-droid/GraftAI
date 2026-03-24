"""
SSO (OAuth2, OIDC) authentication implementation with fallback support.
"""
from datetime import datetime, timedelta
import os
import uuid
from fastapi import HTTPException
from authlib.integrations.requests_client import OAuth2Session

# In-memory state manager for demonstration purposes
_oauth_state_cache: dict[str, dict] = {}

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
    _oauth_state_cache[state] = {
        "created_at": datetime.utcnow(),
        "session": session,
        "redirect_to": redirect_to,
        "provider": provider.lower(),
    }

    return {
        "authorization_url": authorization_url,
        "state": state,
        "expires_in_seconds": 300,
        "redirect_to": redirect_to,
        "provider": provider,
    }


def complete_oauth2_flow(code: str, state: str):
    data = _oauth_state_cache.pop(state, None)
    if not data:
        raise RuntimeError("Invalid or expired state")

    if datetime.utcnow() - data.get("created_at", datetime.utcnow()) > timedelta(minutes=5):
        raise RuntimeError("OAuth2 state expired")

    provider_name = data.get("provider", "github")
    config = PROVIDERS.get(provider_name)
    if not config:
        raise RuntimeError(f"Provider config for {provider_name} not found")
    session = data.get("session")
    if session is None:
        raise RuntimeError("OAuth2 session not found in state cache")

    token = session.fetch_token(
        config.get("token_url"),
        code=code,
        client_id=config.get("client_id"),
        client_secret=config.get("client_secret"),
        authorization_response=f"?code={code}&state={state}",
    )

    import httpx

    userinfo_url = config.get("userinfo_url")

    if userinfo_url:
        # Standard OAuth2/OIDC: fetch user info from the provider's endpoint
        headers = {"Authorization": f"Bearer {token.get('access_token')}"}
        userinfo_resp = httpx.get(userinfo_url, headers=headers)
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

