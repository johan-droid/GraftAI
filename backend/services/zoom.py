import os
import base64
import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
import httpx
from typing import Optional, Dict, Any
from sqlalchemy import select
from backend.services.redis_client import get_redis
from backend.models.tables import UserTable
from backend.utils.db import AsyncSessionLocal
from backend.utils.security import encrypt_token, decrypt_token

# Initialize logger
logger = logging.getLogger(__name__)

class ZoomService:
    """
    Advanced SaaS-Grade Zoom Service.
    Supports individual User OAuth with background refresh and S2S fallback.
    """
    
    def __init__(self):
        self.client_id = os.getenv("ZOOM_CLIENT_ID")
        self.client_secret = os.getenv("ZOOM_CLIENT_SECRET")
        self.account_id = os.getenv("ZOOM_ACCOUNT_ID")
        self.base_url = "https://api.zoom.us/v2"
        self.token_url = "https://zoom.us/oauth/token"

    def _get_auth_header(self) -> str:
        """Encodes client_id and client_secret for the Authorization header."""
        auth_str = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        return f"Basic {encoded_auth}"

    async def get_s2s_token(self, force_refresh: bool = False) -> Optional[str]:
        """Retrieves a system-wide Server-to-Server access token."""
        if not self.account_id:
            return None
            
        cache_key = f"zoom:token:s2s:{self.account_id}"
        redis = await get_redis()
        
        if not force_refresh:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    return cached
            except Exception:
                pass

        headers = {"Authorization": self._get_auth_header(), "Content-Type": "application/x-www-form-urlencoded"}
        params = {"grant_type": "account_credentials", "account_id": self.account_id}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.token_url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    token = data.get("access_token")
                    try:
                        await redis.setex(cache_key, data.get("expires_in", 3600) - 60, token)
                    except Exception:
                        pass
                    return token
        except Exception as e:
            logger.error(f"S2S Token Error: {e}")
        return None

    # No changes needed to get_user_token, refresh_user_token, save_user_tokens as they don't use self.redis

    async def get_user_token(self, user_id: str) -> Optional[str]:
        """
        Retrieves, decrypts, and automatically refreshes a user's Zoom token.
        """
        async with AsyncSessionLocal() as db:
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()
            
            if not user or not user.zoom_access_token:
                return await self.get_s2s_token() # Fallback to system token

            # Check expiry (naive compare with UTC)
            now = datetime.now(timezone.utc)
            if user.zoom_token_expires_at and now > user.zoom_token_expires_at - timedelta(minutes=5):
                logger.info(f"Refreshing Zoom token for user {user_id}")
                return await self.refresh_user_token(user, db)

            return decrypt_token(user.zoom_access_token)

    async def refresh_user_token(self, user: UserTable, db) -> Optional[str]:
        """Exchanges refresh_token for a new access_token with distributed locking to prevent race conditions."""
        refresh_token = decrypt_token(user.zoom_refresh_token)
        if not refresh_token:
            return None

        # Acquire distributed lock to prevent concurrent token refreshes
        lock_key = f"zoom:token_refresh:{user.id}"
        redis = await get_redis()
        lock_acquired = False
        
        try:
            # Try to acquire lock for 30 seconds
            lock_acquired = await redis.set(lock_key, "locked", ex=30, nx=True)
            
            if not lock_acquired:
                # Another process is refreshing the token, wait and check cache
                logger.info(f"Token refresh for user {user.id} already in progress, waiting...")
                for _ in range(10):  # Wait up to 5 seconds
                    await asyncio.sleep(0.5)
                    # Re-check if token was refreshed by another process
                    await db.refresh(user)
                    if user.zoom_access_token and user.zoom_token_expires_at:
                        now = datetime.now(timezone.utc)
                        if user.zoom_token_expires_at > now + timedelta(minutes=5):
                            return decrypt_token(user.zoom_access_token)
                return None

            headers = {"Authorization": self._get_auth_header(), "Content-Type": "application/x-www-form-urlencoded"}
            data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.token_url, data=data, headers=headers)
                if resp.status_code == 200:
                    new_data = resp.json()
                    user.zoom_access_token = encrypt_token(new_data["access_token"])
                    user.zoom_refresh_token = encrypt_token(new_data["refresh_token"])
                    user.zoom_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=new_data["expires_in"])
                    await db.commit()
                    logger.info(f"Successfully refreshed Zoom token for user {user.id}")
                    return new_data["access_token"]
                else:
                    logger.error(f"Zoom token refresh failed: HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"User Token Refresh Error: {e}")
        finally:
            # Always release the lock
            if lock_acquired:
                try:
                    await redis.delete(lock_key)
                except Exception:
                    pass
        return None

    async def save_user_tokens(self, user_id: str, token_data: Dict[str, Any]):
        """Persists new OAuth tokens to the user's record with encryption."""
        async with AsyncSessionLocal() as db:
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()
            if user:
                user.zoom_access_token = encrypt_token(token_data["access_token"])
                user.zoom_refresh_token = encrypt_token(token_data["refresh_token"])
                user.zoom_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
                await db.commit()
                logger.info(f"Saved encrypted Zoom tokens for user {user_id}")

    async def create_meeting(self, user_id: str, topic: str, start_time: str, duration: int = 60) -> Optional[Dict[str, Any]]:
        """Creates a meeting on behalf of a specific user or the system account."""
        token = await self.get_user_token(user_id)
        if not token:
            return None

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "topic": topic,
            "type": 2,
            "start_time": start_time,
            "duration": duration,
            "settings": {"waiting_room": True, "join_before_host": False}
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            # If using user token, 'me' works. If using S2S, 'me' uses the account owner.
            resp = await client.post(f"{self.base_url}/users/me/meetings", headers=headers, json=payload)
            return resp.json() if resp.status_code == 201 else None

zoom_service = ZoomService()
