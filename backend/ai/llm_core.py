"""
LLaMA Model Core for GraftAI
Handles natural language understanding, decision making, and tool selection
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
import os
import json
from groq import AsyncGroq
from dataclasses import dataclass
from enum import Enum
import re
from backend.utils.logger import get_logger

# Optional: Async OpenAI client for streaming responses
try:
    from openai import AsyncOpenAI

    _OPENAI_AVAILABLE = True
except Exception:
    AsyncOpenAI = None  # type: ignore
    _OPENAI_AVAILABLE = False
from backend.ai.prompts import (
    BOOKING_DECISION_SYSTEM_PROMPT,
    AGENT_SYSTEM_PROMPT,
    HUMANIZED_SYSTEM_PROMPT,
    format_agent_cognition_prompt,
)

logger = get_logger(__name__)


class LLaMAModel(Enum):
    """Available LLaMA model variants"""

    LLAMA_3_3_70B = "llama-3.3-70b-versatile"
    LLAMA_3_1_70B = "llama-3.1-70b-versatile"
    LLAMA_3_1_8B = "llama-3.1-8b-instant"
    LLAMA_3_1_405B = "llama-3.1-405b-reasoning"


@dataclass
class LLMResponse:
    """Structured response from LLM"""

    content: str
    tool_calls: List[Dict[str, Any]]
    reasoning: Optional[str] = None
    confidence: float = 0.0
    tokens_used: int = 0


@dataclass
class ConversationMessage:
    """Single message in conversation"""

    role: str  # system, user, assistant
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict] = None


class LLaMACore:
    """
    Core LLaMA integration for GraftAI

    Responsibilities:
    - Natural language understanding
    - Decision making and reasoning
    - Tool selection and function calling
    - Context maintenance across conversations
    - Response generation
    """

    def __init__(self, model: LLaMAModel = LLaMAModel.LLAMA_3_1_70B):
        self.model = model
        # prefer the HUMANIZED_SYSTEM_PROMPT for system behavior
        self.system_prompt = HUMANIZED_SYSTEM_PROMPT
        self.tools: List[Dict[str, Any]] = []

        # Initialize AsyncGroq client for Groq API if configured
        self.client = None
        try:
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                self.client = AsyncGroq(api_key=groq_key)
                logger.info(f"AsyncGroq client initialized for model: {self.model}")
        except Exception as e:
            logger.warning(f"Failed to initialize AsyncGroq client: {e}")

        logger.info(f"LLaMACore initialized with model: {model.value}")

    def _load_system_prompt(self) -> str:
        """Load the system prompt for the scheduling assistant"""
        # Use the comprehensive agent system prompt
        return AGENT_SYSTEM_PROMPT

    def set_booking_decision_mode(self):
        """Switch to booking decision mode with specialized prompt"""
        self.system_prompt = BOOKING_DECISION_SYSTEM_PROMPT
        logger.info("LLaMACore switched to booking decision mode")

    def set_agent_mode(self):
        """Switch to general agent mode"""
        self.system_prompt = AGENT_SYSTEM_PROMPT
        logger.info("LLaMACore switched to agent mode")

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any]):
        """Register a tool that the LLM can call"""
        tool = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self.tools.append(tool)
        logger.info(f"Registered tool: {name}")

    async def _get_history(self, conversation_id: str) -> List[ConversationMessage]:
        """Retrieve conversation history from Redis."""
        try:
            from backend.core.redis import cache_get
            key = f"chat_history:{conversation_id}"
            data = await cache_get(key)
            if data and isinstance(data, list):
                return [
                    ConversationMessage(
                        role=m["role"],
                        content=m["content"],
                        timestamp=m.get("timestamp"),
                        metadata=m.get("metadata")
                    ) for m in data
                ]
        except Exception as e:
            logger.error(f"Failed to retrieve chat history from Redis: {e}")
        return []

    async def _save_history(self, conversation_id: str, history: List[ConversationMessage]):
        """Save conversation history to Redis."""
        try:
            from backend.core.redis import cache_set
            key = f"chat_history:{conversation_id}"
            data = [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata
                } for m in history
            ]
            await cache_set(key, data, expire=3600 * 24) # 24 hour retention
        except Exception as e:
            logger.error(f"Failed to save chat history to Redis: {e}")

    async def generate_response(
        self,
        user_message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Generate a response to user message

        Args:
            user_message: The user's input message
            user_id: User identifier
            conversation_id: Optional conversation ID for context
            context: Additional context (calendar data, preferences, etc.)

        Returns:
            LLMResponse with content and any tool calls
        """
        # Normalize conversation_id so it is never None
        if conversation_id is None:
            import uuid

            conversation_id = str(uuid.uuid4())

        # Get or create conversation history
        history = await self._get_history(conversation_id)

        # Build messages
        messages = [ConversationMessage(role="system", content=self.system_prompt)]

        # Add context if provided
        if context:
            context_str = self._format_context(context)
            messages.append(ConversationMessage(role="system", content=context_str))

        # Add conversation history
        messages.extend(history)

        # Add user message
        messages.append(ConversationMessage(role="user", content=user_message))

        # Call LLM
        response = await self._call_llm(messages)

        # Parse tool calls if any
        tool_calls = self._parse_tool_calls(response.content)

        # Update conversation history
        history.append(ConversationMessage(role="user", content=user_message))
        history.append(
            ConversationMessage(
                role="assistant",
                content=response.content,
                metadata={"tool_calls": tool_calls},
            )
        )

        # Keep history manageable
        if len(history) > 20:
            history = history[-20:]

        await self._save_history(conversation_id, history)

        return LLMResponse(
            content=response.content,
            tool_calls=tool_calls,
            reasoning=response.reasoning,
            confidence=response.confidence,
            tokens_used=response.tokens_used,
        )

    async def generate_json_response(
        self, messages: List[ConversationMessage]
    ) -> LLMResponse:
        """
        Public wrapper for JSON-required LLM responses.
        """
        return await self._call_llm(messages, require_json=True)

    async def generate_streaming_response(
        self,
        user_message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response

        Yields:
            Chunks of the response as they become available
        """
        # Ensure conversation_id exists
        if conversation_id is None:
            import uuid

            conversation_id = str(uuid.uuid4())

        # Build ConversationMessage list
        messages_cm: List[ConversationMessage] = [
            ConversationMessage(role="system", content=self.system_prompt)
        ]

        if context:
            context_str = self._format_context(context)
            messages_cm.append(ConversationMessage(role="system", content=context_str))

        history = await self._get_history(conversation_id)
        messages_cm.extend(history)

        messages_cm.append(ConversationMessage(role="user", content=user_message))

        # Stream via Groq if client available
        full_response = ""
        if self.client is not None:
            try:
                formatted_messages = [
                    {"role": m.role, "content": m.content} for m in messages_cm
                ]
                stream = await self.client.chat.completions.create(
                    model=self.model.value,
                    messages=formatted_messages,
                    stream=True,
                    temperature=0.7,
                )

                async for chunk in stream:
                    try:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            text = delta.content
                        elif isinstance(delta, dict):
                            text = delta.get("content")
                        else:
                            text = None
                    except Exception:
                        text = None

                    if text:
                        full_response += text
                        yield text

            except Exception as e:
                full_response = ""
                logger.warning(
                    f"Groq streaming failed, falling back to local streamer: {e}"
                )

        # Fallback
        if not full_response:
            async for chunk in self._stream_llm(messages_cm):
                full_response += chunk
                yield chunk

        # Update conversation history
        if conversation_id:
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []

            self.conversation_history[conversation_id].append(
                ConversationMessage(role="user", content=user_message)
            )
            self.conversation_history[conversation_id].append(
                ConversationMessage(role="assistant", content=full_response)
            )

    async def make_decision(
        self, decision_context: Dict[str, Any], options: List[str], criteria: List[str]
    ) -> Dict[str, Any]:
        """
        Make a decision based on context and criteria

        Args:
            decision_context: Information about the decision to be made
            options: Available options
            criteria: Decision criteria

        Returns:
            Decision with reasoning
        """
        prompt = f"""You are an intelligent decision-making assistant. Analyze the following situation and make the best decision.

CONTEXT:
{json.dumps(decision_context, indent=2)}

OPTIONS:
{chr(10).join(f"{i + 1}. {opt}" for i, opt in enumerate(options))}

DECISION CRITERIA:
{chr(10).join(f"- {c}" for c in criteria)}

Please:
1. Analyze each option against the criteria
2. Select the best option
3. Provide clear reasoning
4. Assign a confidence score (0-1)

Respond in this JSON format:
{{
    "decision": "selected_option",
    "confidence": 0.95,
    "reasoning": "detailed explanation",
    "option_analysis": {{
        "option1": "analysis",
        "option2": "analysis"
    }}
}}"""

        messages = [ConversationMessage(role="user", content=prompt)]
        response = await self._call_llm(messages, require_json=True)

        # Parse JSON response
        try:
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError:
            logger.error(f"Failed to parse decision response: {response.content}")
            return {
                "decision": options[0] if options else None,
                "confidence": 0.5,
                "reasoning": "Failed to parse LLM response",
                "option_analysis": {},
            }

    async def select_tools(
        self, user_intent: str, available_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Select appropriate tools based on user intent

        Args:
            user_intent: What the user wants to accomplish
            available_tools: List of available tools

        Returns:
            Selected tools with parameters
        """
        tools_str = json.dumps(available_tools, indent=2)

        prompt = f"""Given the user's intent, select the appropriate tools to accomplish their goal.

USER INTENT: {user_intent}

AVAILABLE TOOLS:
{tools_str}

Select the tools needed and provide parameters. Respond in JSON format:
[
    {{
        "tool": "tool_name",
        "parameters": {{"param1": "value1"}},
        "reasoning": "why this tool is needed"
    }}
]"""

        messages = [ConversationMessage(role="user", content=prompt)]
        response = await self._call_llm(messages, require_json=True)

        try:
            selected_tools = json.loads(response.content)
            return selected_tools if isinstance(selected_tools, list) else []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse tool selection: {response.content}")
            return []

    async def understand_context(
        self, message: str, previous_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract intent, entities, and context from a message

        Args:
            message: User message to analyze
            previous_context: Previous conversation context

        Returns:
            Structured understanding of the message
        """
        prompt = f"""Analyze the following message and extract key information.

MESSAGE: "{message}"

Extract and respond in JSON format:
{{
    "intent": "primary_intent (schedule_meeting, check_availability, etc.)",
    "entities": {{
        "dates": ["2024-04-15"],
        "times": ["14:00"],
        "people": ["john@example.com"],
        "duration": 60,
        "meeting_title": "Project Review"
    }},
    "sentiment": "positive/neutral/negative",
    "urgency": "low/medium/high",
    "clarification_needed": ["missing_info_1", "missing_info_2"],
    "suggested_response": "how to respond to this message"
}}"""

        messages = [ConversationMessage(role="user", content=prompt)]
        response = await self._call_llm(messages, require_json=True)

        try:
            understanding = json.loads(response.content)
            return understanding
        except json.JSONDecodeError:
            logger.error(f"Failed to parse understanding: {response.content}")
            return {
                "intent": "unknown",
                "entities": {},
                "sentiment": "neutral",
                "urgency": "low",
                "clarification_needed": ["Could you please clarify your request?"],
                "suggested_response": "I'm not sure I understood. Could you provide more details?",
            }

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
            logger.info(f"Cleared conversation: {conversation_id}")

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context data for LLM"""
        parts = ["CURRENT CONTEXT:"]

        if "user_preferences" in context:
            parts.append(f"User Preferences: {json.dumps(context['user_preferences'])}")

        if "calendar_summary" in context:
            parts.append(f"Calendar: {context['calendar_summary']}")

        if "availability" in context:
            parts.append(f"Availability: {context['availability']}")

        if "upcoming_meetings" in context:
            meetings = context["upcoming_meetings"]
            parts.append(f"Upcoming Meetings: {len(meetings)} in next 7 days")

        return "\n".join(parts)

    def _parse_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response"""
        tool_calls = []

        # Look for function calls in various formats
        # Format 1: ```json {...} ```
        json_pattern = r"```(?:json)?\s*({[\s\S]*?})\s*```"
        json_matches = re.findall(json_pattern, content)

        for match in json_matches:
            try:
                data = json.loads(match)
                if "function" in data or "tool" in data:
                    tool_calls.append(data)
            except json.JSONDecodeError:
                continue

        # Format 2: <tool> tags
        tool_pattern = r"<tool>(.*?)</tool>"
        tool_matches = re.findall(tool_pattern, content, re.DOTALL)

        for match in tool_matches:
            try:
                data = json.loads(match.strip())
                tool_calls.append(data)
            except json.JSONDecodeError:
                continue

        return tool_calls

    async def _call_llm(
        self, messages: List[ConversationMessage], require_json: bool = False
    ) -> LLMResponse:
        """
        Call the LLM (Groq preferred) for completions.

        If `require_json` is True, request structured JSON from the model.
        """
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        response_format = {"type": "json_object"} if require_json else None

        # Try Groq first
        if self.client is not None:
            try:
                completion = await self.client.chat.completions.create(
                    model=self.model.value,
                    messages=formatted_messages,
                    response_format=response_format,
                    temperature=0.2 if require_json else 0.7,
                )

                # Extract content and token usage
                content = None
                tokens = 0
                try:
                    choice = completion.choices[0]
                    # Groq's SDK may provide message.content
                    content = (
                        getattr(choice, "message", {}).get("content")
                        if isinstance(choice, dict)
                        else getattr(choice.message, "content", None)
                    )
                except Exception:
                    # Fallback: try to access as nested dict
                    try:
                        content = completion.choices[0]["message"]["content"]
                    except Exception:
                        content = getattr(completion, "text", None) or ""

                try:
                    tokens = (
                        getattr(completion, "usage", {}).get("total_tokens", 0)
                        if isinstance(completion, dict)
                        else getattr(completion.usage, "total_tokens", 0)
                    )
                except Exception:
                    tokens = 0

                return LLMResponse(
                    content=content or "", tool_calls=[], tokens_used=int(tokens)
                )

            except Exception as e:
                logger.error(f"Groq API Error: {e}")
                # Fall through to local fallback below

        # 🔴 [DEGRADED MODE] Fallback: simple rule-based placeholder (retained for offline/dev)
        logger.warning("System entered DEGRADED MODE: Using keyword-based fallback logic")
        last_message = messages[-1].content if messages else ""

        if "schedule" in last_message.lower() or "book" in last_message.lower():
            content = "I'd be happy to help you schedule a meeting. To get started, I'll need a few details: 1) Meeting title 2) Date/time 3) Duration 4) Attendees."
        elif "availability" in last_message.lower() or "free" in last_message.lower():
            content = "I can check availability. Please provide the date range or a proposed time."
        else:
            content = "How can I help with your schedule today?"

        return LLMResponse(
            content=content,
            tool_calls=[],
            reasoning="fallback",
            confidence=0.6,
            tokens_used=0,
        )

    async def _stream_llm(
        self, messages: List[ConversationMessage]
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from LLaMA (placeholder)

        In production, this would connect to streaming API endpoint
        """
        # If Groq client is available, stream directly from it
        if self.client is not None:
            try:
                formatted_messages = [
                    {"role": m.role, "content": m.content} for m in messages
                ]
                stream = await self.client.chat.completions.create(
                    model=self.model.value,
                    messages=formatted_messages,
                    stream=True,
                    temperature=0.7,
                )

                async for chunk in stream:
                    try:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            yield delta.content
                        elif isinstance(delta, dict) and delta.get("content"):
                            yield delta.get("content")
                    except Exception:
                        continue
                return
            except Exception as e:
                logger.error(f"Groq Streaming Error: {str(e)}")

        # Fallback: return full response as single chunk and yield words
        response = await self._call_llm(messages)
        words = response.content.split()
        for word in words:
            yield word + " "

    async def generate_booking_decision(
        self, booking: Dict[str, Any], attendee: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate decision for booking automation using specialized prompt

        Args:
            booking: Booking data
            attendee: Attendee data

        Returns:
            Decision JSON with actions, risk assessment, etc.
        """
        # Switch to booking decision mode
        self.set_booking_decision_mode()

        # Format the booking decision prompt
        from backend.ai.prompts.booking_prompts import format_prompt_from_booking_data

        prompt = format_prompt_from_booking_data(booking, attendee)

        # Build messages
        messages = [
            ConversationMessage(role="system", content=self.system_prompt),
            ConversationMessage(role="user", content=prompt),
        ]

        # Generate response (expect JSON)
        response = await self._call_llm(messages, require_json=True)

        # Parse JSON response
        try:
            decision = json.loads(response.content)
            logger.info(
                f"Booking decision generated: {decision.get('risk_assessment')}"
            )
            return decision
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse decision JSON: {e}")
            # Return fallback decision
            return self._generate_fallback_decision(booking, attendee)

    async def generate_agent_cognition(
        self, phase: str, context: Dict[str, Any], available_tools: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate cognition response for a specific agent phase

        Args:
            phase: One of "perception", "cognition", "action", "reflection"
            context: Context data for the phase
            available_tools: List of available tool names

        Returns:
            Cognition response with decisions, plans, etc.
        """
        # Switch to agent mode
        self.set_agent_mode()

        # Format the phase-specific prompt
        prompt = format_agent_cognition_prompt(phase, context, available_tools)

        # Build messages
        messages = [
            ConversationMessage(role="system", content=self.system_prompt),
            ConversationMessage(role="user", content=prompt),
        ]

        # Generate response (expect JSON)
        response = await self._call_llm(messages, require_json=True)

        # Parse JSON response
        try:
            cognition = json.loads(response.content)
            logger.info(f"Agent cognition generated for phase {phase}")
            return cognition
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse cognition JSON: {e}")
            # Return fallback cognition
            return self._generate_fallback_cognition(phase, context)

    def _generate_fallback_decision(
        self, booking: Dict[str, Any], attendee: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback decision when LLM fails"""
        # Use rule-based fallback
        no_show_rate = attendee.get("no_show_rate", 0)

        if no_show_rate > 0.3:
            # High-risk booking
            return {
                "actions": [
                    {"type": "send_email", "priority": "critical"},
                    {"type": "send_sms", "priority": "high"},
                    {"type": "create_task", "priority": "high"},
                ],
                "risk_assessment": "high",
                "confidence": 0.7,
                "special_handling": "High-risk booking - extra reminders",
            }
        else:
            # Standard booking
            return {
                "actions": [
                    {"type": "send_email", "priority": "medium"},
                    {"type": "create_calendar_event", "priority": "medium"},
                ],
                "risk_assessment": "low",
                "confidence": 0.8,
                "special_handling": "None",
            }

    def _generate_fallback_cognition(
        self, phase: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback cognition when LLM fails"""
        if phase == "cognition":
            return {
                "analysis": {
                    "goal": context.get("current_goal", "Complete task"),
                    "selected_approach": "Standard approach",
                },
                "plan": {
                    "steps": [
                        {
                            "step": 1,
                            "action": "execute_primary_tool",
                            "priority": "high",
                        }
                    ]
                },
                "confidence": 0.7,
            }
        elif phase == "reflection":
            return {
                "assessment": {"overall": "success"},
                "learnings": {"successful_strategies": []},
                "confidence": 0.7,
            }
        else:
            return {"confidence": 0.7}


# Global instance
_llm_core: Optional[LLaMACore] = None


async def get_llm_core() -> LLaMACore:
    """Get or create the global LLM core"""
    global _llm_core
    if _llm_core is None:
        _llm_core = LLaMACore()
    return _llm_core
