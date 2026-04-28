"""
Unit tests for AIQuotaMiddleware changes introduced in this PR:
- Removed module-level QUOTA_LUA_SCRIPT constant; script is now inlined in _check_quota_redis
- Replaced r.register_script(...); script(keys=..., args=...) with r.eval(lua, 1, key, ...)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from backend.utils.quota_middleware import (
    AIQuotaExceeded,
    AIQuotaMiddleware,
    AI_QUOTA_CONFIG,
)


# ---------------------------------------------------------------------------
# AIQuotaExceeded tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAIQuotaExceeded:
    """Tests for the AIQuotaExceeded custom exception."""

    def test_status_code_is_429(self):
        exc = AIQuotaExceeded(retry_after=60)
        assert exc.status_code == 429

    def test_retry_after_header_present(self):
        exc = AIQuotaExceeded(retry_after=30)
        assert exc.headers["Retry-After"] == "30"

    def test_detail_contains_retry_seconds(self):
        exc = AIQuotaExceeded(retry_after=120)
        assert "120" in exc.detail

    def test_retry_after_zero(self):
        exc = AIQuotaExceeded(retry_after=0)
        assert exc.headers["Retry-After"] == "0"


# ---------------------------------------------------------------------------
# AIQuotaMiddleware._check_quota_redis tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCheckQuotaRedis:
    """Tests for _check_quota_redis which now uses r.eval() directly."""

    @pytest.fixture
    def middleware(self):
        app = MagicMock()
        return AIQuotaMiddleware(app)

    @pytest.fixture
    def mock_redis(self):
        r = AsyncMock()
        return r

    async def test_allowed_when_tokens_available(self, middleware, mock_redis):
        """When Redis returns allowed=1, the middleware should permit the request."""
        mock_redis.eval = AsyncMock(return_value=[1, 9.0])

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            allowed, tokens_left, retry_after = await middleware._check_quota_redis(
                user_id="user-1",
                path="/api/v1/bookings",
                config=AI_QUOTA_CONFIG["/api/v1/bookings"],
            )

        assert allowed is True
        assert tokens_left == 9.0
        assert retry_after == 0

    async def test_denied_when_tokens_exhausted(self, middleware, mock_redis):
        """When Redis returns allowed=0, the middleware should deny the request."""
        mock_redis.eval = AsyncMock(return_value=[0, 0.0])

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            allowed, tokens_left, retry_after = await middleware._check_quota_redis(
                user_id="user-2",
                path="/api/v1/bookings",
                config=AI_QUOTA_CONFIG["/api/v1/bookings"],
            )

        assert allowed is False
        assert tokens_left == 0.0
        assert retry_after > 0

    async def test_eval_called_with_correct_key_format(self, middleware, mock_redis):
        """r.eval must be called with the expected Redis key ai_quota:{user_id}:{path}."""
        mock_redis.eval = AsyncMock(return_value=[1, 5.0])

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            await middleware._check_quota_redis(
                user_id="user-abc",
                path="/api/v1/ai/chat",
                config=AI_QUOTA_CONFIG["/api/v1/ai/chat"],
            )

        call_args = mock_redis.eval.call_args
        # Second positional arg after the lua script and numkeys should be the key
        # Signature: r.eval(lua, numkeys, key, now, refill_rate, capacity, cost)
        positional_args = call_args[0]
        assert positional_args[2] == "ai_quota:user-abc:/api/v1/ai/chat"

    async def test_eval_called_with_numkeys_1(self, middleware, mock_redis):
        """r.eval must be called with numkeys=1."""
        mock_redis.eval = AsyncMock(return_value=[1, 5.0])

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            await middleware._check_quota_redis(
                user_id="user-abc",
                path="/api/v1/ai/chat",
                config=AI_QUOTA_CONFIG["/api/v1/ai/chat"],
            )

        call_args = mock_redis.eval.call_args
        positional_args = call_args[0]
        # positional_args[1] is numkeys
        assert positional_args[1] == 1

    async def test_eval_receives_capacity_and_refill_rate(self, middleware, mock_redis):
        """r.eval args must include the correct capacity and refill_rate from config."""
        mock_redis.eval = AsyncMock(return_value=[1, 49.0])
        config = AI_QUOTA_CONFIG["/api/v1/ai/chat"]

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            await middleware._check_quota_redis(
                user_id="user-x",
                path="/api/v1/ai/chat",
                config=config,
            )

        call_args = mock_redis.eval.call_args
        positional_args = call_args[0]
        # positional_args: (lua, 1, key, now, refill_rate, capacity, cost)
        refill_rate = positional_args[4]
        capacity = positional_args[5]
        cost = positional_args[6]
        assert refill_rate == config["refill_rate"]
        assert capacity == config["capacity"]
        assert cost == config["cost"]

    async def test_retry_after_calculated_from_cost_and_tokens(self, middleware, mock_redis):
        """retry_after = int((cost - tokens_left) / refill_rate) + 1."""
        config = AI_QUOTA_CONFIG["/api/v1/bookings"]
        tokens_left = 0.0
        mock_redis.eval = AsyncMock(return_value=[0, tokens_left])

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            _, _, retry_after = await middleware._check_quota_redis(
                user_id="user-rate",
                path="/api/v1/bookings",
                config=config,
            )

        expected = int((config["cost"] - tokens_left) / config["refill_rate"]) + 1
        assert retry_after == expected

    async def test_retry_after_is_zero_when_allowed(self, middleware, mock_redis):
        """retry_after must be 0 when request is allowed."""
        mock_redis.eval = AsyncMock(return_value=[1, 8.0])

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            allowed, _, retry_after = await middleware._check_quota_redis(
                user_id="user-ok",
                path="/api/v1/bookings",
                config=AI_QUOTA_CONFIG["/api/v1/bookings"],
            )

        assert allowed is True
        assert retry_after == 0

    async def test_exception_falls_back_to_allow(self, middleware, mock_redis):
        """If Redis raises an exception the middleware should fail-open: return (True, 0, 0)."""
        mock_redis.eval = AsyncMock(side_effect=Exception("Redis down"))

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            allowed, tokens_left, retry_after = await middleware._check_quota_redis(
                user_id="user-err",
                path="/api/v1/bookings",
                config=AI_QUOTA_CONFIG["/api/v1/bookings"],
            )

        assert allowed is True
        assert tokens_left == 0
        assert retry_after == 0

    async def test_no_register_script_usage(self, middleware, mock_redis):
        """register_script must NOT be called; only r.eval should be used."""
        mock_redis.eval = AsyncMock(return_value=[1, 5.0])
        mock_redis.register_script = MagicMock()

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            await middleware._check_quota_redis(
                user_id="user-noscript",
                path="/api/v1/bookings",
                config=AI_QUOTA_CONFIG["/api/v1/bookings"],
            )

        mock_redis.register_script.assert_not_called()
        mock_redis.eval.assert_called_once()

    async def test_partial_tokens_left_returns_float(self, middleware, mock_redis):
        """tokens_left should be returned as a float."""
        mock_redis.eval = AsyncMock(return_value=[1, 3.7])

        with patch("backend.utils.quota_middleware.get_redis", return_value=mock_redis):
            _, tokens_left, _ = await middleware._check_quota_redis(
                user_id="user-float",
                path="/api/v1/bookings",
                config=AI_QUOTA_CONFIG["/api/v1/bookings"],
            )

        assert isinstance(tokens_left, float)
        assert tokens_left == pytest.approx(3.7)


# ---------------------------------------------------------------------------
# AIQuotaMiddleware.dispatch tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAIQuotaMiddlewareDispatch:
    """Tests for the dispatch method path logic (unchanged logic, verify integration)."""

    @pytest.fixture
    def middleware(self):
        app = MagicMock()
        return AIQuotaMiddleware(app)

    def _make_request(self, path: str, method: str = "POST", user_id: str = "user-1"):
        request = MagicMock()
        request.url.path = path
        request.method = method
        request.headers = {}
        request.cookies = {}
        request.state = MagicMock(spec=[])  # no user attribute
        return request

    async def test_non_quota_path_passes_through(self, middleware):
        """Requests to paths not in AI_QUOTA_CONFIG are allowed without quota check."""
        request = self._make_request(path="/api/v1/other")
        call_next = AsyncMock(return_value=MagicMock(headers={}))

        await middleware.dispatch(request, call_next)

        call_next.assert_called_once()

    async def test_get_method_skips_quota_check(self, middleware):
        """GET requests to quota-protected paths bypass the quota check."""
        request = self._make_request(path="/api/v1/bookings", method="GET")
        call_next = AsyncMock(return_value=MagicMock(headers={}))

        await middleware.dispatch(request, call_next)

        call_next.assert_called_once()

    async def test_raises_ai_quota_exceeded_when_denied(self, middleware):
        """dispatch must raise AIQuotaExceeded (HTTP 429) when quota is exceeded."""
        request = self._make_request(path="/api/v1/bookings", method="POST")
        # Provide a Bearer token so user_id extraction works
        request.headers = {"Authorization": "Bearer fake.token.here"}

        call_next = AsyncMock(return_value=MagicMock(headers={}))

        with patch.object(
            middleware, "_get_user_id", new=AsyncMock(return_value="user-denied")
        ), patch.object(
            middleware,
            "_check_quota_redis",
            new=AsyncMock(return_value=(False, 0.0, 42)),
        ):
            with pytest.raises(AIQuotaExceeded) as exc_info:
                await middleware.dispatch(request, call_next)

        assert exc_info.value.status_code == 429

    async def test_quota_remaining_header_added_on_success(self, middleware):
        """X-AI-Quota-Remaining header is set in the response when request is allowed."""
        request = self._make_request(path="/api/v1/bookings", method="POST")
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        with patch.object(
            middleware, "_get_user_id", new=AsyncMock(return_value="user-ok")
        ), patch.object(
            middleware,
            "_check_quota_redis",
            new=AsyncMock(return_value=(True, 7.0, 0)),
        ):
            response = await middleware.dispatch(request, call_next)

        assert "X-AI-Quota-Remaining" in response.headers
        assert response.headers["X-AI-Quota-Remaining"] == "7"


# ---------------------------------------------------------------------------
# Module-level constant tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestQuotaModuleConstants:
    """Verify that the module-level QUOTA_LUA_SCRIPT constant was removed."""

    def test_quota_lua_script_constant_not_exported(self):
        """QUOTA_LUA_SCRIPT should no longer exist at module level after the PR."""
        import backend.utils.quota_middleware as mod
        assert not hasattr(mod, "QUOTA_LUA_SCRIPT"), (
            "QUOTA_LUA_SCRIPT was removed from module scope in this PR; "
            "it should not be a module attribute"
        )