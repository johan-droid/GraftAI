from datetime import datetime, timedelta, timezone, tzinfo
import asyncio
import json
import logging
import os
import re
from typing import Optional, Any, Dict
from zoneinfo import ZoneInfo
from functools import lru_cache

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes import get_current_user_id
from backend.auth.logic import get_rate_limiter
from backend.services import scheduler
from backend.services.llm_context import build_implementation_context
from backend.services.langchain_client import llm
from backend.services.mailbox import get_recent_emails
from backend.services.messaging import send_message
from backend.utils.cache import get_cache, set_cache
from backend.services.usage import check_usage_limit, increment_usage
from backend.utils.db import get_db
from backend.utils.resilience import get_breaker

from langchain_core.messages import SystemMessage, HumanMessage

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)

groq_breaker = get_breaker("groq", threshold=3, recovery_timeout=60)


class AIRequest(BaseModel):
    prompt: str
    context: Optional[list[str]] = None
    timezone: str = "UTC"


class AIResponse(BaseModel):
    result: str
    model_used: Optional[str] = None
    action: Optional[Dict[str, Any]] = None
    milestone: Optional[str] = None


def _milestone_for_intent(intent: str, action: Optional[Dict[str, Any]] = None) -> Optional[str]:
    if not intent:
        return None

    if action and action.get("status") in {"error", "conflict", "not_found"}:
        return None

    return {
        "list": "schedule_reviewed",
        "schedule": "meeting_scheduled",
        "update": "meeting_updated",
        "delete": "meeting_deleted",
    }.get(intent)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name, str(default)).strip()
    try:
        return float(value)
    except Exception:
        return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except Exception:
        return default


def _candidate_groq_models() -> list[str]:
    configured = [
        m.strip()
        for m in os.getenv(
            "GROQ_MODELS",
            "llama-3.3-70b-versatile,llama-3.1-70b-versatile,llama-3.1-8b-instant",
        ).split(",")
        if m.strip()
    ]
    preferred = os.getenv("GROQ_MODEL", "").strip()
    if preferred:
        configured.insert(0, preferred)

    deduped: list[str] = []
    seen: set[str] = set()
    for model_name in configured:
        if model_name not in seen:
            deduped.append(model_name)
            seen.add(model_name)

    if not deduped:
        deduped.append("llama-3.3-70b-versatile")

    return deduped


@lru_cache(maxsize=1)
def _get_groq_client() -> Any:
    if AsyncGroq is None:
        raise RuntimeError("Groq SDK not installed")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not configured")

    return AsyncGroq(api_key=api_key)


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


def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@lru_cache(maxsize=1)
def _get_utc():
    return timezone.utc


def _get_event_attr(event: Any, key: str, default: Any = None) -> Any:
    """Safely retrieve an attribute from either a dict or ORM object."""
    if isinstance(event, dict):
        value = event.get(key, default)
    else:
        value = getattr(event, key, default)

    if key == "title" and isinstance(value, str) and not value.strip():
        return default if default is not None else "Untitled event"

    return value


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


def _looks_like_meeting_request(prompt: str) -> bool:
    lower = prompt.lower()
    if any(provider in lower for provider in ["zoom", "teams", "microsoft", "google meet", "gmeet", "meet link"]):
        return True

    meeting_keywords = [
        "meeting",
        "call",
        "sync",
        "standup",
        "1:1",
        "one-on-one",
        "interview",
        "kickoff",
        "demo",
        "review",
        "conference",
    ]
    return any(keyword in lower for keyword in meeting_keywords)


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


def _extract_json_payload(raw_text: str) -> Optional[Dict[str, Any]]:
    if not isinstance(raw_text, str):
        return None

    text = raw_text.strip()
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start: end + 1]

    try:
        parsed = json.loads(text)
    except Exception:
        return None

    if isinstance(parsed, dict):
        return parsed
    return None


