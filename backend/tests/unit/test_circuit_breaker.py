"""
Unit tests for Circuit Breaker implementation.
Tests all three states: CLOSED, OPEN, HALF_OPEN
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from backend.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpen,
    circuit_breaker,
    SENDGRID_BREAKER,
    TWILIO_BREAKER,
    SLACK_BREAKER,
    GOOGLE_CALENDAR_BREAKER,
)


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions."""

    @pytest.fixture
    def fresh_breaker(self):
        """Create a fresh circuit breaker for testing."""
        # Use a unique name to avoid singleton conflicts
        import uuid
        name = f"test-breaker-{uuid.uuid4()}"
        return CircuitBreaker(
            name=name,
            failure_threshold=3,
            recovery_timeout=1.0,  # 1 second for fast tests
            half_open_max_calls=2,
            success_threshold=2,
        )

    def test_initial_state_is_closed(self, fresh_breaker):
        """Test that new circuit breaker starts in CLOSED state."""
        assert fresh_breaker.state == CircuitState.CLOSED

    def test_can_execute_in_closed_state(self, fresh_breaker):
        """Test that calls are allowed in CLOSED state."""
        assert fresh_breaker.can_execute() is True

    @pytest.mark.asyncio
    async def test_opens_after_failure_threshold(self, fresh_breaker):
        """Test that circuit opens after failure threshold reached."""
        # Record failures up to threshold
        for _ in range(3):
            fresh_breaker.record_failure()
            await asyncio.sleep(0.1)  # Allow async processing
        
        await asyncio.sleep(0.2)  # Wait for async state update
        
        assert fresh_breaker.state == CircuitState.OPEN
        assert fresh_breaker.can_execute() is False

    @pytest.mark.asyncio
    async def test_opens_after_consecutive_failures(self, fresh_breaker):
        """Test that circuit opens only after consecutive failures."""
        # Mix of successes and failures - should stay closed
        fresh_breaker.record_success()
        await asyncio.sleep(0.1)
        
        fresh_breaker.record_failure()
        await asyncio.sleep(0.1)
        
        fresh_breaker.record_success()
        await asyncio.sleep(0.1)
        
        fresh_breaker.record_failure()
        await asyncio.sleep(0.1)
        
        # Still closed - not enough consecutive failures
        assert fresh_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(self, fresh_breaker):
        """Test that circuit transitions to HALF_OPEN after recovery timeout."""
        # Open the circuit
        for _ in range(3):
            fresh_breaker.record_failure()
            await asyncio.sleep(0.1)
        
        await asyncio.sleep(0.2)
        assert fresh_breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout (1 second in test config)
        await asyncio.sleep(1.5)
        
        # Should now be able to execute (half-open)
        assert fresh_breaker.can_execute() is True
        # State should be HALF_OPEN
        # Note: state transitions to HALF_OPEN inside can_execute()

    @pytest.mark.asyncio
    async def test_closes_after_success_threshold_in_half_open(self, fresh_breaker):
        """Test that circuit closes after success threshold in HALF_OPEN."""
        # Open the circuit
        for _ in range(3):
            fresh_breaker.record_failure()
            await asyncio.sleep(0.1)
        
        await asyncio.sleep(0.2)
        assert fresh_breaker.state == CircuitState.OPEN
        
        # Wait for recovery
        await asyncio.sleep(1.5)
        
        # Record successes to close circuit
        fresh_breaker.record_success()
        await asyncio.sleep(0.1)
        
        fresh_breaker.record_success()
        await asyncio.sleep(0.1)
        
        assert fresh_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_failure_in_half_open(self, fresh_breaker):
        """Test that circuit reopens on failure in HALF_OPEN state."""
        # Open the circuit
        for _ in range(3):
            fresh_breaker.record_failure()
            await asyncio.sleep(0.1)
        
        await asyncio.sleep(0.2)
        assert fresh_breaker.state == CircuitState.OPEN
        
        # Wait for recovery
        await asyncio.sleep(1.5)
        
        # First call allowed in HALF_OPEN
        assert fresh_breaker.can_execute() is True
        
        # Record failure in half-open
        fresh_breaker.record_failure()
        await asyncio.sleep(0.1)
        
        # Should reopen
        assert fresh_breaker.state == CircuitState.OPEN


class TestCircuitBreakerDecorator:
    """Test the circuit breaker decorator."""

    @pytest.fixture
    def test_breaker(self):
        """Create a test circuit breaker."""
        import uuid
        return CircuitBreaker(
            name=f"decorator-test-{uuid.uuid4()}",
            failure_threshold=2,
            recovery_timeout=1.0,
        )

    @pytest.mark.asyncio
    async def test_decorator_allows_normal_execution(self, test_breaker):
        """Test that decorated function executes normally."""
        @test_breaker
        async def successful_function():
            return {"success": True, "data": "test"}
        
        result = await successful_function()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_decorator_records_success(self, test_breaker):
        """Test that successful execution records success."""
        @test_breaker
        async def successful_function():
            return {"success": True}
        
        await successful_function()
        await asyncio.sleep(0.1)
        
        stats = test_breaker.stats
        assert stats.successes == 1
        assert stats.consecutive_successes == 1

    @pytest.mark.asyncio
    async def test_decorator_records_failure(self, test_breaker):
        """Test that failed execution records failure."""
        @test_breaker
        async def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await failing_function()
        
        await asyncio.sleep(0.1)
        
        stats = test_breaker.stats
        assert stats.failures == 1
        assert stats.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_decorator_blocks_when_open(self, test_breaker):
        """Test that decorated function is blocked when circuit is open."""
        # Manually open the circuit
        for _ in range(2):
            test_breaker.record_failure()
            await asyncio.sleep(0.1)
        
        await asyncio.sleep(0.2)
        
        @test_breaker
        async def should_be_blocked():
            return {"success": True}
        
        with pytest.raises(CircuitBreakerOpen):
            await should_be_blocked()


