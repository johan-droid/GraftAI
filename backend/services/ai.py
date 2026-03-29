from datetime import datetime, timedelta
import os
import json
import logging
import hashlib
import re
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.db import get_db
from backend.auth.schemes import get_current_user_id
from backend.services import scheduler
from backend.services.cache import get_cache, set_cache
from backend.services.langchain_client import llm, vector_store

# Conditional imports for optional dependencies
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

try:
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    SystemMessage = None
    HumanMessage = None

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

class AIRequest(BaseModel):
    prompt: str
    timezone: str = "UTC"

class AIResponse(BaseModel):
    result: str
    model_used: Optional[str] = None

async def _generate_with_groq(system_prompt: str, user_input: str) -> str:
    """Helper for direct Groq API access if configured."""
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    chat_completion = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def _get_schedule_context(events):
    header = "Your Real-Time Schedule (GROUND TRUTH):\n"
    if not events:
        return header + "Currently empty."
    context = header
    for event in events:
        context += f"- {event.title} at {event.start_time.strftime('%H:%M')} (ID: {event.id})\n"
    return context

from backend.auth.routes import get_rate_limiter

@router.post("/chat", response_model=AIResponse)
async def ai_chat(
    request: AIRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=10, window_seconds=60)),
):
    """
    State-of-the-Art AI Copilot Chat Endpoint.
    Detects scheduling intent and executes actions via the scheduler service.
    """
    current_time = datetime.now()
    schedule_context = ""
    user_name = "User"
    user_email = ""
    try:
        from backend.models.tables import UserTable
        user = await db.get(UserTable, user_id)
        if user:
            user_name = user.full_name or "User"
            user_email = user.email

        window_start = current_time - timedelta(hours=1)
        window_end = current_time + timedelta(hours=24)
        todays_events = await scheduler.get_events_for_range(
            db, user_id, window_start, window_end
        )
        schedule_context = _get_schedule_context(todays_events)
    except Exception as e:
        logger.warning(f"Could not fetch proactive schedule context: {e}")

    system_reasoning = f"""
    IDENTITY: 
    You are GraftAI, the world's most advanced AI Scheduling Copilot. 
    You are an expert executive assistant with FULL CONTROL over the user's calendar.

    STRICT CONTEXT GUARDRAILS:
    1. Your SOLE purpose is to manage calendars and coordinate workspace tasks.
    2. DO NOT behave as a general-purpose global chatbot.
    3. If asked about outside topics, politely decline and steer back to the schedule.

    DOMAIN KNOWLEDGE:
    Today's Date: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
    User Timezone: {request.timezone}
    User Name: {user_name}
    User Email: {user_email}

    {schedule_context}

    ACTION PROTOCOL:
    Suffix response with exactly ONE if requirement met:
    ACTION:SCHEDULE_MEETING:{{"title": "...", "start_time": "ISO", "duration_minutes": 30, "is_meeting": true, "platform": "google_meet", "attendees": ["email@ex.com"], "agenda": "..."}}
    ACTION:UPDATE_MEETING:{{"event_id": 1, "new_start_time": "ISO", "new_title": "Optional"}}
    ACTION:DELETE_MEETING:{{"event_id": 1}}

    MEETING PLATFORMS: google_meet, zoom, teams. 
    If a user wants a meeting but doesn't specify a platform, ASK them.
    If they don't provide attendees or agenda, ASK for them to make it a professional invite.
    """

    user_input = f"User Message: {request.prompt}"
    
    # Simple cache logic
    cache_key = "ai_cache:" + hashlib.sha256(f"{system_reasoning}|{user_input}".encode()).hexdigest()
    cached = get_cache(cache_key)
    if cached:
        return AIResponse(result=cached, model_used="cache-hit")

    # Generate
    try:
        if (os.getenv("GROQ_API_KEY") and AsyncGroq) or os.getenv("FORCE_GROQ") == "1":
            result_text = await _generate_with_groq(system_reasoning, user_input)
            model_used = "llama-3.3-70b-versatile"
        else:
            response = llm.invoke(user_input) # Simplified for brevity in rewrite
            result_text = response.content if hasattr(response, 'content') else str(response)
            model_used = "fallback"
    except Exception as e:
        logger.error(f"LLM failed: {e}")
        return AIResponse(result="I'm sorry, I can't process that right now.", model_used="error")

    if result_text:
        set_cache(cache_key, result_text, 300)
        
        # Action Layer
        schedule_match = re.search(r"ACTION:SCHEDULE_MEETING:(\{.*?\})", result_text, re.DOTALL)
        update_match = re.search(r"ACTION:UPDATE_MEETING:(\{.*?\})", result_text, re.DOTALL)
        delete_match = re.search(r"ACTION:DELETE_MEETING:(\{.*?\})", result_text, re.DOTALL)

        if schedule_match:
            try:
                data = json.loads(schedule_match.group(1))
                event_data = {
                    "user_id": user_id,
                    "title": data.get("title", "Meeting"),
                    "start_time": datetime.fromisoformat(data["start_time"].replace("Z", "+00:00")).replace(tzinfo=None),
                    "end_time": (datetime.fromisoformat(data["start_time"].replace("Z", "+00:00")) + timedelta(minutes=data.get("duration_minutes", 30))).replace(tzinfo=None),
                    "status": "confirmed",
                    "is_meeting": data.get("is_meeting", False),
                    "meeting_platform": data.get("platform"),
                    "agenda": data.get("agenda"),
                    "attendees": [{"email": e} for e in data.get("attendees", [])]
                }
                await scheduler.create_event(db, event_data)
                result_text = re.sub(r"ACTION:SCHEDULE_MEETING:\{.*?\}", "", result_text, flags=re.DOTALL).strip() + "\n(Scheduled)"
            except Exception as e:
                logger.error(f"Action failed: {e}")

        elif update_match:
            try:
                data = json.loads(update_match.group(1))
                payload = {}
                if "new_start_time" in data:
                    payload["start_time"] = datetime.fromisoformat(data["new_start_time"].replace("Z", "+00:00"))
                    payload["end_time"] = payload["start_time"] + timedelta(minutes=30)
                if "new_title" in data: payload["title"] = data["new_title"]
                await scheduler.update_event(db, data["event_id"], user_id, payload)
                result_text = re.sub(r"ACTION:UPDATE_MEETING:\{.*?\}", "", result_text, flags=re.DOTALL).strip() + "\n(Updated)"
            except Exception as e:
                logger.error(f"Action failed: {e}")

        elif delete_match:
            try:
                data = json.loads(delete_match.group(1))
                await scheduler.delete_event(db, data["event_id"], user_id)
                result_text = re.sub(r"ACTION:DELETE_MEETING:\{.*?\}", "", result_text, flags=re.DOTALL).strip() + "\n(Deleted)"
            except Exception as e:
                logger.error(f"Action failed: {e}")

    return AIResponse(result=result_text, model_used=model_used)
