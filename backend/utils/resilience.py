"""Lightweight circuit-breaker utility used by AI service.

This is intentionally minimal: it provides `get_breaker(name, threshold, recovery_timeout)`
which returns an async callable that will run the decorated function and trip
open the circuit after `threshold` consecutive failures for `recovery_timeout` seconds.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
logger = logging.getLogger(__name__)

def get_breaker(name: str, threshold: int=5, recovery_timeout: int=60) -> Callable:
    state = {"fails": 0, "opened_until": 0.0, "guard": asyncio.Lock()}

    async def _breaker(fn: Callable, *args: Any, **kwargs: Any) -> Any:
        now = time.time()
        if state["opened_until"] > now:
            msg = f"Circuit '{name}' is open until {state['opened_until']}"
            raise RuntimeError(msg)
        try:
            if inspect.iscoroutinefunction(fn):
                result = await fn(*args, **kwargs)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: fn(*args, **kwargs))
            state["fails"] = 0
            return result
        except Exception:
            async with state["guard"]:
                state["fails"] += 1
                if state["fails"] >= int(threshold):
                    state["opened_until"] = time.time() + float(recovery_timeout)
                    logger.warning("Circuit '%s' opened for %ss after %s failures", name, recovery_timeout, state["fails"])
            raise
    return _breaker
