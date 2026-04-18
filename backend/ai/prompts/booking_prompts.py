"""
Booking Decision Prompts

Structured prompts for the LLM to make intelligent decisions about
booking automation based on context, attendee history, and preferences.
"""

from typing import Dict, Any
from datetime import datetime

# ═════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═════════════════════════════════════════════════════════════════

BOOKING_DECISION_SYSTEM_PROMPT = """
You are an intelligent scheduler automation agent for GraftAI.

Use a natural, human tone in any user-facing confirmation. When the booking succeeds, keep the confirmation short, clear, and slightly celebratory without overdoing it.

When a booking is created, analyze the complete context and decide the best actions to take.

CONSIDER:

1. ATTENDEE RELIABILITY HISTORY
   - Past attendance rate
   - Booking patterns
   - Cancellation history
   - No-show probability
   - Response time trends

2. BOOKING CHARACTERISTICS
   - Value/importance
   - Urgency
   - Complexity
   - Duration
   - Attendee count

3. EXTERNAL FACTORS
   - Time of day
   - Day of week
   - Timezone differences
   - Holidays/events
   - Weather (for in-person)

4. PREFERENCES
   - Communication channel preference
   - Response time preference
   - Document preferences
   - Meeting format preference

DECIDE:
- Which actions to take (email, SMS, calendar, CRM task, etc.)
- What priority level (critical, high, medium, low)
- In what order to execute
- Any special handling needed
- If human review needed
- What to monitor/track

AVAILABLE ACTIONS:
- send_email: Send email confirmation
- send_sms: Send SMS reminder
- send_calendar_invite: Send calendar invitation
- create_calendar_event: Create calendar entry
- create_task: Create CRM task
- post_to_slack: Post to Slack channel
- send_teams_message: Send Teams message
- check_calendar_availability: Verify availability
- analyze_booking_pattern: Analyze patterns
- predict_no_show_risk: Predict no-show probability

RESPONSE FORMAT:
Return a JSON object with the following structure:

{
  "actions": [
    {
      "type": "action_type",
      "template": "template_name",
      "priority": "critical|high|medium|low",
      "execute_immediately": true|false,
      "condition": "optional_condition",
      "parameters": {
        "key": "value"
      },
      "reasoning": "Why this action is needed"
    }
  ],
  "risk_assessment": "low|medium|high|critical",
  "confidence": 0.0-1.0,
  "special_handling": "Description of any special handling",
  "monitoring": ["item1", "item2"],
  "next_steps": ["step1", "step2"],
  "human_review_required": true|false,
  "human_review_reason": "Reason if review needed"
}

Be specific and actionable in your decisions. Consider the context carefully.
"""

# ═════════════════════════════════════════════════════════════════
# BOOKING DECISION PROMPT TEMPLATE
# ═════════════════════════════════════════════════════════════════

BOOKING_DECISION_PROMPT_TEMPLATE = """
Analyze and decide actions for this booking:

ATTENDEE INFORMATION:
- Name: {attendee_name}
- Email: {attendee_email}
- Phone: {attendee_phone}
- Past bookings: {past_count}
- Attendance rate: {attendance_rate}%
- Cancellation rate: {cancellation_rate}%
- Average response time: {avg_response_time} hours
- Preferred communication: {preferred_channel}
- No-show rate: {no_show_rate}%

ORGANIZER INFORMATION:
- Name: {organizer_name}
- Email: {organizer_email}
- VIP status: {is_vip}
- Industry: {industry}
- Company: {company}
- Timezone: {timezone}
- Department: {department}

BOOKING DETAILS:
- Type: {booking_type}
- Value: ${booking_value}
- Scheduled for: {scheduled_time}
- Duration: {duration} minutes
- Current time: {current_time}
- Lead time: {lead_time} hours
- Calendar conflicts: {conflicts}
- Attendee count: {attendee_count}

CONTEXT:
- Day of week: {day_of_week}
- Time of day: {time_of_day}
- Is holiday: {is_holiday}
- Is weekend: {is_weekend}
- Business hours aligned: {business_hours_aligned}
- Timezone difference: {timezone_difference} hours

RECENT HISTORY:
- Last booking: {last_booking_date}
- Last interaction: {last_interaction_date}
- Satisfaction score: {satisfaction_score}
- Notes: {notes}

Please analyze this context and decide the best actions to ensure successful booking.
Consider the attendee's reliability, booking value, urgency, and any special circumstances.
"""

# ═════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════════


