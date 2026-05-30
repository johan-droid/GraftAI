"""
AI Orchestration Layer for GraftAI
Manages multi-agent coordination, dispatching, and lifecycle
"""
import asyncio
import contextlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from backend.ai.agents.base import AgentState, BaseAgent
from backend.ai.llm_core import LLaMACore
from backend.ai.memory.graph_store import GraphStore
from backend.ai.memory.vector_store import VectorStore
from backend.utils.logger import get_logger


def _import_agents():
    from backend.ai.agents.booking_agent import BookingAgent
    from backend.ai.agents.execution_agent import ExecutionAgent
    from backend.ai.agents.monitoring_agent import MonitoringAgent
    from backend.ai.agents.optimization_agent import OptimizationAgent
    return {AgentType.BOOKING: BookingAgent(), AgentType.OPTIMIZATION: OptimizationAgent(), AgentType.EXECUTION: ExecutionAgent(), AgentType.MONITORING: MonitoringAgent()}
logger = get_logger(__name__)

class AgentType(Enum):
    """Types of specialized agents"""
    BOOKING = "booking"
    OPTIMIZATION = "optimization"
    EXECUTION = "execution"
    MONITORING = "monitoring"

@dataclass
class AgentRequest:
    """Request to be processed by an agent"""
    id: str
    type: AgentType
    user_id: str
    context: dict[str, Any]
    priority: int = 5
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    callback: Callable | None = None

@dataclass
class AgentResponse:
    """Response from an agent"""
    request_id: str
    agent_type: AgentType
    success: bool
    result: dict[str, Any]
    error: str | None = None
    processing_time_ms: float = 0.0

