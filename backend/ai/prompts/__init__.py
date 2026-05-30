"""
Prompt Templates for AI Agent Decision Making

Provides structured prompts for the LLM to make intelligent decisions
about booking automation based on context, attendee history, and preferences.
"""
from .agent_prompts import (
    AGENT_SYSTEM_PROMPT,
    HUMANIZED_SYSTEM_PROMPT,
    format_agent_cognition_prompt,
)
from .agent_prompts import COGNITION_PROMPT_TEMPLATE as AGENT_COGNITION_PROMPT_TEMPLATE
from .booking_prompts import (
    BOOKING_DECISION_PROMPT_TEMPLATE,
    BOOKING_DECISION_SYSTEM_PROMPT,
    format_booking_decision_prompt,
)

__all__ = ["AGENT_COGNITION_PROMPT_TEMPLATE", "AGENT_SYSTEM_PROMPT", "BOOKING_DECISION_PROMPT_TEMPLATE", "BOOKING_DECISION_SYSTEM_PROMPT", "HUMANIZED_SYSTEM_PROMPT", "format_agent_cognition_prompt", "format_booking_decision_prompt"]
