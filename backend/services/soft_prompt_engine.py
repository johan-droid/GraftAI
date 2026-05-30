"""
Soft Prompt Engine for AI Automation

This service manages prompt templates, context building, and confidence scoring
for AI-driven automation tasks in GraftAI.

Features:
- Prompt template management with variables
- Context-aware prompt building
- Confidence scoring for AI actions
- Multi-turn conversation context
- Personality customization
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)

class PromptPersonality(StrEnum):
    """AI assistant personality types."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    CONCISE = "concise"
    DETAILED = "detailed"
    FRIENDLY = "friendly"

class AutomationTier(StrEnum):
    """Automation confidence tiers."""
    DRAFT = "draft"
    TRUSTED = "trusted"
    FULL_AUTO = "full_auto"

@dataclass
class PromptTemplate:
    """Prompt template with variable substitution."""
    id: str
    name: str
    template: str
    variables: list[str] = field(default_factory=list)
    personality: PromptPersonality = PromptPersonality.PROFESSIONAL
    category: str = "general"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

@dataclass
class PromptContext:
    """Context for prompt generation."""
    user_id: str
    timezone: str
    current_time: datetime
    calendar_events: list[dict[str, Any]] = field(default_factory=list)
    recent_emails: list[dict[str, Any]] = field(default_factory=list)
    user_preferences: dict[str, Any] = field(default_factory=list)
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PromptResult:
    """Result of prompt generation."""
    system_prompt: str
    user_prompt: str
    confidence_score: float
    suggested_action: dict[str, Any] | None = None
    automation_tier: AutomationTier = AutomationTier.DRAFT
    reasoning: str = ""

