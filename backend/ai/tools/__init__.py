"""
Agent Tools System for GraftAI

Provides a comprehensive toolkit for AI agents to execute real-world actions
across communication, scheduling, CRM, data analysis, and query operations.
"""

import os
from .registry import ToolRegistry, register_tool, get_tool, list_tools

USE_REAL_TOOLS = os.getenv("USE_REAL_TOOLS", "false").strip().lower() in {"1", "true", "yes"}

if USE_REAL_TOOLS:
    from .communication_tools_real import (
        send_email,
        send_sms,
        post_to_slack,
        send_teams_message,
        send_calendar_invite
    )
    from .scheduling_tools_real import (
        create_calendar_event,
        update_calendar_event,
        check_calendar_availability,
        search_available_slots,
        get_conflicts
    )
else:
    from .communication_tools import (
        send_email,
        send_sms,
        post_to_slack,
        send_teams_message,
        send_calendar_invite
    )
    from .scheduling_tools import (
        create_calendar_event,
        update_calendar_event,
        check_calendar_availability,
        search_available_slots,
        get_conflicts
    )
from .crm_tools import (
    create_contact,
    update_contact,
    create_task,
    query_contacts,
    get_contact_history
)
from .data_analysis_tools import (
    analyze_booking_pattern,
    predict_no_show_risk,
    find_best_time_slot,
    estimate_booking_value,
    get_attendee_preferences
)
from .query_tools import (
    query_database,
    get_booking_history,
    get_attendee_info,
    check_business_rules
)

__all__ = [
    # Registry
    "ToolRegistry",
    "register_tool",
    "get_tool",
    "list_tools",
    # Communication
    "send_email",
    "send_sms",
    "post_to_slack",
    "send_teams_message",
    "send_calendar_invite",
    # Scheduling
    "create_calendar_event",
    "update_calendar_event",
    "check_calendar_availability",
    "search_available_slots",
    "get_conflicts",
    # CRM
    "create_contact",
    "update_contact",
    "create_task",
    "query_contacts",
    "get_contact_history",
    # Data Analysis
    "analyze_booking_pattern",
    "predict_no_show_risk",
    "find_best_time_slot",
    "estimate_booking_value",
    "get_attendee_preferences",
    # Query
    "query_database",
    "get_booking_history",
    "get_attendee_info",
    "check_business_rules",
]
