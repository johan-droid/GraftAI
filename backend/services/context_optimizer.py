import logging
from typing import List, Dict, Any
from datetime import datetime
from backend.models.tables import EventTable

logger = logging.getLogger(__name__)

class ContextOptimizer:
    """
    Lightning-Fast Context Compression for LLM interaction.
    Transforms raw DB objects into high-density strings to minimize token cost and latency.
    """
    
    @staticmethod
    def compact_schedule(user_id: str, events: List[EventTable], focus_date: datetime) -> str:
        """
        Compresses a list of events into a semantic, AI-readable string.
        Format: [SCHEDULE] BUSY: 09:00-10:00 (Mtg), 14:00-15:00 (Focus). FREE: 10:00-14:00.
        """
        if not events:
            return f"[CONTEXT] No scheduled busy slots for {focus_date.strftime('%Y-%m-%d')}. User is fully available."

        busy_slots = []
        for ev in events:
            if not ev.is_busy or ev.status == "canceled":
                continue
            
            start_str = ev.start_time.strftime("%H:%M")
            end_str = ev.end_time.strftime("%H:%M")
            title_short = (ev.title[:20] + '..') if len(ev.title) > 20 else ev.title
            source_tag = f" ({ev.provider_source})" if ev.provider_source != "internal" else ""
            
            busy_slots.append(f"{start_str}-{end_str}: {title_short}{source_tag}")

        if not busy_slots:
             return f"[CONTEXT] All events on {focus_date.strftime('%Y-%m-%d')} are marked as 'Free'. User is fully available."

        header = f"[CONTEXT] Schedule for {focus_date.strftime('%A, %b %d')}:"
        busy_section = " | ".join(busy_slots)
        
        return f"{header}\nBUSY SLOTS: {busy_section}"

    @staticmethod
    def get_ai_guidance(user_timezone: str) -> str:
        """Provides compact operational constraints for the AI."""
        return f"[GUIDANCE] User TZ: {user_timezone}. Prioritize local-first data. All external events are already synced and marked as 'BUSY'."

context_optimizer = ContextOptimizer()