def format_booking_decision_prompt(
    attendee_name: str,
    attendee_email: str,
    organizer_name: str,
    booking_type: str,
    scheduled_time: str,
    **context: Dict[str, Any],
) -> str:
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
    # Default values for context
    defaults = {
        "attendee_phone": "Not provided",
        "past_count": 0,
        "attendance_rate": 100,
        "cancellation_rate": 0,
        "avg_response_time": 24,
        "preferred_channel": "email",
        "no_show_rate": 0,
        "organizer_email": "",
        "is_vip": "false",
        "industry": "Unknown",
        "company": "Unknown",
        "timezone": "UTC",
        "department": "Unknown",
        "booking_value": 0,
        "duration": 30,
        "current_time": datetime.utcnow().isoformat(),
        "lead_time": 24,
        "conflicts": "None",
        "attendee_count": 1,
        "day_of_week": datetime.utcnow().strftime("%A"),
        "time_of_day": datetime.utcnow().strftime("%H:%M"),
        "is_holiday": "false",
        "is_weekend": "false" if datetime.utcnow().weekday() < 5 else "true",
        "business_hours_aligned": "true",
        "timezone_difference": 0,
        "last_booking_date": "Never",
        "last_interaction_date": "Never",
        "satisfaction_score": "N/A",
        "notes": "None",
    }

    # Merge with provided context
    context = {**defaults, **context}

    # Format the prompt
    return BOOKING_DECISION_PROMPT_TEMPLATE.format(
        attendee_name=attendee_name,
        attendee_email=attendee_email,
        attendee_phone=context["attendee_phone"],
        past_count=context["past_count"],
        attendance_rate=context["attendance_rate"],
        cancellation_rate=context["cancellation_rate"],
        avg_response_time=context["avg_response_time"],
        preferred_channel=context["preferred_channel"],
        no_show_rate=context["no_show_rate"],
        organizer_name=organizer_name,
        organizer_email=context["organizer_email"],
        is_vip=context["is_vip"],
        industry=context["industry"],
        company=context["company"],
        timezone=context["timezone"],
        department=context["department"],
        booking_type=booking_type,
        booking_value=context["booking_value"],
        scheduled_time=scheduled_time,
        duration=context["duration"],
        current_time=context["current_time"],
        lead_time=context["lead_time"],
        conflicts=context["conflicts"],
        attendee_count=context["attendee_count"],
        day_of_week=context["day_of_week"],
        time_of_day=context["time_of_day"],
        is_holiday=context["is_holiday"],
        is_weekend=context["is_weekend"],
        business_hours_aligned=context["business_hours_aligned"],
        timezone_difference=context["timezone_difference"],
        last_booking_date=context["last_booking_date"],
        last_interaction_date=context["last_interaction_date"],
        satisfaction_score=context["satisfaction_score"],
        notes=context["notes"],
    )


def format_prompt_from_booking_data(
    booking: Dict[str, Any], attendee: Dict[str, Any]
) -> str:
    """
    Format prompt from booking and attendee data structures

    Args:
        booking: Booking data dict
        attendee: Attendee data dict

    Returns:
        Formatted prompt string
    """
    # Extract attendee info
    attendee_name = attendee.get("name", "Unknown")
    attendee_email = attendee.get("email", "unknown@example.com")

    # Extract booking info
    organizer_name = booking.get("organizer_name", "Unknown")
    booking_type = booking.get("type", "consultation")
    scheduled_time = booking.get("start_time", "")

    # Build context from both
    context = {
        "attendee_phone": attendee.get("phone", "Not provided"),
        "past_count": attendee.get("past_bookings", 0),
        "attendance_rate": attendee.get("attendance_rate", 100),
        "cancellation_rate": attendee.get("cancellation_rate", 0),
        "avg_response_time": attendee.get("avg_response_time", 24),
        "preferred_channel": (
            pref[0]
            if (pref := attendee.get("preferred_communication"))
            and isinstance(pref, (list, tuple))
            and len(pref) > 0
            else "email"
        ),
        "no_show_rate": attendee.get("no_show_rate", 0),
        "organizer_email": booking.get("organizer_email", ""),
        "is_vip": str(attendee.get("vip_level", "standard") == "executive").lower(),
        "industry": attendee.get("industry", "Unknown"),
        "company": attendee.get("company", "Unknown"),
        "timezone": attendee.get("timezone", "UTC"),
        "department": booking.get("department", "Unknown"),
        "booking_value": booking.get("estimated_value", 0),
        "duration": booking.get("duration_minutes", 30),
        "current_time": datetime.utcnow().isoformat(),
        "lead_time": booking.get("lead_time_hours", 24),
        "conflicts": booking.get("conflicts", "None"),
        "attendee_count": len(booking.get("attendees", [])),
        "day_of_week": datetime.fromisoformat(
            scheduled_time.replace("Z", "+00:00")
        ).strftime("%A")
        if scheduled_time
        else datetime.utcnow().strftime("%A"),
        "time_of_day": datetime.fromisoformat(
            scheduled_time.replace("Z", "+00:00")
        ).strftime("%H:%M")
        if scheduled_time
        else datetime.utcnow().strftime("%H:%M"),
        "is_holiday": str(booking.get("is_holiday", False)).lower(),
        "is_weekend": str(booking.get("is_weekend", False)).lower(),
        "business_hours_aligned": str(
            booking.get("business_hours_aligned", True)
        ).lower(),
        "timezone_difference": booking.get("timezone_difference", 0),
        "last_booking_date": attendee.get("last_booking_date", "Never"),
        "last_interaction_date": attendee.get("last_interaction_date", "Never"),
        "satisfaction_score": attendee.get("satisfaction_score", "N/A"),
        "notes": booking.get("notes", "None"),
    }

    return format_booking_decision_prompt(
        attendee_name=attendee_name,
        attendee_email=attendee_email,
        organizer_name=organizer_name,
        booking_type=booking_type,
        scheduled_time=scheduled_time,
        **context,
    )


# ═════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Example: High-risk booking
    prompt = format_booking_decision_prompt(
        attendee_name="John Smith",
        attendee_email="john@example.com",
        organizer_name="Jane Doe",
        booking_type="consultation",
        scheduled_time="2024-04-15T14:00:00",
        past_count=4,
        attendance_rate=50,
        cancellation_rate=25,
        avg_response_time=48,
        preferred_channel="email",
        no_show_rate=50,
        booking_value=500,
        duration=60,
        lead_time=2,
        conflicts="None",
        is_holiday="false",
    )

    print("=" * 80)
    print("BOOKING DECISION PROMPT EXAMPLE")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