class TestCircuitBreakerStats:
    """Test circuit breaker statistics."""

    @pytest.fixture
    def stats_breaker(self):
        """Create a breaker for stats testing."""
        import uuid
        return CircuitBreaker(
            name=f"stats-test-{uuid.uuid4()}",
            failure_threshold=5,
        )

    @pytest.mark.asyncio
    async def test_stats_tracking(self, stats_breaker):
        """Test that statistics are tracked correctly."""
        # Record mixed successes and failures
        stats_breaker.record_success()
        await asyncio.sleep(0.05)
        
        stats_breaker.record_success()
        await asyncio.sleep(0.05)
        
        stats_breaker.record_failure()
        await asyncio.sleep(0.05)
        
        stats_breaker.record_success()
        await asyncio.sleep(0.05)
        
        stats = stats_breaker.stats
        assert stats.total_calls == 4
        assert stats.successes == 3
        assert stats.failures == 1
        assert stats.consecutive_successes == 1
        assert stats.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_get_status(self, stats_breaker):
        """Test the get_status method."""
        stats_breaker.record_success()
        await asyncio.sleep(0.05)
        
        status = stats_breaker.get_status()
        
        assert "name" in status
        assert "state" in status
        assert "stats" in status
        assert "config" in status
        assert status["state"] == "closed"
        assert status["stats"]["successes"] == 1


class TestPreconfiguredBreakers:
    """Test the pre-configured circuit breakers."""

    def test_sendgrid_breaker_exists(self):
        """Test that SendGrid breaker is configured."""
        assert SENDGRID_BREAKER is not None
        assert SENDGRID_BREAKER.name == "sendgrid"
        assert SENDGRID_BREAKER.failure_threshold == 5

    def test_twilio_breaker_exists(self):
        """Test that Twilio breaker is configured."""
        assert TWILIO_BREAKER is not None
        assert TWILIO_BREAKER.name == "twilio"

    def test_slack_breaker_exists(self):
        """Test that Slack breaker is configured."""
        assert SLACK_BREAKER is not None
        assert SLACK_BREAKER.name == "slack"

    def test_google_calendar_breaker_exists(self):
        """Test that Google Calendar breaker is configured."""
        assert GOOGLE_CALENDAR_BREAKER is not None
        assert GOOGLE_CALENDAR_BREAKER.name == "google_calendar"
        assert GOOGLE_CALENDAR_BREAKER.recovery_timeout == 120  # Longer timeout


class TestCircuitBreakerFactory:
    """Test the circuit breaker factory function."""

    def test_circuit_breaker_decorator_factory(self):
        """Test the circuit_breaker decorator factory."""
        import uuid
        name = f"factory-test-{uuid.uuid4()}"
        
        breaker_decorator = circuit_breaker(
            name=name,
            failure_threshold=3,
            recovery_timeout=30.0,
        )
        
        assert breaker_decorator is not None
        
        @breaker_decorator
        async def test_func():
            return True
        
        assert test_func is not None


class TestCircuitBreakerSingleton:
    """Test that circuit breakers are singletons by name."""

    def test_same_name_returns_same_instance(self):
        """Test that same name returns the same instance."""
        import uuid
        name = f"singleton-test-{uuid.uuid4()}"
        
        breaker1 = CircuitBreaker(name=name, failure_threshold=5)
        breaker2 = CircuitBreaker(name=name, failure_threshold=10)  # Different config
        
        # Should be same instance (singleton)
        assert breaker1 is breaker2
        # Config from first instantiation wins
        assert breaker1.failure_threshold == 5

    def test_different_names_return_different_instances(self):
        """Test that different names return different instances."""
        import uuid
        
        breaker1 = CircuitBreaker(name=f"test-1-{uuid.uuid4()}", failure_threshold=5)
        breaker2 = CircuitBreaker(name=f"test-2-{uuid.uuid4()}", failure_threshold=5)
        
        assert breaker1 is not breaker2


class TestCircuitBreakerConcurrency:
    """Test circuit breaker under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_successes(self):
        """Test concurrent successful calls."""
        import uuid
        breaker = CircuitBreaker(
            name=f"concurrent-test-{uuid.uuid4()}",
            failure_threshold=100,  # High threshold
        )
        
        @breaker
        async def successful_call(id: int):
            await asyncio.sleep(0.01)  # Simulate work
            return {"id": id, "success": True}
        
        # Run 10 concurrent calls
        tasks = [successful_call(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(r["success"] for r in results)
        
        await asyncio.sleep(0.2)
        assert breaker.stats.successes == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
