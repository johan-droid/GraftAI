"""Apple Sign In and iCloud Calendar integration."""

import os
import jwt
import requests
from typing import Dict, Any
from authlib.integrations.httpx_client import AsyncOAuth2Client
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID")
APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID")
APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
APPLE_REDIRECT_URI = os.getenv(
    "APPLE_REDIRECT_URI", f"{BACKEND_URL}/api/v1/auth/apple/callback"
)

# Apple OAuth endpoints
APPLE_AUTH_URL = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"

# Validate Apple OAuth configuration
if not all([APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]):
    import logging

    logging.warning(
        "⚠️  Apple Sign In not fully configured. Set APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, and APPLE_PRIVATE_KEY. "
        "Visit https://developer.apple.com/account/resources/identifiers/list/serviceId to configure."
    )


def generate_apple_client_secret() -> str:
    """Generate client secret JWT for Apple Sign In."""
    if not all([APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]):
        raise ValueError("Apple OAuth credentials not configured")

    # Clean up private key
    private_key = APPLE_PRIVATE_KEY.replace("\\n", "\n")

    # Load private key
    try:
        key = serialization.load_pem_private_key(
            private_key.encode(), password=None, backend=default_backend()
        )
    except Exception as e:
        raise ValueError(f"Invalid Apple private key: {e}")

    # Generate JWT
    now = jwt.utils.get_int_from_datetime(
        jwt.utils.get_datetime_from_timestamp(jwt.utils.get_time())
    )
    headers = {
        "kid": APPLE_KEY_ID,
        "alg": "ES256",
    }
    payload = {
        "iss": APPLE_TEAM_ID,
        "iat": now,
        "exp": now + 86400 * 180,  # 6 months
        "aud": "https://appleid.apple.com",
        "sub": APPLE_CLIENT_ID,
    }

    return jwt.encode(payload, key, algorithm="ES256", headers=headers)


async def get_apple_auth_url(state: str) -> str:
    """Get Apple Sign In authorization URL."""
    if not APPLE_CLIENT_ID:
        raise ValueError(
            "Apple OAuth is not configured. Set APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, and APPLE_PRIVATE_KEY. "
            "Get credentials from: https://developer.apple.com/account/resources/identifiers/list/serviceId"
        )

    client = AsyncOAuth2Client(
        client_id=APPLE_CLIENT_ID,
        redirect_uri=APPLE_REDIRECT_URI,
        scope="name email",
    )

    authorization_url, _ = client.create_authorization_url(
        APPLE_AUTH_URL,
        state=state,
        response_mode="form_post",
        scope="name email",
    )
    return authorization_url


async def fetch_apple_tokens(code: str) -> Dict[str, Any]:
    """Exchange authorization code for Apple tokens."""
    if not all([APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]):
        raise ValueError(
            "Apple OAuth is not configured. Set APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, and APPLE_PRIVATE_KEY. "
            "Get credentials from: https://developer.apple.com/account/resources/identifiers/list/serviceId"
        )

    client_secret = generate_apple_client_secret()

    async with AsyncOAuth2Client(
        client_id=APPLE_CLIENT_ID,
        client_secret=client_secret,
    ) as client:
        token = await client.fetch_token(
            APPLE_TOKEN_URL,
            code=code,
            grant_type="authorization_code",
            redirect_uri=APPLE_REDIRECT_URI,
        )

    # Decode identity token to get user info
    id_token = token.get("id_token")
    user_info = {}

    if id_token:
        # Fetch Apple's public keys
        keys_response = requests.get(APPLE_KEYS_URL)
        keys = keys_response.json().get("keys", [])

        # Find matching key
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")

        for key in keys:
            if key.get("kid") == kid:
                # Verify and decode
                try:
                    decoded = jwt.decode(
                        id_token,
                        jwt.algorithms.RSAAlgorithm.from_jwk(key),
                        algorithms=["RS256"],
                        audience=APPLE_CLIENT_ID,
                        issuer="https://appleid.apple.com",
                    )
                    user_info = {
                        "email": decoded.get("email"),
                        "full_name": None,  # Apple only provides name on first sign-in
                        "apple_user_id": decoded.get("sub"),
                    }
                except jwt.InvalidTokenError as e:
                    raise ValueError(f"Invalid Apple ID token: {e}")
                break

    return {
        "email": user_info.get("email"),
        "full_name": user_info.get("full_name"),
        "apple_user_id": user_info.get("apple_user_id"),
        "token": token,
    }


async def refresh_apple_token(refresh_token: str) -> Dict[str, Any]:
    """Refresh Apple access token."""
    if not all([APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]):
        raise ValueError("Apple OAuth credentials not configured")

    client_secret = generate_apple_client_secret()

    async with AsyncOAuth2Client(
        client_id=APPLE_CLIENT_ID,
        client_secret=client_secret,
    ) as client:
        token = await client.fetch_token(
            APPLE_TOKEN_URL,
            refresh_token=refresh_token,
            grant_type="refresh_token",
        )

    return token