class AgentController:
    """
    Central controller for managing AI agents
    Handles routing, lifecycle, and coordination
    """

    def __init__(self, llm_core: LLaMACore, vector_store: VectorStore, graph_store: GraphStore):
        self.llm_core = llm_core
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.agents: dict[AgentType, BaseAgent] = {}
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.pending_requests: dict[str, asyncio.Future] = {}
        self.is_running = False
        self._worker_task: asyncio.Task | None = None
        logger.info("AgentController initialized")

    def register_agent(self, agent_type: AgentType, agent: BaseAgent):
        """Register an agent with the controller"""
        self.agents[agent_type] = agent
        agent.controller = self
        if not isinstance(getattr(agent, "state", None), AgentState):
            agent.state = AgentState.READY
        logger.info("Registered %s agent", agent_type.value)

    async def start(self):
        """Start the orchestration loop"""
        self.is_running = True
        self._worker_task = asyncio.create_task(self._orchestration_loop())
        logger.info("AgentController started")

    async def stop(self):
        """Stop the orchestration loop"""
        self.is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
        logger.info("AgentController stopped")

    async def dispatch(self, agent_type: AgentType, user_id: str, context: dict[str, Any], priority: int=5, timeout: float=30.0) -> AgentResponse:
        """
        Dispatch a request to an agent

        Args:
            agent_type: Type of agent to handle the request
            user_id: User making the request
            context: Request context/data
            priority: Priority level (1-10)
            timeout: Maximum wait time in seconds

        Returns:
            AgentResponse with results
        """
        import uuid
        request_id = str(uuid.uuid4())
        request = AgentRequest(id=request_id, type=agent_type, user_id=user_id, context=context, priority=priority)
        agent = self.agents.get(agent_type)
        if not agent:
            return AgentResponse(request_id=request_id, agent_type=agent_type, success=False, result={}, error=f"No agent registered for type: {agent_type.value}")
        if not self.is_running:
            try:
                result = await agent.execute(request)
                if isinstance(result, AgentResponse):
                    return result
                if isinstance(result, dict):
                    success = bool(result.get("success", False))
                    error = result.get("error")
                else:
                    success = True
                    error = None
                return AgentResponse(request_id=request_id, agent_type=agent_type, success=success, result=result if isinstance(result, dict) else {"result": result}, error=error, processing_time_ms=0.0)
            except Exception as exc:
                logger.exception("Request %s failed: %s", request_id, exc)
                return AgentResponse(request_id=request_id, agent_type=agent_type, success=False, result={}, error=str(exc), processing_time_ms=0.0)
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_requests[request_id] = future
        await self.request_queue.put(request)
        logger.info("Dispatched request %s to %s", request_id, agent_type.value)
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except TimeoutError:
            logger.exception("Request %s timed out", request_id)
            return AgentResponse(request_id=request_id, agent_type=agent_type, success=False, result={}, error="Request timed out")
        finally:
            self.pending_requests.pop(request_id, None)

    async def _orchestration_loop(self):
        """Main orchestration loop processing requests"""
        while self.is_running:
            try:
                request: AgentRequest = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                asyncio.create_task(self._process_request(request))
            except TimeoutError:
                continue
            except Exception as e:
                logger.exception("Orchestration loop error: %s", e)

    async def _process_request(self, request: AgentRequest):
        """Process a single request"""
        start_time = datetime.now(UTC)
        try:
            agent = self.agents.get(request.type)
            if not agent:
                msg = f"No agent registered for type: {request.type}"
                raise ValueError(msg)
            if agent.state != AgentState.READY:
                msg = f"Agent {request.type.value} is not ready"
                raise RuntimeError(msg)
            logger.info("Executing %s agent for request %s", request.type.value, request.id)
            result = await agent.execute(request)
            processing_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            response = AgentResponse(request_id=request.id, agent_type=request.type, success=bool(result.get("success", False)) if isinstance(result, dict) else False, result=result if isinstance(result, dict) else {"result": result}, error=None if not isinstance(result, dict) else result.get("error"), processing_time_ms=processing_time)
        except Exception as e:
            logger.exception("Request %s failed: %s", request.id, e)
            processing_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            response = AgentResponse(request_id=request.id, agent_type=request.type, success=False, result={}, error=str(e), processing_time_ms=processing_time)
        future = self.pending_requests.get(request.id)
        if future and (not future.done()):
            future.set_result(response)
        try:
            from backend.tasks.automation_tasks import log_agent_interaction_task
            req_data = {"id": request.id, "agent_type": request.type.value, "user_id": request.user_id, "context": request.context, "timestamp": request.timestamp.isoformat() if request.timestamp else None}
            res_data = {"success": response.success, "result": response.result, "error": response.error, "processing_time_ms": response.processing_time_ms}
            log_agent_interaction_task.delay(req_data, res_data)
            logger.info("Queued persistent logging for request %s", request.id)
        except Exception as e:
            logger.exception("Failed to queue logging task: %s", e)

    async def _log_interaction(self, request: AgentRequest, response: AgentResponse):
        """Log agent interaction for learning"""
        try:
            await self.vector_store.add_document(collection="agent_interactions", document={"request_id": request.id, "agent_type": request.type.value, "user_id": request.user_id, "context": request.context, "result": response.result, "success": response.success, "error": response.error, "processing_time_ms": response.processing_time_ms, "timestamp": datetime.now(UTC).isoformat()}, metadata={"agent_type": request.type.value, "user_id": request.user_id, "success": response.success})
        except Exception as e:
            logger.exception("Failed to log interaction: %s", e)

    async def coordinate_agents(self, agents: list[AgentType], user_id: str, context: dict[str, Any]) -> dict[str, AgentResponse]:
        """
        Coordinate multiple agents for complex workflows

        Args:
            agents: List of agent types to coordinate
            user_id: User ID
            context: Shared context

        Returns:
            Dictionary of agent responses
        """
        logger.info("Coordinating agents: %s", [a.value for a in agents])
        tasks = [self.dispatch(agent_type, user_id, context) for agent_type in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        responses = {}
        for agent_type, result in zip(agents, results, strict=False):
            if isinstance(result, Exception):
                responses[agent_type.value] = AgentResponse(request_id="", agent_type=agent_type, success=False, result={}, error=str(result))
            else:
                responses[agent_type.value] = result
        return responses

    def get_agent_status(self) -> dict[str, Any]:
        """Get status of all registered agents"""
        return {agent_type.value: {"state": agent.state.value, "metrics": agent.metrics} for agent_type, agent in self.agents.items()}
_controller: AgentController | None = None

async def get_agent_controller() -> AgentController:
    """Get or create the global agent controller"""
    global _controller
    if _controller is None:
        llm_core = LLaMACore()
        vector_store = VectorStore()
        graph_store = GraphStore()
        _controller = AgentController(llm_core, vector_store, graph_store)
        agents = _import_agents()
        for agent_type, agent in agents.items():
            _controller.register_agent(agent_type, agent)
        await _controller.start()
    return _controller
