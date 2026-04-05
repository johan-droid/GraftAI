from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging
from backend.auth.schemes import get_current_user_id
from backend.api.deps import get_db
from backend.models.tables import UserTable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentRequest(BaseModel):
    consent_type: str
    granted: bool


class ConsentResponse(BaseModel):
    status: str


@router.post("/set", response_model=ConsentResponse)
async def set_consent(
    request: ConsentRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Consent updated by user: {user_id} type={request.consent_type}")

    consent_field_map = {
        "analytics": "consent_analytics",
        "notifications": "consent_notifications",
        "ai_training": "consent_ai_training",
    }
    target_field = consent_field_map.get(request.consent_type)
    if not target_field:
        raise HTTPException(status_code=400, detail="Unsupported consent type")

    result = await db.execute(select(UserTable).where(UserTable.id == str(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    setattr(user, target_field, bool(request.granted))
    await db.commit()

    return ConsentResponse(status="updated")
