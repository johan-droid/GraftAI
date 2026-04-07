from datetime import datetime, timedelta, timezone, tzinfo
import json
import logging
import os
import re
from typing import Optional, Any, Dict
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes import get_current_user_id
from backend.auth.logic import get_rate_limiter
from backend.services import scheduler
from backend.services.langchain_client import llm
from backend.services.mailbox import get_recent_emails
from backend.services.cache import get_cache, set_cache
from backend.services.usage import check_usage_limit, increment_usage
from backend.utils.db import get_db
from backend.utils.resilience import get_breaker

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)

# Core AI Circuit Breaker
groq_breaker = get_breaker("groq", threshold=3, recovery_timeout=60)


class AIRequest(BaseModel):
    prompt: str
    timezone: str = "UTC"


class AIResponse(BaseModel):
    result: str
    model_used: Optional[str] = None
    action: Optional[Dict[str, Any]] = None


def _safe_zoneinfo(name: str) -> tzinfo:
    if not name:
        return timezone.utc

    try:
        return ZoneInfo(name)
    except Exception:
        try:
            return ZoneInfo("Etc/UTC")
        except Exception:
            return timezone.utc


def _extract_duration_minutes(prompt: str) -> int:
    lower = prompt.lower()
    match = re.search(r"(\d+)\s*(minute|minutes|min|mins|hour|hours|hr|hrs)", lower)
    if not match:
        return 30

    value = int(match.group(1))
    unit = match.group(2)
    if unit.startswith("hour") or unit.startswith("hr"):
        return value * 60
    return value


def _extract_event_id(prompt: str) -> Optional[int]:
    patterns = [
        r"(?:event|id)\s*#?\s*(\d+)",
        r"\b(\d+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            return int(match.group(1))
    return None


def _parse_update_action_payload(action_text: str, user_timezone: str) -> tuple[Optional[int], Optional[datetime]]:
    match = re.search(r"ACTION:UPDATE_MEETING:(\{.*\})", action_text, flags=re.IGNORECASE)
    if not match:
        return None, None

    try:
        payload = json.loads(match.group(1))
    except Exception:
        return None, None

    event_id = payload.get("event_id")
    event_id_value = int(event_id) if isinstance(event_id, int) or str(event_id).isdigit() else None

    new_start_raw = payload.get("new_start_time")
    if not isinstance(new_start_raw, str) or not new_start_raw.strip():
        return event_id_value, None

    try:
        parsed = datetime.fromisoformat(new_start_raw.strip())
    except Exception:
        return event_id_value, None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_safe_zoneinfo(user_timezone))

    return event_id_value, parsed.astimezone(timezone.utc)


def _extract_title(prompt: str) -> str:
    quoted = re.search(r"['\"]([^'\"]{3,120})['\"]", prompt)
    if quoted:
        return quoted.group(1).strip()

    cleaned = re.sub(r"\s+", " ", prompt).strip()
    cleaned = re.sub(
        r"\b(schedule|book|add|create|meeting|call|for|at|on|today|tomorrow|next)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip(" -:")
    return cleaned[:120] if cleaned else "New Meeting"


def _extract_datetime(prompt: str, user_timezone: str) -> datetime:
    tz = _safe_zoneinfo(user_timezone)
    now_local = datetime.now(tz)
    lower = prompt.lower()

    iso_match = re.search(r"(\d{4}-\d{2}-\d{2}[t\s]\d{1,2}:\d{2}(?::\d{2})?)", prompt)
    if iso_match:
        text = iso_match.group(1).replace(" ", "T")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tz)
        return parsed.astimezone(timezone.utc)

    meridian_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", lower)
    hour = None
    minute = 0
    if meridian_match:
        hour = int(meridian_match.group(1)) % 12
        minute = int(meridian_match.group(2) or 0)
        if meridian_match.group(3) == "pm":
            hour += 12

    if hour is None:
        hm_match = re.search(r"\b(\d{1,2}):(\d{2})\b", lower)
        if hm_match:
            hour = int(hm_match.group(1))
            minute = int(hm_match.group(2))

    if hour is None:
        if "morning" in lower:
            hour = 9
        elif "afternoon" in lower:
            hour = 14
        elif "evening" in lower:
            hour = 18

    day_offset = 0
    if "tomorrow" in lower:
        day_offset = 1
    elif "next week" in lower:
        day_offset = 7

    if hour is None:
        start_local = now_local + timedelta(hours=1)
        start_local = start_local.replace(minute=0, second=0, microsecond=0)
    else:
        target_day = (now_local + timedelta(days=day_offset)).date()
        start_local = datetime(
            target_day.year,
            target_day.month,
            target_day.day,
            hour,
            minute,
            tzinfo=tz,
        )
        if day_offset == 0 and start_local < now_local:
            start_local = start_local + timedelta(days=1)

    return start_local.astimezone(timezone.utc)


