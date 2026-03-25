import bleach
import logging
from typing import Any, Dict, List, Union

# Initialize logger
logger = logging.getLogger(__name__)

# Allowed tags and attributes for sanitization (minimal set for basics)
ALLOWED_TAGS = ["p", "br", "strong", "em", "u", "ul", "ol", "li"]
ALLOWED_ATTRS = {}


def sanitize_text(text: str) -> str:
    """
    Sanitize a string to prevent XSS by stripping/escaping dangerous HTML tags.
    """
    if not text or not isinstance(text, str):
        return text

    try:
        return bleach.clean(
            text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True
        )
    except Exception as e:
        logger.error(f"Sanitization failed: {e}")
        # Fallback to absolute minimum if bleach fails
        return text.replace("<", "&lt;").replace(">", "&gt;")


def sanitize_recursive(data: Any) -> Any:
    """
    Recursively sanitize strings in dictionaries and lists.
    """
    if isinstance(data, str):
        return sanitize_text(data)
    elif isinstance(data, dict):
        return {k: sanitize_recursive(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_recursive(item) for item in data]
    return data
