from functools import lru_cache
from pathlib import Path


DEFAULT_IMPLEMENTATION_CONTEXT = """This file is the compact source of truth for LLM-aware automation.

## Product Shape

- GraftAI is an AI-first scheduling and ops platform.
- The backend is a FastAPI monolith with async SQLAlchemy, Redis cache, background workers, and PostgreSQL.
- The frontend is Next.js and acts as the interactive scheduling cockpit.

## Core Domain Objects

- Users own events, bookings, event types, notifications, and webhook subscriptions.
- Events are timezone-aware and can represent local calendar blocks or synced external meetings.
- Booking flows use signed public action links and preserve lifecycle email handling.

## Integrations

- Active calendar providers: Google Calendar and Microsoft Graph.
- Meeting and delivery integrations include Zoom and email providers.
- The system already supports provider-backed sync, reminders, and notification dispatch.

## AI / Automation Rules

- Prefer deterministic actions when the request is clearly list, schedule, update, or delete.
- Use LLM reasoning for summaries, drafting, disambiguation, and high-precision extraction.
- Keep responses concise and action-oriented.
- Ask for missing title, time, platform, or agenda details before creating meetings.
- Treat the runtime calendar context as authoritative over speculative reasoning.

## Safety and Operating Constraints

- Respect user-scoped data boundaries, quotas, and rate limits.
- Prefer direct state transitions over free-form advice when the intent is clear.
- Maintain timezone correctness in all scheduling decisions.
- Preserve fallback behavior when provider access or model calls fail.
"""


@lru_cache(maxsize=1)
def build_implementation_context() -> str:
    root = Path(__file__).resolve().parents[2]
    context_path = root / "LLM_IMPLEMENTATION_CONTEXT.md"

    if context_path.exists():
        text = context_path.read_text(encoding="utf-8").strip()
        if text:
            return text

    return DEFAULT_IMPLEMENTATION_CONTEXT.strip()
