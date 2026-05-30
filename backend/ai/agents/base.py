"""
Base Agent class for GraftAI - Single Agent Loop Architecture
Agent = LLM + Memory + Tools + Loop

The 4-Phase Agent Loop:
1. PERCEPTION - Receive trigger, read memory, get context, understand state
2. COGNITION - Think about goal, consider options, plan steps, decide actions
3. ACTION - Call tools, execute functions, update systems, record results
4. REFLECTION - Check outcomes, learn from results, update memory, improve next time
"""
import asyncio
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from backend.ai.memory.multi_layer_memory import MemoryLayer, MemoryPriority
from backend.utils.logger import get_logger

logger = get_logger(__name__)
MAX_EPISODIC_MEMORY_ITEMS = 100
SLOW_PHASE_THRESHOLD_MS = 1000

class AgentTimeoutError(Exception):
    """Raised when an agent phase exceeds its timeout limit."""

class AgentState(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    READY = "ready"
    PERCEIVING = "perceiving"
    COGNIZING = "cognizing"
    ACTING = "acting"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class AgentPhase(Enum):
    """The 4 phases of the agent loop"""
    PERCEPTION = "perception"
    COGNITION = "cognition"
    ACTION = "action"
    REFLECTION = "reflection"
PHASE_TIMEOUTS = {AgentPhase.PERCEPTION: 15.0, AgentPhase.COGNITION: 15.0, AgentPhase.ACTION: 15.0, AgentPhase.REFLECTION: 15.0}

@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_processing_time_ms: float = 0.0
    last_request_time: datetime | None = None
    errors: list = field(default_factory=list)
    phase_times: dict[str, float] = field(default_factory=dict)

@dataclass
class AgentMemory:
    """
    Agent's working memory during execution

    Uses Multi-Layer Memory Architecture:
    - short_term: ShortTermMemory (current execution)
    - medium_term: MediumTermMemory (session/user level)
    - long_term: LongTermMemory (persistent knowledge)

    Also maintains backward compatibility with simple dict interface
    """
    short_term: dict[str, Any] = field(default_factory=dict)
    long_term: dict[str, Any] = field(default_factory=dict)
    episodic: list[dict[str, Any]] = field(default_factory=list)
    learnings: list[dict[str, Any]] = field(default_factory=list)
    manager: Any | None = None
    context: Any | None = None

@dataclass
class AgentContext:
    """Context passed to agents during execution"""
    user_id: str
    request_id: str
    data: dict[str, Any]
    memory: AgentMemory = field(default_factory=AgentMemory)
    tools_available: list[dict[str, Any]] = field(default_factory=list)
    llm_client: Any | None = None
    phase_results: dict[str, Any] = field(default_factory=dict)

class BaseAgent:
    """
    Base class for all AI agents in GraftAI

    Implements the Single Agent Loop: Perception → Cognition → Action → Reflection

    Agent = LLM + Memory + Tools + Loop

    Specialized agents:
    - BookingAgent: Validates and routes bookings
    - OptimizationAgent: Analyzes patterns and optimizes timing
    - ExecutionAgent: Executes actions with retry logic
    - MonitoringAgent: Tracks outcomes and alerts
    """

    def __init__(self, name: str, description: str=""):
        self.name = name
        self.description = description
        self.state = AgentState.IDLE
        self.metrics = AgentMetrics()
        self.controller: Any | None = None
        self.memory: dict[str, Any] = {}
        self.logger = logger
        self._lock = asyncio.Lock()
        self.tools: dict[str, Any] = {}
        logger.info("Agent %s initializing", name)

    async def initialize(self):
        """Initialize the agent - override in subclass"""
        self.state = AgentState.READY
        logger.info("Agent %s ready", self.name)

    def transition_to(self, new_state: AgentState):
        """Transition the agent to a new lifecycle state."""
        if not isinstance(new_state, AgentState):
            error_message = "new_state must be an AgentState"
            raise TypeError(error_message)
        self.state = new_state

    async def perception_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def cognition_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def action_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def reflection_phase(self, context: dict[str, Any], results: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def execute(self, request: Any) -> dict[str, Any]:
        """
        Execute the complete 4-phase agent loop

        Phase 1: PERCEPTION - Understand the situation
        Phase 2: COGNITION - Think and plan
        Phase 3: ACTION - Execute tools
        Phase 4: REFLECTION - Learn and improve

        Returns:
            Complete result with all phase outputs
        """
        async with self._lock:
            if self.state != AgentState.READY:
                error_message = f"Agent {self.name} not ready (state: {self.state.value})"
                raise RuntimeError(error_message)
            self.metrics.total_requests += 1
            loop_start = datetime.now(UTC)
            context = AgentContext(user_id=request.user_id, request_id=request.id, data=request.context, tools_available=self._get_available_tools(), memory=AgentMemory(), phase_results={})
            result = {"agent": self.name, "request_id": request.id, "phases": {}, "success": False, "error": None}
            try:
                self.state = AgentState.PERCEIVING
                phase_start = datetime.now(UTC)
                perception = await self._execute_phase_with_timeout("perception", self._phase_perception, context, timeout_sec=PHASE_TIMEOUTS[AgentPhase.PERCEPTION])
                context.phase_results["perception"] = perception
                context.memory.short_term["perception"] = perception
                result["phases"]["perception"] = {"status": "completed", "time_ms": (datetime.now(UTC) - phase_start).total_seconds() * 1000, "understanding": perception.get("understanding"), "trigger": perception.get("trigger")}
                self.state = AgentState.COGNIZING
                phase_start = datetime.now(UTC)
                cognition = await self._execute_phase_with_timeout("cognition", self._phase_cognition, context, timeout_sec=PHASE_TIMEOUTS[AgentPhase.COGNITION])
                context.phase_results["cognition"] = cognition
                context.memory.short_term["plan"] = cognition.get("plan")
                context.memory.short_term["decision"] = cognition.get("decision")
                result["phases"]["cognition"] = {"status": "completed", "time_ms": (datetime.now(UTC) - phase_start).total_seconds() * 1000, "goal": cognition.get("goal"), "plan": cognition.get("plan"), "decision": cognition.get("decision")}
                self.state = AgentState.ACTING
                phase_start = datetime.now(UTC)
                action = await self._execute_phase_with_timeout("action", self._phase_action, context, timeout_sec=PHASE_TIMEOUTS[AgentPhase.ACTION])
                context.phase_results["action"] = action
                context.memory.short_term["results"] = action.get("results")
                result["phases"]["action"] = {"status": "completed", "time_ms": (datetime.now(UTC) - phase_start).total_seconds() * 1000, "tools_called": action.get("tools_called", []), "results": action.get("results"), "systems_updated": action.get("systems_updated", [])}
                self.state = AgentState.REFLECTING
                phase_start = datetime.now(UTC)
                reflection = await self._execute_phase_with_timeout("reflection", lambda ctx: self._phase_reflection(ctx, result), context, timeout_sec=PHASE_TIMEOUTS[AgentPhase.REFLECTION])
                context.phase_results["reflection"] = reflection
                result["phases"]["reflection"] = {"status": "completed", "time_ms": (datetime.now(UTC) - phase_start).total_seconds() * 1000, "outcome": reflection.get("outcome"), "learnings": reflection.get("learnings", []), "improvements": reflection.get("improvements", [])}
                total_time = (datetime.now(UTC) - loop_start).total_seconds() * 1000
                self.metrics.successful_requests += 1
                self._update_average_time(total_time)
                result["success"] = True
                result["total_time_ms"] = total_time
                result["final_output"] = action.get("final_output")
                self.state = AgentState.READY
                logger.info("Agent %s completed 4-phase loop in %.2fms", self.name, total_time)
            except Exception as e:
                self.metrics.failed_requests += 1
                self.metrics.errors.append({"timestamp": datetime.now(UTC).isoformat(), "error": str(e), "request_id": request.id, "phase": self.state.value})
                result["success"] = False
                result["error"] = str(e)
                result["failed_phase"] = self.state.value
                logger.exception("Agent %s failed in %s", self.name, self.state.value)
                self.state = AgentState.ERROR
                await self._handle_error_with_reflection(e, context, result)
            return result

    async def _execute_phase_with_timeout(self, phase_name: str, phase_func, context: AgentContext, timeout_sec: float=25.0) -> dict[str, Any]:
        """Forces a hard timeout on AI operations to prevent server DoS."""
        try:
            return await asyncio.wait_for(phase_func(context), timeout=timeout_sec)
        except TimeoutError:
            self.logger.critical("CRITICAL: Agent phase '%s' timed out after %ss.", phase_name, timeout_sec)
            self.state = AgentState.ERROR
            error_message = f"AI Provider timeout during {phase_name} phase after {timeout_sec}s."
            raise AgentTimeoutError(error_message) from None

    async def _phase_perception(self, context: AgentContext) -> dict[str, Any]:
        """
        PHASE 1: PERCEPTION

        Receive trigger → Read memory → Get context → Understand state

        Uses Multi-Layer Memory:
        - Short-term: Current conversation, recent tools
        - Medium-term: User preferences, recent patterns, contextual rules
        - Long-term: Historical episodes, best practices

        Returns:
            perception_data: {
                "trigger": what activated the agent,
                "context_summary": summary of situation,
                "understanding": structured understanding,
                "relevant_memories": retrieved memories from all layers,
                "current_state": inferred state
            }
        """
        logger.info("[%s] Phase 1: PERCEPTION", self.name)
        trigger = context.data
        memories = await self._retrieve_memories_multi_layer(context)
        if context.memory.manager:
            context.memory.short_term = {"trigger": trigger, "query": trigger.get("user_message", "")}
            context.memory.long_term = memories.get("long_term", {})
        else:
            context.memory.long_term = memories
        enriched_context = await self._enrich_context(context)
        if context.memory.manager:
            await context.memory.manager.store(key="enriched_context", value=enriched_context, layer=MemoryLayer.SHORT_TERM, priority=MemoryPriority.HIGH, source="perception_phase")
        understanding = await self._understand_state(trigger, enriched_context, memories)
        if context.memory.context:
            await context.memory.context.store_phase_result(phase="perception", key="understanding", value=understanding)
        perception = {"trigger": trigger, "context_summary": self._summarize_context(enriched_context), "understanding": understanding, "relevant_memories": memories, "current_state": understanding.get("state", "unknown"), "user_intent": understanding.get("intent", "unknown"), "memory_layers_accessed": list(memories.keys()) if isinstance(memories, dict) else ["legacy"]}
        logger.info("[%s] Perception complete: intent=%s", self.name, perception["user_intent"])
        return perception

    async def _phase_cognition(self, context: AgentContext) -> dict[str, Any]:
        """
        PHASE 2: COGNITION

        Think about goal → Consider options → Plan steps → Decide actions

        Returns:
            cognition_data: {
                "goal": what we want to achieve,
                "options": possible approaches,
                "plan": step-by-step plan,
                "decision": chosen approach,
                "reasoning": why this approach
            }
        """
        logger.info("[%s] Phase 2: COGNITION", self.name)
        perception = context.phase_results.get("perception", {})
        understanding = perception.get("understanding", {})
        goal = await self._determine_goal(understanding, context)
        options = await self._generate_options(goal, context)
        plan = await self._create_plan(goal, options, context)
        decision = await self._make_decision(goal, options, plan, context)
        cognition = {"goal": goal, "options": options, "plan": plan, "decision": decision, "reasoning": decision.get("reasoning", "No reasoning provided"), "selected_option": decision.get("selected_option"), "confidence": decision.get("confidence", 0.5)}
        logger.info("[%s] Cognition complete: goal='%s', confidence=%.2f", self.name, goal, cognition["confidence"])
        return cognition

    async def _phase_action(self, context: AgentContext) -> dict[str, Any]:
        """
        PHASE 3: ACTION

        Call tools → Execute functions → Update systems → Record results

        Returns:
            action_data: {
                "tools_called": list of tool executions,
                "results": tool outputs,
                "systems_updated": what was modified,
                "final_output": result to return,
                "success": overall success
            }
        """
        logger.info("[%s] Phase 3: ACTION", self.name)
        cognition = context.phase_results.get("cognition", {})
        plan = cognition.get("plan", {})
        tools_called = []
        results = []
        systems_updated = []
        for step in plan.get("steps", []):
            step_result = await self._execute_step(step, context)
            tools_called.append({"step": step, "tool": step.get("tool"), "params": step.get("params"), "success": step_result.get("success"), "result": step_result.get("output")})
            results.append(step_result)
            if step_result.get("system_updated"):
                systems_updated.append(step_result["system_updated"])
            if not step_result.get("success", False) and step.get("critical", False):
                logger.error("Critical step failed: %s", step)
                break
        final_output = await self._aggregate_results(results, context)
        action = {"tools_called": tools_called, "results": results, "systems_updated": systems_updated, "final_output": final_output, "success": all(r.get("success", False) for r in results)}
        logger.info("[%s] Action complete: %s tools called, success=%s", self.name, len(tools_called), action["success"])
        return action

    async def _phase_reflection(self, context: AgentContext, result: dict[str, Any]) -> dict[str, Any]:
        """
        PHASE 4: REFLECTION

        Check outcomes → Learn from results → Update memory → Improve next time

        Multi-Layer Memory Updates:
        - Short-term: Clear at end (workflow complete)
        - Medium-term: Store user-specific patterns (TTL: days)
        - Long-term: Store important learnings (permanent)

        Returns:
            reflection_data: {
                "outcome": success/failure assessment,
                "evaluation": what went well/badly,
                "learnings": insights gained,
                "improvements": suggestions for next time,
                "memory_updates": what was stored in each layer
            }
        """
        logger.info("[%s] Phase 4: REFLECTION", self.name)
        outcome = self._assess_outcome(result)
        learnings = await self._extract_learnings(result, context)
        if context.memory.context:
            for learning in learnings:
                await context.memory.context.learn(pattern_type=learning.get("type", "general"), pattern_data=learning, outcome="success" if result.get("success") else "failure", confidence=learning.get("confidence", 0.5))
        else:
            context.memory.learnings.extend(learnings)
        memory_updates = await self._update_memory_multi_layer(result, learnings, context)
        improvements = self._identify_improvements(result, context)
        if context.memory.manager and result.get("success") and ("cognition" in context.phase_results):
            await context.memory.manager.promote_to_long_term(key="successful_strategy", importance=0.8)
        reflection = {"outcome": outcome, "evaluation": outcome.get("evaluation"), "learnings": learnings, "improvements": improvements, "memory_updates": memory_updates, "memory_layers_updated": ["short_term", "medium_term", "long_term"] if context.memory.manager else ["legacy"], "episodic_memory": {"request": context.data, "result": result, "timestamp": datetime.now(UTC).isoformat(), "importance": 0.8 if result.get("success") else 0.5}}
        if context.memory.manager:
            await context.memory.manager.long_term.store_episode(reflection["episodic_memory"])
        logger.info("[%s] Reflection complete: %s learnings, %s improvements", self.name, len(learnings), len(improvements))
        return reflection

    async def _retrieve_memories(self, context: AgentContext) -> dict[str, Any]:
        """
        Retrieve relevant memories from long-term storage
        Legacy method - use _retrieve_memories_multi_layer for full capability
        """
        if context.memory.manager:
            return await self._retrieve_memories_multi_layer(context)
        return {}

    async def _retrieve_memories_multi_layer(self, context: AgentContext) -> dict[str, Any]:
        """
        Retrieve memories from all three layers

        Returns:
            Dict with keys: short_term, medium_term, long_term
        """
        if not context.memory.manager:
            return await self._retrieve_memories_legacy(context)
        user_message = context.data.get("user_message", "")
        relevant_context = await context.memory.context.get_relevant_context(query=user_message, include_short_term=True, include_medium_term=True, include_long_term=True)
        return {"short_term": relevant_context.get("short_term", []), "medium_term": relevant_context.get("medium_term", []), "long_term": relevant_context.get("long_term", []), "query": user_message}

    async def _retrieve_memories_legacy(self, _context: AgentContext) -> dict[str, Any]:
        """Legacy memory retrieval for backward compatibility"""
        return {}

    async def _enrich_context(self, context: AgentContext) -> dict[str, Any]:
        """Enrich context with additional data from systems"""
        raise NotImplementedError

    async def _understand_state(self, trigger: dict[str, Any], context: dict[str, Any], memories: dict[str, Any]) -> dict[str, Any]:
        """Understand current state using LLM"""
        raise NotImplementedError

    async def _determine_goal(self, understanding: dict[str, Any], context: AgentContext) -> str:
        """Determine what we want to achieve"""
        raise NotImplementedError

    async def _generate_options(self, goal: str, context: AgentContext) -> list[dict[str, Any]]:
        """Generate possible approaches"""
        raise NotImplementedError

    async def _create_plan(self, goal: str, options: list[dict[str, Any]], context: AgentContext) -> dict[str, Any]:
        """Create step-by-step plan"""
        raise NotImplementedError

    async def _make_decision(self, goal: str, options: list[dict[str, Any]], plan: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        """Decide on best approach"""
        raise NotImplementedError

    async def _execute_step(self, step: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        """Execute a single step"""
        raise NotImplementedError

    async def _aggregate_results(self, results: list[dict[str, Any]], context: AgentContext) -> Any:
        """Aggregate step results into final output"""
        raise NotImplementedError

    def _summarize_context(self, context: dict[str, Any]) -> str:
        """Create a summary of the context"""
        return json.dumps(context, default=str)[:500]

    def _assess_outcome(self, result: dict[str, Any]) -> dict[str, Any]:
        """Assess the outcome of the agent loop"""
        success = result.get("success", False)
        return {"success": success, "status": "success" if success else "failure", "evaluation": {"all_phases_completed": "reflection" in result.get("phases", {}), "action_success": result.get("phases", {}).get("action", {}).get("status") == "completed", "error": result.get("error")}}

    async def _extract_learnings(self, result: dict[str, Any], context: AgentContext) -> list[dict[str, Any]]:
        """Extract learnings from the execution"""
        learnings = []
        if result.get("success"):
            learnings.append({"type": "success_pattern", "description": f"Plan executed successfully for {context.user_id}", "plan": context.memory.short_term.get("plan"), "confidence": "high"})
        action_phase = result.get("phases", {}).get("action", {})
        for tool in action_phase.get("tools_called", []):
            if tool.get("success"):
                learnings.append({"type": "tool_effectiveness", "tool": tool.get("tool"), "effective": True, "context": tool.get("step", {})})
        return learnings

    async def _update_memory(self, result: dict[str, Any], learnings: list[dict[str, Any]], context: AgentContext) -> list[str]:
        """
        Update memory with learnings (legacy method)
        Use _update_memory_multi_layer for full capability
        """
        return await self._update_memory_multi_layer(result, learnings, context)

    async def _update_memory_multi_layer(self, result: dict[str, Any], learnings: list[dict[str, Any]], context: AgentContext) -> list[str]:
        """
        Update all three memory layers with learnings

        Layer-specific updates:
        - Short-term: Clear at workflow end
        - Medium-term: User patterns with TTL
        - Long-term: Important learnings (permanent)
        """
        updates = []
        context.memory.episodic.append({"request_id": context.request_id, "user_id": context.user_id, "result": result, "learnings": learnings, "timestamp": datetime.now(UTC).isoformat()})
        updates.append(f"short_term:episodic_{context.request_id}")
        if context.memory.manager:
            manager = context.memory.manager
            for learning in learnings:
                if learning.get("type") == "pattern":
                    await manager.store(key=f"pattern_{context.request_id}_{len(updates)}", value=learning, layer=MemoryLayer.MEDIUM_TERM, priority=MemoryPriority.MEDIUM, ttl_seconds=7 * 24 * 3600, tags=["pattern", "user_specific"], source="reflection_phase")
                    updates.append(f"medium_term:pattern_{len(updates)}")
            if result.get("success") and learnings:
                best_practice = {"situation": context.data.get("user_message", ""), "solution": learnings[0].get("description", ""), "effectiveness": 0.9, "agent": self.name}
                manager.long_term.add_best_practice(**best_practice)
                updates.append("long_term:best_practice")
        if len(context.memory.episodic) > MAX_EPISODIC_MEMORY_ITEMS:
            context.memory.episodic = context.memory.episodic[-MAX_EPISODIC_MEMORY_ITEMS:]
        return updates

    def _identify_improvements(self, result: dict[str, Any], _context: AgentContext) -> list[str]:
        """Identify potential improvements"""
        improvements = []
        for phase_name, phase_data in result.get("phases", {}).items():
            time_ms = phase_data.get("time_ms", 0)
            if time_ms > SLOW_PHASE_THRESHOLD_MS:
                improvements.append(f"Optimize {phase_name} phase (took {time_ms:.0f}ms)")
        if not result.get("success"):
            improvements.append("Review error handling for this type of request")
        return improvements

    async def _handle_error_with_reflection(self, error: Exception, context: AgentContext, _result: dict[str, Any]):
        """Handle error and record for learning"""
        logger.exception("Agent %s error in %s", self.name, self.state.value)
        learning = {"type": "failure_pattern", "error": str(error), "phase": self.state.value, "request": context.data, "timestamp": datetime.now(UTC).isoformat(), "confidence": 0.9}
        context.memory.learnings.append(learning)
        if context.memory.manager:
            context.memory.manager.long_term.add_edge_case(scenario=str(context.data.get("user_message", "")), issue=str(error), resolution=f"Failed in {self.state.value} phase")
        await asyncio.sleep(0.5)
        self.state = AgentState.READY

    def _get_available_tools(self) -> list[dict[str, Any]]:
        """Get list of tools available to this agent - override in subclass"""
        return []

    def _update_average_time(self, new_time_ms: float):
        """Update rolling average processing time"""
        n = self.metrics.successful_requests
        current_avg = self.metrics.average_processing_time_ms
        self.metrics.average_processing_time_ms = (current_avg * (n - 1) + new_time_ms) / n if n > 0 else new_time_ms

    async def shutdown(self):
        """Graceful shutdown of the agent"""
        self.state = AgentState.SHUTDOWN
        logger.info("Agent %s shutdown", self.name)

    def get_capabilities(self) -> dict[str, Any]:
        """Return agent capabilities and configuration"""
        return {"name": self.name, "description": self.description, "state": self.state.value, "loop_phases": [p.value for p in AgentPhase], "metrics": {"total_requests": self.metrics.total_requests, "success_rate": self.metrics.successful_requests / self.metrics.total_requests * 100 if self.metrics.total_requests > 0 else 0, "average_processing_time_ms": self.metrics.average_processing_time_ms, "recent_errors": len(self.metrics.errors[-5:])}}
