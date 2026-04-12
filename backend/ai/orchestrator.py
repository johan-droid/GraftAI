"""
AI Orchestration Layer for GraftAI
Manages multi-agent coordination, dispatching, and lifecycle
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime
from backend.utils.logger import get_logger
from backend.ai.agents.base import BaseAgent, AgentState
from backend.ai.memory.vector_store import VectorStore
from backend.ai.memory.graph_store import GraphStore
from backend.ai.llm_core import LLaMACore

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
    context: Dict[str, Any]
    priority: int = 5  # 1-10, lower is higher priority
    timestamp: datetime = field(default_factory=datetime.utcnow)
    callback: Optional[Callable] = None


@dataclass
class AgentResponse:
    """Response from an agent"""
    request_id: str
    agent_type: AgentType
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None
    processing_time_ms: float = 0.0


class AgentController:
    """
    Central controller for managing AI agents
    Handles routing, lifecycle, and coordination
    """
    
    def __init__(
        self,
        llm_core: LLaMACore,
        vector_store: VectorStore,
        graph_store: GraphStore
    ):
        self.llm_core = llm_core
        self.vector_store = vector_store
        self.graph_store = graph_store
        
        # Agent registry
        self.agents: Dict[AgentType, BaseAgent] = {}
        
        # Request queue
        self.request_queue: asyncio.Queue = asyncio.Queue()
        
        # Response handlers
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
        # Running state
        self.is_running = False
        self._worker_task: Optional[asyncio.Task] = None
        
        logger.info("AgentController initialized")
    
    def register_agent(self, agent_type: AgentType, agent: BaseAgent):
        """Register an agent with the controller"""
        self.agents[agent_type] = agent
        agent.controller = self
        logger.info(f"Registered {agent_type.value} agent")
    
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
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("AgentController stopped")
    
    async def dispatch(
        self,
        agent_type: AgentType,
        user_id: str,
        context: Dict[str, Any],
        priority: int = 5,
        timeout: float = 30.0
    ) -> AgentResponse:
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
        request = AgentRequest(
            id=request_id,
            type=agent_type,
            user_id=user_id,
            context=context,
            priority=priority
        )
        
        # Create future for response
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_requests[request_id] = future
        
        # Add to queue
        await self.request_queue.put(request)
        
        logger.info(f"Dispatched request {request_id} to {agent_type.value}")
        
        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.error(f"Request {request_id} timed out")
            return AgentResponse(
                request_id=request_id,
                agent_type=agent_type,
                success=False,
                result={},
                error="Request timed out"
            )
        finally:
            self.pending_requests.pop(request_id, None)
    
    async def _orchestration_loop(self):
        """Main orchestration loop processing requests"""
        while self.is_running:
            try:
                # Get request from queue
                request: AgentRequest = await asyncio.wait_for(
                    self.request_queue.get(),
                    timeout=1.0
                )
                
                # Process request
                asyncio.create_task(self._process_request(request))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Orchestration loop error: {e}")
    
    async def _process_request(self, request: AgentRequest):
        """Process a single request"""
        start_time = datetime.utcnow()
        
        try:
            # Get appropriate agent
            agent = self.agents.get(request.type)
            if not agent:
                raise ValueError(f"No agent registered for type: {request.type}")
            
            # Check agent health
            if agent.state != AgentState.READY:
                raise RuntimeError(f"Agent {request.type.value} is not ready")
            
            # Execute agent
            logger.info(f"Executing {request.type.value} agent for request {request.id}")
            result = await agent.execute(request)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create response
            response = AgentResponse(
                request_id=request.id,
                agent_type=request.type,
                success=True,
                result=result,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Request {request.id} failed: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            response = AgentResponse(
                request_id=request.id,
                agent_type=request.type,
                success=False,
                result={},
                error=str(e),
                processing_time_ms=processing_time
            )
        
        # Complete the future
        future = self.pending_requests.get(request.id)
        if future and not future.done():
            future.set_result(response)
        
        # Log to vector store for learning
        await self._log_interaction(request, response)
    
    async def _log_interaction(self, request: AgentRequest, response: AgentResponse):
        """Log agent interaction for learning"""
        try:
            await self.vector_store.add_document(
                collection="agent_interactions",
                document={
                    "request_id": request.id,
                    "agent_type": request.type.value,
                    "user_id": request.user_id,
                    "context": request.context,
                    "result": response.result,
                    "success": response.success,
                    "error": response.error,
                    "processing_time_ms": response.processing_time_ms,
                    "timestamp": datetime.utcnow().isoformat()
                },
                metadata={
                    "agent_type": request.type.value,
                    "user_id": request.user_id,
                    "success": response.success
                }
            )
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
    
    async def coordinate_agents(
        self,
        agents: List[AgentType],
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, AgentResponse]:
        """
        Coordinate multiple agents for complex workflows
        
        Args:
            agents: List of agent types to coordinate
            user_id: User ID
            context: Shared context
            
        Returns:
            Dictionary of agent responses
        """
        logger.info(f"Coordinating agents: {[a.value for a in agents]}")
        
        # Dispatch all agents concurrently
        tasks = [
            self.dispatch(agent_type, user_id, context)
            for agent_type in agents
        ]
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile responses
        responses = {}
        for agent_type, result in zip(agents, results):
            if isinstance(result, Exception):
                responses[agent_type.value] = AgentResponse(
                    request_id="",
                    agent_type=agent_type,
                    success=False,
                    result={},
                    error=str(result)
                )
            else:
                responses[agent_type.value] = result
        
        return responses
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        return {
            agent_type.value: {
                "state": agent.state.value,
                "metrics": agent.metrics
            }
            for agent_type, agent in self.agents.items()
        }


# Global controller instance
_controller: Optional[AgentController] = None


async def get_agent_controller() -> AgentController:
    """Get or create the global agent controller"""
    global _controller
    if _controller is None:
        # Initialize components
        llm_core = LLaMACore()
        vector_store = VectorStore()
        graph_store = GraphStore()
        
        _controller = AgentController(llm_core, vector_store, graph_store)
        await _controller.start()
    
    return _controller
