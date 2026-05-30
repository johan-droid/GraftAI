import os
import time


def generate_sequential_id() -> str:
    """
    Generates a standard-compliant UUID v7 (string representation).
    Format: 48-bit timestamp | 4-bit version | 12-bit randomness | 2-bit variant | 62-bit randomness
    Total: 128 bits, represented as 36-character hyphenated hex.
    """
    ts_ms = int(time.time() * 1000)
    random_bytes = bytearray(os.urandom(10))
    uuid_bytes = ts_ms.to_bytes(6, byteorder="big") + random_bytes
    uuid_bytes = bytearray(uuid_bytes)
    uuid_bytes[6] = uuid_bytes[6] & 15 | 112
    uuid_bytes[8] = uuid_bytes[8] & 63 | 128
    h = uuid_bytes.hex()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"
