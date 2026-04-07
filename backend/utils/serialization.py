import msgpack
import json
import logging
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartSerializer:
    """
    Handles high-performance serialization for 'big masses' of data.
    Supports JSON and MessagePack (Binary).
    """
    
    @staticmethod
    def default_handler(obj: Any) -> Any:
        """Custom handler for non-serializable types like datetime."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    @classmethod
    def to_binary(cls, data: Any) -> bytes:
        """Serialize data to MessagePack binary format."""
        try:
            return msgpack.packb(data, default=cls.default_handler, use_bin_type=True)
        except Exception as e:
            logger.error(f"❌ Msgpack serialization failed: {e}")
            # Fallback to JSON-in-bytes if msgpack fails
            return json.dumps(data, default=cls.default_handler).encode('utf-8')

    @classmethod
    def from_binary(cls, data: bytes) -> Any:
        """Deserialize data from MessagePack binary format."""
        try:
            return msgpack.unpackb(data, raw=False)
        except Exception as e:
            logger.error(f"❌ Msgpack deserialization failed: {e}")
            # Fallback to JSON if possible
            return json.loads(data.decode('utf-8'))

    @classmethod
    def pack_for_cache(cls, data: Any) -> bytes:
        """Pre-compressed binary format for storage in Redis."""
        return cls.to_binary(data)

# Global Serializer Instance
serializer = SmartSerializer()
