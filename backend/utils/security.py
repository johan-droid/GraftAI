import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_encryption_key():
    """Derives a Fernet key from the SECRET_KEY environment variable."""
    secret_key = os.getenv("SECRET_KEY", "insecure-dev-fallback")
    salt = b'graftai-salt-v1' # Consistent salt for persistence
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key

def encrypt_token(token: str) -> str:
    """Encrypts a string using Fernet."""
    if not token:
        return ""
    f = Fernet(get_encryption_key())
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypts a Fernet-encrypted string."""
    if not encrypted_token:
        return ""
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_token.encode()).decode()
    except Exception:
        return ""
