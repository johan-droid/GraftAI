from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from backend.auth.schemes import get_current_user_id

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proactive", tags=["proactive"])


class ProactiveRequest(BaseModel):
    context: Optional[str] = None


class ProactiveResponse(BaseModel):
    suggestion: str


@router.post("/suggest", response_model=ProactiveResponse)
async def proactive_suggest(
    request: ProactiveRequest, user_id: int = Depends(get_current_user_id)
):
    logger.info(f"Proactive suggestion requested by user: {user_id}")
    # TODO: Implement proactive AI logic (e.g., suggest optimal times)
    return ProactiveResponse(suggestion="Proactive suggestion coming soon.")
