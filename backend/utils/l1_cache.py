import logging
import time
from typing import Any, Optional
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class LayeredCache:
    """
    A high-performance L1 (In-Memory) + L2 (Redis) cache bridge.
    L1 reduces serialization overhead and network latency for 'hot' keys.
    """
    def __init__(self, maxsize: int = 1000, ttl: int = 10):
        # Default 10s TTL for L1 to keep memory pressure low and consistency high
        self._l1 = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve from L1 memory."""
        val = self._l1.get(key)
        if val is not None:
            # logger.debug(f"🎯 [L1-HIT] {key}")
            return val
        return None

    def set(self, key: str, value: Any):
        """Set into L1 memory."""
        if value is not None:
            self._l1[key] = value

    def invalidate(self, key_pattern: Optional[str] = None):
        """Invalidate L1 entries."""
        if not key_pattern:
            self._l1.clear()
        else:
            # Simple prefix-based invalidation logic
            to_del = [k for k in self._l1.keys() if k.startswith(key_pattern)]
            for k in to_del:
                del self._l1[k]

# Global L1 Instance
l1_cache = LayeredCache(maxsize=2000, ttl=8)
