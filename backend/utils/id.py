import time
import os

def generate_sequential_id() -> str:
    """
    Generates a standard-compliant UUID v7 (string representation).
    Format: 48-bit timestamp | 4-bit version | 12-bit randomness | 2-bit variant | 62-bit randomness
    Total: 128 bits, represented as 36-character hyphenated hex.
    """
    # 1. 48-bit timestamp (milliseconds since epoch)
    ts_ms = int(time.time() * 1000)
    
    # 2. Generate 10 bytes of randomness
    random_bytes = bytearray(os.urandom(10))
    
    # 3. Construct the 16-byte UUID v7
    # Byte 0-5: Timestamp
    uuid_bytes = ts_ms.to_bytes(6, byteorder='big') + random_bytes
    
    # Byte 6: Set version (0111 = 7) in high 4 bits
    uuid_bytes = bytearray(uuid_bytes)
    uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x70
    
    # Byte 8: Set variant (10xx = RFC 4122) in high 2 bits
    uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80
    
    # 4. Convert to hex string with standard hyphenation
    h = uuid_bytes.hex()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"
