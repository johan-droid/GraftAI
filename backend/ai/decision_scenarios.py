"""
Decision Scenarios Implementation

Implements 6 key booking scenarios with specific agent behaviors:

1. High-Risk Booking (50% no-show rate)
2. VIP/High-Value Booking (major client)
3. Timezone Conflict (5 different time zones)
4. Conflict Detected (calendar overlap)
5. Low-Value, Low-Risk Booking (standard automation)
6. Follow-up Booking (memory-based optimization)
"""
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytz
from backend.ai.decision_engine import (
    ActionDecision,
    DecisionEngine,
    RiskLevel,
    VIPLevel,
)
from backend.ai.tools.registry import ToolPriority as ToolPriorityEnum
from backend.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ScenarioResult:
    """Result of scenario execution"""
    scenario_name: str
    risk_level: RiskLevel
    vip_level: VIPLevel
    actions_planned: list[str]
    special_handling: list[str]
    reasoning: str
    expected_outcome: str

class ScenarioEngine:
    """
    Handles specific booking scenarios with tailored agent behaviors
    """

    def __init__(self):
        self.decision_engine = DecisionEngine()

    async def handle_scenario_1_high_risk_booking(self, booking: dict[str, Any], attendee_info: dict[str, Any]) -> ScenarioResult:
        """
        SCENARIO 1: High-Risk Booking

        Situation:
        - Attendee has 50% no-show rate
        - Agent needs to minimize no-show risk

        Agent Decisions:
        1. Send confirmation email immediately
        2. SMS reminder 24 hours before
        3. Second SMS reminder 1 hour before
        4. Create high-priority task for organizer
        5. Flag in system for human follow-up if no confirmation
        """
        logger.info("🚨 SCENARIO 1: High-Risk Booking for %s", booking.get("attendees"))
        attendee_info["no_show_rate"] = 0.5
        attendee_info["past_bookings"] = [{"status": "no_show", "date": "2024-01-10"}, {"status": "no_show", "date": "2024-02-15"}, {"status": "attended", "date": "2024-03-20"}, {"status": "no_show", "date": "2024-04-05"}]
        decision = await self.decision_engine.analyze_and_decide(booking=booking, attendee_info=attendee_info, context={"risk_mitigation_required": True})
        scenario_actions = [ActionDecision(tool_name="send_email", parameters={"to": booking["attendees"][0], "subject": "IMPORTANT: Please Confirm Your Attendance", "template": "high_risk_confirmation", "body": f"\nDear {booking['attendees'][0]},\n\nWe've noticed you've missed some recent meetings. Please confirm your attendance\nfor this booking by clicking the confirmation link below.\n\nMeeting: {booking['title']}\nTime: {booking['start_time']}\nDuration: {booking['duration_minutes']} minutes\n\n[CONFIRM ATTENDANCE]\n\nIf you cannot attend, please let us know so we can reschedule.\n                    ".strip()}, priority=ToolPriorityEnum.CRITICAL, execute_immediately=True), ActionDecision(tool_name="send_sms", parameters={"to": attendee_info.get("phone"), "message": f"Reminder: {booking['title']} tomorrow at {booking['start_time']}. Please confirm attendance.", "condition": "24_hours_before_meeting"}, priority=ToolPriorityEnum.HIGH, execute_immediately=False), ActionDecision(tool_name="send_sms", parameters={"to": attendee_info.get("phone"), "message": f"Starting in 1 hour: {booking['title']}", "condition": "1_hour_before_meeting"}, priority=ToolPriorityEnum.HIGH, execute_immediately=False), ActionDecision(tool_name="create_task", parameters={"title": f"Monitor high-risk booking: {booking['title']}", "due_date": booking["start_time"], "owner": booking["organizer"], "priority": "high", "description": "Check if attendee confirmed. If not, follow up manually."}, priority=ToolPriorityEnum.HIGH, execute_immediately=True), ActionDecision(tool_name="flag_booking", parameters={"booking_id": booking["id"], "flag": "requires_confirmation", "reason": "High no-show rate (50%)", "action_if_no_confirmation": "human_follow_up"}, priority=ToolPriorityEnum.HIGH, execute_immediately=True)]
        decision.actions.extend(scenario_actions)
        return ScenarioResult(scenario_name="High-Risk Booking", risk_level=RiskLevel.HIGH, vip_level=decision.attendee_analysis.vip_level, actions_planned=["Send confirmation email immediately", "SMS reminder 24 hours before", "SMS reminder 1 hour before", "Create high-priority monitoring task", "Flag for human follow-up if no confirmation"], special_handling=["Multiple reminders", "Confirmation required", "Human monitoring"], reasoning="Attendee has 50% no-show rate based on 4 recent bookings. Aggressive reminder strategy required to minimize risk.", expected_outcome="No-show risk minimized through multi-channel reminders")

    async def handle_scenario_2_vip_booking(self, booking: dict[str, Any], attendee_info: dict[str, Any]) -> ScenarioResult:
        """
        SCENARIO 2: VIP/High-Value Booking

        Situation:
        - Attendee is major client
        - Agent needs to deliver premium experience

        Agent Decisions:
        1. Send personalized welcome email
        2. Include preparation checklist
        3. Schedule pre-call with team
        4. Set up premium video conferencing
        5. Create follow-up task (mandatory)
        6. Notify manager immediately
        """
        logger.info("⭐ SCENARIO 2: VIP Booking for %s", booking.get("attendees"))
        attendee_info["monthly_booking_count"] = 15
        attendee_info["engagement_score"] = 0.95
        attendee_info["company_size"] = "enterprise"
        attendee_info["estimated_value"] = 50000
        decision = await self.decision_engine.analyze_and_decide(booking=booking, attendee_info=attendee_info, context={"vip_treatment_required": True})
        scenario_actions = [ActionDecision(tool_name="send_email", parameters={"to": booking["attendees"][0], "subject": f"Welcome, {attendee_info.get('name')} - Premium Meeting Setup", "template": "vip_welcome", "body": f"\nDear {attendee_info.get('name')},\n\nThank you for choosing us for your upcoming meeting.\n\n🎯 Meeting Details:\n• Title: {booking['title']}\n• Time: {booking['start_time']}\n• Duration: {booking['duration_minutes']} minutes\n• Location: Premium Video Conference Suite\n\n📋 Preparation Checklist:\n- Review agenda (attached)\n- Prepare any materials for discussion\n- Test video conferencing link below\n\n🎬 Video Conference Link:\nhttps://premium-meetings.yourcompany.com/{booking['id']}\n\nYour dedicated support team has been notified and will ensure everything is perfect.\n\nBest regards,\nYour Premium Services Team\n                    ".strip()}, priority=ToolPriorityEnum.CRITICAL, execute_immediately=True), ActionDecision(tool_name="create_task", parameters={"title": f"Pre-call team sync for {booking['title']}", "due_date": self._calculate_pre_call_time(booking["start_time"]), "owner": "team_lead@company.com", "priority": "high", "description": "Prepare for VIP meeting, review materials, ensure video suite ready", "task_type": "vip_preparation"}, priority=ToolPriorityEnum.HIGH, execute_immediately=True), ActionDecision(tool_name="setup_premium_video", parameters={"booking_id": booking["id"], "suite": "premium_suite_a", "features": ["hd_video", "recording", "transcription", "ai_assistant"], "attendees": booking["attendees"]}, priority=ToolPriorityEnum.HIGH, execute_immediately=True), ActionDecision(tool_name="create_task", parameters={"title": f"Post-meeting follow-up for {booking['title']}", "due_date": self._calculate_followup_time(booking["start_time"]), "owner": "account_manager@company.com", "priority": "critical", "description": "Mandatory follow-up with VIP client", "task_type": "vip_followup"}, priority=ToolPriorityEnum.CRITICAL, execute_immediately=False, condition="immediately_after_meeting"), ActionDecision(tool_name="send_email", parameters={"to": "manager@company.com", "subject": f"VIP Meeting Scheduled: {booking['title']}", "template": "vip_notification", "body": f"\nManager,\n\nA VIP meeting has been scheduled:\n\nClient: {attendee_info.get('name')}\nCompany: {attendee_info.get('company')}\nValue: ${attendee_info.get('estimated_value'):,}\nTime: {booking['start_time']}\n\nPlease ensure team is prepared and premium suite is reserved.\n                    ".strip()}, priority=ToolPriorityEnum.HIGH, execute_immediately=True)]
        decision.actions.extend(scenario_actions)
        return ScenarioResult(scenario_name="VIP/High-Value Booking", risk_level=RiskLevel.LOW, vip_level=VIPLevel.EXECUTIVE, actions_planned=["Send personalized welcome email", "Include preparation checklist", "Schedule pre-call with team", "Set up premium video conferencing", "Create mandatory follow-up task", "Notify manager immediately"], special_handling=["Premium video suite", "Pre-call team sync", "Mandatory follow-up", "Manager notification"], reasoning="Attendee is executive-level VIP with $50k estimated value. Premium treatment required to maintain relationship.", expected_outcome="Premium experience delivered, client satisfaction maximized")

    async def handle_scenario_3_timezone_conflict(self, booking: dict[str, Any], attendee_info: dict[str, Any]) -> ScenarioResult:
        """
        SCENARIO 3: Timezone Conflict

        Situation:
        - Attendees in 5 different time zones
        - Agent needs to handle timezone complexity

        Agent Decisions:
        1. Convert all times to individual timezones
        2. Send customized reminders per timezone
        3. Create calendar entries in local times
        4. Suggest video call over phone due to timezones
        5. Add timezone conversions to confirmation
        """
        logger.info("🌍 SCENARIO 3: Timezone Conflict - 5 time zones")
        timezones = ["America/New_York", "Europe/London", "Asia/Tokyo", "Australia/Sydney", "America/Los_Angeles"]
        attendees_with_tz = []
        for i, tz in enumerate(timezones):
            attendees_with_tz.append({"email": f"attendee{i}@example.com", "timezone": tz, "name": f"Attendee {i}"})
        booking["attendees"] = [a["email"] for a in attendees_with_tz]
        booking["attendees_with_tz"] = attendees_with_tz
        decision = await self.decision_engine.analyze_and_decide(booking=booking, attendee_info=attendee_info, context={"timezone_complexity": "high", "attendee_count": 5})
        meeting_time_utc = datetime.fromisoformat(booking["start_time"].replace("Z", "+00:00"))
        timezone_conversions = []
        for attendee in attendees_with_tz:
            tz = pytz.timezone(attendee["timezone"])
            local_time = meeting_time_utc.astimezone(tz)
            timezone_conversions.append({"attendee": attendee["name"], "timezone": attendee["timezone"], "local_time": local_time.strftime("%Y-%m-%d %H:%M %Z")})
        scenario_actions = []
        for i, attendee in enumerate(attendees_with_tz):
            local_time_str = timezone_conversions[i]["local_time"]
            scenario_actions.append(ActionDecision(tool_name="send_email", parameters={"to": attendee["email"], "subject": f"Meeting in Your Timezone: {local_time_str}", "template": "timezone_aware", "body": f"\nHi {attendee['name']},\n\nYour meeting is scheduled for:\n\n📅 Your Local Time: {local_time_str}\n🌍 Timezone: {attendee['timezone']}\n📹 Format: Video Conference (recommended for multi-timezone)\n\nAll Timezones:\n{self._format_timezone_table(timezone_conversions)}\n\nVideo Conference Link: https://meet.yourcompany.com/{booking['id']}\n\nBest regards,\n                    ".strip()}, priority=ToolPriorityEnum.HIGH, execute_immediately=True))
        scenario_actions.append(ActionDecision(tool_name="create_calendar_event", parameters={"title": booking["title"], "start_time": booking["start_time"], "duration_minutes": booking["duration_minutes"], "attendees": [a["email"] for a in attendees_with_tz], "location": "Video Conference (Multi-timezone)", "description": f"Multi-timezone meeting. Timezone conversions: {timezone_conversions}", "timezone": "UTC"}, priority=ToolPriorityEnum.CRITICAL, execute_immediately=True))
        scenario_actions.append(ActionDecision(tool_name="send_sms", parameters={"to": booking["organizer"], "message": "Multi-timezone meeting set up. Video conference recommended due to 5 time zones."}, priority=ToolPriorityEnum.MEDIUM, execute_immediately=False))
        decision.actions.extend(scenario_actions)
        return ScenarioResult(scenario_name="Timezone Conflict", risk_level=RiskLevel.MEDIUM, vip_level=decision.attendee_analysis.vip_level, actions_planned=["Convert times to individual timezones", "Send customized reminders per timezone", "Create calendar entries in local times", "Suggest video call over phone", "Add timezone conversions to confirmation"], special_handling=["Per-attendee timezone conversions", "Video conference recommended", "Customized reminders"], reasoning=f"5 attendees across {len(set(timezones))} time zones. Individual timezone conversions required to avoid confusion.", expected_outcome="No confusion, optimized scheduling across time zones")

    async def handle_scenario_4_conflict_detected(self, booking: dict[str, Any], attendee_info: dict[str, Any]) -> ScenarioResult:
        """
        SCENARIO 4: Conflict Detected

        Situation:
        - Calendar shows organizer has overlapping event
        - Agent needs to prevent double-booking

        Agent Decisions:
        1. Pause automation
        2. Alert organizer to conflict
        3. Suggest alternative times
        4. Ask for human decision
        5. Resume when conflict resolved
        """
        logger.info("⚠️ SCENARIO 4: Conflict Detected")
        conflict_event = {"title": "Existing Meeting", "start_time": booking["start_time"], "end_time": booking.get("end_time"), "overlap_minutes": 15}
        decision = await self.decision_engine.analyze_and_decide(booking=booking, attendee_info=attendee_info, context={"calendar_conflict": True, "conflict_event": conflict_event})
        alternatives = self._suggest_alternative_times(booking["start_time"])
        scenario_actions = [ActionDecision(tool_name="pause_automation", parameters={"booking_id": booking["id"], "reason": "Calendar conflict detected", "conflict_event": conflict_event}, priority=ToolPriorityEnum.CRITICAL, execute_immediately=True), ActionDecision(tool_name="send_email", parameters={"to": booking["organizer"], "subject": f"⚠️ CONFLICT: {booking['title']}", "template": "conflict_alert", "body": f"\nCONFLICT DETECTED!\n\nYour new booking conflicts with:\n• Existing: {conflict_event['title']}\n• Overlap: {conflict_event['overlap_minutes']} minutes\n• Time: {booking['start_time']}\n\n⏰ Suggested Alternative Times:\n{self._format_alternatives(alternatives)}\n\nPlease choose an alternative time or resolve the conflict manually.\n                    ".strip()}, priority=ToolPriorityEnum.CRITICAL, execute_immediately=True), ActionDecision(tool_name="create_task", parameters={"title": f"Resolve booking conflict: {booking['title']}", "due_date": datetime.now(UTC).isoformat(), "owner": booking["organizer"], "priority": "critical", "description": "Calendar conflict requires human intervention", "task_type": "conflict_resolution"}, priority=ToolPriorityEnum.CRITICAL, execute_immediately=True), ActionDecision(tool_name="wait_for_resolution", parameters={"booking_id": booking["id"], "timeout_hours": 2, "fallback": "cancel_booking"}, priority=ToolPriorityEnum.HIGH, execute_immediately=False)]
        decision.actions.extend(scenario_actions)
        decision.requires_human_review = True
        decision.human_review_reason = "Calendar conflict detected - human intervention required"
        return ScenarioResult(scenario_name="Conflict Detected", risk_level=RiskLevel.HIGH, vip_level=decision.attendee_analysis.vip_level, actions_planned=["Pause automation", "Alert organizer to conflict", "Suggest alternative times", "Ask for human decision", "Resume when conflict resolved"], special_handling=["Automation paused", "Human intervention required", "Alternative time suggestions"], reasoning=f"Calendar conflict detected with {conflict_event['title']}. {conflict_event['overlap_minutes']} minute overlap. Human decision required to resolve.", expected_outcome="Prevents double-booking, allows human to resolve conflict")

    async def handle_scenario_5_low_value_low_risk(self, booking: dict[str, Any], attendee_info: dict[str, Any]) -> ScenarioResult:
        """
        SCENARIO 5: Low-Value, Low-Risk Booking

        Situation:
        - Standard meeting, reliable attendee
        - Agent needs efficient automation

        Agent Decisions:
        1. Send standard confirmation email
        2. Create calendar event
        3. Minimal follow-up
        4. No special handling needed
        """
        logger.info("✅ SCENARIO 5: Low-Value Low-Risk Booking")
        attendee_info["no_show_rate"] = 0.05
        attendee_info["monthly_booking_count"] = 2
        attendee_info["engagement_score"] = 0.7
        attendee_info["estimated_value"] = 100
        decision = await self.decision_engine.analyze_and_decide(booking=booking, attendee_info=attendee_info, context={"standard_booking": True})
        scenario_actions = [ActionDecision(tool_name="send_email", parameters={"to": booking["attendees"][0], "subject": f"Meeting Confirmed: {booking['title']}", "template": "standard_confirmation", "body": f"\nYour meeting has been scheduled:\n\n{booking['title']}\nTime: {booking['start_time']}\nDuration: {booking['duration_minutes']} minutes\n\nCalendar invite attached.\n                    ".strip()}, priority=ToolPriorityEnum.MEDIUM, execute_immediately=True), ActionDecision(tool_name="create_calendar_event", parameters={"title": booking["title"], "start_time": booking["start_time"], "duration_minutes": booking["duration_minutes"], "attendees": booking["attendees"], "reminder_minutes": 15}, priority=ToolPriorityEnum.MEDIUM, execute_immediately=True)]
        decision.actions.extend(scenario_actions)
        return ScenarioResult(scenario_name="Low-Value Low-Risk Booking", risk_level=RiskLevel.LOW, vip_level=VIPLevel.STANDARD, actions_planned=["Send standard confirmation email", "Create calendar event", "Minimal follow-up", "No special handling"], special_handling=["Standard automation", "Minimal overhead"], reasoning="Standard meeting with reliable attendee (5% no-show rate). Efficient automation with minimal overhead.", expected_outcome="Efficient automation, minimal overhead")

    async def handle_scenario_6_follow_up_booking(self, booking: dict[str, Any], attendee_info: dict[str, Any], memory_manager) -> ScenarioResult:
        """
        SCENARIO 6: Follow-up Booking

        Situation:
        - Attendee scheduling second meeting with same organizer
        - Agent remembers from past interaction

        Past Learning:
        - Attendee preferred email over phone
        - Organizer typically meets in Conference Room A
        - Both were happy with timing
        - No special requirements flagged

        Agent Decisions:
        1. Use same communication style
        2. Pre-book same room
        3. Send streamlined confirmation
        4. Faster process overall
        """
        logger.info("🧠 SCENARIO 6: Follow-up Booking (Memory-Based)")
        if not memory_manager:
            logger.warning("Memory manager unavailable for follow-up booking; using defaults.")
            attendee_info["preferred_communication"] = "email"
            booking["location"] = "Conference Room A"
            booking["duration_minutes"] = booking.get("duration_minutes", 30)
            past_interaction = []
        else:
            past_interaction = await memory_manager.retrieve_by_context(query=f"meeting with {booking['attendees'][0]}", n_results=1)
        if past_interaction:
            learned_preferences = past_interaction[0]
            logger.info("Retrieved preferences: %s", learned_preferences)
            attendee_info["preferred_communication"] = learned_preferences.get("preferred_communication", "email")
            booking["location"] = learned_preferences.get("preferred_location", "Conference Room A")
            booking["duration_minutes"] = learned_preferences.get("preferred_duration", 30)
        else:
            attendee_info["preferred_communication"] = "email"
            booking["location"] = "Conference Room A"
        decision = await self.decision_engine.analyze_and_decide(booking=booking, attendee_info=attendee_info, context={"follow_up_booking": True, "use_learned_preferences": True})
        scenario_actions = [ActionDecision(tool_name="send_email", parameters={"to": booking["attendees"][0], "subject": f"Meeting Confirmed (as before): {booking['title']}", "template": "streamlined_confirmation", "body": f"\nHi again,\n\nYour follow-up meeting is confirmed (same format as last time):\n\n{booking['title']}\nTime: {booking['start_time']}\nLocation: {booking['location']}\nDuration: {booking['duration_minutes']} minutes\n\nCalendar invite attached.\n                    ".strip()}, priority=ToolPriorityEnum.MEDIUM, execute_immediately=True), ActionDecision(tool_name="create_calendar_event", parameters={"title": booking["title"], "start_time": booking["start_time"], "duration_minutes": booking["duration_minutes"], "attendees": booking["attendees"], "location": booking["location"], "reminder_minutes": 15}, priority=ToolPriorityEnum.MEDIUM, execute_immediately=True), ActionDecision(tool_name="learn_from_interaction", parameters={"booking_id": booking["id"], "attendee": booking["attendees"][0], "preferences": {"preferred_communication": "email", "preferred_location": booking["location"], "preferred_duration": booking["duration_minutes"]}, "outcome": "success", "confidence": 0.9}, priority=ToolPriorityEnum.LOW, execute_immediately=False)]
        decision.actions.extend(scenario_actions)
        return ScenarioResult(scenario_name="Follow-up Booking", risk_level=RiskLevel.LOW, vip_level=decision.attendee_analysis.vip_level, actions_planned=["Use same communication style", "Pre-book same room", "Send streamlined confirmation", "Faster process overall"], special_handling=["Memory-based optimization", "Streamlined process", "Learned preferences applied"], reasoning="Follow-up booking with same organizer. Memory retrieved: email preferred, Conference Room A, 30min duration. Applied learned preferences for optimized experience.", expected_outcome="Optimized based on learning, faster process")

    def _calculate_pre_call_time(self, meeting_time: str) -> str:
        """Calculate time for pre-call team sync"""
        meeting = datetime.fromisoformat(meeting_time.replace("Z", "+00:00"))
        pre_call = meeting - timedelta(hours=2)
        return pre_call.isoformat()

    def _calculate_followup_time(self, meeting_time: str) -> str:
        """Calculate time for post-meeting follow-up"""
        meeting = datetime.fromisoformat(meeting_time.replace("Z", "+00:00"))
        followup = meeting + timedelta(hours=2)
        return followup.isoformat()

    def _format_timezone_table(self, conversions: list[dict]) -> str:
        """Format timezone conversions into readable table"""
        lines = ["Attendee | Timezone | Local Time", "-" * 50]
        for conv in conversions:
            lines.append(f"{conv['attendee']} | {conv['timezone']} | {conv['local_time']}")
        return "\n".join(lines)

    def _suggest_alternative_times(self, original_time: str) -> list[str]:
        """Suggest alternative meeting times"""
        original = datetime.fromisoformat(original_time.replace("Z", "+00:00"))
        alternatives = []
        alternatives.append((original + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"))
        alternatives.append((original + timedelta(days=1)).strftime("%Y-%m-%d %H:%M"))
        alternatives.append((original + timedelta(days=1, hours=2)).strftime("%Y-%m-%d %H:%M"))
        return alternatives

    def _format_alternatives(self, alternatives: list[str]) -> str:
        """Format alternative times"""
        lines = []
        for i, alt in enumerate(alternatives, 1):
            lines.append(f"{i}. {alt}")
        return "\n".join(lines)

async def create_scenario_engine() -> ScenarioEngine:
    """Create a scenario engine instance"""
    return ScenarioEngine()

async def run_all_scenarios():
    """Run all 6 scenarios for demonstration"""
    engine = await create_scenario_engine()
    try:
        from backend.ai.memory.multi_layer_memory import create_memory_manager
        engine.memory_manager = await create_memory_manager()
    except Exception:
        engine.memory_manager = None
    scenarios = [("High-Risk Booking", engine.handle_scenario_1_high_risk_booking), ("VIP Booking", engine.handle_scenario_2_vip_booking), ("Timezone Conflict", engine.handle_scenario_3_timezone_conflict), ("Conflict Detected", engine.handle_scenario_4_conflict_detected), ("Low-Value Booking", engine.handle_scenario_5_low_value_low_risk)]
    if engine.memory_manager is not None:
        scenarios.append(("Follow-up Booking", engine.handle_scenario_6_follow_up_booking))
    else:
        logger.warning("Skipping scenario 6 follow-up booking because memory manager could not be initialized.")
    results = []
    for scenario_name, handler in scenarios:
        booking = {"id": f"booking_{scenario_name.lower().replace(' ', '_')}", "title": f"Sample {scenario_name}", "start_time": "2024-04-15T14:00:00", "duration_minutes": 30, "attendees": ["user@example.com"], "organizer": "organizer@company.com"}
        attendee_info = {"email": "user@example.com", "name": "Test User", "phone": "+1234567890"}
        if handler == engine.handle_scenario_6_follow_up_booking:
            result = await handler(booking, attendee_info, engine.memory_manager)
        else:
            result = await handler(booking, attendee_info)
        results.append(result)
    return results
