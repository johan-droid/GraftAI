"""
Booking Decision Prompts

Structured prompts for the LLM to make intelligent decisions about
booking automation based on context, attendee history, and preferences.
"""
from datetime import UTC, datetime
from typing import Any

BOOKING_DECISION_SYSTEM_PROMPT = '\nYou are an intelligent scheduler automation agent for GraftAI.\n\nUse a natural, human tone in any user-facing confirmation. When the booking succeeds, keep the confirmation short, clear, and slightly celebratory without overdoing it.\n\nWhen a booking is created, analyze the complete context and decide the best actions to take.\n\nCONSIDER:\n\n1. ATTENDEE RELIABILITY HISTORY\n   - Past attendance rate\n   - Booking patterns\n   - Cancellation history\n   - No-show probability\n   - Response time trends\n\n2. BOOKING CHARACTERISTICS\n   - Value/importance\n   - Urgency\n   - Complexity\n   - Duration\n   - Attendee count\n\n3. EXTERNAL FACTORS\n   - Time of day\n   - Day of week\n   - Timezone differences\n   - Holidays/events\n   - Weather (for in-person)\n\n4. PREFERENCES\n   - Communication channel preference\n   - Response time preference\n   - Document preferences\n   - Meeting format preference\n\nDECIDE:\n- Which actions to take (email, SMS, calendar, CRM task, etc.)\n- What priority level (critical, high, medium, low)\n- In what order to execute\n- Any special handling needed\n- If human review needed\n- What to monitor/track\n\nAVAILABLE ACTIONS:\n- send_email: Send email confirmation\n- send_sms: Send SMS reminder\n- send_calendar_invite: Send calendar invitation\n- create_calendar_event: Create calendar entry\n- create_task: Create CRM task\n- post_to_slack: Post to Slack channel\n- send_teams_message: Send Teams message\n- check_calendar_availability: Verify availability\n- analyze_booking_pattern: Analyze patterns\n- predict_no_show_risk: Predict no-show probability\n\nRESPONSE FORMAT:\nReturn a JSON object with the following structure:\n\n{\n  "actions": [\n    {\n      "type": "action_type",\n      "template": "template_name",\n      "priority": "critical|high|medium|low",\n      "execute_immediately": true|false,\n      "condition": "optional_condition",\n      "parameters": {\n        "key": "value"\n      },\n      "reasoning": "Why this action is needed"\n    }\n  ],\n  "risk_assessment": "low|medium|high|critical",\n  "confidence": 0.0-1.0,\n  "special_handling": "Description of any special handling",\n  "monitoring": ["item1", "item2"],\n  "next_steps": ["step1", "step2"],\n  "human_review_required": true|false,\n  "human_review_reason": "Reason if review needed"\n}\n\nBe specific and actionable in your decisions. Consider the context carefully.\n'
BOOKING_DECISION_PROMPT_TEMPLATE = "\nAnalyze and decide actions for this booking:\n\nATTENDEE INFORMATION:\n- Name: {attendee_name}\n- Email: {attendee_email}\n- Phone: {attendee_phone}\n- Past bookings: {past_count}\n- Attendance rate: {attendance_rate}%\n- Cancellation rate: {cancellation_rate}%\n- Average response time: {avg_response_time} hours\n- Preferred communication: {preferred_channel}\n- No-show rate: {no_show_rate}%\n\nORGANIZER INFORMATION:\n- Name: {organizer_name}\n- Email: {organizer_email}\n- VIP status: {is_vip}\n- Industry: {industry}\n- Company: {company}\n- Timezone: {timezone}\n- Department: {department}\n\nBOOKING DETAILS:\n- Type: {booking_type}\n- Value: ${booking_value}\n- Scheduled for: {scheduled_time}\n- Duration: {duration} minutes\n- Current time: {current_time}\n- Lead time: {lead_time} hours\n- Calendar conflicts: {conflicts}\n- Attendee count: {attendee_count}\n\nCONTEXT:\n- Day of week: {day_of_week}\n- Time of day: {time_of_day}\n- Is holiday: {is_holiday}\n- Is weekend: {is_weekend}\n- Business hours aligned: {business_hours_aligned}\n- Timezone difference: {timezone_difference} hours\n\nRECENT HISTORY:\n- Last booking: {last_booking_date}\n- Last interaction: {last_interaction_date}\n- Satisfaction score: {satisfaction_score}\n- Notes: {notes}\n\nPlease analyze this context and decide the best actions to ensure successful booking.\nConsider the attendee's reliability, booking value, urgency, and any special circumstances.\n"

