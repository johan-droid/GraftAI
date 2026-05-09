"""
Input validation and sanitization utilities for GraftAI backend.
Provides comprehensive validation for common input types and patterns.
"""

import html
import logging
import re
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Security-focused input validation and sanitization."""

    # Common attack patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(--|#|\/\*|\*\/)",
        r"(\b(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b)",
        r"(\b(WAITFOR|DELAY|BENCHMARK)\b)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"expression\s*\(",
        r"@import",
        r"vbscript:",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.[/\\]",
        r"%2e%2e[/\\]",
        r"\.\.%2f",
        r"\.\.%5c",
        r"/etc/passwd",
        r"/etc/shadow",
        r"/proc/",
        r"/sys/",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]]",
        r"\b(curl|wget|nc|netcat|telnet|ssh|ftp)\b",
        r"\b(rm|mv|cp|cat|ls|ps|kill|chmod|chown)\b",
        r"\b(python|perl|ruby|bash|sh|cmd|powershell)\b",
    ]

    @classmethod
    def sanitize_string(cls, input_str: str, max_length: int = 1000) -> str:
        """
        Sanitize string input by removing dangerous characters and limiting length.
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            str: Sanitized string
        """
        if not input_str:
            return ""

        # HTML escape
        sanitized = html.escape(input_str)

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Limit length
        sanitized = sanitized[:max_length]

        return sanitized.strip()

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Validate email format with additional security checks.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not email or len(email) > 254:
            return False

        # Basic email regex (simplified for security)
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, email):
            return False

        # Check for dangerous patterns
        dangerous_patterns = cls.SQL_INJECTION_PATTERNS + cls.XSS_PATTERNS
        for pattern in dangerous_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return False

        return True

    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not phone:
            return False

        # Remove common formatting characters
        clean_phone = re.sub(r"[+()\s-]", "", phone)

        # Check if it's all digits and reasonable length
        return bool(re.match(r"^\d{10,15}$", clean_phone))

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """
        Validate URL format and check for dangerous patterns.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not url or len(url) > 2048:
            return False

        # Basic URL pattern
        url_pattern = r"^https?:\/\/[^\s/$.?#].[^\s]*$"

        if not re.match(url_pattern, url):
            return False

        # Check for dangerous patterns
        dangerous_patterns = cls.XSS_PATTERNS + cls.JAVASCRIPT_PATTERNS
        for pattern in dangerous_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False

        return True

    @classmethod
    def validate_file_path(cls, file_path: str) -> bool:
        """
        Validate file path to prevent path traversal attacks.
        
        Args:
            file_path: File path to validate
            
        Returns:
            bool: True if safe, False otherwise
        """
        if not file_path:
            return False

        # Check for path traversal patterns
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return False

        # Only allow specific safe characters
        safe_pattern = r"^[a-zA-Z0-9._/-]+$"
        return bool(re.match(safe_pattern, file_path))

    @classmethod
    def validate_sql_input(cls, input_str: str) -> bool:
        """
        Validate input to prevent SQL injection.
        
        Args:
            input_str: Input string to validate
            
        Returns:
            bool: True if safe, False otherwise
        """
        if not input_str:
            return True

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                return False

        return True

    @classmethod
    def validate_command_input(cls, input_str: str) -> bool:
        """
        Validate input to prevent command injection.
        
        Args:
            input_str: Input string to validate
            
        Returns:
            bool: True if safe, False otherwise
        """
        if not input_str:
            return True

        # Check for command injection patterns
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                return False

        return True

    @classmethod
    def sanitize_html(cls, html_content: str, allowed_tags: list[str] | None = None) -> str:
        """
        Basic HTML sanitization (simplified - consider using bleach library for production).
        
        Args:
            html_content: HTML content to sanitize
            allowed_tags: List of allowed HTML tags
            
        Returns:
            str: Sanitized HTML
        """
        if not html_content:
            return ""

        allowed_tags = allowed_tags or ["p", "br", "strong", "em", "ul", "ol", "li"]

        # Remove all HTML tags except allowed ones
        tag_pattern = r"<(?!\/?(" + "|".join(allowed_tags) + ")\b)[^>]*>"
        sanitized = re.sub(tag_pattern, "", html_content, flags=re.IGNORECASE)

        # Remove dangerous attributes
        attr_pattern = r"\s*(on\w+|javascript:|vbscript:|data:)[^>]*"
        sanitized = re.sub(attr_pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized


class SecureBaseModel(BaseModel):
    """Base model with security validation."""

    @validator("*", pre=True)
    def sanitize_strings(cls, v):
        """Sanitize all string inputs."""
        if isinstance(v, str):
            return SecurityValidator.sanitize_string(v)
        return v

    @validator("*", pre=True)
    def validate_sql_injection(cls, v):
        """Validate against SQL injection."""
        if isinstance(v, str) and not SecurityValidator.validate_sql_input(v):
            raise ValueError("Input contains potentially dangerous SQL patterns")
        return v


class UserInputSchema(SecureBaseModel):
    """Schema for user input validation."""

    email: str | None = None
    name: str | None = None
    phone: str | None = None
    message: str | None = None

    @validator("email")
    def validate_email_field(cls, v):
        err_msg = "Invalid email format"
        if v and not SecurityValidator.validate_email(v):
            raise ValueError(err_msg)
        return v

    @validator("phone")
    def validate_phone_field(cls, v):
        err_msg = "Invalid phone number format"
        if v and not SecurityValidator.validate_phone(v):
            raise ValueError(err_msg)
        return v

    @validator("name", "message")
    def validate_length(cls, v):
        err_msg = "Input too long"
        if v and len(v) > 1000:
            raise ValueError(err_msg)
        return v


def validate_and_sanitize_input(input_data: str | dict | list, schema_class: type | None = None) -> Any:
    """
    Validate and sanitize input data.
    
    Args:
        input_data: Input data to validate
        schema_class: Pydantic schema class for validation
        
    Returns:
        Any: Validated and sanitized data
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        if schema_class:
            if isinstance(input_data, dict):
                return schema_class(**input_data)
            return schema_class.parse_obj(input_data)

        if isinstance(input_data, str):
            return SecurityValidator.sanitize_string(input_data)
        if isinstance(input_data, dict):
            return {
                SecurityValidator.sanitize_string(str(k)):
                SecurityValidator.sanitize_string(str(v))
                for k, v in input_data.items()
            }
        if isinstance(input_data, list):
            return [SecurityValidator.sanitize_string(str(item)) for item in input_data]
        return input_data
    except Exception as e:
        logger.exception("Input validation failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data"
        ) from e


# Add missing patterns that were referenced
SecurityValidator.JAVASCRIPT_PATTERNS = [
    r"javascript:",
    r"vbscript:",
    r"data:",
    r"expression\s*\(",
]
