"""
LlamaIndex Integration for GraftAI

Provides LlamaIndex ReAct Agent integration with the existing tool system.
Allows using LlamaIndex's reasoning capabilities with GraftAI's tools.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from llama_index.core.agent import ReActAgent
from backend.ai.prompts import BOOKING_DECISION_SYSTEM_PROMPT
from backend.ai.tools import (
    analyze_booking_pattern,
    check_business_rules,
    check_calendar_availability,
    create_calendar_event,
    create_contact,
    create_task,
    estimate_booking_value,
    find_best_time_slot,
    get_attendee_info,
    get_attendee_preferences,
    get_booking_history,
    get_conflicts,
    get_contact_history,
    post_to_slack,
    predict_no_show_risk,
    search_available_slots,
    send_email,
    send_sms,
    send_teams_message,
    update_calendar_event,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class LlamaIndexToolWrapper:
    """
    Wrapper to convert GraftAI tools to LlamaIndex FunctionTool format

    This allows seamless integration with LlamaIndex's ReActAgent
    """

    def __init__(self):
        self.tools = {}
        self._register_all_tools()

    def _register_all_tools(self):
        """Register all GraftAI tools with LlamaIndex-compatible metadata"""
        self.tools["send_email"] = {"fn": send_email, "name": "send_email", "description": "Send an email to attendee or contact.\n\n            Use for:\n            - Booking confirmations\n            - Reminders\n            - Follow-ups\n            - VIP notifications\n\n            Templates available: confirmation, reminder, follow_up, vip_welcome, high_risk_confirmation\n            Personalizes content based on attendee context and risk level.\n\n            Args:\n                to: Recipient email address\n                subject: Email subject line\n                body: Email body content\n                template: Optional template name\n\n            Returns:\n                Email delivery status, message ID, and timestamp\n            ", "return_description": "Email delivery status and ID"}
        self.tools["send_sms"] = {"fn": send_sms, "name": "send_sms", "description": "Send SMS message to attendee.\n\n            Use for:\n            - Urgent reminders\n            - High-risk booking alerts\n            - VIP notifications\n            - Last-minute changes\n\n            Best for high-priority communications when email may not be seen promptly.\n\n            Args:\n                to: Recipient phone number\n                message: SMS content (keep under 160 chars for single message)\n\n            Returns:\n                SMS delivery status and message ID\n            ", "return_description": "SMS delivery status and ID"}
        self.tools["post_to_slack"] = {"fn": post_to_slack, "name": "post_to_slack", "description": "Post message to Slack channel.\n\n            Use for:\n            - Team notifications\n            - VIP booking alerts\n            - Conflict notifications\n            - Team coordination\n\n            Args:\n                channel: Slack channel name (e.g., #bookings)\n                message: Message content\n\n            Returns:\n                Post status and message ID\n            ", "return_description": "Slack post status"}
        self.tools["send_teams_message"] = {"fn": send_teams_message, "name": "send_teams_message", "description": "Send message to Microsoft Teams.\n\n            Use for internal team notifications and coordination.\n\n            Args:\n                team_id: Teams team ID\n                channel: Channel name\n                message: Message content\n\n            Returns:\n                Teams message status\n            ", "return_description": "Teams message status"}
        self.tools["create_calendar_event"] = {"fn": create_calendar_event, "name": "create_calendar_event", "description": "Create or update calendar event.\n\n            Automatically:\n            - Adjusts for timezone differences\n            - Sends calendar invites to attendees\n            - Syncs with external calendars (Google, Outlook)\n            - Sets up reminders\n            - Checks for conflicts\n\n            Args:\n                title: Event title\n                start_time: Event start time (ISO format)\n                duration_minutes: Event duration\n                attendees: List of attendee emails\n                location: Meeting location or video link\n                reminder_minutes: Reminder time before event\n\n            Returns:\n                Calendar event ID, sync status, and invite links\n            ", "return_description": "Calendar event ID and sync status"}
        self.tools["update_calendar_event"] = {"fn": update_calendar_event, "name": "update_calendar_event", "description": "Update existing calendar event.\n\n            Use to modify time, attendees, or details.\n            Automatically notifies all attendees of changes.\n\n            Args:\n                event_id: Calendar event ID to update\n                title: New title (optional)\n                start_time: New start time (optional)\n                duration_minutes: New duration (optional)\n                attendees: Updated attendee list (optional)\n\n            Returns:\n                Update status and new event details\n            ", "return_description": "Update status and event details"}
        self.tools["check_calendar_availability"] = {"fn": check_calendar_availability, "name": "check_calendar_availability", "description": "Check if time slot is available.\n\n            Verifies organizer and attendee availability.\n            Checks for conflicts and busy times.\n\n            Args:\n                attendee_email: Email to check\n                start_time: Proposed start time\n                duration_minutes: Meeting duration\n\n            Returns:\n                Availability status and conflicting events\n            ", "return_description": "Availability status and conflicts"}
        self.tools["search_available_slots"] = {"fn": search_available_slots, "name": "search_available_slots", "description": "Search for available time slots.\n\n            Finds optimal meeting times considering:\n            - Organizer availability\n            - Attendee availability\n            - Business hours\n            - Preferred times\n\n            Args:\n                attendee_email: Attendee to schedule with\n                duration_minutes: Meeting duration needed\n                date_range: Date range to search\n                preferred_times: Preferred time windows\n\n            Returns:\n                List of available slots with scores\n            ", "return_description": "Available time slots"}
        self.tools["get_conflicts"] = {"fn": get_conflicts, "name": "get_conflicts", "description": "Detect calendar conflicts.\n\n            Identifies overlapping events and scheduling issues.\n            Use before creating events to prevent double-booking.\n\n            Args:\n                start_time: Proposed meeting time\n                duration_minutes: Meeting duration\n                organizer_email: Organizer to check\n                attendee_emails: Attendees to check\n\n            Returns:\n                List of conflicting events with severity\n            ", "return_description": "List of conflicts"}
        self.tools["create_task"] = {"fn": create_task, "name": "create_task", "description": "Create task in CRM system.\n\n            Links task to contact and booking records.\n            Use for:\n            - Follow-up reminders\n            - Preparation tasks\n            - Monitoring tasks (high-risk bookings)\n            - VIP follow-ups\n\n            Args:\n                contact_id: Associated contact\n                task_type: Type of task (follow_up, preparation, monitoring, vip_followup)\n                title: Task title\n                due_date: Task due date\n                priority: Task priority (low, medium, high, critical)\n                description: Task details\n\n            Returns:\n                Task ID and creation confirmation\n            ", "return_description": "Task ID and confirmation"}
        self.tools["create_contact"] = {"fn": create_contact, "name": "create_contact", "description": "Create new contact in CRM.\n\n            Adds attendee to CRM system with full profile.\n\n            Args:\n                name: Contact name\n                email: Contact email\n                phone: Contact phone\n                company: Company name\n                industry: Industry sector\n                vip_level: VIP status (standard, preferred, vip, executive)\n\n            Returns:\n                Contact ID and creation status\n            ", "return_description": "Contact ID and status"}
        self.tools["get_contact_history"] = {"fn": get_contact_history, "name": "get_contact_history", "description": "Get contact interaction history.\n\n            Retrieves all past bookings, communications, and notes.\n            Use to understand attendee patterns and preferences.\n\n            Args:\n                contact_id: Contact to lookup\n\n            Returns:\n                Complete interaction history\n            ", "return_description": "Contact history"}
        self.tools["analyze_booking_pattern"] = {"fn": analyze_booking_pattern, "name": "analyze_booking_pattern", "description": "Analyze booking patterns and trends.\n\n            Provides insights on:\n            - No-show rates\n            - Cancellation patterns\n            - Preferred times/days\n            - Attendee reliability\n\n            Args:\n                attendee_email: Email to analyze\n                time_period_days: Analysis period\n\n            Returns:\n                Pattern analysis with trends and recommendations\n            ", "return_description": "Pattern analysis"}
        self.tools["predict_no_show_risk"] = {"fn": predict_no_show_risk, "name": "predict_no_show_risk", "description": "Predict no-show probability.\n\n            Uses ML model to assess no-show risk based on:\n            - Attendee history\n            - Booking characteristics\n            - External factors\n            - Time patterns\n\n            Args:\n                attendee_email: Attendee to assess\n                booking_details: Booking information\n\n            Returns:\n                Risk score (0-100), probability, and recommended actions\n            ", "return_description": "Risk score 0-100, recommendations"}
        self.tools["find_best_time_slot"] = {"fn": find_best_time_slot, "name": "find_best_time_slot", "description": "Find optimal meeting time.\n\n            Considers:\n            - Attendee preferences\n            - Past successful meeting times\n            - Business hours\n            - Timezone alignment\n            - Conflict avoidance\n\n            Args:\n                attendee_email: Attendee to optimize for\n                duration_minutes: Meeting duration\n                date_range: Search window\n\n            Returns:\n                Best time slots with scores and reasoning\n            ", "return_description": "Optimal time slots"}
        self.tools["estimate_booking_value"] = {"fn": estimate_booking_value, "name": "estimate_booking_value", "description": "Estimate booking business value.\n\n            Calculates potential value based on:\n            - Attendee company\n            - Industry standards\n            - Past engagement\n            - Meeting type\n\n            Args:\n                attendee_email: Attendee to assess\n                booking_type: Type of meeting\n\n            Returns:\n                Estimated value in dollars\n            ", "return_description": "Estimated value"}
        self.tools["get_attendee_preferences"] = {"fn": get_attendee_preferences, "name": "get_attendee_preferences", "description": "Get attendee communication preferences.\n\n            Retrieves learned preferences:\n            - Communication channel (email, SMS)\n            - Response time patterns\n            - Preferred meeting times\n            - Meeting format preferences\n\n            Args:\n                attendee_email: Attendee to lookup\n\n            Returns:\n                Preference profile\n            ", "return_description": "Attendee preferences"}
        self.tools["get_booking_history"] = {"fn": get_booking_history, "name": "get_booking_history", "description": "Get attendee booking history.\n\n            Retrieves all past bookings with outcomes.\n            Use to assess reliability and patterns.\n\n            Args:\n                attendee_email: Attendee to lookup\n                limit: Number of bookings to retrieve\n\n            Returns:\n                Booking history with outcomes\n            ", "return_description": "Booking history"}
        self.tools["get_attendee_info"] = {"fn": get_attendee_info, "name": "get_attendee_info", "description": "Get complete attendee information.\n\n            Retrieves profile, history, and preferences.\n\n            Args:\n                attendee_email: Attendee to lookup\n\n            Returns:\n                Complete attendee profile\n            ", "return_description": "Attendee info"}
        self.tools["check_business_rules"] = {"fn": check_business_rules, "name": "check_business_rules", "description": "Check booking against business rules.\n\n            Validates:\n            - VIP requirements\n            - Compliance rules\n            - Scheduling policies\n            - Value thresholds\n\n            Args:\n                booking_details: Booking to validate\n\n            Returns:\n                Compliance status and any issues\n            ", "return_description": "Business rules compliance"}

    def get_tool(self, name: str) -> dict[str, Any] | None:
        """Get a tool by name"""
        return self.tools.get(name)

    def get_all_tools(self) -> list[dict[str, Any]]:
        """Get all registered tools"""
        return list(self.tools.values())

    def get_tool_names(self) -> list[str]:
        """Get list of all tool names"""
        return list(self.tools.keys())

class ReActAgentSetup:
    """
    Setup for LlamaIndex ReAct Agent with GraftAI tools

    ReAct = Reasoning + Acting
    The agent reasons about the problem, then acts using tools
    """

    def __init__(self, llm=None):
        self.tool_wrapper = LlamaIndexToolWrapper()
        self.llm = llm
        self.system_prompt = BOOKING_DECISION_SYSTEM_PROMPT
        logger.info("ReActAgentSetup initialized")

    def create_react_agent(self, tools: list[str] | None=None, verbose: bool=True, max_iterations: int=10) -> ReActAgent:
        """
        Create LlamaIndex ReActAgent with selected tools

        Args:
            tools: List of tool names to include (None = all tools)
            verbose: Enable verbose logging
            max_iterations: Maximum reasoning iterations

        Returns:
            Configured ReActAgent
        """
        try:
            from llama_index.core.agent import ReActAgent
            from llama_index.core.tools import FunctionTool
            if tools is None:
                tool_list = self.tool_wrapper.get_all_tools()
            else:
                tool_list = [self.tool_wrapper.get_tool(name) for name in tools if self.tool_wrapper.get_tool(name)]
            llama_tools = []
            for tool in tool_list:
                llama_tool = FunctionTool.from_defaults(fn=tool["fn"], name=tool["name"], description=tool["description"], return_direct=False)
                llama_tools.append(llama_tool)
            agent = ReActAgent.from_tools(tools=llama_tools, llm=self.llm, verbose=verbose, max_iterations=max_iterations, system_prompt=self.system_prompt)
            logger.info("Created ReActAgent with %s tools", len(llama_tools))
            return agent
        except ImportError:
            logger.exception("LlamaIndex not installed. Install with: pip install llama-index")
            raise
        except Exception as e:
            logger.exception("Failed to create ReActAgent: %s", e)
            raise

    async def execute_with_react(self, user_request: str, tools: list[str] | None=None, context: dict[str, Any] | None=None) -> dict[str, Any]:
        """
        Execute user request using ReAct Agent

        Args:
            user_request: User's natural language request
            tools: Tools to make available
            context: Additional context

        Returns:
            Execution results
        """
        agent = self.create_react_agent(tools=tools)
        if context:
            context_str = self._format_context(context)
            full_request = f"Context: {context_str}\n\nRequest: {user_request}"
        else:
            full_request = user_request
        response = await agent.achat(full_request)
        return {"response": response.response, "sources": response.sources, "tool_calls": self._extract_tool_calls(response), "reasoning": self._extract_reasoning(response)}

    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context for agent"""
        parts = []
        for key, value in context.items():
            parts.append(f"{key}: {value}")
        return "; ".join(parts)

    def _extract_tool_calls(self, response) -> list[dict[str, Any]]:
        """Extract tool calls from response"""
        tool_calls = []
        if hasattr(response, "sources"):
            for source in response.sources:
                if hasattr(source, "tool_name"):
                    tool_calls.append({"tool": source.tool_name, "input": getattr(source, "raw_input", {}), "output": getattr(source, "raw_output", {})})
        return tool_calls

    def _extract_reasoning(self, response) -> str:
        """Extract reasoning steps from response"""
        if hasattr(response, "response"):
            return response.response
        return ""

