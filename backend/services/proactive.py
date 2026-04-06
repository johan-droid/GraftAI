from fastapi import APIRouter, Depends, HTTPException
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


from backend.services import scheduler
from backend.services.sync_engine import sync_user_calendar
from backend.utils.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

@router.post("/suggest", response_model=ProactiveResponse)
async def proactive_suggest(
    request: ProactiveRequest, 
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Proactive suggestion requested by user: {user_id}")
    
    try:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)

        # Ensure calendar is up to date before computing slot-based suggestions
        try:
            await sync_user_calendar(db, user_id)
        except Exception as sync_err:
            logger.warning(f"Proactive sync warning: {sync_err}")

        events = await scheduler.get_events_for_range(db, user_id, now, tomorrow)

        if not events:
            slots = await scheduler.find_available_slots(db, user_id, now, 60, target_timezone="UTC")
            if slots:
                first_slot = slots[0]
                return ProactiveResponse(
                    suggestion=(
                        f"Your schedule is clear for the next 24 hours. The next smart slot is {first_slot['local_label']}"
                        + (f" (guest {first_slot.get('guest_label')})" if first_slot.get('guest_label') else "")
                        + ". Would you like me to book it for you?"
                    )
                )
            return ProactiveResponse(suggestion="Your schedule is clear for the next 24 hours. Great time to focus on that big project!")

        next_event = events[0]
        time_until = next_event.start_time.replace(tzinfo=None) - now.replace(tzinfo=None)
        minutes_until = int(time_until.total_seconds() / 60)

        if minutes_until < 30:
            return ProactiveResponse(suggestion=f"You have '{next_event.title}' starting in just {max(0, minutes_until)} minutes. Need me to gather some prep notes?")
        elif minutes_until < 120:
            return ProactiveResponse(suggestion=f"Ready for '{next_event.title}' at {next_event.start_time.strftime('%I:%M %p')}? You've got a good window for deep work until then.")
        else:
            return ProactiveResponse(suggestion=f"Your next meeting is '{next_event.title}' later today. I've optimized your morning for maximum productivity.")

    except Exception as e:
        logger.error(f"Proactive engine failure: {e}")
        raise HTTPException(status_code=500, detail="Unable to compute proactive suggestion")
