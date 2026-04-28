"""
Unit tests for backend/utils/rate_limit.py changes in this PR:
- RateLimit.limit() now calls redis.eval() directly instead of
  redis.register_script(RATE_LIMIT_LUA)(...)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from redis.exceptions import RedisError

from backend.utils.rate_limit import RateLimit, RateLimitResult, rate_limit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_rate_limit(name: str = "test", max_requests: int = 5, window_seconds: int = 60) -> RateLimit:
    return RateLimit(name=name, max_requests=max_requests, window_seconds=window_seconds)


# ---------------------------------------------------------------------------
# RateLimit.limit — redis.eval call shape
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRateLimitEvalUsage:
    """Verify that RateLimit.limit calls redis.eval (not register_script)."""

    async def test_eval_called_instead_of_register_script(self):
        """redis.eval must be called; register_script must not be called."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 1, 60])
        mock_redis.register_script = MagicMock()

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit()
            await limiter.limit("user-1")

        mock_redis.eval.assert_called_once()
        mock_redis.register_script.assert_not_called()

    async def test_eval_receives_lua_script_as_first_arg(self):
        """First positional arg to redis.eval must be the RATE_LIMIT_LUA script string."""
        from backend.utils.rate_limit import RATE_LIMIT_LUA

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 1, 60])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit()
            await limiter.limit("user-2")

        call_args = mock_redis.eval.call_args[0]
        assert call_args[0] == RATE_LIMIT_LUA

    async def test_eval_numkeys_is_1(self):
        """Second positional arg (numkeys) must be 1."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 1, 60])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit()
            await limiter.limit("user-3")

        call_args = mock_redis.eval.call_args[0]
        assert call_args[1] == 1

    async def test_eval_key_format(self):
        """The Redis key arg must follow the format rate_limit:{name}:{identifier}."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 1, 60])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit(name="login")
            await limiter.limit("192.168.1.1")

        call_args = mock_redis.eval.call_args[0]
        key = call_args[2]
        assert key == "rate_limit:login:192.168.1.1"

    async def test_eval_passes_window_and_max_requests(self):
        """window_seconds and max_requests must appear as args to redis.eval."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 1, 60])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit(max_requests=10, window_seconds=300)
            await limiter.limit("user-4")

        call_args = mock_redis.eval.call_args[0]
        # args layout: (lua, numkeys, key, now, window_seconds, max_requests, member)
        window = call_args[4]
        max_req = call_args[5]
        assert window == 300
        assert max_req == 10


# ---------------------------------------------------------------------------
# RateLimit.limit — success path
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRateLimitSuccess:
    """Tests for the successful (allowed) path of RateLimit.limit."""

    async def test_returns_rate_limit_result(self):
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 3, 60])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit(max_requests=5)
            result = await limiter.limit("user-ok")

        assert isinstance(result, RateLimitResult)

    async def test_success_true_when_allowed(self):
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 2, 60])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            result = await make_rate_limit(max_requests=5).limit("user-allowed")

        assert result.success is True

    async def test_remaining_computed_correctly(self):
        """remaining = max(0, max_requests - count) when success."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 3, 60])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            result = await make_rate_limit(max_requests=5).limit("user-rem")

        assert result.remaining == 2  # max_requests(5) - count(3)

    async def test_count_reflects_redis_response(self):
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 4, 60])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            result = await make_rate_limit(max_requests=5).limit("user-cnt")

        assert result.count == 4

    async def test_reset_seconds_from_redis(self):
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 1, 45])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            result = await make_rate_limit().limit("user-reset")

        assert result.reset_seconds == 45


# ---------------------------------------------------------------------------
# RateLimit.limit — denied path
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRateLimitDenied:
    """Tests for the denied (rate-limited) path of RateLimit.limit."""

    async def test_success_false_when_denied(self):
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[0, 5, 30])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            result = await make_rate_limit(max_requests=5).limit("user-denied")

        assert result.success is False

    async def test_remaining_zero_when_denied(self):
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[0, 5, 30])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            result = await make_rate_limit(max_requests=5).limit("user-denied-rem")

        assert result.remaining == 0

    async def test_reset_seconds_when_denied(self):
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[0, 5, 25])

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            result = await make_rate_limit(max_requests=5).limit("user-denied-reset")

        assert result.reset_seconds == 25


# ---------------------------------------------------------------------------
# RateLimit.limit — Redis failure / fail-closed & fail-open behaviour
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRateLimitRedisFailure:
    """Tests for Redis unavailability behaviour."""

    async def test_login_fails_closed_on_redis_error(self):
        """Sensitive endpoints (login) must fail-closed when Redis is unavailable."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=RedisError("connection refused"))

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit(name="login")
            result = await limiter.limit("attacker-ip")

        assert result.success is False
        assert result.remaining == 0
        assert result.reset_seconds == limiter.window_seconds

    async def test_register_fails_closed_on_redis_error(self):
        """'register' endpoint must also fail-closed on Redis errors."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=RedisError("timeout"))

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit(name="register")
            result = await limiter.limit("user-reg")

        assert result.success is False

    async def test_non_sensitive_endpoint_fails_open_on_redis_error(self):
        """Non-sensitive endpoints must fail-open (allow) on Redis errors."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=RedisError("timeout"))

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit(name="availability", max_requests=10, window_seconds=60)
            result = await limiter.limit("user-avail")

        assert result.success is True
        assert result.remaining == limiter.max_requests

    async def test_connection_error_treated_same_as_redis_error(self):
        """ConnectionError should be treated as a Redis failure."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=ConnectionError("refused"))

        with patch("backend.utils.rate_limit.get_redis_client", return_value=mock_redis):
            limiter = make_rate_limit(name="login")
            result = await limiter.limit("user-conn-err")

        assert result.success is False


# ---------------------------------------------------------------------------
# rate_limit() helper function
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRateLimitHelperFunction:
    """Tests for the standalone rate_limit() function."""

    async def test_raises_http_429_when_denied(self):
        """rate_limit() must raise HTTP 429 when the limit result is not successful."""
        from fastapi import HTTPException

        limiter = make_rate_limit(name="test-helper", max_requests=1, window_seconds=60)
        denied_result = RateLimitResult(success=False, count=1, remaining=0, reset_seconds=30)

        with patch.object(limiter, "limit", new=AsyncMock(return_value=denied_result)):
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit("user-id", limiter)

        assert exc_info.value.status_code == 429
        assert "30" in exc_info.value.headers.get("Retry-After", "")

    async def test_returns_result_when_allowed(self):
        """rate_limit() must return the RateLimitResult when the request is allowed."""
        limiter = make_rate_limit(name="test-helper-ok")
        ok_result = RateLimitResult(success=True, count=1, remaining=9, reset_seconds=60)

        with patch.object(limiter, "limit", new=AsyncMock(return_value=ok_result)):
            result = await rate_limit("user-id-ok", limiter)

        assert result is ok_result

    async def test_empty_identifier_defaults_to_anonymous(self):
        """rate_limit() should substitute 'anonymous' for an empty identifier."""
        limiter = make_rate_limit(name="test-anon")
        ok_result = RateLimitResult(success=True, count=1, remaining=9, reset_seconds=60)

        with patch.object(limiter, "limit", new=AsyncMock(return_value=ok_result)) as mock_limit:
            await rate_limit("", limiter)

        mock_limit.assert_called_once_with("anonymous")