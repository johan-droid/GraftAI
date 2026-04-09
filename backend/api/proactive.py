from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.api.deps import get_current_user
from backend.models.tables import UserTable
from typing import Optional

router = APIRouter(prefix="/proactive", tags=["proactive"])

class ProactiveSuggestRequest(BaseModel):
    context: Optional[str] = None

class ProactiveSuggestResponse(BaseModel):
    suggestion: str

@router.post("/suggest", response_model=ProactiveSuggestResponse)
async def suggest_action(
    payload: ProactiveSuggestRequest,
    current_user: UserTable = Depends(get_current_user),
):
    """Return a lightweight proactive suggestion based on dashboard context."""
    context = (payload.context or "").strip().lower()
    if "dashboard" in context:
        suggestion = "Review your next meetings and ask me to reschedule if anything conflicts."
    elif "meeting" in context:
        suggestion = "Ask me to find the best time to schedule a follow-up meeting."
    else:
        suggestion = "Try asking for your next availability or to summarize today’s schedule."

    return {"suggestion": suggestion}