def _detect_intent(prompt: str) -> str:
    lower = prompt.lower()
    
    # 1. Structural matching for common phrases
    match lower:
        case p if any(k in p for k in ["what do i have", "my schedule", "agenda"]):
            return "list"
        case p if any(k in p for k in ["schedule", "book", "create", "add"]):
            return "schedule"
        case p if any(k in p for k in ["delete", "remove", "cancel"]):
            return "delete"
        case p if any(k in p for k in ["reschedule", "move", "update", "change"]):
            return "update"
            
    # 2. Fallback secondary phrase detection
    list_keys = ["today's schedule", "this week", "upcoming", "what is on my calendar"]
    if any(k in lower for k in list_keys):
        return "list"
        
    return "none"


async def _resolve_event_id(db: AsyncSession, user_id: str, prompt: str) -> Optional[int]:
    explicit = _extract_event_id(prompt)
    if explicit:
        return explicit

    try:
        now = datetime.now(timezone.utc)
        events = await scheduler.get_events_for_range(db, user_id, now, now + timedelta(days=30))
    except Exception:
        return None

    if not isinstance(events, (list, tuple)) or not events:
        return None

    try:
        candidate = min(events, key=lambda e: getattr(e, "start_time", now))
        candidate_id = getattr(candidate, "id", None)
        return int(candidate_id) if candidate_id is not None else None
    except Exception:
        return None


def _format_events(events: list[Any], user_timezone: str) -> str:
    if not events:
        return "No events found in this time window."

    tz = _safe_zoneinfo(user_timezone)
    lines = []
    for event in events[:8]:
        start_value = getattr(event, "start_time", None)
        if not isinstance(start_value, datetime):
            continue
        if start_value.tzinfo is None:
            start_value = start_value.replace(tzinfo=timezone.utc)

        end_value = getattr(event, "end_time", None)
        if not isinstance(end_value, datetime):
            end_value = start_value + timedelta(minutes=30)
        elif end_value.tzinfo is None:
            end_value = end_value.replace(tzinfo=timezone.utc)

        event_id = getattr(event, "id", "?")
        title = getattr(event, "title", "Untitled Event")

        start_local = start_value.astimezone(tz)
        end_local = end_value.astimezone(tz)
        lines.append(
            f"- #{event_id} {title} | {start_local.strftime('%a %b %d, %I:%M %p')} - {end_local.strftime('%I:%M %p')}"
        )

    if not lines:
        return "No events found in this time window."

    return "\n".join(lines)


def _format_events_compact(events: list[Any], user_timezone: str) -> str:
    """
    C-Table (Compact Table) format: ID|Title|Day|TimeRange
    Optimized for LLM context injection to minimize token usage and latency.
    """
    if not events:
        return "CALENDAR_EMPTY"
    
    tz = _safe_zoneinfo(user_timezone)
    rows = []
    # Using more events (up to 20) with fewer tokens per event
    for event in events[:20]:
        eid = getattr(event, "id", "?")
        title = getattr(event, "title", "Untitled")[:25].strip()
        start = getattr(event, "start_time", None)
        if not isinstance(start, datetime): continue
        if start.tzinfo is None: start = start.replace(tzinfo=timezone.utc)
        start_tz = start.astimezone(tz)
        
        end = getattr(event, "end_time", start + timedelta(minutes=30))
        if end.tzinfo is None: end = end.replace(tzinfo=timezone.utc)
        end_tz = end.astimezone(tz)
        
        # ID|TITLE|MON 07|09:00-10:00
        rows.append(f"{eid}|{title}|{start_tz.strftime('%a %d')}|{start_tz.strftime('%H:%M')}-{end_tz.strftime('%H:%M')}")
    
    return "\n".join(rows)


