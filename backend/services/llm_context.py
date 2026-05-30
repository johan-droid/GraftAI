from functools import lru_cache
from pathlib import Path

DEFAULT_IMPLEMENTATION_CONTEXT = "This file is the compact source of truth for LLM-aware automation.\n\n## Product Shape\n\n- GraftAI is an AI-first scheduling and ops platform.\n- The backend is a FastAPI monolith with async SQLAlchemy, Redis cache, background workers, and PostgreSQL.\n- The frontend is Next.js and acts as the interactive scheduling cockpit.\n\n## Core Domain Objects\n\n- Users own events, bookings, event types, notifications, and webhook subscriptions.\n- Events are timezone-aware and can represent local calendar blocks or synced external meetings.\n- Booking flows use signed public action links and preserve lifecycle email handling.\n\n## Integrations\n\n- Active calendar providers: Google Calendar and Microsoft Graph.\n- Meeting and delivery integrations include Zoom and email providers.\n- The system already supports provider-backed sync, reminders, and notification dispatch.\n\n## AI / Automation Rules\n\n- Prefer deterministic actions when the request is clearly list, schedule, update, or delete.\n- Use LLM reasoning for summaries, drafting, disambiguation, and high-precision extraction.\n- Keep responses concise and action-oriented.\n- Ask for missing title, time, platform, or agenda details before creating meetings.\n- Treat the runtime calendar context as authoritative over speculative reasoning.\n\n## Safety and Operating Constraints\n\n- Respect user-scoped data boundaries, quotas, and rate limits.\n- Prefer direct state transitions over free-form advice when the intent is clear.\n- Maintain timezone correctness in all scheduling decisions.\n- Preserve fallback behavior when provider access or model calls fail.\n"

@lru_cache(maxsize=1)
def build_implementation_context() -> str:
    root = Path(__file__).resolve().parents[2]
    context_path = root / "LLM_IMPLEMENTATION_CONTEXT.md"
    if context_path.exists():
        text = context_path.read_text(encoding="utf-8").strip()
        if text:
            return text
    return DEFAULT_IMPLEMENTATION_CONTEXT.strip()
