"""
Unit tests for Circuit Breaker implementation.
Tests all three states: CLOSED, OPEN, HALF_OPEN
"""
import asyncio

import pytest

from backend.utils.circuit_breaker import (
    GOOGLE_CALENDAR_BREAKER,
    SENDGRID_BREAKER,
    SLACK_BREAKER,
    TWILIO_BREAKER,
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
    circuit_breaker,
)


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions."""

    @pytest.fixture
    def fresh_breaker(self):
        """Create a fresh circuit breaker for testing."""
        import uuid
        name = f"test-breaker-{uuid.uuid4()}"
        return CircuitBreaker(name=name, failure_threshold=3, recovery_timeout=1.0, half_open_max_calls=2, success_threshold=2)

    def test_initial_state_is_closed(self, fresh_breaker):
        """Test that new circuit breaker starts in CLOSED state."""
        assert fresh_breaker.state == CircuitState.CLOSED

    def test_can_execute_in_closed_state(self, fresh_breaker):
        """Test that calls are allowed in CLOSED state."""
        assert fresh_breaker.can_execute() is True

    @pytest.mark.asyncio
    async def test_opens_after_failure_threshold(self, fresh_breaker):
        """Test that circuit opens after failure threshold reached."""
        for _ in range(3):
            await fresh_breaker.record_failure()
        assert fresh_breaker.state == CircuitState.OPEN
        assert fresh_breaker.state == CircuitState.OPEN
        assert fresh_breaker.can_execute() is False

    @pytest.mark.asyncio
    async def test_opens_after_consecutive_failures(self, fresh_breaker):
        """Test that circuit opens only after consecutive failures."""
        await fresh_breaker.record_success()
        await fresh_breaker.record_failure()
        await fresh_breaker.record_success()
        await fresh_breaker.record_failure()
        assert fresh_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(self, fresh_breaker):
        """Test that circuit transitions to HALF_OPEN after recovery timeout."""
        for _ in range(3):
            await fresh_breaker.record_failure()
        assert fresh_breaker.state == CircuitState.OPEN
        await asyncio.sleep(1.5)
        assert fresh_breaker.can_execute() is True

    @pytest.mark.asyncio
    async def test_closes_after_success_threshold_in_half_open(self, fresh_breaker):
        """Test that circuit closes after success threshold in HALF_OPEN."""
        for _ in range(3):
            await fresh_breaker.record_failure()
        assert fresh_breaker.state == CircuitState.OPEN
        await asyncio.sleep(1.5)
        assert fresh_breaker.can_execute() is True
        assert fresh_breaker.state == CircuitState.HALF_OPEN
        await fresh_breaker.record_success()
        await fresh_breaker.record_success()
        assert fresh_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_failure_in_half_open(self, fresh_breaker):
        """Test that circuit reopens on failure in HALF_OPEN state."""
        for _ in range(3):
            await fresh_breaker.record_failure()
        assert fresh_breaker.state == CircuitState.OPEN
        await asyncio.sleep(1.5)
        assert fresh_breaker.can_execute() is True
        await fresh_breaker.record_failure()
        assert fresh_breaker.state == CircuitState.OPEN

class TestCircuitBreakerDecorator:
    """Test the circuit breaker decorator."""

    @pytest.fixture
    def test_breaker(self):
        """Create a test circuit breaker."""
        import uuid
        return CircuitBreaker(name=f"decorator-test-{uuid.uuid4()}", failure_threshold=2, recovery_timeout=1.0)

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
            msg = "Test error"
            raise ValueError(msg)
        with pytest.raises(ValueError):
            await failing_function()
        await asyncio.sleep(0.1)
        stats = test_breaker.stats
        assert stats.failures == 1
        assert stats.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_decorator_blocks_when_open(self, test_breaker):
        """Test that decorated function is blocked when circuit is open."""
        for _ in range(2):
            await test_breaker.record_failure()
        assert test_breaker.state == CircuitState.OPEN

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
        return CircuitBreaker(name=f"stats-test-{uuid.uuid4()}", failure_threshold=5)

    @pytest.mark.asyncio
    async def test_stats_tracking(self, stats_breaker):
        """Test that statistics are tracked correctly."""
        await stats_breaker.record_success()
        await stats_breaker.record_success()
        await stats_breaker.record_failure()
        await stats_breaker.record_success()
        stats = stats_breaker.stats
        assert stats.total_calls == 4
        assert stats.successes == 3
        assert stats.failures == 1
        assert stats.consecutive_successes == 1
        assert stats.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_get_status(self, stats_breaker):
        """Test the get_status method."""
        await stats_breaker.record_success()
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
        assert GOOGLE_CALENDAR_BREAKER.recovery_timeout == 120

class TestCircuitBreakerFactory:
    """Test the circuit breaker factory function."""

    def test_circuit_breaker_decorator_factory(self):
        """Test the circuit_breaker decorator factory."""
        import uuid
        name = f"factory-test-{uuid.uuid4()}"
        breaker_decorator = circuit_breaker(name=name, failure_threshold=3, recovery_timeout=30.0)
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
        breaker2 = CircuitBreaker(name=name, failure_threshold=10)
        assert breaker1 is breaker2
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
        breaker = CircuitBreaker(name=f"concurrent-test-{uuid.uuid4()}", failure_threshold=100)

        @breaker
        async def successful_call(id: int):
            await asyncio.sleep(0.01)
            return {"id": id, "success": True}
        tasks = [successful_call(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        assert all(r["success"] for r in results)
        await asyncio.sleep(0.2)
        assert breaker.stats.successes == 10
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