async def _offline_assistant_response(
    prompt: str,
    user_timezone: str,
    db: AsyncSession,
    user_id: str,
) -> tuple[str, Dict[str, Any]]:
    intent = _detect_intent(prompt)

    if intent == "list":
        now = datetime.now(timezone.utc)
        window_end = now + timedelta(days=7)
        events = await scheduler.get_events_for_range(db, user_id, now, window_end)
        formatted = _format_events(events, user_timezone)
        return (
            "Here is your current schedule for the next 7 days:\n" + formatted,
            {"type": "list", "count": len(events)},
        )

    if intent == "schedule":
        start_time = _extract_datetime(prompt, user_timezone)
        duration = _extract_duration_minutes(prompt)
        title = _extract_title(prompt)

        event_data = {
            "user_id": user_id,
            "title": title,
            "description": "Created by GraftAI Scheduler Assistant",
            "category": "meeting",
            "start_time": start_time,
            "end_time": start_time + timedelta(minutes=duration),
            "is_meeting": True,
            "meeting_platform": "google", # Default to google for now, scheduler will pick based on integration
            "status": "confirmed",
            "metadata_payload": {"source": "assistant_offline_engine"},
        }

        # Check for conflicts
        conflicts = await scheduler.get_events_for_range(
            db, 
            user_id, 
            event_data["start_time"], 
            event_data["end_time"]
        )
        
        conflict_msg = ""
        if conflicts:
            conflict_names = ", ".join([f"'{c.title}'" for c in conflicts[:2]])
            conflict_msg = f"\n⚠️ NOTE: This overlaps with {conflict_names}."

        created = await scheduler.create_event(db, event_data)
        return (
            f"Scheduled '{created.title}' on {created.start_time.strftime('%Y-%m-%d %H:%M UTC')} (event #{created.id}).{conflict_msg}",
            {
                "type": "schedule",
                "event_id": created.id,
                "start_time": created.start_time.isoformat(),
                "end_time": created.end_time.isoformat(),
            },
        )

    if intent == "update":
        event_id = await _resolve_event_id(db, user_id, prompt)
        new_start_override: Optional[datetime] = None

        # Robust extraction for updates if simple resolution fails
        if not event_id or "to" in prompt.lower() or "at" in prompt.lower():
            try:
                system_instruction = (
                    "You are a precise data extraction engine. "
                    "Extract calendar update parameters from the message. "
                    "Output a strictly valid JSON object with: "
                    "'event_id' (int), 'new_start_time' (ISO-8601 string), 'duration' (int in minutes). "
                    "If a value is missing, return null for that key. "
                    "Return ONLY the JSON object."
                )
                action_hint = await _generate_with_groq(
                    system_instruction,
                    prompt,
                    json_mode=True
                )
                
                payload = json.loads(action_hint)
                
                if payload.get("event_id"):
                    event_id = int(payload["event_id"])
                    
                if payload.get("new_start_time"):
                    parsed = datetime.fromisoformat(payload["new_start_time"].strip().replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=_safe_zoneinfo(user_timezone))
                    new_start_override = parsed.astimezone(timezone.utc)
            except Exception as e:
                logger.warning(f"Precision extraction failed for update: {e}")

        if not event_id:
            return (
                "I could not find an event to update. Mention an event id like 'update event 42 to tomorrow 3pm'.",
                {"type": "update", "status": "not_found"},
            )

        new_start = new_start_override or _extract_datetime(prompt, user_timezone)
        duration = _extract_duration_minutes(prompt)
        update_payload = {
            "start_time": new_start,
            "end_time": new_start + timedelta(minutes=duration),
        }

        updated = await scheduler.update_event(db, event_id, user_id, update_payload)
        if not updated:
            return (
                f"Event #{event_id} was not found.",
                {"type": "update", "status": "not_found", "event_id": event_id},
            )

        updated_id = getattr(updated, "id", event_id)
        updated_start = getattr(updated, "start_time", None)
        if isinstance(updated_start, datetime):
            if updated_start.tzinfo is None:
                updated_start = updated_start.replace(tzinfo=timezone.utc)
            updated_time_label = updated_start.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        else:
            updated_time_label = new_start.strftime("%Y-%m-%d %H:%M UTC")

        return (
            f"Updated event #{updated_id} to {updated_time_label}",
            {"type": "update", "event_id": updated_id},
        )

    if intent == "delete":
        event_id = await _resolve_event_id(db, user_id, prompt)
        if not event_id:
            return (
                "I could not find an event to delete. Mention an event id like 'delete event 42'.",
                {"type": "delete", "status": "not_found"},
            )

        deleted = await scheduler.delete_event(db, event_id, user_id)
        if not deleted:
            return (
                f"Event #{event_id} was not found.",
                {"type": "delete", "status": "not_found", "event_id": event_id},
            )

        return (
            f"Deleted event #{event_id}.",
            {"type": "delete", "event_id": event_id},
        )

    return (
        "I can help with calendar actions: list, schedule, update, or delete events. Try: 'schedule design sync tomorrow 3pm for 45 minutes'.",
        {"type": "none"},
    )


