from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from backend.auth.schemes import get_current_user_id
from backend.utils.tenant import get_current_org_id, get_current_workspace_id

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proactive", tags=["proactive"])


class ProactiveRequest(BaseModel):
    context: Optional[str] = None


class ProactiveResponse(BaseModel):
    suggestion: str


from backend.services import scheduler
from backend.utils.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

@router.post("/suggest", response_model=ProactiveResponse)
async def proactive_suggest(
    request: ProactiveRequest, 
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    workspace_id: Optional[int] = Depends(get_current_workspace_id),
):
    logger.info(f"Proactive suggestion requested by user: {user_id}")
    
    try:
        # Fetch events for the next 24 hours
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)
        events = await scheduler.get_events_for_range(db, user_id, now, tomorrow, org_id=org_id, workspace_id=workspace_id)
        
        if not events:
            return ProactiveResponse(suggestion="Your schedule is clear for the next 24 hours. Great time to focus on that big project!")
            
        next_event = events[0]
        time_until = next_event.start_time - now
        minutes_until = int(time_until.total_seconds() / 60)
        
        if minutes_until < 30:
            return ProactiveResponse(suggestion=f"You have '{next_event.title}' starting in just {max(0, minutes_until)} minutes. Need me to gather some prep notes?")
        elif minutes_until < 120:
            return ProactiveResponse(suggestion=f"Ready for '{next_event.title}' at {next_event.start_time.strftime('%I:%M %p')}? You've got a good window for deep work until then.")
        else:
            return ProactiveResponse(suggestion=f"Your next meeting is '{next_event.title}' later today. I've optimized your morning for maximum productivity.")
            
    except Exception as e:
        logger.error(f"Proactive engine failure: {e}")
        return ProactiveResponse(suggestion="Your AI Copilot is monitoring your schedule and will have a suggestion for you soon.")
