"""
Unit tests for Rate Limiter implementation.
Tests sliding window, fixed window, and token bucket strategies.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

from backend.utils.rate_limiter import (
    RateLimiter,
    RateLimitStrategy,
    RateLimitExceeded,
    RateLimitMiddleware,
    rate_limit,
    get_rate_limiter,
    reset_rate_limiter,
)


class MockRequest:
    """Mock FastAPI Request for testing."""
    
    def __init__(self, path="/api/v1/test", client_host="127.0.0.1", 
                 headers=None, user=None):
        self.url = MagicMock()
        self.url.path = path
        self.client = MagicMock()
        self.client.host = client_host
        self.headers = headers or {}
        self.state = MagicMock()
        self.state.user = user


class TestRateLimitStrategies:
    """Test different rate limiting strategies."""

    @pytest_asyncio.fixture
    async def memory_limiter(self):
        """Create a rate limiter with in-memory storage."""
        return RateLimiter(
            redis_client=None,  # Force in-memory fallback
            default_limit=10,
            default_window=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
        )

    @pytest.mark.asyncio
    async def test_fixed_window_in_memory(self, memory_limiter):
        """Test fixed window rate limiting with in-memory storage."""
        memory_limiter.strategy = RateLimitStrategy.FIXED_WINDOW
        
        request = MockRequest(path="/api/v1/test")
        
        # Should allow first 10 requests
        for _ in range(10):
            allowed, remaining, retry_after = await memory_limiter.is_allowed(request)
            assert allowed is True
            assert remaining >= 0
        
        # 11th request should be blocked
        allowed, remaining, retry_after = await memory_limiter.is_allowed(request)
        assert allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_sliding_window_in_memory(self, memory_limiter):
        """Test sliding window rate limiting with in-memory storage."""
        memory_limiter.strategy = RateLimitStrategy.SLIDING_WINDOW
        
        request = MockRequest(path="/api/v1/test")
        
        # Should allow requests up to limit
        for i in range(10):
            allowed, remaining, retry_after = await memory_limiter.is_allowed(request)
            assert allowed is True, f"Request {i+1} should be allowed"

    @pytest.mark.asyncio
    async def test_token_bucket_in_memory(self, memory_limiter):
        """Test token bucket rate limiting with in-memory storage."""
        memory_limiter.strategy = RateLimitStrategy.TOKEN_BUCKET
        
        request = MockRequest(path="/api/v1/test")
        
        # Should allow requests when tokens available
        allowed, remaining, retry_after = await memory_limiter.is_allowed(request)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limit_key_generation(self, memory_limiter):
        """Test that rate limit keys are generated correctly."""
        request = MockRequest(
            path="/api/v1/test",
            client_host="192.168.1.1"
        )
        
        key = memory_limiter._get_rate_limit_key(request)
        
        assert "rate_limit" in key
        assert "/api/v1/test" in key
        assert "192.168.1.1" in key

    @pytest.mark.asyncio
    async def test_client_identifier_with_api_key(self, memory_limiter):
        """Test client identification with API key."""
        request = MockRequest(
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        client_id = memory_limiter._get_client_identifier(request)
        
        assert "apikey:test-api-key-123" == client_id

    @pytest.mark.asyncio
    async def test_client_identifier_with_user(self, memory_limiter):
        """Test client identification with authenticated user."""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        request = MockRequest(user=mock_user)
        
        client_id = memory_limiter._get_client_identifier(request)
        
        assert "user:user-123" == client_id

    @pytest.mark.asyncio
    async def test_client_identifier_fallback_ip(self, memory_limiter):
        """Test client identification falls back to IP."""
        request = MockRequest(client_host="10.0.0.5")
        
        client_id = memory_limiter._get_client_identifier(request)
        
        assert "ip:10.0.0.5" == client_id

    @pytest.mark.asyncio
    async def test_endpoint_limits(self, memory_limiter):
        """Test that endpoint-specific limits are applied."""
        # Test auth endpoint (stricter limits)
        auth_request = MockRequest(path="/api/v1/auth/login")
        limit, window = memory_limiter._get_endpoint_limit(auth_request.url.path)
        
        assert limit == 5  # Login has 5 request limit
        assert window == 60

    @pytest.mark.asyncio
    async def test_ai_endpoint_limits(self, memory_limiter):
        """Test AI endpoint limits."""
        ai_request = MockRequest(path="/api/v1/ai/chat")
        limit, window = memory_limiter._get_endpoint_limit(ai_request.url.path)
        
        assert limit == 60  # AI chat has 60 request limit
        assert window == 60

    @pytest.mark.asyncio
    async def test_default_limits(self, memory_limiter):
        """Test default limits for unknown endpoints."""
        unknown_request = MockRequest(path="/api/v1/unknown")
        limit, window = memory_limiter._get_endpoint_limit(unknown_request.url.path)
        
        assert limit == 10  # Default limit
        assert window == 60  # Default window


class TestRateLimitMiddleware:
    """Test the rate limit middleware."""

    @pytest.mark.asyncio
    async def test_middleware_skips_health_checks(self):
        """Test that health check paths are skipped."""
        app = MagicMock()
        middleware = RateLimitMiddleware(
            app=app,
            skip_paths=["/health", "/docs"]
        )
        
        # Health check should be in skip paths
        assert "/health" in middleware.skip_paths
        assert "/docs" in middleware.skip_paths

    @pytest.mark.asyncio
    @patch("backend.utils.rate_limiter.RateLimiter.is_allowed")
    async def test_middleware_allows_requests_when_allowed(self, mock_is_allowed):
        """Test that middleware allows requests when rate limit permits."""
        mock_is_allowed.return_value = (True, 5, 0)
        
        app = AsyncMock()
        middleware = RateLimitMiddleware(app=app)
        
        request = MockRequest(path="/api/v1/users")
        
        # Mock call_next
        async def mock_call_next(req):
            response = MagicMock()
            response.headers = {}
            return response
        
        response = await middleware.dispatch(request, mock_call_next)
        
        assert response is not None
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    @pytest.mark.asyncio
    @patch("backend.utils.rate_limiter.RateLimiter.is_allowed")
    async def test_middleware_rejects_when_rate_limited(self, mock_is_allowed):
        """Test that middleware rejects requests when rate limited."""
        mock_is_allowed.return_value = (False, 0, 30)
        
        app = MagicMock()
        middleware = RateLimitMiddleware(app=app)
        
        request = MockRequest(path="/api/v1/users")
        
        async def mock_call_next(req):
            return MagicMock()
        
        with pytest.raises(RateLimitExceeded) as exc_info:
            await middleware.dispatch(request, mock_call_next)
        
        assert exc_info.value.status_code == 429
        assert "30" in exc_info.value.headers.get("Retry-After", "")


class TestRateLimitDecorator:
    """Test the rate limit decorator."""

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_allows_request(self):
        """Test that decorator allows request within limit."""
        
        @rate_limit(limit=5, window=60)
        async def test_endpoint(request):
            return {"success": True}
        
        mock_request = MagicMock()
        mock_request.app = MagicMock()
        mock_request.app.state = MagicMock()
        
        # Mock rate limiter in app state
        mock_limiter = AsyncMock()
        mock_limiter.is_allowed.return_value = (True, 4, 0)
        mock_request.app.state.rate_limiter = mock_limiter
        
        result = await test_endpoint(mock_request)
        
        assert result["success"] is True


class TestRedisIntegration:
    """Test Redis-based rate limiting."""

    @pytest.mark.asyncio
    @patch("backend.utils.rate_limiter.redis.from_url")
    async def test_redis_connection_attempt(self, mock_from_url):
        """Test that Redis connection is attempted."""
        reset_rate_limiter()
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        limiter = get_rate_limiter(redis_url="redis://localhost:6379")
        
        # Redis client should be set
        mock_from_url.assert_called_once_with("redis://localhost:6379", decode_responses=True)

    @pytest.mark.asyncio
    @patch("backend.utils.rate_limiter.redis.from_url")
    async def test_redis_fallback_on_failure(self, mock_from_url):
        """Test fallback to in-memory when Redis fails."""
        reset_rate_limiter()
        mock_from_url.side_effect = Exception("Redis connection failed")
        
        limiter = get_rate_limiter(redis_url="redis://localhost:6379")
        
        # Should still have a limiter, but with no Redis
        assert limiter is not None
        assert limiter.redis is None


class TestRateLimitEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_rate_limit_with_forwarded_header(self):
        """Test rate limiting with X-Forwarded-For header."""
        limiter = RateLimiter(redis_client=None)
        
        request = MockRequest(
            headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.2, 10.0.0.3"}
        )
        
        client_id = limiter._get_client_identifier(request)
        
        # Should use first IP from forwarded header
        assert "10.0.0.1" in client_id

    @pytest.mark.asyncio
    async def test_memory_store_cleanup(self):
        """Test that memory store is cleaned periodically."""
        limiter = RateLimiter(redis_client=None)
        
        # Add many entries to trigger cleanup
        for i in range(100):
            key = f"test-key-{i}"
            limiter._memory_store[key] = {"count": 1, "expiration": time.time() - 1}
        
        # Trigger cleanup
        request = MockRequest()
        await limiter.is_allowed(request)
        
        # Cleanup should have removed expired entries
        assert len(limiter._memory_store) < 100

    @pytest.mark.asyncio
    async def test_rate_limit_reset_after_window(self):
        """Test that rate limit resets after window expires."""
        limiter = RateLimiter(
            redis_client=None,
            default_limit=2,
            default_window=1,  # 1 second window for fast test
        )
        limiter.strategy = RateLimitStrategy.FIXED_WINDOW
        
        request = MockRequest(path="/test")
        
        # Use up the limit
        for _ in range(2):
            allowed, _, _ = await limiter.is_allowed(request)
            assert allowed is True
        
        # Should be blocked
        allowed, _, retry_after = await limiter.is_allowed(request)
        assert allowed is False
        
        # Wait for window to expire
        await asyncio.sleep(1.1)
        
        # Should be allowed again
        allowed, _, _ = await limiter.is_allowed(request)
        assert allowed is True


class TestRateLimitStrategiesComparison:
    """Compare behavior of different rate limiting strategies."""

    @pytest.mark.asyncio
    async def test_sliding_window_vs_fixed_window(self):
        """Test behavioral differences between sliding and fixed window."""
        
        # Fixed window can have traffic spikes at window boundaries
        fixed_limiter = RateLimiter(
            redis_client=None,
            default_limit=10,
            default_window=60,
            strategy=RateLimitStrategy.FIXED_WINDOW,
        )
        
        # Sliding window provides smoother rate limiting
        sliding_limiter = RateLimiter(
            redis_client=None,
            default_limit=10,
            default_window=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
        )
        
        request = MockRequest(path="/test")
        
        # Both should allow initial requests
        for _ in range(5):
            fixed_allowed, _, _ = await fixed_limiter.is_allowed(request)
            sliding_allowed, _, _ = await sliding_limiter.is_allowed(request)
            
            assert fixed_allowed is True
            assert sliding_allowed is True


class TestRateLimiterTypingImport:
    """
    Regression tests for the PR change that removed `Any` from the
    `from typing import ...` statement in rate_limiter.py.

    Ensures the module still imports cleanly and RateLimiter is usable
    even though `Any` was removed from the explicit imports.
    """

    def test_module_imports_without_error(self):
        """Importing backend.utils.rate_limiter must not raise any NameError."""
        import importlib
        import backend.utils.rate_limiter as mod
        # If Any removal breaks anything, importlib.reload would surface it.
        importlib.reload(mod)

    def test_rate_limiter_instantiates(self):
        """RateLimiter() must construct successfully after the import cleanup."""
        limiter = RateLimiter(redis_client=None)
        assert limiter is not None

    def test_memory_store_is_dict(self):
        """_memory_store must still be an initialised dict after the typing change."""
        limiter = RateLimiter(redis_client=None)
        assert isinstance(limiter._memory_store, dict)

    def test_any_not_in_module_imports(self):
        """Verify that `Any` is no longer imported at module level in rate_limiter."""
        import typing
        import backend.utils.rate_limiter as mod
        # 'Any' should not appear as a direct attribute of the module namespace
        # (it was only used as a typing annotation, not exported).
        assert not hasattr(mod, "Any"), (
            "Any was removed from rate_limiter imports in this PR; "
            "it should not be a module-level name"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