def format_booking_decision_prompt(attendee_name: str, attendee_email: str, organizer_name: str, booking_type: str, scheduled_time: str, **context: dict[str, Any]) -> str:
    """
    Format the booking decision prompt with actual values

    Args:
        attendee_name: Attendee's name
        attendee_email: Attendee's email
        organizer_name: Organizer's name
        booking_type: Type of booking
        scheduled_time: Scheduled time (ISO format)
        **context: Additional context fields

    Returns:
        Formatted prompt string
    """
    defaults = {"attendee_phone": "Not provided", "past_count": 0, "attendance_rate": 100, "cancellation_rate": 0, "avg_response_time": 24, "preferred_channel": "email", "no_show_rate": 0, "organizer_email": "", "is_vip": "false", "industry": "Unknown", "company": "Unknown", "timezone": "UTC", "department": "Unknown", "booking_value": 0, "duration": 30, "current_time": datetime.now(UTC).isoformat(), "lead_time": 24, "conflicts": "None", "attendee_count": 1, "day_of_week": datetime.now(UTC).strftime("%A"), "time_of_day": datetime.now(UTC).strftime("%H:%M"), "is_holiday": "false", "is_weekend": "false" if datetime.now(UTC).weekday() < 5 else "true", "business_hours_aligned": "true", "timezone_difference": 0, "last_booking_date": "Never", "last_interaction_date": "Never", "satisfaction_score": "N/A", "notes": "None"}
    context = {**defaults, **context}
    return BOOKING_DECISION_PROMPT_TEMPLATE.format(attendee_name=attendee_name, attendee_email=attendee_email, attendee_phone=context["attendee_phone"], past_count=context["past_count"], attendance_rate=context["attendance_rate"], cancellation_rate=context["cancellation_rate"], avg_response_time=context["avg_response_time"], preferred_channel=context["preferred_channel"], no_show_rate=context["no_show_rate"], organizer_name=organizer_name, organizer_email=context["organizer_email"], is_vip=context["is_vip"], industry=context["industry"], company=context["company"], timezone=context["timezone"], department=context["department"], booking_type=booking_type, booking_value=context["booking_value"], scheduled_time=scheduled_time, duration=context["duration"], current_time=context["current_time"], lead_time=context["lead_time"], conflicts=context["conflicts"], attendee_count=context["attendee_count"], day_of_week=context["day_of_week"], time_of_day=context["time_of_day"], is_holiday=context["is_holiday"], is_weekend=context["is_weekend"], business_hours_aligned=context["business_hours_aligned"], timezone_difference=context["timezone_difference"], last_booking_date=context["last_booking_date"], last_interaction_date=context["last_interaction_date"], satisfaction_score=context["satisfaction_score"], notes=context["notes"])

def format_prompt_from_booking_data(booking: dict[str, Any], attendee: dict[str, Any]) -> str:
    """
    Format prompt from booking and attendee data structures

    Args:
        booking: Booking data dict
        attendee: Attendee data dict

    Returns:
        Formatted prompt string
    """
    attendee_name = attendee.get("name", "Unknown")
    attendee_email = attendee.get("email", "unknown@example.com")
    organizer_name = booking.get("organizer_name", "Unknown")
    booking_type = booking.get("type", "consultation")
    scheduled_time = booking.get("start_time", "")
    context = {"attendee_phone": attendee.get("phone", "Not provided"), "past_count": attendee.get("past_bookings", 0), "attendance_rate": attendee.get("attendance_rate", 100), "cancellation_rate": attendee.get("cancellation_rate", 0), "avg_response_time": attendee.get("avg_response_time", 24), "preferred_channel": pref[0] if (pref := attendee.get("preferred_communication")) and isinstance(pref, (list, tuple)) and (len(pref) > 0) else "email", "no_show_rate": attendee.get("no_show_rate", 0), "organizer_email": booking.get("organizer_email", ""), "is_vip": str(attendee.get("vip_level", "standard") == "executive").lower(), "industry": attendee.get("industry", "Unknown"), "company": attendee.get("company", "Unknown"), "timezone": attendee.get("timezone", "UTC"), "department": booking.get("department", "Unknown"), "booking_value": booking.get("estimated_value", 0), "duration": booking.get("duration_minutes", 30), "current_time": datetime.now(UTC).isoformat(), "lead_time": booking.get("lead_time_hours", 24), "conflicts": booking.get("conflicts", "None"), "attendee_count": len(booking.get("attendees", [])), "day_of_week": datetime.fromisoformat(scheduled_time.replace("Z", "+00:00")).strftime("%A") if scheduled_time else datetime.now(UTC).strftime("%A"), "time_of_day": datetime.fromisoformat(scheduled_time.replace("Z", "+00:00")).strftime("%H:%M") if scheduled_time else datetime.now(UTC).strftime("%H:%M"), "is_holiday": str(booking.get("is_holiday", False)).lower(), "is_weekend": str(booking.get("is_weekend", False)).lower(), "business_hours_aligned": str(booking.get("business_hours_aligned", True)).lower(), "timezone_difference": booking.get("timezone_difference", 0), "last_booking_date": attendee.get("last_booking_date", "Never"), "last_interaction_date": attendee.get("last_interaction_date", "Never"), "satisfaction_score": attendee.get("satisfaction_score", "N/A"), "notes": booking.get("notes", "None")}
    return format_booking_decision_prompt(attendee_name=attendee_name, attendee_email=attendee_email, organizer_name=organizer_name, booking_type=booking_type, scheduled_time=scheduled_time, **context)
if __name__ == "__main__":
    prompt = format_booking_decision_prompt(attendee_name="John Smith", attendee_email="john@example.com", organizer_name="Jane Doe", booking_type="consultation", scheduled_time="2024-04-15T14:00:00", past_count=4, attendance_rate=50, cancellation_rate=25, avg_response_time=48, preferred_channel="email", no_show_rate=50, booking_value=500, duration=60, lead_time=2, conflicts="None", is_holiday="false")
