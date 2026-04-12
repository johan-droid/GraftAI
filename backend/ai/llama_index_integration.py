"""
LlamaIndex Integration for GraftAI

Provides LlamaIndex ReAct Agent integration with the existing tool system.
Allows using LlamaIndex's reasoning capabilities with GraftAI's tools.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from llama_index.core.agent import ReActAgent

from backend.ai.tools import (
    send_email,
    send_sms,
    post_to_slack,
    send_teams_message,
    create_calendar_event,
    update_calendar_event,
    check_calendar_availability,
    search_available_slots,
    get_conflicts,
    create_contact,
    create_task,
    get_contact_history,
    analyze_booking_pattern,
    predict_no_show_risk,
    find_best_time_slot,
    estimate_booking_value,
    get_attendee_preferences,
    get_booking_history,
    get_attendee_info,
    check_business_rules
)
from backend.ai.prompts import BOOKING_DECISION_SYSTEM_PROMPT
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════
# LLAMAINDEX TOOL WRAPPERS
# ═══════════════════════════════════════════════════════════════════

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
        
        # Communication Tools
        self.tools["send_email"] = {
            "fn": send_email,
            "name": "send_email",
            "description": """Send an email to attendee or contact.
            
            Use for:
            - Booking confirmations
            - Reminders
            - Follow-ups
            - VIP notifications
            
            Templates available: confirmation, reminder, follow_up, vip_welcome, high_risk_confirmation
            Personalizes content based on attendee context and risk level.
            
            Args:
                to: Recipient email address
                subject: Email subject line
                body: Email body content
                template: Optional template name
                
            Returns:
                Email delivery status, message ID, and timestamp
            """,
            "return_description": "Email delivery status and ID"
        }
        
        self.tools["send_sms"] = {
            "fn": send_sms,
            "name": "send_sms",
            "description": """Send SMS message to attendee.
            
            Use for:
            - Urgent reminders
            - High-risk booking alerts
            - VIP notifications
            - Last-minute changes
            
            Best for high-priority communications when email may not be seen promptly.
            
            Args:
                to: Recipient phone number
                message: SMS content (keep under 160 chars for single message)
                
            Returns:
                SMS delivery status and message ID
            """,
            "return_description": "SMS delivery status and ID"
        }
        
        self.tools["post_to_slack"] = {
            "fn": post_to_slack,
            "name": "post_to_slack",
            "description": """Post message to Slack channel.
            
            Use for:
            - Team notifications
            - VIP booking alerts
            - Conflict notifications
            - Team coordination
            
            Args:
                channel: Slack channel name (e.g., #bookings)
                message: Message content
                
            Returns:
                Post status and message ID
            """,
            "return_description": "Slack post status"
        }
        
        self.tools["send_teams_message"] = {
            "fn": send_teams_message,
            "name": "send_teams_message",
            "description": """Send message to Microsoft Teams.
            
            Use for internal team notifications and coordination.
            
            Args:
                team_id: Teams team ID
                channel: Channel name
                message: Message content
                
            Returns:
                Teams message status
            """,
            "return_description": "Teams message status"
        }
        
        # Scheduling Tools
        self.tools["create_calendar_event"] = {
            "fn": create_calendar_event,
            "name": "create_calendar_event",
            "description": """Create or update calendar event.
            
            Automatically:
            - Adjusts for timezone differences
            - Sends calendar invites to attendees
            - Syncs with external calendars (Google, Outlook)
            - Sets up reminders
            - Checks for conflicts
            
            Args:
                title: Event title
                start_time: Event start time (ISO format)
                duration_minutes: Event duration
                attendees: List of attendee emails
                location: Meeting location or video link
                reminder_minutes: Reminder time before event
                
            Returns:
                Calendar event ID, sync status, and invite links
            """,
            "return_description": "Calendar event ID and sync status"
        }
        
        self.tools["update_calendar_event"] = {
            "fn": update_calendar_event,
            "name": "update_calendar_event",
            "description": """Update existing calendar event.
            
            Use to modify time, attendees, or details.
            Automatically notifies all attendees of changes.
            
            Args:
                event_id: Calendar event ID to update
                title: New title (optional)
                start_time: New start time (optional)
                duration_minutes: New duration (optional)
                attendees: Updated attendee list (optional)
                
            Returns:
                Update status and new event details
            """,
            "return_description": "Update status and event details"
        }
        
        self.tools["check_calendar_availability"] = {
            "fn": check_calendar_availability,
            "name": "check_calendar_availability",
            "description": """Check if time slot is available.
            
            Verifies organizer and attendee availability.
            Checks for conflicts and busy times.
            
            Args:
                attendee_email: Email to check
                start_time: Proposed start time
                duration_minutes: Meeting duration
                
            Returns:
                Availability status and conflicting events
            """,
            "return_description": "Availability status and conflicts"
        }
        
        self.tools["search_available_slots"] = {
            "fn": search_available_slots,
            "name": "search_available_slots",
            "description": """Search for available time slots.
            
            Finds optimal meeting times considering:
            - Organizer availability
            - Attendee availability
            - Business hours
            - Preferred times
            
            Args:
                attendee_email: Attendee to schedule with
                duration_minutes: Meeting duration needed
                date_range: Date range to search
                preferred_times: Preferred time windows
                
            Returns:
                List of available slots with scores
            """,
            "return_description": "Available time slots"
        }
        
        self.tools["get_conflicts"] = {
            "fn": get_conflicts,
            "name": "get_conflicts",
            "description": """Detect calendar conflicts.
            
            Identifies overlapping events and scheduling issues.
            Use before creating events to prevent double-booking.
            
            Args:
                start_time: Proposed meeting time
                duration_minutes: Meeting duration
                organizer_email: Organizer to check
                attendee_emails: Attendees to check
                
            Returns:
                List of conflicting events with severity
            """,
            "return_description": "List of conflicts"
        }
        
        # CRM Tools
        self.tools["create_task"] = {
            "fn": create_task,
            "name": "create_task",
            "description": """Create task in CRM system.
            
            Links task to contact and booking records.
            Use for:
            - Follow-up reminders
            - Preparation tasks
            - Monitoring tasks (high-risk bookings)
            - VIP follow-ups
            
            Args:
                contact_id: Associated contact
                task_type: Type of task (follow_up, preparation, monitoring, vip_followup)
                title: Task title
                due_date: Task due date
                priority: Task priority (low, medium, high, critical)
                description: Task details
                
            Returns:
                Task ID and creation confirmation
            """,
            "return_description": "Task ID and confirmation"
        }
        
        self.tools["create_contact"] = {
            "fn": create_contact,
            "name": "create_contact",
            "description": """Create new contact in CRM.
            
            Adds attendee to CRM system with full profile.
            
            Args:
                name: Contact name
                email: Contact email
                phone: Contact phone
                company: Company name
                industry: Industry sector
                vip_level: VIP status (standard, preferred, vip, executive)
                
            Returns:
                Contact ID and creation status
            """,
            "return_description": "Contact ID and status"
        }
        
        self.tools["get_contact_history"] = {
            "fn": get_contact_history,
            "name": "get_contact_history",
            "description": """Get contact interaction history.
            
            Retrieves all past bookings, communications, and notes.
            Use to understand attendee patterns and preferences.
            
            Args:
                contact_id: Contact to lookup
                
            Returns:
                Complete interaction history
            """,
            "return_description": "Contact history"
        }
        
        # Analytics Tools
        self.tools["analyze_booking_pattern"] = {
            "fn": analyze_booking_pattern,
            "name": "analyze_booking_pattern",
            "description": """Analyze booking patterns and trends.
            
            Provides insights on:
            - No-show rates
            - Cancellation patterns
            - Preferred times/days
            - Attendee reliability
            
            Args:
                attendee_email: Email to analyze
                time_period_days: Analysis period
                
            Returns:
                Pattern analysis with trends and recommendations
            """,
            "return_description": "Pattern analysis"
        }
        
        self.tools["predict_no_show_risk"] = {
            "fn": predict_no_show_risk,
            "name": "predict_no_show_risk",
            "description": """Predict no-show probability.
            
            Uses ML model to assess no-show risk based on:
            - Attendee history
            - Booking characteristics
            - External factors
            - Time patterns
            
            Args:
                attendee_email: Attendee to assess
                booking_details: Booking information
                
            Returns:
                Risk score (0-100), probability, and recommended actions
            """,
            "return_description": "Risk score 0-100, recommendations"
        }
        
        self.tools["find_best_time_slot"] = {
            "fn": find_best_time_slot,
            "name": "find_best_time_slot",
            "description": """Find optimal meeting time.
            
            Considers:
            - Attendee preferences
            - Past successful meeting times
            - Business hours
            - Timezone alignment
            - Conflict avoidance
            
            Args:
                attendee_email: Attendee to optimize for
                duration_minutes: Meeting duration
                date_range: Search window
                
            Returns:
                Best time slots with scores and reasoning
            """,
            "return_description": "Optimal time slots"
        }
        
        self.tools["estimate_booking_value"] = {
            "fn": estimate_booking_value,
            "name": "estimate_booking_value",
            "description": """Estimate booking business value.
            
            Calculates potential value based on:
            - Attendee company
            - Industry standards
            - Past engagement
            - Meeting type
            
            Args:
                attendee_email: Attendee to assess
                booking_type: Type of meeting
                
            Returns:
                Estimated value in dollars
            """,
            "return_description": "Estimated value"
        }
        
        self.tools["get_attendee_preferences"] = {
            "fn": get_attendee_preferences,
            "name": "get_attendee_preferences",
            "description": """Get attendee communication preferences.
            
            Retrieves learned preferences:
            - Communication channel (email, SMS)
            - Response time patterns
            - Preferred meeting times
            - Meeting format preferences
            
            Args:
                attendee_email: Attendee to lookup
                
            Returns:
                Preference profile
            """,
            "return_description": "Attendee preferences"
        }
        
        # Query Tools
        self.tools["get_booking_history"] = {
            "fn": get_booking_history,
            "name": "get_booking_history",
            "description": """Get attendee booking history.
            
            Retrieves all past bookings with outcomes.
            Use to assess reliability and patterns.
            
            Args:
                attendee_email: Attendee to lookup
                limit: Number of bookings to retrieve
                
            Returns:
                Booking history with outcomes
            """,
            "return_description": "Booking history"
        }
        
        self.tools["get_attendee_info"] = {
            "fn": get_attendee_info,
            "name": "get_attendee_info",
            "description": """Get complete attendee information.
            
            Retrieves profile, history, and preferences.
            
            Args:
                attendee_email: Attendee to lookup
                
            Returns:
                Complete attendee profile
            """,
            "return_description": "Attendee info"
        }
        
        self.tools["check_business_rules"] = {
            "fn": check_business_rules,
            "name": "check_business_rules",
            "description": """Check booking against business rules.
            
            Validates:
            - VIP requirements
            - Compliance rules
            - Scheduling policies
            - Value thresholds
            
            Args:
                booking_details: Booking to validate
                
            Returns:
                Compliance status and any issues
            """,
            "return_description": "Business rules compliance"
        }
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def get_tool_names(self) -> List[str]:
        """Get list of all tool names"""
        return list(self.tools.keys())


# ═══════════════════════════════════════════════════════════════════
# REACT AGENT SETUP
# ═══════════════════════════════════════════════════════════════════

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
    
    def create_react_agent(
        self,
        tools: Optional[List[str]] = None,
        verbose: bool = True,
        max_iterations: int = 10
    ) -> "ReActAgent":
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
            # Import LlamaIndex components
            from llama_index.core.agent import ReActAgent
            from llama_index.core.tools import FunctionTool
            
            # Get selected tools
            if tools is None:
                tool_list = self.tool_wrapper.get_all_tools()
            else:
                tool_list = [
                    self.tool_wrapper.get_tool(name)
                    for name in tools
                    if self.tool_wrapper.get_tool(name)
                ]
            
            # Convert to LlamaIndex FunctionTools
            llama_tools = []
            for tool in tool_list:
                llama_tool = FunctionTool.from_defaults(
                    fn=tool["fn"],
                    name=tool["name"],
                    description=tool["description"],
                    return_direct=False
                )
                llama_tools.append(llama_tool)
            
            # Create ReActAgent
            agent = ReActAgent.from_tools(
                tools=llama_tools,
                llm=self.llm,
                verbose=verbose,
                max_iterations=max_iterations,
                system_prompt=self.system_prompt
            )
            
            logger.info(f"Created ReActAgent with {len(llama_tools)} tools")
            return agent
            
        except ImportError:
            logger.error("LlamaIndex not installed. Install with: pip install llama-index")
            raise
        except Exception as e:
            logger.error(f"Failed to create ReActAgent: {e}")
            raise
    
    async def execute_with_react(
        self,
        user_request: str,
        tools: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
        
        # Add context to request if provided
        if context:
            context_str = self._format_context(context)
            full_request = f"Context: {context_str}\n\nRequest: {user_request}"
        else:
            full_request = user_request
        
        # Execute
        response = await agent.achat(full_request)
        
        return {
            "response": response.response,
            "sources": response.sources,
            "tool_calls": self._extract_tool_calls(response),
            "reasoning": self._extract_reasoning(response)
        }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for agent"""
        parts = []
        for key, value in context.items():
            parts.append(f"{key}: {value}")
        return "; ".join(parts)
    
    def _extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        """Extract tool calls from response"""
        tool_calls = []
        if hasattr(response, 'sources'):
            for source in response.sources:
                if hasattr(source, 'tool_name'):
                    tool_calls.append({
                        "tool": source.tool_name,
                        "input": getattr(source, 'raw_input', {}),
                        "output": getattr(source, 'raw_output', {})
                    })
        return tool_calls
    
    def _extract_reasoning(self, response) -> str:
        """Extract reasoning steps from response"""
        if hasattr(response, 'response'):
            return response.response
        return ""


# ═══════════════════════════════════════════════════════════════════
# HYBRID AGENT (LlamaIndex + Existing System)
# ═══════════════════════════════════════════════════════════════════

class HybridAgent:
    """
    Hybrid agent combining LlamaIndex ReAct with GraftAI's 4-phase loop
    
    Uses ReAct for complex reasoning, falls back to rule-based for speed
    """
    
    def __init__(self, llm=None):
        self.react_setup = ReActAgentSetup(llm=llm)
        self.use_react_threshold = 0.7  # Confidence threshold for ReAct
        
        logger.info("HybridAgent initialized")
    
    async def process(
        self,
        user_request: str,
        booking: Optional[Dict[str, Any]] = None,
        attendee: Optional[Dict[str, Any]] = None,
        complexity: str = "auto"
    ) -> Dict[str, Any]:
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
        # Determine approach
        if complexity == "auto":
            complexity = self._assess_complexity(user_request, booking, attendee)
        
        if complexity == "complex":
            # Use ReAct for complex scenarios
            logger.info("Using ReActAgent for complex request")
            return await self._use_react(user_request, booking, attendee)
        else:
            # Use fast rule-based approach
            logger.info("Using rule-based approach for simple request")
            return await self._use_rule_based(user_request, booking, attendee)
    
    def _assess_complexity(
        self,
        request: str,
        booking: Optional[Dict],
        attendee: Optional[Dict]
    ) -> str:
        """Assess request complexity"""
        complexity_score = 0
        
        # Check for complex keywords
        complex_keywords = [
            "optimize", "analyze", "multiple", "conflict", "timezone",
            "risk", "VIP", "urgent", "emergency", "coordinate"
        ]
        for keyword in complex_keywords:
            if keyword in request.lower():
                complexity_score += 0.2
        
        # Check booking complexity
        if booking:
            if len(booking.get("attendees", [])) > 3:
                complexity_score += 0.3
            if booking.get("timezone_difference", 0) > 3:
                complexity_score += 0.2
        
        # Check attendee complexity
        if attendee:
            if attendee.get("vip_level") == "executive":
                complexity_score += 0.2
            if attendee.get("no_show_rate", 0) > 0.3:
                complexity_score += 0.2
        
        return "complex" if complexity_score > 0.5 else "simple"
    
    async def _use_react(
        self,
        request: str,
        booking: Optional[Dict],
        attendee: Optional[Dict]
    ) -> Dict[str, Any]:
        """Process using ReActAgent"""
        context = {}
        if booking:
            context["booking"] = booking
        if attendee:
            context["attendee"] = attendee
        
        return await self.react_setup.execute_with_react(
            user_request=request,
            context=context
        )
    
    async def _use_rule_based(
        self,
        request: str,
        booking: Optional[Dict],
        attendee: Optional[Dict]
    ) -> Dict[str, Any]:
        """Process using rule-based decision engine"""
        from backend.ai.decision_engine import create_decision_engine
        
        engine = await create_decision_engine()
        
        if booking and attendee:
            decision = await engine.analyze_and_decide(
                booking=booking,
                attendee_info=attendee,
                context={"request": request}
            )
            
            return {
                "response": "Decision made using rule-based engine",
                "decision": decision,
                "approach": "rule_based"
            }
        else:
            return {
                "response": "Insufficient data for rule-based processing",
                "approach": "rule_based",
                "error": "Missing booking or attendee data"
            }


# ═══════════════════════════════════════════════════════════════════
# FACTORY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def create_llama_tools() -> LlamaIndexToolWrapper:
    """Create LlamaIndex tool wrapper"""
    return LlamaIndexToolWrapper()


async def create_react_agent(
    llm=None,
    tools: Optional[List[str]] = None
) -> ReActAgentSetup:
    """Create ReActAgent setup"""
    setup = ReActAgentSetup(llm=llm)
    return setup.create_react_agent(tools=tools)


async def create_hybrid_agent(llm=None) -> HybridAgent:
    """Create hybrid agent"""
    return HybridAgent(llm=llm)


# ═══════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════

async def example_react_booking():
    """Example: Use ReActAgent for booking"""
    
    setup = ReActAgentSetup()
    
    # Create agent with all tools
    agent = setup.create_react_agent(
        tools=[
            "send_email",
            "create_calendar_event",
            "predict_no_show_risk",
            "create_task"
        ],
        verbose=True,
        max_iterations=5
    )
    
    # Execute booking request
    result = await setup.execute_with_react(
        user_request="""
        Schedule a high-risk consultation with John Smith (john@example.com).
        He has 50% no-show rate. 
        Time: tomorrow 2pm, duration 60 minutes.
        Ensure multiple reminders and monitoring.
        """,
        context={
            "attendee_no_show_rate": 0.5,
            "booking_value": 500
        }
    )
    
    print(f"ReAct Response: {result['response']}")
    print(f"Tool Calls: {len(result['tool_calls'])}")
    print(f"Reasoning: {result['reasoning'][:200]}...")


async def example_hybrid_processing():
    """Example: Use hybrid agent"""
    
    hybrid = await create_hybrid_agent()
    
    # Simple request - will use rule-based
    result1 = await hybrid.process(
        user_request="Send confirmation email",
        booking={
            "title": "Meeting",
            "start_time": "2024-04-15T14:00:00",
            "attendees": ["user@example.com"]
        },
        attendee={
            "email": "user@example.com",
            "no_show_rate": 0.1
        }
    )
    print(f"Simple request: {result1['approach']}")
    
    # Complex request - will use ReAct
    result2 = await hybrid.process(
        user_request="""
        Optimize scheduling for VIP executive with multiple timezone attendees
        who have conflicting schedules. Analyze risk and coordinate.
        """,
        booking={
            "title": "Executive Review",
            "start_time": "2024-04-15T14:00:00",
            "attendees": [
                "exec1@company.com",
                "exec2@company.com",
                "exec3@company.com"
            ]
        },
        attendee={
            "email": "exec1@company.com",
            "vip_level": "executive",
            "timezone": "America/New_York"
        }
    )
    print(f"Complex request: {result2['approach']}")


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_react_booking())
    asyncio.run(example_hybrid_processing())
