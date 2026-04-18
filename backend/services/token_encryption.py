import base64
import hashlib
import logging
import os
from functools import lru_cache
from typing import Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_TOKEN_PREFIX = "enc:v1:"


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _get_fernet() -> Optional[Fernet]:
    # Prefer a dedicated key and fall back to SECRET_KEY for compatibility.
    secret = (
        os.getenv("OAUTH_TOKEN_ENCRYPTION_KEY")
        or os.getenv("TOKEN_ENCRYPTION_KEY")
        or os.getenv("SECRET_KEY")
    )

    if not secret:
        return None

    try:
        return Fernet(_derive_fernet_key(secret))
    except Exception as exc:
        logger.error("Failed to initialize OAuth token encryption: %s", exc)
        return None


def token_encryption_enabled() -> bool:
    return _get_fernet() is not None


def is_encrypted_token(value: Optional[str]) -> bool:
    return bool(value and value.startswith(_TOKEN_PREFIX))


def encrypt_token_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    if is_encrypted_token(value):
        return value

    fernet = _get_fernet()
    if not fernet:
        return value

    encrypted = fernet.encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{_TOKEN_PREFIX}{encrypted}"


def decrypt_token_value(value: Optional[str]) -> Tuple[Optional[str], bool]:
    """
    Returns (plaintext_value, needs_upgrade).

    - `needs_upgrade=True` means the token is plaintext while encryption is enabled
      and should be re-saved in encrypted form.
    """
    if not value:
        return value, False

    if not is_encrypted_token(value):
        return value, token_encryption_enabled()

    fernet = _get_fernet()
    if not fernet:
        logger.error("Encrypted token found but no encryption key is available")
        return None, False

    try:
        ciphertext = value[len(_TOKEN_PREFIX) :]
        plaintext = fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        return plaintext, False
    except InvalidToken:
        logger.error("Failed to decrypt OAuth token: invalid ciphertext")
    except Exception as exc:
        logger.error("Failed to decrypt OAuth token: %s", exc)

    return None, False
