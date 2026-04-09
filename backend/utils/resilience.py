"""Lightweight circuit-breaker utility used by AI service.

This is intentionally minimal: it provides `get_breaker(name, threshold, recovery_timeout)`
which returns an async callable that will run the decorated function and trip
open the circuit after `threshold` consecutive failures for `recovery_timeout` seconds.
"""
from __future__ import annotations

import time
import asyncio
import inspect
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def get_breaker(name: str, threshold: int = 5, recovery_timeout: int = 60) -> Callable:
    state = {
        "fails": 0,
        "opened_until": 0.0,
        "guard": asyncio.Lock(),
    }

    async def _breaker(fn: Callable, *args: Any, **kwargs: Any) -> Any:
        now = time.time()
        if state["opened_until"] > now:
            raise RuntimeError(f"Circuit '{name}' is open until {state['opened_until']}")

        try:
            if inspect.iscoroutinefunction(fn):
                result = await fn(*args, **kwargs)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: fn(*args, **kwargs))

            # success -> reset failure counter
            state["fails"] = 0
            return result

        except Exception as exc:
            async with state["guard"]:
                state["fails"] += 1
                if state["fails"] >= int(threshold):
                    state["opened_until"] = time.time() + float(recovery_timeout)
                    logger.warning(f"Circuit '{name}' opened for {recovery_timeout}s after {state['fails']} failures")
            raise

    return _breaker
