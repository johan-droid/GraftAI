"""
Base Agent class for GraftAI - Single Agent Loop Architecture
Agent = LLM + Memory + Tools + Loop

The 4-Phase Agent Loop:
1. PERCEPTION - Receive trigger, read memory, get context, understand state
2. COGNITION - Think about goal, consider options, plan steps, decide actions
3. ACTION - Call tools, execute functions, update systems, record results
4. REFLECTION - Check outcomes, learn from results, update memory, improve next time
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import json
from typing import TYPE_CHECKING

from backend.ai.memory.multi_layer_memory import MemoryLayer, MemoryPriority
from backend.utils.logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class AgentTimeoutError(Exception):
    """Raised when an agent phase exceeds its timeout limit."""
    pass

class AgentState(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    PERCEIVING = "perceiving"
    COGNIZING = "cognizing"
    ACTING = "acting"
    REFLECTING = "reflecting"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class AgentPhase(Enum):
    """The 4 phases of the agent loop"""
    PERCEPTION = "perception"
    COGNITION = "cognition"
    ACTION = "action"
    REFLECTION = "reflection"


# Phase timeout configuration (in seconds)
PHASE_TIMEOUTS = {
    AgentPhase.PERCEPTION: 10.0,   # 10 seconds for perception
    AgentPhase.COGNITION: 30.0,    # 30 seconds for LLM reasoning
    AgentPhase.ACTION: 60.0,       # 60 seconds for external API calls
    AgentPhase.REFLECTION: 15.0,    # 15 seconds for reflection
}


@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_processing_time_ms: float = 0.0
    last_request_time: Optional[datetime] = None
    errors: list = field(default_factory=list)
    phase_times: Dict[str, float] = field(default_factory=dict)


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
    short_term: Dict[str, Any] = field(default_factory=dict)
    long_term: Dict[str, Any] = field(default_factory=dict)
    episodic: List[Dict[str, Any]] = field(default_factory=list)
    learnings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Multi-layer memory manager (optional, set during agent initialization)
    manager: Optional[Any] = None
    context: Optional[Any] = None  # AgentMemoryContext wrapper


@dataclass
class AgentContext:
    """Context passed to agents during execution"""
    user_id: str
    request_id: str
    data: Dict[str, Any]
    memory: AgentMemory = field(default_factory=AgentMemory)
    tools_available: List[Dict[str, Any]] = field(default_factory=list)
    llm_client: Optional[Any] = None
    phase_results: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
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
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.state = AgentState.INITIALIZING
        self.metrics = AgentMetrics()
        self.controller: Optional[Any] = None
        self._lock = asyncio.Lock()
        
        # Tool registry
        self.tools: Dict[str, Callable] = {}
        
        logger.info(f"Agent {name} initializing")
    
    async def initialize(self):
        """Initialize the agent - override in subclass"""
        self.state = AgentState.READY
        logger.info(f"Agent {self.name} ready")
    
    # ╔══════════════════════════════════════════════════════════════════╗
    # ║                    THE 4-PHASE AGENT LOOP                        ║
    # ╚══════════════════════════════════════════════════════════════════╝
    
    async def execute(self, request: Any) -> Dict[str, Any]:
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
                raise RuntimeError(f"Agent {self.name} not ready (state: {self.state.value})")
            
            self.metrics.total_requests += 1
            loop_start = datetime.utcnow()
            
            # Initialize context with memory
            context = AgentContext(
                user_id=request.user_id,
                request_id=request.id,
                data=request.context,
                tools_available=self._get_available_tools(),
                memory=AgentMemory(),
                phase_results={}
            )
            
            result = {
                "agent": self.name,
                "request_id": request.id,
                "phases": {},
                "success": False,
                "error": None
            }
            
            try:
                # ╔═══════════════════════════════════════════════════════════════╗
                # ║ PHASE 1: PERCEPTION                                           ║
                # ║ Receive trigger → Read memory → Get context → Understand state ║
                # ╚═══════════════════════════════════════════════════════════════╝
                self.state = AgentState.PERCEIVING
                phase_start = datetime.utcnow()
                
                perception = await self._execute_phase_with_timeout(
                    self._phase_perception,
                    context,
                    PHASE_TIMEOUTS[AgentPhase.PERCEPTION],
                    "perception"
                )
                context.phase_results["perception"] = perception
                context.memory.short_term["perception"] = perception
                
                result["phases"]["perception"] = {
                    "status": "completed",
                    "time_ms": (datetime.utcnow() - phase_start).total_seconds() * 1000,
                    "understanding": perception.get("understanding"),
                    "trigger": perception.get("trigger")
                }
                
                # ╔═══════════════════════════════════════════════════════════════╗
                # ║ PHASE 2: COGNITION                                            ║
                # ║ Think goal → Consider options → Plan steps → Decide actions    ║
                # ╚═══════════════════════════════════════════════════════════════╝
                self.state = AgentState.COGNIZING
                phase_start = datetime.utcnow()
                
                cognition = await self._execute_phase_with_timeout(
                    self._phase_cognition,
                    context,
                    PHASE_TIMEOUTS[AgentPhase.COGNITION],
                    "cognition"
                )
                context.phase_results["cognition"] = cognition
                context.memory.short_term["plan"] = cognition.get("plan")
                context.memory.short_term["decision"] = cognition.get("decision")
                
                result["phases"]["cognition"] = {
                    "status": "completed",
                    "time_ms": (datetime.utcnow() - phase_start).total_seconds() * 1000,
                    "goal": cognition.get("goal"),
                    "plan": cognition.get("plan"),
                    "decision": cognition.get("decision")
                }
                
                # ╔═══════════════════════════════════════════════════════════════╗
                # ║ PHASE 3: ACTION                                               ║
                # ║ Call tools → Execute functions → Update systems → Record      ║
                # ╚═══════════════════════════════════════════════════════════════╝
                self.state = AgentState.ACTING
                phase_start = datetime.utcnow()
                
                action = await self._execute_phase_with_timeout(
                    self._phase_action,
                    context,
                    PHASE_TIMEOUTS[AgentPhase.ACTION],
                    "action"
                )
                context.phase_results["action"] = action
                context.memory.short_term["results"] = action.get("results")
                
                result["phases"]["action"] = {
                    "status": "completed",
                    "time_ms": (datetime.utcnow() - phase_start).total_seconds() * 1000,
                    "tools_called": action.get("tools_called", []),
                    "results": action.get("results"),
                    "systems_updated": action.get("systems_updated", [])
                }
                
                # ╔═══════════════════════════════════════════════════════════════╗
                # ║ PHASE 4: REFLECTION                                           ║
                # ║ Check outcomes → Learn → Update memory → Improve              ║
                # ╚═══════════════════════════════════════════════════════════════╝
                self.state = AgentState.REFLECTING
                phase_start = datetime.utcnow()
                
                reflection = await self._execute_phase_with_timeout(
                    lambda ctx: self._phase_reflection(ctx, result),
                    context,
                    PHASE_TIMEOUTS[AgentPhase.REFLECTION],
                    "reflection"
                )
                context.phase_results["reflection"] = reflection
                
                result["phases"]["reflection"] = {
                    "status": "completed",
                    "time_ms": (datetime.utcnow() - phase_start).total_seconds() * 1000,
                    "outcome": reflection.get("outcome"),
                    "learnings": reflection.get("learnings", []),
                    "improvements": reflection.get("improvements", [])
                }
                
                # Update final metrics
                total_time = (datetime.utcnow() - loop_start).total_seconds() * 1000
                self.metrics.successful_requests += 1
                self._update_average_time(total_time)
                
                result["success"] = True
                result["total_time_ms"] = total_time
                result["final_output"] = action.get("final_output")
                
                self.state = AgentState.READY
                
                logger.info(f"Agent {self.name} completed 4-phase loop in {total_time:.2f}ms")
                
            except Exception as e:
                self.metrics.failed_requests += 1
                self.metrics.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                    "request_id": request.id,
                    "phase": self.state.value
                })
                
                result["success"] = False
                result["error"] = str(e)
                result["failed_phase"] = self.state.value
                
                logger.error(f"Agent {self.name} failed in {self.state.value}: {e}")
                self.state = AgentState.ERROR
                
                # Attempt recovery through reflection
                await self._handle_error_with_reflection(e, context, result)
            
            return result
    
    # ╔══════════════════════════════════════════════════════════════════╗
    # ║                    TIMEOUT PROTECTION                            ║
    # ╚══════════════════════════════════════════════════════════════════╝
    
    async def _execute_phase_with_timeout(
        self,
        phase_func,
        context: AgentContext,
        timeout: float,
        phase_name: str
    ) -> Dict[str, Any]:
        """
        Execute a phase with timeout protection.
        
        Args:
            phase_func: The phase function to execute
            context: AgentContext for the phase
            timeout: Maximum time allowed for the phase (seconds)
            phase_name: Name of the phase for error reporting
            
        Returns:
            Phase result dictionary
            
        Raises:
            AgentTimeoutError: If phase exceeds timeout limit
        """
        import asyncio
        
        try:
            # Execute phase with timeout
            result = await asyncio.wait_for(
                phase_func(context),
                timeout=timeout
            )
            return result
            
        except asyncio.TimeoutError:
            logger.error(
                f"[{self.name}] Phase '{phase_name}' timed out after {timeout}s "
                f"(request: {context.request_id})"
            )
            
            # Update metrics
            self.metrics.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": f"Phase timeout: {phase_name}",
                "request_id": context.request_id,
                "phase": phase_name,
                "timeout_seconds": timeout
            })
            
            # Raise timeout error
            raise AgentTimeoutError(
                f"Phase '{phase_name}' exceeded {timeout} second limit"
            )
    
    # ╔══════════════════════════════════════════════════════════════════╗
    # ║                    PHASE IMPLEMENTATIONS                         ║
    # ╚══════════════════════════════════════════════════════════════════╝
    
    async def _phase_perception(self, context: AgentContext) -> Dict[str, Any]:
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
        logger.info(f"[{self.name}] Phase 1: PERCEPTION")
        
        # 1.1 Receive trigger
        trigger = context.data
        
        # 1.2 READ MEMORY (Multi-Layer)
        memories = await self._retrieve_memories_multi_layer(context)
        
        # Store in context for later phases
        if context.memory.manager:
            # Using multi-layer memory
            context.memory.short_term = {
                "trigger": trigger,
                "query": trigger.get("user_message", "")
            }
            context.memory.long_term = memories.get("long_term", {})
        else:
            # Legacy mode
            context.memory.long_term = memories
        
        # 1.3 Get context (enrich with additional data)
        enriched_context = await self._enrich_context(context)
        
        # Store enriched context in short-term
        if context.memory.manager:
            await context.memory.manager.store(
                key="enriched_context",
                value=enriched_context,
                layer=MemoryLayer.SHORT_TERM,
                priority=MemoryPriority.HIGH,
                source="perception_phase"
            )
        
        # 1.4 Understand state (using LLM)
        understanding = await self._understand_state(trigger, enriched_context, memories)
        
        # Store understanding in short-term
        if context.memory.context:
            await context.memory.context.store_phase_result(
                phase="perception",
                key="understanding",
                value=understanding
            )
        
        perception = {
            "trigger": trigger,
            "context_summary": self._summarize_context(enriched_context),
            "understanding": understanding,
            "relevant_memories": memories,
            "current_state": understanding.get("state", "unknown"),
            "user_intent": understanding.get("intent", "unknown"),
            "memory_layers_accessed": list(memories.keys()) if isinstance(memories, dict) else ["legacy"]
        }
        
        logger.info(f"[{self.name}] Perception complete: intent={perception['user_intent']}")
        return perception
    
    async def _phase_cognition(self, context: AgentContext) -> Dict[str, Any]:
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
        logger.info(f"[{self.name}] Phase 2: COGNITION")
        
        perception = context.phase_results.get("perception", {})
        understanding = perception.get("understanding", {})
        
        # 2.1 Think about goal
        goal = await self._determine_goal(understanding, context)
        
        # 2.2 Consider options
        options = await self._generate_options(goal, context)
        
        # 2.3 Plan steps
        plan = await self._create_plan(goal, options, context)
        
        # 2.4 Decide actions
        decision = await self._make_decision(goal, options, plan, context)
        
        cognition = {
            "goal": goal,
            "options": options,
            "plan": plan,
            "decision": decision,
            "reasoning": decision.get("reasoning", "No reasoning provided"),
            "selected_option": decision.get("selected_option"),
            "confidence": decision.get("confidence", 0.5)
        }
        
        logger.info(f"[{self.name}] Cognition complete: goal='{goal}', confidence={cognition['confidence']:.2f}")
        return cognition
    
    async def _phase_action(self, context: AgentContext) -> Dict[str, Any]:
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
        logger.info(f"[{self.name}] Phase 3: ACTION")
        
        cognition = context.phase_results.get("cognition", {})
        plan = cognition.get("plan", {})
        
        tools_called = []
        results = []
        systems_updated = []
        
        # 3.1 Execute plan steps
        for step in plan.get("steps", []):
            step_result = await self._execute_step(step, context)
            
            tools_called.append({
                "step": step,
                "tool": step.get("tool"),
                "params": step.get("params"),
                "success": step_result.get("success"),
                "result": step_result.get("output")
            })
            
            results.append(step_result)
            
            if step_result.get("system_updated"):
                systems_updated.append(step_result["system_updated"])
            
            # Check for failure
            if not step_result.get("success", False) and step.get("critical", False):
                logger.error(f"Critical step failed: {step}")
                break
        
        # 3.2 Aggregate results
        final_output = await self._aggregate_results(results, context)
        
        action = {
            "tools_called": tools_called,
            "results": results,
            "systems_updated": systems_updated,
            "final_output": final_output,
            "success": all(r.get("success", False) for r in results)
        }
        
        logger.info(f"[{self.name}] Action complete: {len(tools_called)} tools called, success={action['success']}")
        return action
    
    async def _phase_reflection(
        self,
        context: AgentContext,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        logger.info(f"[{self.name}] Phase 4: REFLECTION")
        
        # 4.1 Check outcomes
        outcome = self._assess_outcome(result)
        
        # 4.2 Learn from results (Multi-Layer)
        learnings = await self._extract_learnings(result, context)
        
        # Store learnings in medium-term (user-specific, expires in days)
        if context.memory.context:
            for learning in learnings:
                await context.memory.context.learn(
                    pattern_type=learning.get("type", "general"),
                    pattern_data=learning,
                    outcome="success" if result.get("success") else "failure",
                    confidence=learning.get("confidence", 0.5)
                )
        else:
            context.memory.learnings.extend(learnings)
        
        # 4.3 Update Multi-Layer Memory
        memory_updates = await self._update_memory_multi_layer(result, learnings, context)
        
        # 4.4 Identify improvements
        improvements = self._identify_improvements(result, context)
        
        # 4.5 Promote important memories to long-term
        if context.memory.manager and result.get("success"):
            # Promote successful strategy
            if "cognition" in context.phase_results:
                plan = context.phase_results["cognition"].get("plan", {})
                await context.memory.manager.promote_to_long_term(
                    key="successful_strategy",
                    importance=0.8
                )
        
        reflection = {
            "outcome": outcome,
            "evaluation": outcome.get("evaluation"),
            "learnings": learnings,
            "improvements": improvements,
            "memory_updates": memory_updates,
            "memory_layers_updated": ["short_term", "medium_term", "long_term"] if context.memory.manager else ["legacy"],
            "episodic_memory": {
                "request": context.data,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "importance": 0.8 if result.get("success") else 0.5
            }
        }
        
        # Store episode in long-term memory
        if context.memory.manager:
            await context.memory.manager.long_term.store_episode(reflection["episodic_memory"])
        
        logger.info(f"[{self.name}] Reflection complete: {len(learnings)} learnings, {len(improvements)} improvements")
        return reflection
    
    # ╔══════════════════════════════════════════════════════════════════╗
    # ║              ABSTRACT METHODS FOR SUBCLASSES                     ║
    # ╚══════════════════════════════════════════════════════════════════╝
    
    async def _retrieve_memories(self, context: AgentContext) -> Dict[str, Any]:
        """
        Retrieve relevant memories from long-term storage
        Legacy method - use _retrieve_memories_multi_layer for full capability
        """
        # Default implementation using manager if available
        if context.memory.manager:
            return await self._retrieve_memories_multi_layer(context)
        return {}
    
    async def _retrieve_memories_multi_layer(self, context: AgentContext) -> Dict[str, Any]:
        """
        Retrieve memories from all three layers
        
        Returns:
            Dict with keys: short_term, medium_term, long_term
        """
        if not context.memory.manager:
            # Fallback to legacy behavior
            return await self._retrieve_memories_legacy(context)
        
        user_message = context.data.get("user_message", "")
        
        # Get relevant context from all layers
        relevant_context = await context.memory.context.get_relevant_context(
            query=user_message,
            include_short_term=True,
            include_medium_term=True,
            include_long_term=True
        )
        
        return {
            "short_term": relevant_context.get("short_term", []),
            "medium_term": relevant_context.get("medium_term", []),
            "long_term": relevant_context.get("long_term", []),
            "query": user_message
        }
    
    async def _retrieve_memories_legacy(self, context: AgentContext) -> Dict[str, Any]:
        """Legacy memory retrieval for backward compatibility"""
        return {}
    
    @abstractmethod
    async def _enrich_context(self, context: AgentContext) -> Dict[str, Any]:
        """Enrich context with additional data from systems"""
        pass
    
    @abstractmethod
    async def _understand_state(
        self,
        trigger: Dict[str, Any],
        context: Dict[str, Any],
        memories: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Understand current state using LLM"""
        pass
    
    @abstractmethod
    async def _determine_goal(
        self,
        understanding: Dict[str, Any],
        context: AgentContext
    ) -> str:
        """Determine what we want to achieve"""
        pass
    
    @abstractmethod
    async def _generate_options(
        self,
        goal: str,
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Generate possible approaches"""
        pass
    
    @abstractmethod
    async def _create_plan(
        self,
        goal: str,
        options: List[Dict[str, Any]],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Create step-by-step plan"""
        pass
    
    @abstractmethod
    async def _make_decision(
        self,
        goal: str,
        options: List[Dict[str, Any]],
        plan: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Decide on best approach"""
        pass
    
    @abstractmethod
    async def _execute_step(
        self,
        step: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Execute a single step"""
        pass
    
    @abstractmethod
    async def _aggregate_results(
        self,
        results: List[Dict[str, Any]],
        context: AgentContext
    ) -> Any:
        """Aggregate step results into final output"""
        pass
    
    # ╔══════════════════════════════════════════════════════════════════╗
    # ║                    UTILITY METHODS                               ║
    # ╚══════════════════════════════════════════════════════════════════╝
    
    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Create a summary of the context"""
        return json.dumps(context, default=str)[:500]
    
    def _assess_outcome(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the outcome of the agent loop"""
        success = result.get("success", False)
        
        return {
            "success": success,
            "status": "success" if success else "failure",
            "evaluation": {
                "all_phases_completed": "reflection" in result.get("phases", {}),
                "action_success": result.get("phases", {}).get("action", {}).get("status") == "completed",
                "error": result.get("error")
            }
        }
    
    async def _extract_learnings(
        self,
        result: Dict[str, Any],
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Extract learnings from the execution"""
        learnings = []
        
        # Learn from success
        if result.get("success"):
            learnings.append({
                "type": "success_pattern",
                "description": f"Plan executed successfully for {context.user_id}",
                "plan": context.memory.short_term.get("plan"),
                "confidence": "high"
            })
        
        # Learn from tools
        action_phase = result.get("phases", {}).get("action", {})
        for tool in action_phase.get("tools_called", []):
            if tool.get("success"):
                learnings.append({
                    "type": "tool_effectiveness",
                    "tool": tool.get("tool"),
                    "effective": True,
                    "context": tool.get("step", {})
                })
        
        return learnings
    
    async def _update_memory(
        self,
        result: Dict[str, Any],
        learnings: List[Dict[str, Any]],
        context: AgentContext
    ) -> List[str]:
        """
        Update memory with learnings (legacy method)
        Use _update_memory_multi_layer for full capability
        """
        return await self._update_memory_multi_layer(result, learnings, context)
    
    async def _update_memory_multi_layer(
        self,
        result: Dict[str, Any],
        learnings: List[Dict[str, Any]],
        context: AgentContext
    ) -> List[str]:
        """
        Update all three memory layers with learnings
        
        Layer-specific updates:
        - Short-term: Clear at workflow end
        - Medium-term: User patterns with TTL
        - Long-term: Important learnings (permanent)
        """
        updates = []
        
        # SHORT-TERM: Store execution context (will be cleared at end)
        context.memory.episodic.append({
            "request_id": context.request_id,
            "user_id": context.user_id,
            "result": result,
            "learnings": learnings,
            "timestamp": datetime.utcnow().isoformat()
        })
        updates.append(f"short_term:episodic_{context.request_id}")
        
        if context.memory.manager:
            manager = context.memory.manager
            
            # MEDIUM-TERM: Store user patterns (expires in days)
            for learning in learnings:
                if learning.get("type") == "pattern":
                    await manager.store(
                        key=f"pattern_{context.request_id}_{len(updates)}",
                        value=learning,
                        layer=MemoryLayer.MEDIUM_TERM,
                        priority=MemoryPriority.MEDIUM,
                        ttl_seconds=7 * 24 * 3600,  # 7 days
                        tags=["pattern", "user_specific"],
                        source="reflection_phase"
                    )
                    updates.append(f"medium_term:pattern_{len(updates)}")
            
            # LONG-TERM: Store best practices if successful
            if result.get("success") and learnings:
                best_practice = {
                    "situation": context.data.get("user_message", ""),
                    "solution": learnings[0].get("description", ""),
                    "effectiveness": 0.9,
                    "agent": self.name
                }
                manager.long_term.add_best_practice(**best_practice)
                updates.append("long_term:best_practice")
        
        # Keep short-term episodes manageable
        if len(context.memory.episodic) > 100:
            context.memory.episodic = context.memory.episodic[-100:]
        
        return updates
    
    def _identify_improvements(
        self,
        result: Dict[str, Any],
        context: AgentContext
    ) -> List[str]:
        """Identify potential improvements"""
        improvements = []
        
        # Check for slow phases
        for phase_name, phase_data in result.get("phases", {}).items():
            time_ms = phase_data.get("time_ms", 0)
            if time_ms > 1000:  # > 1 second
                improvements.append(f"Optimize {phase_name} phase (took {time_ms:.0f}ms)")
        
        # Check for failures
        if not result.get("success"):
            improvements.append("Review error handling for this type of request")
        
        return improvements
    
    async def _handle_error_with_reflection(
        self,
        error: Exception,
        context: AgentContext,
        result: Dict[str, Any]
    ):
        """Handle error and record for learning"""
        logger.error(f"Agent {self.name} error in {self.state.value}: {error}")
        
        # Create a failure learning
        learning = {
            "type": "failure_pattern",
            "error": str(error),
            "phase": self.state.value,
            "request": context.data,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.9
        }
        
        context.memory.learnings.append(learning)
        
        # Store in long-term memory for future avoidance
        if context.memory.manager:
            context.memory.manager.long_term.add_edge_case(
                scenario=str(context.data.get("user_message", "")),
                issue=str(error),
                resolution=f"Failed in {self.state.value} phase"
            )
        
        # Attempt recovery
        await asyncio.sleep(0.5)
        self.state = AgentState.READY
    
    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of tools available to this agent - override in subclass"""
        return []
    
    def _update_average_time(self, new_time_ms: float):
        """Update rolling average processing time"""
        n = self.metrics.successful_requests
        current_avg = self.metrics.average_processing_time_ms
        self.metrics.average_processing_time_ms = (
            (current_avg * (n - 1) + new_time_ms) / n if n > 0 else new_time_ms
        )
    
    async def shutdown(self):
        """Graceful shutdown of the agent"""
        self.state = AgentState.SHUTDOWN
        logger.info(f"Agent {self.name} shutdown")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities and configuration"""
        return {
            "name": self.name,
            "description": self.description,
            "state": self.state.value,
            "loop_phases": [p.value for p in AgentPhase],
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": (
                    self.metrics.successful_requests / self.metrics.total_requests * 100
                    if self.metrics.total_requests > 0 else 0
                ),
                "average_processing_time_ms": self.metrics.average_processing_time_ms,
                "recent_errors": len(self.metrics.errors[-5:])
            }
        }