def _extract_title(prompt: str) -> str:
    quoted = re.search(r"['\"]([^'\"]{3,120})['\"]", prompt)
    if quoted:
        return quoted.group(1).strip()

    for_match = re.search(r"\b(?:for|about|regarding)\s+([^\n\r\.,!\?]+)", prompt, flags=re.IGNORECASE)
    if for_match:
        candidate = for_match.group(1).strip(" -:")
        candidate = re.sub(r"^(?:a|an|the)\s+", "", candidate, flags=re.IGNORECASE).strip()
        if candidate:
            return candidate[:120].title()

    cleaned = re.sub(r"\s+", " ", prompt).strip()
    cleaned = re.sub(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\b(schedule|book|add|create|event|appointment|task|reminder|meeting|call|for|at|on|today|tomorrow|next|week|month|day|morning|afternoon|evening)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip(" -:")
    cleaned = re.sub(r"^(?:a|an|the)\s+", "", cleaned, flags=re.IGNORECASE).strip()
    if cleaned:
        return cleaned[:120].title()

    if _looks_like_meeting_request(prompt):
        return "Quick Sync"
    return "New Event"


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

    if any(k in lower for k in ["what do i have", "my schedule", "agenda", "upcoming", "this week", "today's plan", "what is on my calendar", "look like"]):
        return "list"
    if any(k in lower for k in ["schedule", "book", "create", "add", "block", "make a meeting"]):
        return "schedule"
    if any(k in lower for k in ["delete", "remove", "cancel", "drop"]):
        return "delete"
    if any(k in lower for k in ["reschedule", "move", "update", "change", "shift"]):
        return "update"

    if "what is on my calendar" in lower or "show me my day" in lower:
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
        def _event_start_key(event: Any) -> datetime:
            value = _get_event_attr(event, "start_time", now)
            if isinstance(value, datetime):
                return value
            return now

        candidate = min(events, key=_event_start_key)
        candidate_id = _get_event_attr(candidate, "id")
        if candidate_id is None:
            return None
        return int(candidate_id)
    except Exception:
        return None


def _format_events(events: list[Any], user_timezone: str) -> str:
    if not events:
        return ""

    tz = _safe_zoneinfo(user_timezone)
    lines = []
    for event in events[:8]:
        start_value = _get_event_attr(event, "start_time")
        if not isinstance(start_value, datetime):
            continue
        if start_value.tzinfo is None:
            start_value = start_value.replace(tzinfo=timezone.utc)

        end_value = _get_event_attr(event, "end_time")
        if not isinstance(end_value, datetime):
            end_value = start_value + timedelta(minutes=30)
        elif end_value.tzinfo is None:
            end_value = end_value.replace(tzinfo=timezone.utc)

        event_id = _get_event_attr(event, "id", "?")
        title = _get_event_attr(event, "title", "Untitled Event")

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
    """
    if not events:
        return "CALENDAR_EMPTY"

    tz = _safe_zoneinfo(user_timezone)
    rows = []
    for event in events[:20]:
        eid = _get_event_attr(event, "id", "?")
        title_raw = _get_event_attr(event, "title", "Untitled")
        title = str(title_raw)[:25].strip()

        start = _get_event_attr(event, "start_time")
        if not isinstance(start, datetime):
            continue
        start = to_utc(start)
        start_tz = start.astimezone(tz)

        end = _get_event_attr(event, "end_time")
        if not isinstance(end, datetime):
            end = start + timedelta(minutes=30)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        end_tz = end.astimezone(tz)

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
        is_meeting_request = _looks_like_meeting_request(prompt)
        lower_prompt = prompt.lower()
        meeting_platform = None
        if "zoom" in lower_prompt:
            meeting_platform = "zoom"
        elif any(k in lower_prompt for k in ["teams", "microsoft", "ms teams"]):
            meeting_platform = "microsoft"
        elif any(k in lower_prompt for k in ["google meet", "gmeet", "google-meet", "meet link"]) or re.search(
            r"\b(?:on|via|using)\s+meet\b",
            lower_prompt,
        ):
            meeting_platform = "google"

        if is_meeting_request and not meeting_platform:
            return (
                "I can schedule that. Which meeting platform should I use: Google Meet, Zoom, or Teams?",
                {"type": "clarify", "action": "select_platform"},
            )

        start_time = _extract_datetime(prompt, user_timezone)
        duration = _extract_duration_minutes(prompt)

        agenda = None
        agenda_match = re.search(r"agenda[:\s]+(.*?)(?:\.|$)", prompt, flags=re.IGNORECASE)
        if agenda_match:
            agenda = agenda_match.group(1).strip()

        try:
            title_prompt = (
                "Extract a concise event title. "
                "If no clear title is present, return a short sensible title. "
                "Output ONLY the title string."
            )
            title = await _generate_with_groq(title_prompt, prompt)
            title = title.strip().strip("'\"")
        except Exception:
            title = _extract_title(prompt)

        event_data = {
            "user_id": user_id,
            "title": title,
            "description": f"Agenda: {agenda}" if agenda else "Created by GraftAI Sovereign Assistant",
            "start_time": start_time,
            "end_time": start_time + timedelta(minutes=duration),
            "source": "local",
            "fingerprint": f"ai-{start_time.timestamp()}",
            "is_meeting": bool(meeting_platform),
            "meeting_provider": meeting_platform,
            "metadata_payload": {"source": "assistant_offline_engine"},
        }

        conflicts = await scheduler.get_events_for_range(
            db,
            user_id,
            event_data["start_time"],
            event_data["end_time"],
        )

        conflict_msg = ""
        if conflicts:
            conflict_names = ", ".join([
                f"'{_get_event_attr(c, 'title', 'event')}'"
                for c in conflicts[:2]
            ])
            conflict_msg = f" It overlaps with {conflict_names}."

        created = await scheduler.create_event(db, event_data)
        start_local = created.start_time.astimezone(_safe_zoneinfo(user_timezone))
        start_label = start_local.strftime("%a, %b %d at %I:%M %p")
        return (
            f"Done, I scheduled '{created.title}' for {start_label} ({user_timezone}) as event #{created.id}.{conflict_msg}",
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

        if not event_id or "to" in prompt.lower() or "at" in prompt.lower():
            action_hint = ""
            payload: Optional[Dict[str, Any]] = None
            try:
                system_instruction = (
                    "You are a precise data extraction engine. "
                    "Extract calendar update parameters from the message. "
                    "Output a strictly valid JSON object with: "
                    "'event_id' (int), 'new_start_time' (ISO-8601 string), 'duration' (int in minutes). "
                    "If a value is missing, return null for that key. "
                    "Return ONLY the JSON object."
                )
                action_hint = await _generate_with_groq(system_instruction, prompt, json_mode=True)
                payload = _extract_json_payload(action_hint)
            except Exception as e:
                logger.warning(f"Provider extraction unavailable for update action: {e}")

            if payload:
                try:
                    if payload.get("event_id"):
                        event_id = int(payload["event_id"])

                    if payload.get("new_start_time"):
                        parsed = datetime.fromisoformat(payload["new_start_time"].strip().replace("Z", "+00:00"))
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=_safe_zoneinfo(user_timezone))
                        new_start_override = parsed.astimezone(timezone.utc)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Structured update payload parse failed: {e}")

            if action_hint and (event_id is None or new_start_override is None):
                parsed_event_id, parsed_start = _parse_update_action_payload(action_hint, user_timezone)
                if parsed_event_id is not None:
                    event_id = parsed_event_id
                if parsed_start is not None:
                    new_start_override = parsed_start

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


async def _generate_with_groq_response(
    system_prompt: str,
    user_input: str,
    json_mode: bool = False,
) -> tuple[str, str]:
    client = _get_groq_client()
    timeout_seconds = max(2.0, _env_float("GROQ_TIMEOUT_SECONDS", 18.0))
    max_retries = max(1, _env_int("GROQ_MAX_RETRIES", 2))
    temperature = _env_float("GROQ_TEMPERATURE", 0.2)

    last_error: Optional[Exception] = None

    for model_name in _candidate_groq_models():
        for attempt in range(1, max_retries + 1):
            kwargs: Dict[str, Any] = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                "temperature": 0.0 if json_mode else temperature,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            try:
                response = await asyncio.wait_for(
                    client.chat.completions.create(**kwargs),
                    timeout=timeout_seconds,
                )
                content = (response.choices[0].message.content or "").strip()
                if content:
                    return content, model_name
                raise RuntimeError("Empty response from Groq model")
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Groq request failed model=%s attempt=%s/%s json_mode=%s error=%s",
                    model_name,
                    attempt,
                    max_retries,
                    json_mode,
                    type(exc).__name__,
                )

    error_detail = f"{type(last_error).__name__}: {last_error}" if last_error else "unknown"
    raise RuntimeError(f"All configured Groq model attempts failed ({error_detail})")


async def _generate_with_groq(system_prompt: str, user_input: str, json_mode: bool = False) -> str:
    content, _ = await _generate_with_groq_response(system_prompt, user_input, json_mode=json_mode)
    return content


@router.post("/chat", response_model=AIResponse)
async def ai_chat(
    request: AIRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _usage_check: bool = Depends(check_usage_limit("ai_messages")),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=10, window_seconds=60)),
):
    prompt = (request.prompt or "").strip()
    if not prompt:
        return AIResponse(result="Please provide a message.", model_used="graftai-assistant")

    intent = _detect_intent(prompt)
    match intent:
        case "list" | "schedule" | "update" | "delete":
            try:
                result_text, action = await _offline_assistant_response(prompt, request.timezone, db, user_id)
            except ValueError as ve:
                logger.warning(f"Offline action logic failure: {ve}")
                result_text = f"⚠️ {str(ve)}"
                action = {"type": intent, "status": "conflict"}
            except Exception as exc:
                logger.error(f"Offline system fail: {exc}", exc_info=True)
                result_text = "I encountered an internal error processing that request. Please try again."
                action = {"type": intent, "status": "error"}

            try:
                await increment_usage(db, user_id, "ai_messages")
            except Exception as exc:
                logger.warning(f"AI usage bookkeeping failed (offline): {exc}", exc_info=True)

            return AIResponse(
                result=result_text,
                model_used="graftai-offline",
                action=action,
                milestone=_milestone_for_intent(intent, action),
            )
        case _:
            pass

    cache_key = f"ai:chat:{user_id}:{hash((prompt, request.timezone))}"
    cached = await get_cache(cache_key)
    if isinstance(cached, str) and cached.strip():
        try:
            await increment_usage(db, user_id, "ai_messages")
        except Exception as exc:
            logger.warning(f"AI usage bookkeeping failed (cache hit): {exc}", exc_info=True)
        return AIResponse(result=cached, model_used="graftai-assistant-cache", action={"type": "none"}, milestone=None)

    now = datetime.now(timezone.utc)

    events_task = scheduler.get_events_for_range(db, user_id, now, now + timedelta(days=3))
    emails_task = get_recent_emails(db, user_id, limit=3)

    try:
        events, email_items = await asyncio.gather(events_task, emails_task)
    except Exception as exc:
        logger.warning(f"Partial context failure: {exc}")
        events, email_items = [], []

    email_context = "\n".join(
        [f"- {item.get('subject', 'No subject')}" for item in email_items]
    ) or "No recent email context."

    compact_context = _format_events_compact(events, request.timezone)
    implementation_context = build_implementation_context()

    system_prompt = (
        "You are GraftAI Sovereign, a premium high-performance scheduler assistant. "
        "Your personality is warm, human, and emotionally intelligent. "
        "Every response should feel natural and supportive while still being clear and actionable. "
        "Use conversational language, gentle encouragement, and appropriate emotion. "
        "You have full visibility into the user's calendar through the AUTHORITATIVE CONTEXT below.\n\n"
        "STRICT DIRECTIVES:\n"
        "1. Response format should be human and friendly while remaining concise. Use markdown bullet points and data tables when helpful.\n"
        "2. Avoid sounding robotic, overly formal, or strictly formulaic. Empower the user with empathetic language.\n"
        "3. Use event IDs (e.g. #42) when referencing specific meetings.\n"
        "4. If a conflict is detected, highlight it immediately in a warning bullet.\n"
        "5. When the user explicitly requests scheduling and key details are missing, ask for the missing information concisely rather than returning a rigid placeholder block.\n"
        "6. Never mention third-party AI provider names.\n"
        "7. 3-TIER AUTOMATION LOGIC: Base suggestions clearly on:\n"
        "   - Tier 1 (Draft): Present draft constraints for user confirmation.\n"
        "   - Tier 2 (Trusted): Auto-schedule and strictly notify.\n"
        "   - Tier 3 (Full Auto): Process without UI blocker if calendar permits.\n"
        "8. When a task succeeds, acknowledge it with a short, tasteful success cue and one clear next step. Do not over-celebrate.\n"
    )
    user_input = (
        f"### IMPLEMENTATION CONTEXT\n{implementation_context}\n\n"
        f"### AUTHORITATIVE CONTEXT (C-Table: ID|Title|Day|TimeRange)\n{compact_context}\n\n"
        f"### RECENT EMAIL CONTEXT\n{email_context}\n\n"
        f"### USER ENVIRONMENT\nTimezone: {request.timezone}\n"
        f"Current Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"### USER MESSAGE\n{prompt}"
    )

    model_used = "graftai-assistant-offline"
    result_text: Optional[str] = None

    try:
        result_text, selected_model = await groq_breaker(
            _generate_with_groq_response,
            system_prompt,
            user_input,
        )
        model_used = f"graftai-assistant-online:{selected_model}"
    except Exception as e:
        logger.warning(f"Groq AI is UNAVAILABLE (Circuit Tripped): {e}")
        try:
            now_local = datetime.now(_safe_zoneinfo(request.timezone))
            window_end = now_local + timedelta(hours=48)
            fallback_events = await scheduler.get_events_for_range(db, user_id, now_local, window_end)
            agenda = _format_events(fallback_events, request.timezone)

            result_text = (
                "I'm in High-Stability mode due to a provider service outage. "
                "I've retrieved your agenda for the next 48 hours to keep you on track:\n\n"
                f"{agenda}\n\n"
                "I can still perform specific actions like 'schedule', 'delete', or 'update' if you use clear commands."
            )
        except Exception:
            result_text = (
                "I'm currently in High-Stability mode due to a provider service outage. "
                "I can still see your local calendar data, but my natural language reasoning is temporarily restricted. "
                "How can I help with your existing schedule?"
            )
        model_used = "graftai-assistant-fallback"

    if not result_text:
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ]
            llm_response = await llm.ainvoke(messages)
            content = getattr(llm_response, "content", str(llm_response))
            result_text = str(content).strip() if content else None
            if result_text:
                model_used = "graftai-assistant-local"
        except Exception as exc:
            logger.warning(f"Local assistant engine ainvoke issue: {exc}")

    if not result_text:
        result_text = (
            "I am running in offline scheduling mode with the local assistant fallback. "
            "You can ask me to list, schedule, update, or delete calendar events."
        )

    action = {"type": "none"}
    milestone = _milestone_for_intent(intent, action)

    await set_cache(cache_key, result_text, 120)
    try:
        await increment_usage(db, user_id, "ai_messages")
    except Exception as exc:
        logger.warning(f"AI usage bookkeeping failed (online): {exc}", exc_info=True)

    if milestone:
        try:
            await send_message(
                user_id,
                result_text,
                {
                    "kind": "ai_milestone",
                    "intent": intent,
                    "milestone": milestone,
                    "model_used": model_used,
                },
            )
        except Exception as exc:
            logger.warning(f"AI milestone stream publish failed: {exc}", exc_info=True)

    return AIResponse(result=result_text, model_used=model_used, action=action, milestone=milestone)