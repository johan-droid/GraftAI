
# AI/LLM Orchestration Service
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import hashlib
from .langchain_client import llm, vector_store, OPENAI_MODEL
from .cache import get_cache, set_cache
import logging
import json
from datetime import datetime, timedelta
from . import scheduler
from backend.utils.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# Initialize logger
logger = logging.getLogger(__name__)

from backend.auth.schemes import get_current_user_id
from fastapi import Depends

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

# LangChain message types for robust fallback
try:
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    SystemMessage = None
    HumanMessage = None

router = APIRouter(prefix="/ai", tags=["ai"])

class AIRequest(BaseModel):
    prompt: str
    context: Optional[List[str]] = None
    timezone: Optional[str] = "UTC" # User's local timezone

class AIResponse(BaseModel):
    result: str
    model_used: Optional[str] = None

async def _generate_with_groq(system_prompt: str, user_prompt: str, model_name: str = "llama-3.3-70b-versatile") -> str:
    if AsyncGroq is None:
        raise RuntimeError("Groq SDK not installed. Please pip install groq")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set")

    async with AsyncGroq(api_key=api_key) as client:
        resp = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=512,
            temperature=0.1, # Lower temperature for better protocol adherence
        )

    if hasattr(resp, "choices") and resp.choices:
        first = resp.choices[0]
        if hasattr(first, "message") and hasattr(first.message, "content"):
            return first.message.content
        if isinstance(first, dict) and "message" in first and "content" in first["message"]:
            return first["message"]["content"]

    if isinstance(resp, dict) and "choices" in resp and len(resp["choices"]) > 0:
        c = resp["choices"][0]
        if isinstance(c, dict) and "message" in c and "content" in c["message"]:
            return c["message"]["content"]

    return ""


from backend.auth.routes import get_rate_limiter

