from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional

from backend.auth.schemes import get_current_user_id
from backend.services.notifications import send_custom_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


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
