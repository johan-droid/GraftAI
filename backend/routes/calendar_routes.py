"""Calendar integration routes for connecting external calendars."""
from backend.auth.schemes import get_current_user_id
from backend.models.tables import UserTokenTable
from backend.utils.db import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/calendar", tags=["Calendar Integration"])

class AppleCalendarConnectRequest(BaseModel):
    """Request to connect Apple Calendar with app-specific password."""
    app_specific_password: str

@router.post("/apple/connect")
async def connect_apple_calendar(request: AppleCalendarConnectRequest, user_id: str=Depends(get_current_user_id), db: AsyncSession=Depends(get_db)):
    """
    Connect Apple iCloud Calendar using an app-specific password.

    Users must generate an app-specific password at https://appleid.apple.com
    after signing in with Apple.
    """
    stmt = select(UserTokenTable).where(UserTokenTable.user_id == user_id, UserTokenTable.provider == "apple")
    token = (await db.execute(stmt)).scalars().first()
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please sign in with Apple first to connect your calendar")
    metadata = token.metadata_payload or {}
    apple_user_id = metadata.get("apple_user_id")
    if not apple_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Apple user ID not found. Please sign in with Apple again.")
    token.metadata_payload = {**metadata, "apple_user_id": apple_user_id, "app_specific_password": request.app_specific_password, "calendar_connected": True}
    token.is_active = True
    await db.commit()
    return {"message": "Apple Calendar connected successfully", "provider": "apple", "connected": True}

@router.post("/apple/disconnect")
async def disconnect_apple_calendar(user_id: str=Depends(get_current_user_id), db: AsyncSession=Depends(get_db)):
    """Disconnect Apple Calendar (removes app-specific password)."""
    stmt = select(UserTokenTable).where(UserTokenTable.user_id == user_id, UserTokenTable.provider == "apple")
    token = (await db.execute(stmt)).scalars().first()
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apple Calendar not connected")
    metadata = token.metadata_payload or {}
    token.metadata_payload = {**metadata, "app_specific_password": None, "calendar_connected": False}
    await db.commit()
    return {"message": "Apple Calendar disconnected", "provider": "apple", "connected": False}

@router.get("/connections")
async def list_calendar_connections(user_id: str=Depends(get_current_user_id), db: AsyncSession=Depends(get_db)):
    """List all connected calendar providers for the user."""
    stmt = select(UserTokenTable).where(UserTokenTable.user_id == user_id, UserTokenTable.is_active)
    tokens = (await db.execute(stmt)).scalars().all()
    connections = []
    for token in tokens:
        metadata = token.metadata_payload or {}
        is_calendar_connected = metadata.get("calendar_connected", False)
        connections.append({"provider": token.provider, "connected": is_calendar_connected, "provider_name": {"google": "Google Calendar", "microsoft": "Microsoft Outlook", "apple": "Apple iCloud Calendar"}.get(token.provider, token.provider.title()), "requires_app_password": token.provider == "apple" and (not is_calendar_connected)})
    return {"connections": connections}