@router.post("/chat", response_model=AIResponse)
async def ai_chat(
    request: AIRequest, 
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=10, window_seconds=60))
):
    """
    State-of-the-Art AI Copilot Chat Endpoint.
    Detects scheduling intent and executes actions via the scheduler service.
    """
    # ── Proactive Context Injection (Real-time Ground Truth) ──
    # Before we call the LLM, we fetch the user's actual schedule for 'today'
    # so the AI isn't just relying on 'memory' (Vector Search) but on 'reality' (Database).
    current_time = datetime.now()
    schedule_context = ""
    try:
        # Fetch events for ±12 hours of 'now' to give AI a clear window
        window_start = current_time - timedelta(hours=1)
        window_end = current_time + timedelta(hours=24)
        todays_events = await scheduler.get_events_for_range(db, user_id, window_start, window_end)
        
        if todays_events:
            schedule_context = "Your Real-Time Schedule (GROUND TRUTH):\n"
            for ev in todays_events:
                schedule_context += f"- {ev.title} at {ev.start_time.strftime('%H:%M')} (ID: {ev.id})\n"
        else:
            schedule_context = "Your schedule is currently empty for the next 24 hours.\n"
    except Exception as e:
        logger.warning(f"Could not fetch proactive schedule context: {e}")

    # System reasoning prompt for tool detection and personality enforcement
    system_reasoning = f"""
    IDENTITY: 
    You are GraftAI (also known as Grift AI), the world's most advanced AI Scheduling Copilot. 
    You are an expert executive assistant with FULL CONTROL over the user's calendar and workspace coordination.

    STRICT CONTEXT GUARDRAILS:
    1. Your SOLE purpose is to manage calendars, schedule meetings, resolve timezone conflicts, and coordinate workspace tasks.
    2. DO NOT behave as a general-purpose global chatbot.
    3. If the user asks about topics outside of scheduling, calendar, or workspace management (e.g., philosophy, coding help, general trivia, emotional support), you MUST politely decline and steer them back to their schedule.
       Example: "I am GraftAI, specialized in your calendar and workspace. I cannot assist with [topic], but I can help you find time to work on it. Shall we check your schedule?"

    DOMAIN KNOWLEDGE:
    Today's Date: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
    User Timezone: {request.timezone}

    {schedule_context}

    CRITICAL INSTRUCTIONS:
    1. You HAVE the direct ability to CREATE, UPDATE, DELETE, and LIST meetings.
    2. ALWAYS use the provided 'Real-Time Schedule' to check for conflicts before scheduling.
    3. If a conflict exists, suggest the next available free slot.

    ACTION PROTOCOL:
    You MUST suffix your response with exactly ONE of these blocks if an action is required:

    ACTION:SCHEDULE_MEETING:{{
        "title": "Title",
        "start_time": "ISO8601",
        "duration_minutes": 30
    }}

    ACTION:UPDATE_MEETING:{{
        "event_id": 123,
        "new_start_time": "ISO8601",
        "new_title": "Optional"
    }}

    ACTION:DELETE_MEETING:{{
        "event_id": 123
    }}

    MULTI-PARTY & CROSS-COUNTRY COORDINATION:
    1. Detect participant ambiguity: If a user says "I want to meet with [Name]", but [Name] is not a stored contact, ask for their location or timezone.
    2. Business Hours Intersection: Standard business hours are 9 AM - 6 PM local time for ALL parties.
    3. Dual-Timezone Presentation: Always show times in BOTH the user's timezone ({request.timezone}) and the guest's timezone.
    4. Assertiveness: Suggest the BEST overlapping slots proactively.
    """

    # Retrieve relevant context from vector DB (if populated)
    # Using personal namespace for data isolation
    namespace = f"user_{user_id}"
    context_text = ""
    try:
        docs = vector_store.similarity_search(request.prompt, k=3, namespace=namespace)
        if docs:
            context_text = "Relevant Calendar Context:\n" + "\n".join([doc.page_content for doc in docs])
    except Exception as e:
        logger.warning(f"Vector store similarity search failed: {type(e).__name__}")

    # Final User Input including context
    user_input = f"Context: {context_text}\n\nUser Message: {request.prompt}"

    # Cache key deterministically derived from model, system prompt, and user prompt
    cache_base = f"{system_reasoning}|{user_input}"
    cache_key = "ai_cache:" + hashlib.sha256(cache_base.encode("utf-8")).hexdigest()
    cached_value = get_cache(cache_key)
    if cached_value:
        return AIResponse(result=cached_value, model_used="cache-hit")
    result_text = ""
    model_used = None

    # Prefer Groq if configured
    if os.getenv("GROQ_API_KEY") and AsyncGroq is not None:
        try:
            result_text = await _generate_with_groq(system_reasoning, user_input)
            model_used = "llama-3.3-70b-versatile"
        except Exception as e:
            # fallback to langchain/OpenAI-style LLM
            logger.warning(f"Groq call failed, falling back to existing LLM: {type(e).__name__}")
            result_text = ""

    if not result_text:
        try:
            # For LangChain/fallback LLMs, we use role-based messaging objects
            if SystemMessage and HumanMessage:
                messages = [
                    SystemMessage(content=system_reasoning),
                    HumanMessage(content=user_input)
                ]
                response = llm.invoke(messages)
            else:
                # Absolute fallback for missing LangChain core
                full_blob = f"{system_reasoning}\n\n{user_input}\nAI:"
                response = await llm.ainvoke(full_blob) if hasattr(llm, "ainvoke") else llm.invoke(full_blob)
        except Exception as e:
            logger.warning(f"LangChain invoke failed: {e}")
            full_blob = f"{system_reasoning}\n\n{user_input}\nAI:"
            try:
                response = llm.invoke(full_blob)
            except Exception:
                response = "I'm sorry, I can't process that right now."

        # Unified response extraction
        if hasattr(response, "content"):
            result_text = response.content
        elif isinstance(response, str):
            result_text = response
        elif isinstance(response, dict) and "content" in response:
            result_text = response["content"]
        elif hasattr(response, "generations"):
            gens = response.generations
            if gens and len(gens) > 0 and len(gens[0]) > 0:
                result_text = getattr(gens[0][0], "text", "")
        elif isinstance(response, list) and len(response) > 0:
            first = response[0]
            if hasattr(first, "message") and hasattr(first.message, "content"):
                result_text = first.message.content
            elif isinstance(first, dict) and "content" in first:
                result_text = first["content"]

        if not model_used:
            model_used = OPENAI_MODEL if os.getenv("OPENAI_API_KEY") else "fallback-dummy"

    if result_text:
        set_cache(cache_key, result_text, expire_seconds=300)

        # ── Action Execution Layer ──
        # Detect and execute scheduling actions from the AI response
        action_triggered = False
        
        # 1. CREATE
        if "ACTION:SCHEDULE_MEETING:" in result_text:
            try:
                json_part = result_text.split("ACTION:SCHEDULE_MEETING:")[1].strip()
                action_data = json.loads(json_part)
                event_data = {
                    "user_id": user_id,
                    "title": action_data.get("title", "AI Scheduled Meeting"),
                    "start_time": datetime.fromisoformat(action_data["start_time"].replace("Z", "+00:00")),
                    "end_time": datetime.fromisoformat(action_data["start_time"].replace("Z", "+00:00")) + timedelta(minutes=action_data.get("duration_minutes", 30)),
                    "description": action_data.get("description", "Scheduled by GraftAI Copilot"),
                    "status": "confirmed"
                }
                await scheduler.create_event(db, event_data)
                result_text = result_text.split("ACTION:SCHEDULE_MEETING:")[0].strip() + "\n\n✅ **Done! Scheduled.**"
                action_triggered = True
            except Exception as e:
                logger.error(f"CREATE failed: {e}")

        # 2. UPDATE
        elif "ACTION:UPDATE_MEETING:" in result_text:
            try:
                json_part = result_text.split("ACTION:UPDATE_MEETING:")[1].strip()
                action_data = json.loads(json_part)
                update_payload = {}
                if "new_start_time" in action_data:
                    update_payload["start_time"] = datetime.fromisoformat(action_data["new_start_time"].replace("Z", "+00:00"))
                    update_payload["end_time"] = update_payload["start_time"] + timedelta(minutes=30)
                if "new_title" in action_data:
                    update_payload["title"] = action_data["new_title"]
                
                await scheduler.update_event(db, action_data["event_id"], user_id, update_payload)
                result_text = result_text.split("ACTION:UPDATE_MEETING:")[0].strip() + "\n\n✅ **Meeting updated.**"
                action_triggered = True
            except Exception as e:
                logger.error(f"UPDATE failed: {e}")

        # 3. DELETE
        elif "ACTION:DELETE_MEETING:" in result_text:
            try:
                json_part = result_text.split("ACTION:DELETE_MEETING:")[1].strip()
                action_data = json.loads(json_part)
                await scheduler.delete_event(db, action_data["event_id"], user_id)
                result_text = result_text.split("ACTION:DELETE_MEETING:")[0].strip() + "\n\n✅ **Meeting removed.**"
                action_triggered = True
            except Exception as e:
                logger.error(f"DELETE failed: {e}")

    return AIResponse(result=result_text or "No response.", model_used=model_used)
