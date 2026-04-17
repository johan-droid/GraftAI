"""
Prompt Templates for AI Agent Decision Making

Provides structured prompts for the LLM to make intelligent decisions
about booking automation based on context, attendee history, and preferences.
"""

from .booking_prompts import (
    BOOKING_DECISION_SYSTEM_PROMPT,
    BOOKING_DECISION_PROMPT_TEMPLATE,
    format_booking_decision_prompt
)
from .agent_prompts import (
    AGENT_SYSTEM_PROMPT,
    COGNITION_PROMPT_TEMPLATE as AGENT_COGNITION_PROMPT_TEMPLATE,
    format_agent_cognition_prompt
)

from .agent_prompts import HUMANIZED_SYSTEM_PROMPT

__all__ = [
    # Booking prompts
    "BOOKING_DECISION_SYSTEM_PROMPT",
    "BOOKING_DECISION_PROMPT_TEMPLATE",
    "format_booking_decision_prompt",
    # Agent prompts
    "AGENT_SYSTEM_PROMPT",
    "AGENT_COGNITION_PROMPT_TEMPLATE",
    "format_agent_cognition_prompt"
    ,"HUMANIZED_SYSTEM_PROMPT"
]