class SoftPromptEngine:
    """
    Engine for generating context-aware prompts with confidence scoring.

    Uses soft prompting techniques to guide AI behavior while maintaining
    flexibility for natural language understanding.
    """

    def __init__(self):
        self.templates: dict[str, PromptTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default prompt templates."""
        self.templates["schedule_meeting"] = PromptTemplate(id="schedule_meeting", name="Schedule Meeting", template="You are GraftAI, a professional scheduling assistant.\n\nCURRENT CONTEXT:\n- User Timezone: {timezone}\n- Current Time: {current_time}\n- Upcoming Events: {events_summary}\n\nUSER REQUEST:\n{user_message}\n\nINSTRUCTIONS:\n1. Extract meeting details (title, time, duration, attendees)\n2. Check for conflicts with existing events\n3. Suggest optimal times if conflicts exist\n4. Provide confidence score for your suggestions\n\nRESPONSE FORMAT:\n- **Title**: [meeting title]\n- **Time**: [proposed time]\n- **Duration**: [duration in minutes]\n- **Confidence**: [0-100]\n- **Reasoning**: [brief explanation]", variables=["timezone", "current_time", "events_summary", "user_message"], personality=PromptPersonality.PROFESSIONAL, category="calendar")
        self.templates["reschedule_meeting"] = PromptTemplate(id="reschedule_meeting", name="Reschedule Meeting", template="You are GraftAI, helping reschedule a meeting.\n\nCURRENT CONTEXT:\n- User Timezone: {timezone}\n- Current Time: {current_time}\n- Event to Reschedule: {event_details}\n- Available Slots: {available_slots}\n\nUSER REQUEST:\n{user_message}\n\nINSTRUCTIONS:\n1. Understand the rescheduling request\n2. Find the best alternative time from available slots\n3. Consider attendee availability if provided\n4. Provide confidence for your suggestion\n\nRESPONSE FORMAT:\n- **New Time**: [proposed time]\n- **Reason for Change**: [why this time works]\n- **Confidence**: [0-100]", variables=["timezone", "current_time", "event_details", "available_slots", "user_message"], personality=PromptPersonality.PROFESSIONAL, category="calendar")
        self.templates["resolve_conflict"] = PromptTemplate(id="resolve_conflict", name="Resolve Scheduling Conflict", template="You are GraftAI, resolving a calendar conflict.\n\nCONFLICT DETAILS:\n- Conflicting Events: {conflicting_events}\n- User Preferences: {preferences}\n\nINSTRUCTIONS:\n1. Analyze the conflict severity\n2. Propose resolution options:\n   - Move one event\n   - Split/shorten events\n   - Find alternative time\n3. Rank options by confidence\n\nRESPONSE FORMAT:\n- **Conflict Severity**: [low/medium/high]\n- **Option 1**: [description] - Confidence: [0-100]\n- **Option 2**: [description] - Confidence: [0-100]\n- **Recommendation**: [best option with reasoning]", variables=["conflicting_events", "preferences"], personality=PromptPersonality.PROFESSIONAL, category="calendar")
        self.templates["team_availability"] = PromptTemplate(id="team_availability", name="Find Team Availability", template="You are GraftAI, finding optimal meeting times for a team.\n\nTEAM CONTEXT:\n- Team Members: {team_members}\n- Individual Availability: {member_availability}\n- Meeting Duration: {duration}\n- Timezone: {timezone}\n\nINSTRUCTIONS:\n1. Find overlapping availability slots\n2. Consider time zone differences\n3. Prioritize business hours for all members\n4. Provide confidence for each suggestion\n\nRESPONSE FORMAT:\n- **Best Slot**: [time] - Confidence: [0-100]\n- **Alternative 1**: [time] - Confidence: [0-100]\n- **Alternative 2**: [time] - Confidence: [0-100]", variables=["team_members", "member_availability", "duration", "timezone"], personality=PromptPersonality.PROFESSIONAL, category="team")
        self.templates["book_resource"] = PromptTemplate(id="book_resource", name="Book Resource", template="You are GraftAI, helping book a resource (room, equipment, etc.).\n\nRESOURCE CONTEXT:\n- Resource Type: {resource_type}\n- Available Resources: {available_resources}\n- Resource Capacity: {capacity}\n- Time Requirements: {time_requirements}\n\nINSTRUCTIONS:\n1. Find the best resource for the need\n2. Check availability for requested time\n3. Suggest alternatives if not available\n4. Provide confidence for your recommendation\n\nRESPONSE FORMAT:\n- **Recommended Resource**: [resource name]\n- **Time**: [booking time]\n- **Reasoning**: [why this resource]\n- **Confidence**: [0-100]", variables=["resource_type", "available_resources", "capacity", "time_requirements"], personality=PromptPersonality.PROFESSIONAL, category="resource")

    def register_template(self, template: PromptTemplate) -> None:
        """Register a new prompt template."""
        self.templates[template.id] = template
        logger.info("Registered template: %s", template.id)

    def get_template(self, template_id: str) -> PromptTemplate | None:
        """Get a template by ID."""
        return self.templates.get(template_id)

    def list_templates(self, category: str | None=None) -> list[PromptTemplate]:
        """List templates, optionally filtered by category."""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates

    def build_prompt(self, template_id: str, context: PromptContext, personality_override: PromptPersonality | None=None) -> PromptResult:
        """
        Build a prompt from a template with context substitution.

        Args:
            template_id: ID of the template to use
            context: Context data for variable substitution
            personality_override: Override template personality

        Returns:
            PromptResult with generated prompts and confidence score
        """
        template = self.get_template(template_id)
        if not template:
            msg = f"Template not found: {template_id}"
            raise ValueError(msg)
        variables = self._build_variables(template, context)
        user_prompt = template.template
        for var_name, var_value in variables.items():
            user_prompt = user_prompt.replace(f"{{{var_name}}}", str(var_value))
        personality = personality_override or template.personality
        system_prompt = self._build_system_prompt(personality)
        confidence = self._calculate_confidence(template_id, context, variables)
        automation_tier = self._determine_automation_tier(confidence, template_id, context)
        suggested_action = self._generate_suggested_action(template_id, variables, confidence)
        reasoning = self._build_reasoning(template_id, context, confidence)
        return PromptResult(system_prompt=system_prompt, user_prompt=user_prompt, confidence_score=confidence, suggested_action=suggested_action, automation_tier=automation_tier, reasoning=reasoning)

    def _build_variables(self, template: PromptTemplate, context: PromptContext) -> dict[str, str]:
        """Build variable values from context."""
        variables = {}
        for var_name in template.variables:
            if var_name == "timezone":
                variables[var_name] = context.timezone
            elif var_name == "current_time":
                variables[var_name] = context.current_time.strftime("%Y-%m-%d %H:%M %Z")
            elif var_name == "user_message":
                if context.conversation_history:
                    last_user_msg = next((msg for msg in reversed(context.conversation_history) if msg.get("role") == "user"), "")
                    variables[var_name] = last_user_msg
                else:
                    variables[var_name] = ""
            elif var_name == "events_summary":
                variables[var_name] = self._format_events_summary(context.calendar_events)
            elif var_name == "event_details":
                variables[var_name] = self._format_event_details(context.metadata.get("event"))
            elif var_name == "available_slots":
                variables[var_name] = self._format_available_slots(context.metadata.get("slots", []))
            elif var_name == "conflicting_events":
                variables[var_name] = self._format_conflicting_events(context.metadata.get("conflicts", []))
            elif var_name == "preferences":
                variables[var_name] = json.dumps(context.user_preferences)
            elif var_name == "team_members":
                variables[var_name] = self._format_team_members(context.metadata.get("team_members", []))
            elif var_name == "member_availability":
                variables[var_name] = self._format_member_availability(context.metadata.get("availability", {}))
            elif var_name == "duration":
                variables[var_name] = str(context.metadata.get("duration", 30))
            elif var_name == "resource_type":
                variables[var_name] = context.metadata.get("resource_type", "room")
            elif var_name == "available_resources":
                variables[var_name] = self._format_resources(context.metadata.get("resources", []))
            elif var_name == "capacity":
                variables[var_name] = str(context.metadata.get("capacity", "any"))
            elif var_name == "time_requirements":
                variables[var_name] = self._format_time_requirements(context.metadata)
            else:
                variables[var_name] = str(context.metadata.get(var_name, ""))
        return variables

    def _build_system_prompt(self, personality: PromptPersonality) -> str:
        """Build system prompt based on personality."""
        base_prompt = "You are GraftAI, an intelligent scheduling assistant."
        personality_prompts = {PromptPersonality.PROFESSIONAL: "Be professional, concise, and efficient. Focus on providing actionable information without unnecessary pleasantries.", PromptPersonality.CASUAL: "Be friendly and approachable while remaining helpful. Use a conversational tone.", PromptPersonality.CONCISE: "Be extremely brief and to the point. Use bullet points and minimal text. No filler words.", PromptPersonality.DETAILED: "Provide comprehensive information with full explanations. Include all relevant details and context.", PromptPersonality.FRIENDLY: "Be warm and helpful. Use encouraging language and show enthusiasm."}
        return f"{base_prompt} {personality_prompts.get(personality, personality_prompts[PromptPersonality.PROFESSIONAL])}"

    def _calculate_confidence(self, template_id: str, context: PromptContext, variables: dict[str, str]) -> float:
        """
        Calculate confidence score for the prompt/action.

        Confidence factors:
        - Information completeness (0-40 points)
        - Context quality (0-30 points)
        - Pattern matching (0-20 points)
        - User history (0-10 points)
        """
        score = 0.0
        required_vars = self.templates[template_id].variables
        provided_vars = sum(1 for var in required_vars if variables.get(var) and variables[var].strip())
        score += provided_vars / len(required_vars) * 40 if required_vars else 40
        if context.calendar_events:
            score += 10
        if context.user_preferences:
            score += 10
        if context.conversation_history:
            score += 10
        if context.conversation_history:
            last_msg = next((msg for msg in reversed(context.conversation_history) if msg.get("role") == "user"), {})
            if last_msg.get("content"):
                content = last_msg["content"].lower()
                intent_keywords = {"schedule_meeting": ["schedule", "book", "meeting", "call"], "reschedule_meeting": ["reschedule", "move", "change", "update"], "resolve_conflict": ["conflict", "overlap", "double book"], "team_availability": ["team", "everyone", "group"], "book_resource": ["room", "desk", "equipment", "resource"]}
                keywords = intent_keywords.get(template_id, [])
                if any(kw in content for kw in keywords):
                    score += 20
        score += 5
        return min(score, 100.0)

    def _determine_automation_tier(self, confidence: float, template_id: str, context: PromptContext) -> AutomationTier:
        """
        Determine automation tier based on confidence and context.

        - DRAFT (0-60): User confirmation required
        - TRUSTED (60-85): Auto-schedule with notification
        - FULL_AUTO (85-100): Process without UI blocker
        """
        if confidence >= 85:
            if template_id in ["schedule_meeting", "book_resource"]:
                if context.metadata.get("is_recurring"):
                    return AutomationTier.TRUSTED
                return AutomationTier.FULL_AUTO
            return AutomationTier.TRUSTED
        if confidence >= 60:
            return AutomationTier.TRUSTED
        return AutomationTier.DRAFT

    def _generate_suggested_action(self, template_id: str, variables: dict[str, str], confidence: float) -> dict[str, Any] | None:
        """Generate a suggested action based on the prompt."""
        if confidence < 60:
            return None
        action = {"type": template_id, "confidence": confidence}
        if template_id == "schedule_meeting":
            action["action"] = "create_event"
            action["data"] = {"title": variables.get("user_message", "Meeting")[:100], "duration": 30}
        elif template_id == "reschedule_meeting":
            action["action"] = "update_event"
            action["data"] = {"event_id": variables.get("event_details", "")}
        return action

    def _build_reasoning(self, template_id: str, context: PromptContext, confidence: float) -> str:
        """Build reasoning explanation for the confidence score."""
        reasons = []
        if confidence >= 80:
            reasons.append("High information completeness")
        if context.calendar_events:
            reasons.append("Rich calendar context available")
        if context.user_preferences:
            reasons.append("User preferences known")
        if confidence < 60:
            reasons.append("Missing key information")
        return "; ".join(reasons) if reasons else "Standard confidence based on available context"

    def _format_events_summary(self, events: list[dict[str, Any]]) -> str:
        """Format calendar events for prompt."""
        if not events:
            return "No upcoming events"
        summaries = []
        for event in events[:5]:
            title = event.get("title", "Untitled")
            start = event.get("start_time", "")
            summaries.append(f"- {title} at {start}")
        return "\n".join(summaries)

    def _format_event_details(self, event: dict[str, Any] | None) -> str:
        """Format single event details."""
        if not event:
            return "No event specified"
        return f"{event.get('title', 'Untitled')} at {event.get('start_time', '')}"

    def _format_available_slots(self, slots: list[dict[str, Any]]) -> str:
        """Format available time slots."""
        if not slots:
            return "No available slots"
        formatted = []
        for slot in slots[:5]:
            formatted.append(f"- {slot.get('start', '')} to {slot.get('end', '')}")
        return "\n".join(formatted)

    def _format_conflicting_events(self, conflicts: list[dict[str, Any]]) -> str:
        """Format conflicting events."""
        if not conflicts:
            return "No conflicts"
        formatted = []
        for conflict in conflicts:
            formatted.append(f"- {conflict.get('title', 'Event')} at {conflict.get('time', '')}")
        return "\n".join(formatted)

    def _format_team_members(self, members: list[dict[str, Any]]) -> str:
        """Format team members list."""
        if not members:
            return "No team members"
        return ", ".join([m.get("name", "Unknown") for m in members])

    def _format_member_availability(self, availability: dict[str, Any]) -> str:
        """Format member availability."""
        if not availability:
            return "No availability data"
        formatted = []
        for member, slots in availability.items():
            formatted.append(f"- {member}: {len(slots)} available slots")
        return "\n".join(formatted)

    def _format_resources(self, resources: list[dict[str, Any]]) -> str:
        """Format available resources."""
        if not resources:
            return "No resources available"
        formatted = []
        for resource in resources[:5]:
            formatted.append(f"- {resource.get('name', 'Unknown')} ({resource.get('type', 'resource')})")
        return "\n".join(formatted)

    def _format_time_requirements(self, metadata: dict[str, Any]) -> str:
        """Format time requirements."""
        return f"Start: {metadata.get('start_time', 'flexible')}, Duration: {metadata.get('duration', 30)}min"
soft_prompt_engine = SoftPromptEngine()
