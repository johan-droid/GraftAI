"""
Unit tests for AI Agent implementations.
Tests the 4-phase agent loop: Perception → Cognition → Action → Reflection
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.ai.agents.base import BaseAgent, AgentState
from backend.ai.agents.booking_agent import BookingAgent
from backend.ai.orchestrator import AgentController, AgentType, AgentRequest, AgentResponse


@pytest.mark.unit
@pytest.mark.ai
class TestBaseAgent:
    """Test the base agent functionality."""

    def test_base_agent_initialization(self):
        """Test that base agent initializes with correct state."""
        agent = BaseAgent(name="test_agent")
        
        assert agent.name == "test_agent"
        assert agent.state == AgentState.IDLE
        assert agent.controller is None
        assert agent.memory == {}

    def test_agent_state_transitions(self):
        """Test agent state machine transitions."""
        agent = BaseAgent(name="test_agent")
        
        # Test valid transitions
        agent.transition_to(AgentState.PERCEIVING)
        assert agent.state == AgentState.PERCEIVING
        
        agent.transition_to(AgentState.COGNIZING)
        assert agent.state == AgentState.COGNIZING
        
        agent.transition_to(AgentState.ACTING)
        assert agent.state == AgentState.ACTING
        
        agent.transition_to(AgentState.REFLECTING)
        assert agent.state == AgentState.REFLECTING
        
        agent.transition_to(AgentState.COMPLETED)
        assert agent.state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_perception_phase_not_implemented(self):
        """Test that perception_phase raises NotImplementedError."""
        agent = BaseAgent(name="test_agent")
        
        with pytest.raises(NotImplementedError):
            await agent.perception_phase({})

    @pytest.mark.asyncio
    async def test_cognition_phase_not_implemented(self):
        """Test that cognition_phase raises NotImplementedError."""
        agent = BaseAgent(name="test_agent")
        
        with pytest.raises(NotImplementedError):
            await agent.cognition_phase({})

    @pytest.mark.asyncio
    async def test_action_phase_not_implemented(self):
        """Test that action_phase raises NotImplementedError."""
        agent = BaseAgent(name="test_agent")
        
        with pytest.raises(NotImplementedError):
            await agent.action_phase({})

    @pytest.mark.asyncio
    async def test_reflection_phase_not_implemented(self):
        """Test that reflection_phase raises NotImplementedError."""
        agent = BaseAgent(name="test_agent")
        
        with pytest.raises(NotImplementedError):
            await agent.reflection_phase({}, {})


@pytest.mark.unit
@pytest.mark.ai
class TestBookingAgent:
    """Test the booking agent implementation."""

    @pytest.fixture
    def booking_agent(self):
        """Create a booking agent instance."""
        return BookingAgent()

    @pytest.mark.asyncio
    async def test_booking_agent_name(self, booking_agent):
        """Test booking agent has correct name."""
        assert booking_agent.name == "booking"

    @pytest.mark.asyncio
    async def test_perception_phase_extracts_entities(self, booking_agent):
        """Test perception phase extracts meeting entities from context."""
        context = {
            "user_message": "Schedule a meeting tomorrow at 2pm with john@example.com",
            "entities": {
                "date": "tomorrow",
                "time": "14:00",
                "attendees": ["john@example.com"],
            }
        }
        
        result = await booking_agent.perception_phase(context)
        
        assert "perception" in result
        assert result["perception"]["raw_input"] == context["user_message"]
        assert "extracted_entities" in result["perception"]

    @pytest.mark.asyncio
    async def test_cognition_phase_evaluates_constraints(self, booking_agent):
        """Test cognition phase evaluates scheduling constraints."""
        context = {
            "user_id": "test-user-123",
            "entities": {
                "date": "2024-01-15",
                "time": "14:00",
                "duration": 30,
            }
        }
        
        # Mock the check_availability function
        with patch("backend.ai.agents.booking_agent.check_availability", return_value=True):
            result = await booking_agent.cognition_phase(context)
        
        assert "cognition" in result
        assert "decision" in result["cognition"]
        assert "confidence" in result["cognition"]
        assert "constraints_evaluated" in result["cognition"]

    @pytest.mark.asyncio
    async def test_action_phase_creates_booking(self, booking_agent):
        """Test action phase creates booking with correct data."""
        context = {
            "user_id": "test-user-123",
            "decision": {
                "action": "create_meeting",
                "title": "Test Meeting",
                "start_time": "2024-01-15T14:00:00",
                "duration": 30,
            }
        }
        
        with patch("backend.ai.agents.booking_agent.create_booking", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"id": "booking-123", "status": "confirmed"}
            result = await booking_agent.action_phase(context)
        
        assert "action" in result
        assert result["action"]["success"] is True
        assert "booking_id" in result["action"]

    @pytest.mark.asyncio
    async def test_reflection_phase_evaluates_success(self, booking_agent):
        """Test reflection phase evaluates action success."""
        context = {"user_id": "test-user-123"}
        results = {
            "action": {
                "success": True,
                "booking_id": "booking-123",
            }
        }
        
        result = await booking_agent.reflection_phase(context, results)
        
        assert "reflection" in result
        assert "quality_score" in result["reflection"]
        assert result["reflection"]["success"] is True
        assert "lessons" in result["reflection"]

    @pytest.mark.asyncio
    async def test_full_agent_execution_flow(self, booking_agent):
        """Test complete 4-phase execution flow."""
        context = {
            "user_id": "test-user-123",
            "user_message": "Book a 30min meeting tomorrow at 2pm",
            "entities": {
                "date": "tomorrow",
                "time": "14:00",
                "duration": 30,
            }
        }
        
        # Mock all external calls
        with patch.object(booking_agent, "perception_phase", new_callable=AsyncMock) as mock_perceive, \
             patch.object(booking_agent, "cognition_phase", new_callable=AsyncMock) as mock_cognize, \
             patch.object(booking_agent, "action_phase", new_callable=AsyncMock) as mock_act, \
             patch.object(booking_agent, "reflection_phase", new_callable=AsyncMock) as mock_reflect:
            
            mock_perceive.return_value = {"perception": {"entities": context["entities"]}}
            mock_cognize.return_value = {"cognition": {"decision": "create_meeting", "confidence": 0.9}}
            mock_act.return_value = {"action": {"success": True, "booking_id": "bk-123"}}
            mock_reflect.return_value = {"reflection": {"success": True, "quality_score": 95}}
            
            # Execute full flow
            await booking_agent.perception_phase(context)
            await booking_agent.cognition_phase(context)
            await booking_agent.action_phase(context)
            await booking_agent.reflection_phase(context, mock_act.return_value)
            
            # Verify all phases were called
            mock_perceive.assert_called_once()
            mock_cognize.assert_called_once()
            mock_act.assert_called_once()
            mock_reflect.assert_called_once()


@pytest.mark.unit
@pytest.mark.ai
class TestAgentController:
    """Test the agent controller orchestration."""

    @pytest.fixture
    def mock_llm_core(self):
        """Create mock LLM core."""
        return MagicMock()

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        return MagicMock()

    @pytest.fixture
    def mock_graph_store(self):
        """Create mock graph store."""
        return MagicMock()

    @pytest.fixture
    def controller(self, mock_llm_core, mock_vector_store, mock_graph_store):
        """Create an agent controller instance."""
        return AgentController(
            llm_core=mock_llm_core,
            vector_store=mock_vector_store,
            graph_store=mock_graph_store
        )

    @pytest.mark.asyncio
    async def test_controller_initialization(self, controller):
        """Test controller initializes correctly."""
        assert controller.llm_core is not None
        assert controller.vector_store is not None
        assert controller.graph_store is not None
        assert controller.is_running is False
        assert len(controller.agents) == 0

    def test_register_agent(self, controller):
        """Test agent registration."""
        mock_agent = MagicMock(spec=BaseAgent)
        mock_agent.name = "test_agent"
        
        controller.register_agent(AgentType.BOOKING, mock_agent)
        
        assert AgentType.BOOKING in controller.agents
        assert controller.agents[AgentType.BOOKING] == mock_agent
        assert mock_agent.controller == controller

    @pytest.mark.asyncio
    async def test_dispatch_unknown_agent_type(self, controller):
        """Test dispatch fails for unregistered agent type."""
        result = await controller.dispatch(
            agent_type=AgentType.BOOKING,
            user_id="test-user",
            context={}
        )
        
        assert result.success is False
        assert "No agent registered" in result.error

    @pytest.mark.asyncio
    async def test_dispatch_successful_execution(self, controller):
        """Test successful agent dispatch and execution."""
        # Create and register a mock agent
        mock_agent = MagicMock(spec=BaseAgent)
        mock_agent.name = "booking"
        mock_agent.execute = AsyncMock(return_value={
            "success": True,
            "booking_id": "bk-123",
            "phases": {
                "perception": {"status": "completed"},
                "cognition": {"status": "completed"},
                "action": {"status": "completed"},
                "reflection": {"status": "completed"},
            }
        })
        
        controller.register_agent(AgentType.BOOKING, mock_agent)
        
        # Execute dispatch
        result = await controller.dispatch(
            agent_type=AgentType.BOOKING,
            user_id="test-user",
            context={"message": "Book a meeting"}
        )
        
        assert result.success is True
        assert result.result["booking_id"] == "bk-123"
        mock_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_stop_orchestration(self, controller):
        """Test orchestration loop start and stop."""
        await controller.start()
        assert controller.is_running is True
        assert controller._worker_task is not None
        
        await controller.stop()
        assert controller.is_running is False


@pytest.mark.unit
@pytest.mark.ai
class TestAgentResponse:
    """Test agent response data structures."""

    def test_agent_response_creation(self):
        """Test AgentResponse dataclass creation."""
        response = AgentResponse(
            request_id="req-123",
            agent_type=AgentType.BOOKING,
            success=True,
            result={"booking_id": "bk-123"},
            processing_time_ms=150.5
        )
        
        assert response.request_id == "req-123"
        assert response.agent_type == AgentType.BOOKING
        assert response.success is True
        assert response.result["booking_id"] == "bk-123"
        assert response.processing_time_ms == 150.5
        assert response.error is None

    def test_agent_response_with_error(self):
        """Test AgentResponse with error."""
        response = AgentResponse(
            request_id="req-456",
            agent_type=AgentType.OPTIMIZATION,
            success=False,
            result={},
            error="Failed to optimize schedule",
            processing_time_ms=500.0
        )
        
        assert response.success is False
        assert response.error == "Failed to optimize schedule"


@pytest.mark.unit
@pytest.mark.ai
class TestAgentRequest:
    """Test agent request data structures."""

    def test_agent_request_creation(self):
        """Test AgentRequest dataclass creation."""
        request = AgentRequest(
            id="req-123",
            type=AgentType.BOOKING,
            user_id="user-456",
            context={"message": "Book a meeting"},
            priority=3
        )
        
        assert request.id == "req-123"
        assert request.type == AgentType.BOOKING
        assert request.user_id == "user-456"
        assert request.context["message"] == "Book a meeting"
        assert request.priority == 3
        assert request.timestamp is not None

    def test_agent_request_default_priority(self):
        """Test AgentRequest default priority."""
        request = AgentRequest(
            id="req-123",
            type=AgentType.EXECUTION,
            user_id="user-456",
            context={}
        )
        
        assert request.priority == 5  # Default priority