class HybridAgent:
    """
    Hybrid agent combining LlamaIndex ReAct with GraftAI's 4-phase loop

    Uses ReAct for complex reasoning, falls back to rule-based for speed
    """

    def __init__(self, llm=None):
        self.react_setup = ReActAgentSetup(llm=llm)
        self.use_react_threshold = 0.7
        logger.info("HybridAgent initialized")

    async def process(self, user_request: str, booking: dict[str, Any] | None=None, attendee: dict[str, Any] | None=None, complexity: str="auto") -> dict[str, Any]:
        """
        Process request using best approach

        Args:
            user_request: User's request
            booking: Optional booking data
            attendee: Optional attendee data
            complexity: "simple", "complex", or "auto"

        Returns:
            Processing results
        """
        if complexity == "auto":
            complexity = self._assess_complexity(user_request, booking, attendee)
        if complexity == "complex":
            logger.info("Using ReActAgent for complex request")
            return await self._use_react(user_request, booking, attendee)
        logger.info("Using rule-based approach for simple request")
        return await self._use_rule_based(user_request, booking, attendee)

    def _assess_complexity(self, request: str, booking: dict | None, attendee: dict | None) -> str:
        """Assess request complexity"""
        complexity_score = 0
        complex_keywords = ["optimize", "analyze", "multiple", "conflict", "timezone", "risk", "VIP", "urgent", "emergency", "coordinate"]
        for keyword in complex_keywords:
            if keyword in request.lower():
                complexity_score += 0.2
        if booking:
            if len(booking.get("attendees", [])) > 3:
                complexity_score += 0.3
            if booking.get("timezone_difference", 0) > 3:
                complexity_score += 0.2
        if attendee:
            if attendee.get("vip_level") == "executive":
                complexity_score += 0.2
            if attendee.get("no_show_rate", 0) > 0.3:
                complexity_score += 0.2
        return "complex" if complexity_score > 0.5 else "simple"

    async def _use_react(self, request: str, booking: dict | None, attendee: dict | None) -> dict[str, Any]:
        """Process using ReActAgent"""
        context = {}
        if booking:
            context["booking"] = booking
        if attendee:
            context["attendee"] = attendee
        return await self.react_setup.execute_with_react(user_request=request, context=context)

    async def _use_rule_based(self, request: str, booking: dict | None, attendee: dict | None) -> dict[str, Any]:
        """Process using rule-based decision engine"""
        from backend.ai.decision_engine import create_decision_engine
        engine = await create_decision_engine()
        if booking and attendee:
            decision = await engine.analyze_and_decide(booking=booking, attendee_info=attendee, context={"request": request})
            return {"response": "Decision made using rule-based engine", "decision": decision, "approach": "rule_based"}
        return {"response": "Insufficient data for rule-based processing", "approach": "rule_based", "error": "Missing booking or attendee data"}

