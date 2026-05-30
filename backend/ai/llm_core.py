"""
LLaMA Model Core for GraftAI
Handles natural language understanding, decision making, and tool selection
"""
import json
import os
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.utils.logger import get_logger
from groq import AsyncGroq

try:
    from openai import AsyncOpenAI
    _OPENAI_AVAILABLE = True
except Exception:
    AsyncOpenAI = None
    _OPENAI_AVAILABLE = False
from backend.ai.prompts import (
    AGENT_SYSTEM_PROMPT,
    BOOKING_DECISION_SYSTEM_PROMPT,
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
    tool_calls: list[dict[str, Any]]
    reasoning: str | None = None
    confidence: float = 0.0
    tokens_used: int = 0

@dataclass
class ConversationMessage:
    """Single message in conversation"""
    role: str
    content: str
    timestamp: str | None = None
    metadata: dict | None = None

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

    def __init__(self, model: LLaMAModel=LLaMAModel.LLAMA_3_1_70B):
        self.model = model
        self.system_prompt = HUMANIZED_SYSTEM_PROMPT
        self.tools: list[dict[str, Any]] = []
        self.client = None
        try:
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                self.client = AsyncGroq(api_key=groq_key)
                logger.info("AsyncGroq client initialized for model: %s", self.model)
        except Exception as e:
            logger.warning("Failed to initialize AsyncGroq client: %s", e)
        logger.info("LLaMACore initialized with model: %s", model.value)

    def _load_system_prompt(self) -> str:
        """Load the system prompt for the scheduling assistant"""
        return AGENT_SYSTEM_PROMPT

    def set_booking_decision_mode(self):
        """Switch to booking decision mode with specialized prompt"""
        self.system_prompt = BOOKING_DECISION_SYSTEM_PROMPT
        logger.info("LLaMACore switched to booking decision mode")

    def set_agent_mode(self):
        """Switch to general agent mode"""
        self.system_prompt = AGENT_SYSTEM_PROMPT
        logger.info("LLaMACore switched to agent mode")

    def register_tool(self, name: str, description: str, parameters: dict[str, Any]):
        """Register a tool that the LLM can call"""
        tool = {"type": "function", "function": {"name": name, "description": description, "parameters": parameters}}
        self.tools.append(tool)
        logger.info("Registered tool: %s", name)

    async def _get_history(self, conversation_id: str) -> list[ConversationMessage]:
        """Retrieve conversation history from Redis."""
        try:
            from backend.core.redis import cache_get
            key = f"chat_history:{conversation_id}"
            data = await cache_get(key)
            if data and isinstance(data, list):
                return [ConversationMessage(role=m["role"], content=m["content"], timestamp=m.get("timestamp"), metadata=m.get("metadata")) for m in data]
        except Exception as e:
            logger.exception("Failed to retrieve chat history from Redis: %s", e)
        return []

    async def _save_history(self, conversation_id: str, history: list[ConversationMessage]):
        """Save conversation history to Redis."""
        try:
            from backend.core.redis import cache_set
            key = f"chat_history:{conversation_id}"
            data = [{"role": m.role, "content": m.content, "timestamp": m.timestamp, "metadata": m.metadata} for m in history]
            await cache_set(key, data, expire=3600 * 24)
        except Exception as e:
            logger.exception("Failed to save chat history to Redis: %s", e)

    async def generate_response(self, user_message: str, user_id: str, conversation_id: str | None=None, context: dict[str, Any] | None=None) -> LLMResponse:
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
        if conversation_id is None:
            import uuid
            conversation_id = str(uuid.uuid4())
        history = await self._get_history(conversation_id)
        messages = [ConversationMessage(role="system", content=self.system_prompt)]
        if context:
            context_str = self._format_context(context)
            messages.append(ConversationMessage(role="system", content=context_str))
        messages.extend(history)
        messages.append(ConversationMessage(role="user", content=user_message))
        response = await self._call_llm(messages)
        tool_calls = self._parse_tool_calls(response.content)
        history.append(ConversationMessage(role="user", content=user_message))
        history.append(ConversationMessage(role="assistant", content=response.content, metadata={"tool_calls": tool_calls}))
        if len(history) > 20:
            history = history[-20:]
        await self._save_history(conversation_id, history)
        return LLMResponse(content=response.content, tool_calls=tool_calls, reasoning=response.reasoning, confidence=response.confidence, tokens_used=response.tokens_used)

    async def generate_json_response(self, messages: list[ConversationMessage]) -> LLMResponse:
        """
        Public wrapper for JSON-required LLM responses.
        """
        return await self._call_llm(messages, require_json=True)

    async def generate_streaming_response(self, user_message: str, user_id: str, conversation_id: str | None=None, context: dict[str, Any] | None=None) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response

        Yields:
            Chunks of the response as they become available
        """
        if conversation_id is None:
            import uuid
            conversation_id = str(uuid.uuid4())
        messages_cm: list[ConversationMessage] = [ConversationMessage(role="system", content=self.system_prompt)]
        if context:
            context_str = self._format_context(context)
            messages_cm.append(ConversationMessage(role="system", content=context_str))
        history = await self._get_history(conversation_id)
        messages_cm.extend(history)
        messages_cm.append(ConversationMessage(role="user", content=user_message))
        full_response = ""
        if self.client is not None:
            try:
                formatted_messages = [{"role": m.role, "content": m.content} for m in messages_cm]
                stream = await self.client.chat.completions.create(model=self.model.value, messages=formatted_messages, stream=True, temperature=0.7)
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
                logger.warning("Groq streaming failed, falling back to local streamer: %s", e)
        if not full_response:
            async for chunk in self._stream_llm(messages_cm):
                full_response += chunk
                yield chunk
        if conversation_id:
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            self.conversation_history[conversation_id].append(ConversationMessage(role="user", content=user_message))
            self.conversation_history[conversation_id].append(ConversationMessage(role="assistant", content=full_response))

    async def make_decision(self, decision_context: dict[str, Any], options: list[str], criteria: list[str]) -> dict[str, Any]:
        """
        Make a decision based on context and criteria

        Args:
            decision_context: Information about the decision to be made
            options: Available options
            criteria: Decision criteria

        Returns:
            Decision with reasoning
        """
        prompt = f"""You are an intelligent decision-making assistant. Analyze the following situation and make the best decision.\n\nCONTEXT:\n{json.dumps(decision_context, indent=2)}\n\nOPTIONS:\n{chr(10).join((f'{i + 1}. {opt}' for i, opt in enumerate(options)))}\n\nDECISION CRITERIA:\n{chr(10).join(f'- {c}' for c in criteria)}\n\nPlease:\n1. Analyze each option against the criteria\n2. Select the best option\n3. Provide clear reasoning\n4. Assign a confidence score (0-1)\n\nRespond in this JSON format:\n{{\n    "decision": "selected_option",\n    "confidence": 0.95,\n    "reasoning": "detailed explanation",\n    "option_analysis": {{\n        "option1": "analysis",\n        "option2": "analysis"\n    }}\n}}"""
        messages = [ConversationMessage(role="user", content=prompt)]
        response = await self._call_llm(messages, require_json=True)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            logger.exception("Failed to parse decision response: %s", response.content)
            return {"decision": options[0] if options else None, "confidence": 0.5, "reasoning": "Failed to parse LLM response", "option_analysis": {}}

    async def select_tools(self, user_intent: str, available_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Select appropriate tools based on user intent

        Args:
            user_intent: What the user wants to accomplish
            available_tools: List of available tools

        Returns:
            Selected tools with parameters
        """
        tools_str = json.dumps(available_tools, indent=2)
        prompt = f"""Given the user's intent, select the appropriate tools to accomplish their goal.\n\nUSER INTENT: {user_intent}\n\nAVAILABLE TOOLS:\n{tools_str}\n\nSelect the tools needed and provide parameters. Respond in JSON format:\n[\n    {{\n        "tool": "tool_name",\n        "parameters": {{"param1": "value1"}},\n        "reasoning": "why this tool is needed"\n    }}\n]"""
        messages = [ConversationMessage(role="user", content=prompt)]
        response = await self._call_llm(messages, require_json=True)
        try:
            selected_tools = json.loads(response.content)
            return selected_tools if isinstance(selected_tools, list) else []
        except json.JSONDecodeError:
            logger.exception("Failed to parse tool selection: %s", response.content)
            return []

    async def understand_context(self, message: str, previous_context: dict[str, Any] | None=None) -> dict[str, Any]:
        """
        Extract intent, entities, and context from a message

        Args:
            message: User message to analyze
            previous_context: Previous conversation context

        Returns:
            Structured understanding of the message
        """
        prompt = f'Analyze the following message and extract key information.\n\nMESSAGE: "{message}"\n\nExtract and respond in JSON format:\n{{\n    "intent": "primary_intent (schedule_meeting, check_availability, etc.)",\n    "entities": {{\n        "dates": ["2024-04-15"],\n        "times": ["14:00"],\n        "people": ["john@example.com"],\n        "duration": 60,\n        "meeting_title": "Project Review"\n    }},\n    "sentiment": "positive/neutral/negative",\n    "urgency": "low/medium/high",\n    "clarification_needed": ["missing_info_1", "missing_info_2"],\n    "suggested_response": "how to respond to this message"\n}}'
        messages = [ConversationMessage(role="user", content=prompt)]
        response = await self._call_llm(messages, require_json=True)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            logger.exception("Failed to parse understanding: %s", response.content)
            return {"intent": "unknown", "entities": {}, "sentiment": "neutral", "urgency": "low", "clarification_needed": ["Could you please clarify your request?"], "suggested_response": "I'm not sure I understood. Could you provide more details?"}

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
            logger.info("Cleared conversation: %s", conversation_id)

    def _format_context(self, context: dict[str, Any]) -> str:
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

    def _parse_tool_calls(self, content: str) -> list[dict[str, Any]]:
        """Parse tool calls from LLM response"""
        tool_calls = []
        json_pattern = "```(?:json)?\\s*({[\\s\\S]*?})\\s*```"
        json_matches = re.findall(json_pattern, content)
        for match in json_matches:
            try:
                data = json.loads(match)
                if "function" in data or "tool" in data:
                    tool_calls.append(data)
            except json.JSONDecodeError:
                continue
        tool_pattern = "<tool>(.*?)</tool>"
        tool_matches = re.findall(tool_pattern, content, re.DOTALL)
        for match in tool_matches:
            try:
                data = json.loads(match.strip())
                tool_calls.append(data)
            except json.JSONDecodeError:
                continue
        return tool_calls

    async def _call_llm(self, messages: list[ConversationMessage], require_json: bool=False) -> LLMResponse:
        """
        Call the LLM (Groq preferred) for completions.

        If `require_json` is True, request structured JSON from the model.
        """
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        response_format = {"type": "json_object"} if require_json else None
        if self.client is not None:
            try:
                completion = await self.client.chat.completions.create(model=self.model.value, messages=formatted_messages, response_format=response_format, temperature=0.2 if require_json else 0.7)
                content = None
                tokens = 0
                try:
                    choice = completion.choices[0]
                    content = getattr(choice, "message", {}).get("content") if isinstance(choice, dict) else getattr(choice.message, "content", None)
                except Exception:
                    try:
                        content = completion.choices[0]["message"]["content"]
                    except Exception:
                        content = getattr(completion, "text", None) or ""
                try:
                    tokens = getattr(completion, "usage", {}).get("total_tokens", 0) if isinstance(completion, dict) else getattr(completion.usage, "total_tokens", 0)
                except Exception:
                    tokens = 0
                return LLMResponse(content=content or "", tool_calls=[], tokens_used=int(tokens))
            except Exception as e:
                logger.exception("Groq API Error: %s", e)
        logger.warning("System entered DEGRADED MODE: Using keyword-based fallback logic")
        last_message = messages[-1].content if messages else ""
        if "schedule" in last_message.lower() or "book" in last_message.lower():
            content = "I'd be happy to help you schedule a meeting. To get started, I'll need a few details: 1) Meeting title 2) Date/time 3) Duration 4) Attendees."
        elif "availability" in last_message.lower() or "free" in last_message.lower():
            content = "I can check availability. Please provide the date range or a proposed time."
        else:
            content = "How can I help with your schedule today?"
        return LLMResponse(content=content, tool_calls=[], reasoning="fallback", confidence=0.6, tokens_used=0)

    async def _stream_llm(self, messages: list[ConversationMessage]) -> AsyncGenerator[str, None]:
        """
        Stream response from LLaMA (placeholder)

        In production, this would connect to streaming API endpoint
        """
        if self.client is not None:
            try:
                formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
                stream = await self.client.chat.completions.create(model=self.model.value, messages=formatted_messages, stream=True, temperature=0.7)
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
                logger.exception("Groq Streaming Error: %s", e)
        response = await self._call_llm(messages)
        words = response.content.split()
        for word in words:
            yield (word + " ")

    async def generate_booking_decision(self, booking: dict[str, Any], attendee: dict[str, Any]) -> dict[str, Any]:
        """
        Generate decision for booking automation using specialized prompt

        Args:
            booking: Booking data
            attendee: Attendee data

        Returns:
            Decision JSON with actions, risk assessment, etc.
        """
        self.set_booking_decision_mode()
        from backend.ai.prompts.booking_prompts import format_prompt_from_booking_data
        prompt = format_prompt_from_booking_data(booking, attendee)
        messages = [ConversationMessage(role="system", content=self.system_prompt), ConversationMessage(role="user", content=prompt)]
        response = await self._call_llm(messages, require_json=True)
        try:
            decision = json.loads(response.content)
            logger.info("Booking decision generated: %s", decision.get("risk_assessment"))
            return decision
        except json.JSONDecodeError as e:
            logger.exception("Failed to parse decision JSON: %s", e)
            return self._generate_fallback_decision(booking, attendee)

    async def generate_agent_cognition(self, phase: str, context: dict[str, Any], available_tools: list[str] | None=None) -> dict[str, Any]:
        """
        Generate cognition response for a specific agent phase

        Args:
            phase: One of "perception", "cognition", "action", "reflection"
            context: Context data for the phase
            available_tools: List of available tool names

        Returns:
            Cognition response with decisions, plans, etc.
        """
        self.set_agent_mode()
        prompt = format_agent_cognition_prompt(phase, context, available_tools)
        messages = [ConversationMessage(role="system", content=self.system_prompt), ConversationMessage(role="user", content=prompt)]
        response = await self._call_llm(messages, require_json=True)
        try:
            cognition = json.loads(response.content)
            logger.info("Agent cognition generated for phase %s", phase)
            return cognition
        except json.JSONDecodeError as e:
            logger.exception("Failed to parse cognition JSON: %s", e)
            return self._generate_fallback_cognition(phase, context)

    def _generate_fallback_decision(self, booking: dict[str, Any], attendee: dict[str, Any]) -> dict[str, Any]:
        """Generate fallback decision when LLM fails"""
        no_show_rate = attendee.get("no_show_rate", 0)
        if no_show_rate > 0.3:
            return {"actions": [{"type": "send_email", "priority": "critical"}, {"type": "send_sms", "priority": "high"}, {"type": "create_task", "priority": "high"}], "risk_assessment": "high", "confidence": 0.7, "special_handling": "High-risk booking - extra reminders"}
        return {"actions": [{"type": "send_email", "priority": "medium"}, {"type": "create_calendar_event", "priority": "medium"}], "risk_assessment": "low", "confidence": 0.8, "special_handling": "None"}

    def _generate_fallback_cognition(self, phase: str, context: dict[str, Any]) -> dict[str, Any]:
        """Generate fallback cognition when LLM fails"""
        if phase == "cognition":
            return {"analysis": {"goal": context.get("current_goal", "Complete task"), "selected_approach": "Standard approach"}, "plan": {"steps": [{"step": 1, "action": "execute_primary_tool", "priority": "high"}]}, "confidence": 0.7}
        if phase == "reflection":
            return {"assessment": {"overall": "success"}, "learnings": {"successful_strategies": []}, "confidence": 0.7}
        return {"confidence": 0.7}
_llm_core: LLaMACore | None = None

async def get_llm_core() -> LLaMACore:
    """Get or create the global LLM core"""
    global _llm_core
    if _llm_core is None:
        _llm_core = LLaMACore()
    return _llm_core
