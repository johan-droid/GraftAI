import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import UserTable
import os

logger = logging.getLogger(__name__)

# Essential OAuth Configuration from Env
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")

async def get_valid_google_token(db: AsyncSession, user_id: str) -> Optional[str]:
    """
    Retrieves a valid Google access token for the user.
    If expired, it automatically refreshes it using the refresh token.
    """
    user = await db.get(UserTable, user_id)
    if not user or not user.google_refresh_token:
        return None

    # Check if token is expired or expires in next 5 minutes
    now = datetime.now(timezone.utc)
    if user.google_access_token and user.google_token_expires_at:
        if user.google_token_expires_at > (now + timedelta(minutes=5)):
            return user.google_access_token

    # Token is expired or missing - TRIGGER REFRESH
    logger.info(f"🔄 Refreshing Google token for user {user_id}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "refresh_token": user.google_refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            
            if response.status_code != 200:
                # Security: Don't log response.text as it may contain sensitive tokens
                logger.error(f"❌ Google token refresh failed: HTTP {response.status_code}")
                return None

            data = response.json()
            new_access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)

            # Update DB
            user.google_access_token = new_access_token
            user.google_token_expires_at = now + timedelta(seconds=expires_in)
            await db.commit()
            
            logger.info(f"✅ Google token refreshed successfully for user {user_id}")
            return new_access_token

    except Exception as e:
        logger.error(f"⚠ Unexpected error during Google refresh: {e}")
        return None


async def get_valid_ms_token(db: AsyncSession, user_id: str) -> Optional[str]:
    """
    Retrieves a valid Microsoft Graph access token for the user.
    If expired, it automatically refreshes it using the refresh token.
    """
    user = await db.get(UserTable, user_id)
    if not user or not user.microsoft_refresh_token:
        return None

    # Check if token is expired or expires in next 5 minutes
    now = datetime.now(timezone.utc)
    if user.microsoft_access_token and user.microsoft_token_expires_at:
        if user.microsoft_token_expires_at > (now + timedelta(minutes=5)):
            return user.microsoft_access_token

    # Token is expired or missing - TRIGGER REFRESH
    logger.info(f"🔄 Refreshing Microsoft token for user {user_id}...")
    try:
        # Tenant ID can be 'common' or a specific ID
        tenant = os.getenv("MS_TENANT_ID", "common")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
                data={
                    "client_id": MS_CLIENT_ID,
                    "client_secret": MS_CLIENT_SECRET,
                    "refresh_token": user.microsoft_refresh_token,
                    "grant_type": "refresh_token",
                    "scope": "https://graph.microsoft.com/.default offline_access",
                },
            )
            
            if response.status_code != 200:
                # Security: Don't log response.text as it may contain sensitive tokens
                logger.error(f"❌ Microsoft token refresh failed: HTTP {response.status_code}")
                return None

            data = response.json()
            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token") # MS often rotates refresh tokens
            expires_in = data.get("expires_in", 3600)

            # Update DB
            user.microsoft_access_token = new_access_token
            if new_refresh_token:
                user.microsoft_refresh_token = new_refresh_token
            user.microsoft_token_expires_at = now + timedelta(seconds=expires_in)
            await db.commit()
            
            logger.info(f"✅ Microsoft token refreshed successfully for user {user_id}")
            return new_access_token

    except Exception as e:
        logger.error(f"⚠ Unexpected error during Microsoft refresh: {e}")
        return None
