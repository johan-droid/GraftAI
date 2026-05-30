import json
import logging
from datetime import datetime
from typing import Any

import msgpack

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
            logger.warning("Msgpack serialization failed, falling back to JSON bytes: %s", e)
            return json.dumps(data, default=cls.default_handler).encode("utf-8")

    @classmethod
    def from_binary(cls, data: bytes) -> Any:
        """Deserialize data from MessagePack binary format."""
        if data is None:
            return None
        if isinstance(data, str):
            data = data.encode("utf-8")
        elif isinstance(data, memoryview):
            data = data.tobytes()
        if not isinstance(data, (bytes, bytearray)):
            return data
        payload = bytes(data)
        stripped = payload.lstrip()
        if stripped.startswith((b"{", b"[", b'"', b"null", b"true", b"false")):
            try:
                return json.loads(payload.decode("utf-8"))
            except Exception:
                pass
        try:
            return msgpack.unpackb(payload, raw=False)
        except Exception as msgpack_error:
            try:
                decoded = payload.decode("utf-8")
                return json.loads(decoded)
            except Exception as json_error:
                preview = payload[:80]
                logger.warning("Failed to deserialize payload with msgpack or JSON (msgpack=%s, json=%s, preview=%r)", msgpack_error, json_error, preview)
                return decoded if "decoded" in locals() else payload

    @classmethod
    def pack_for_cache(cls, data: Any) -> bytes:
        """Pre-compressed binary format for storage in Redis."""
        return cls.to_binary(data)
serializer = SmartSerializer()
