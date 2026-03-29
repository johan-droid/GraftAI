from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import os
import logging
from datetime import datetime, timezone, timedelta
from backend.models.tables import UserTable
from backend.auth.schemes import get_current_user_id
from backend.utils.db import get_db
import urllib.parse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])

# --- GOOGLE OAUTH CONFIG ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/integrations/google/callback")

# --- MICROSOFT OAUTH CONFIG ---
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI", "http://localhost:8000/api/v1/integrations/microsoft/callback")
MS_TENANT = os.getenv("MS_TENANT_ID", "common")

@router.get("/google/connect")
async def google_connect(user_id: str = Depends(get_current_user_id)):
    """Redirects the user to Google OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured on server.")
        
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
        "state": user_id # Using user_id as state for simplicity in this lab environment
    }
    url = f"https://accounts.google.com/o/oauth2/v2.auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)

@router.get("/google/callback")
async def google_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Handles Google OAuth callback, exchanges code for tokens, and persists them."""
    user_id = state
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        )
        
        if response.status_code != 200:
            logger.error(f"Google Callback Error: {response.text}")
            return {"error": "Failed to exchange code for tokens"}

        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in", 3600)

        # Update user in DB
        user = await db.get(UserTable, user_id)
        if user:
            user.google_access_token = access_token
            if refresh_token:
                user.google_refresh_token = refresh_token
            user.google_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            await db.commit()
            logger.info(f"✅ Google Calendar connected for user {user_id}")
            
    # Redirect back to frontend
    frontend_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    return RedirectResponse(f"{frontend_url}/dashboard/settings?google_connected=true")


@router.get("/microsoft/connect")
async def microsoft_connect(user_id: str = Depends(get_current_user_id)):
    """Redirects the user to Microsoft OAuth consent screen."""
    if not MS_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Microsoft OAuth not configured on server.")
        
    params = {
        "client_id": MS_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": MS_REDIRECT_URI,
        "response_mode": "query",
        "scope": "https://graph.microsoft.com/Calendars.ReadWrite offline_access",
        "state": user_id
    }
    url = f"https://login.microsoftonline.com/{MS_TENANT}/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)

@router.get("/microsoft/callback")
async def microsoft_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Handles Microsoft OAuth callback."""
    user_id = state
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://login.microsoftonline.com/{MS_TENANT}/oauth2/v2.0/token",
            data={
                "client_id": MS_CLIENT_ID,
                "client_secret": MS_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": MS_REDIRECT_URI,
                "scope": "https://graph.microsoft.com/Calendars.ReadWrite offline_access",
            },
        )
        
        if response.status_code != 200:
            logger.error(f"Microsoft Callback Error: {response.text}")
            return {"error": "Failed to exchange code for tokens"}

        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in", 3600)

        # Update user in DB
        user = await db.get(UserTable, user_id)
        if user:
            user.microsoft_access_token = access_token
            if refresh_token:
                user.microsoft_refresh_token = refresh_token
            user.microsoft_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            await db.commit()
            logger.info(f"✅ Microsoft Graph connected for user {user_id}")
            
    # Redirect back to frontend
    frontend_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    return RedirectResponse(f"{frontend_url}/dashboard/settings?microsoft_connected=true")
