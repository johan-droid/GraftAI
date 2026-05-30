"""
Agent Tools System for GraftAI

Provides a comprehensive toolkit for AI agents to execute real-world actions
across communication, scheduling, CRM, data analysis, and query operations.
"""
import logging
import os

from .registry import ToolRegistry, get_tool, list_tools, register_tool

logger = logging.getLogger(__name__)
_is_production = os.getenv("ENV", "").strip().lower() in {"prod", "production"} or os.getenv("NODE_ENV", "").strip().lower() == "production"
_default_use_real_tools = "true" if _is_production else "false"
USE_REAL_TOOLS = os.getenv("USE_REAL_TOOLS", _default_use_real_tools).strip().lower() in {"1", "true", "yes"}
if _is_production and (not USE_REAL_TOOLS):
    logger.warning("USE_REAL_TOOLS is disabled in production. Agent integrations will run in mock mode.")
if USE_REAL_TOOLS:
    from .communication_tools_real import (
        post_to_slack,
        send_calendar_invite,
        send_email,
        send_sms,
        send_teams_message,
    )
    from .scheduling_tools_real import (
        check_calendar_availability,
        create_calendar_event,
        get_conflicts,
        search_available_slots,
        update_calendar_event,
    )
else:
    from .communication_tools import (
        post_to_slack,
        send_calendar_invite,
        send_email,
        send_sms,
        send_teams_message,
    )
    from .scheduling_tools import (
        check_calendar_availability,
        create_calendar_event,
        get_conflicts,
        search_available_slots,
        update_calendar_event,
    )
from .crm_tools import (
    create_contact,
    create_task,
    get_contact_history,
    query_contacts,
    update_contact,
)
from .data_analysis_tools import (
    analyze_booking_pattern,
    estimate_booking_value,
    find_best_time_slot,
    get_attendee_preferences,
    predict_no_show_risk,
)
from .query_tools import (
    check_business_rules,
    get_attendee_info,
    get_booking_history,
    query_database,
)

__all__ = ["ToolRegistry", "analyze_booking_pattern", "check_business_rules", "check_calendar_availability", "create_calendar_event", "create_contact", "create_task", "estimate_booking_value", "find_best_time_slot", "get_attendee_info", "get_attendee_preferences", "get_booking_history", "get_conflicts", "get_contact_history", "get_tool", "list_tools", "post_to_slack", "predict_no_show_risk", "query_contacts", "query_database", "register_tool", "search_available_slots", "send_calendar_invite", "send_email", "send_sms", "send_teams_message", "update_calendar_event", "update_contact"]
