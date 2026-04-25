from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.auth.schemes import get_current_user_id
from backend.models.tables import NotificationTable
from backend.services.notifications import send_custom_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    body: Optional[str] = None
    data: Optional[dict] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    limit: int = 25,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if unread_only:
        stmt = (
            select(NotificationTable)
            .where(
                NotificationTable.user_id == user_id, NotificationTable.is_read == False
            )
            .order_by(NotificationTable.created_at.desc())
            .limit(limit)
        )
    else:
        stmt = (
            select(NotificationTable)
            .where(NotificationTable.user_id == user_id)
            .order_by(NotificationTable.created_at.desc())
            .limit(limit)
        )

    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows


@router.patch("/mark_all_read")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    stmt = (
        update(NotificationTable)
        .where(NotificationTable.user_id == user_id, NotificationTable.is_read == False)
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.commit()
    return {"status": "ok"}


@router.patch("/{notification_id}")
async def mark_notification(
    notification_id: str,
    is_read: bool = True,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    stmt = select(NotificationTable).where(
        NotificationTable.id == notification_id,
        NotificationTable.user_id == user_id,
    )
    result = await db.execute(stmt)
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = is_read
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return {"status": "ok", "id": notif.id, "is_read": notif.is_read}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    stmt = select(NotificationTable).where(
        NotificationTable.id == notification_id,
        NotificationTable.user_id == user_id,
    )
    result = await db.execute(stmt)
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.delete(notif)
    await db.commit()
    return {"status": "ok"}


class NotificationTestRequest(BaseModel):
    to_email: EmailStr
    subject: str
    message: str
    html_body: Optional[str] = None
    text_body: Optional[str] = None


@router.post("/test")
async def test_notification(
    payload: NotificationTestRequest,
    user_id: str = Depends(get_current_user_id),
):
    if not payload.to_email:
        raise HTTPException(status_code=400, detail="Recipient email is required")

    try:
        await send_custom_notification(
            user_email=payload.to_email,
            subject=payload.subject,
            message=payload.message,
            html_body=payload.html_body,
            text_body=payload.text_body,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to send notification: {e}")

    return JSONResponse(
        status_code=202,
        content={"status": "queued", "message": "Test notification dispatched."},
    )