async def create_llama_tools() -> LlamaIndexToolWrapper:
    """Create LlamaIndex tool wrapper"""
    return LlamaIndexToolWrapper()

async def create_react_agent(llm=None, tools: list[str] | None=None) -> ReActAgentSetup:
    """Create ReActAgent setup"""
    setup = ReActAgentSetup(llm=llm)
    return setup.create_react_agent(tools=tools)

async def create_hybrid_agent(llm=None) -> HybridAgent:
    """Create hybrid agent"""
    return HybridAgent(llm=llm)

async def example_react_booking():
    """Example: Use ReActAgent for booking"""
    setup = ReActAgentSetup()
    setup.create_react_agent(tools=["send_email", "create_calendar_event", "predict_no_show_risk", "create_task"], verbose=True, max_iterations=5)
    await setup.execute_with_react(user_request="\n        Schedule a high-risk consultation with John Smith (john@example.com).\n        He has 50% no-show rate.\n        Time: tomorrow 2pm, duration 60 minutes.\n        Ensure multiple reminders and monitoring.\n        ", context={"attendee_no_show_rate": 0.5, "booking_value": 500})

async def example_hybrid_processing():
    """Example: Use hybrid agent"""
    hybrid = await create_hybrid_agent()
    await hybrid.process(user_request="Send confirmation email", booking={"title": "Meeting", "start_time": "2024-04-15T14:00:00", "attendees": ["user@example.com"]}, attendee={"email": "user@example.com", "no_show_rate": 0.1})
    await hybrid.process(user_request="\n        Optimize scheduling for VIP executive with multiple timezone attendees\n        who have conflicting schedules. Analyze risk and coordinate.\n        ", booking={"title": "Executive Review", "start_time": "2024-04-15T14:00:00", "attendees": ["exec1@company.com", "exec2@company.com", "exec3@company.com"]}, attendee={"email": "exec1@company.com", "vip_level": "executive", "timezone": "America/New_York"})
if __name__ == "__main__":
    asyncio.run(example_react_booking())
    asyncio.run(example_hybrid_processing())