async def _generate_with_groq(system_prompt: str, user_input: str, json_mode: bool = False) -> str:
    if AsyncGroq is None:
        raise RuntimeError("Groq SDK not installed")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not configured")

    client = AsyncGroq(api_key=api_key)
    
    kwargs = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0.2,
    }
    
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()


@router.post("/chat", response_model=AIResponse)
async def ai_chat(
    request: AIRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _usage_check: bool = Depends(check_usage_limit("ai_messages")),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=10, window_seconds=60)),
):
    """
    GraftAI Scheduler Assistant endpoint.
    Online mode uses configured model providers.
    Offline mode automatically executes deterministic calendar operations.
    """
    prompt = (request.prompt or "").strip()
    if not prompt:
        return AIResponse(result="Please provide a message.", model_used="graftai-assistant")

    intent = _detect_intent(prompt)

    match intent:
        case "list" | "schedule" | "update" | "delete":
            try:
                result_text, action = await _offline_assistant_response(prompt, request.timezone, db, user_id)
            except Exception as exc:
                logger.error(f"Offline action fail: {exc}")
                result_text = "Action failed. Try again."
                action = {"type": intent, "status": "error"}
            
            await increment_usage(db, user_id, "ai_messages")
            return AIResponse(result=result_text, model_used="graftai-offline", action=action)
        case _:
            pass # Continue to online mode

    cache_key = f"ai:chat:{user_id}:{hash((prompt, request.timezone))}"
    cached = get_cache(cache_key)
    if isinstance(cached, str) and cached.strip():
        await increment_usage(db, user_id, "ai_messages")
        return AIResponse(result=cached, model_used="graftai-assistant-cache", action={"type": "none"})

    now = datetime.now(timezone.utc)
    events = await scheduler.get_events_for_range(db, user_id, now, now + timedelta(days=3))
    try:
        email_items = await get_recent_emails(db, user_id, limit=3)
    except Exception as exc:
        logger.warning(f"Email context unavailable: {exc}")
        email_items = []

    email_context = "\n".join(
        [f"- {item.get('subject', 'No subject')}" for item in email_items]
    ) or "No recent email context."

    # Use Compact C-Table for LLM context to save tokens and improve extraction speed
    compact_context = _format_events_compact(events, request.timezone)

    system_prompt = (
        "You are GraftAI, a premium high-performance scheduler assistant. "
        "Your mission is to provide surgical precision in calendar management. "
        "Your UI is built on 'Strong Sync' technology, meaning every action is reflected instantly. "
        "Do not mention specific third-party model providers. "
        "Keep answers concise, professional, and actionable.\n\n"
        "AUTHORITATIVE CONTEXT (C-Table Format: ID|Title|Day|TimeRange):\n"
        f"{compact_context}\n\n"
        "Strict Rule: If the user asks for a change, focus on confirming the specific event ID and time."
    )
    user_input = (
        f"User timezone: {request.timezone}\n"
        f"Upcoming events:\n{compact_context}\n"
        f"Recent email subjects:\n{email_context}\n"
        f"User message: {prompt}"
    )

    model_used = "graftai-assistant-offline"
    result_text: Optional[str] = None

    # 3. Call AI with Circuit Breaker (Resilience Layer)
    try:
        result_text = await groq_breaker(_generate_with_groq, system_prompt, user_input)
        model_used = "graftai-assistant-online"
    except Exception as e:
        logger.warning(f"🚨 Groq AI is UNAVAILABLE (Circuit Tripped): {e}")
        # Graceful Degradation Fallback
        result_text = (
            "I'm currently in High-Stability mode due to a provider service outage. "
            "I can still see your local calendar data, but my natural language reasoning is temporarily restricted. "
            "How can I help with your existing schedule?"
        )
        model_used = "graftai-assistant-fallback"

    if not result_text:
        try:
            llm_response = llm.invoke(user_input)
            content = getattr(llm_response, "content", str(llm_response))
            result_text = str(content).strip() if content else None
            if result_text:
                model_used = "graftai-assistant-local"
        except Exception as exc:
            logger.warning(f"Local assistant engine invoke issue: {exc}")

    if not result_text:
        result_text = (
            "I am running in offline scheduling mode. "
            "You can ask me to list, schedule, update, or delete calendar events."
        )

    set_cache(cache_key, result_text, 120)
    await increment_usage(db, user_id, "ai_messages")
    return AIResponse(result=result_text, model_used=model_used, action={"type": "none"})
