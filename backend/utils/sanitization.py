import logging
from typing import Any

import bleach

logger = logging.getLogger(__name__)
ALLOWED_TAGS = ["p", "br", "strong", "em", "u", "ul", "ol", "li"]
ALLOWED_ATTRS = {}

def sanitize_text(text: str) -> str:
    """
    Sanitize a string to prevent XSS by stripping/escaping dangerous HTML tags.
    """
    if not text or not isinstance(text, str):
        return text
    try:
        return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    except Exception as e:
        logger.exception("Sanitization failed: %s", e)
        return text.replace("<", "&lt;").replace(">", "&gt;")

def sanitize_recursive(data: Any) -> Any:
    """
    Recursively sanitize strings in dictionaries and lists.
    """
    if isinstance(data, str):
        return sanitize_text(data)
    if isinstance(data, dict):
        return {k: sanitize_recursive(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize_recursive(item) for item in data]
    return data
