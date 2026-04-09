from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from backend.api.deps import get_current_user
from backend.models.tables import UserTable
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/proactive", tags=["proactive"])

class ProactiveSuggestRequest(BaseModel):
    context: Optional[str] = None

class SmartAction(BaseModel):
    id: str
    action_type: str = Field(..., description="e.g., 'schedule', 'cancel', 'reschedule'")
    title: str
    description: str
    target_entity_id: Optional[str] = None
    suggested_time: Optional[str] = None
    confidence_score: float = 0.0
    payload: Optional[Dict[str, Any]] = None

class ProactiveSuggestResponse(BaseModel):
    suggestion: str
    smart_actions: List[SmartAction] = []

@router.post("/suggest", response_model=ProactiveSuggestResponse)
async def suggest_action(
    payload: ProactiveSuggestRequest,
    current_user: UserTable = Depends(get_current_user),
):
    """Return a lightweight proactive suggestion and structured smart actions based on dashboard context."""
    context = (payload.context or "").strip().lower()
    smart_actions = []
    
    if "dashboard" in context:
        suggestion = "Review your next meetings and ask me to reschedule if anything conflicts."
        smart_actions = [
             SmartAction(
                 id="action_dash_1",
                 action_type="review_schedule",
                 title="Review Schedule",
                 description="Look at today's upcoming meetings.",
                 confidence_score=0.9
             )
        ]
    elif "meeting" in context:
        suggestion = "Ask me to find the best time to schedule a follow-up meeting."
        smart_actions = [
             SmartAction(
                 id="action_meet_1",
                 action_type="schedule",
                 title="Schedule Follow-up",
                 description="Find time for a follow-up meeting.",
                 confidence_score=0.8,
                 payload={"meeting_type": "follow_up"}
             )
        ]
    else:
        suggestion = "Try asking for your next availability or to summarize today’s schedule."
        smart_actions = [
             SmartAction(
                 id="action_gen_1",
                 action_type="summarize",
                 title="Summarize Day",
                 description="Get a quick summary of your schedule today.",
                 confidence_score=0.75
             )
        ]

    return {"suggestion": suggestion, "smart_actions": smart_actions}
