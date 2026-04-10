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

CONSENT_KEYS = {"analytics", "notifications", "ai_training"}


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

    if request.consent_type not in CONSENT_KEYS:
        raise HTTPException(status_code=400, detail="Unsupported consent type")

    result = await db.execute(select(UserTable).where(UserTable.id == str(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Consent flags are stored in preferences JSON since dedicated columns were removed.
    prefs = dict(user.preferences or {})
    consent_key = f"consent_{request.consent_type}"
    prefs[consent_key] = bool(request.granted)
    user.preferences = prefs
    await db.commit()

    return ConsentResponse(status="updated")


@router.get("/")
async def get_consent(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserTable).where(UserTable.id == str(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs = dict(user.preferences or {})
    return {
        "consent_analytics": prefs.get("consent_analytics", True),
        "consent_notifications": prefs.get("consent_notifications", True),
        "consent_ai_training": prefs.get("consent_ai_training", False),
    }
