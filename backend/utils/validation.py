"""
Input validation and sanitization utilities for GraftAI backend.
Provides comprehensive validation for common input types and patterns.
"""
import html
import logging
import re
from typing import Any, ClassVar

from fastapi import HTTPException, status
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Security-focused input validation and sanitization."""
    SQL_INJECTION_PATTERNS: ClassVar[list[str]] = ["(\\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\\b)", "(\\b(OR|AND)\\b\\s+\\d+\\s*=\\s*\\d+)", '(\\b(OR|AND)\\b\\s+[\'\\"]?\\w+[\'\\"]?\\s*=\\s*[\'\\"]?\\w+[\'\\"]?)', "(--|#|\\/\\*|\\*\\/)", "(\\b(LOAD_FILE|INTO\\s+OUTFILE|INTO\\s+DUMPFILE)\\b)", "(\\b(WAITFOR|DELAY|BENCHMARK)\\b)"]
    XSS_PATTERNS: ClassVar[list[str]] = ["<script[^>]*>.*?</script>", "javascript:", "on\\w+\\s*=", "<iframe[^>]*>", "<object[^>]*>", "<embed[^>]*>", "<link[^>]*>", "<meta[^>]*>", "expression\\s*\\(", "@import", "vbscript:"]
    PATH_TRAVERSAL_PATTERNS: ClassVar[list[str]] = ["\\.\\.[/\\\\]", "%2e%2e[/\\\\]", "\\.\\.%2f", "\\.\\.%5c", "/etc/passwd", "/etc/shadow", "/proc/", "/sys/"]
    COMMAND_INJECTION_PATTERNS: ClassVar[list[str]] = ["[;&|`$(){}[\\]]", "\\b(curl|wget|nc|netcat|telnet|ssh|ftp)\\b", "\\b(rm|mv|cp|cat|ls|ps|kill|chmod|chown)\\b", "\\b(python|perl|ruby|bash|sh|cmd|powershell)\\b"]
    JAVASCRIPT_PATTERNS: ClassVar[list[str]] = ["javascript:", "vbscript:", "data:", "expression\\s*\\("]

    @classmethod
    def sanitize_string(cls, input_str: str, max_length: int=1000) -> str:
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
        sanitized = html.escape(input_str)
        sanitized = sanitized.replace("\x00", "")
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
        email_pattern = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            return False
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
        clean_phone = re.sub("[+()\\s-]", "", phone)
        return bool(re.match("^\\d{10,15}$", clean_phone))

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
        url_pattern = "^https?:\\/\\/[^\\s/$.?#].[^\\s]*$"
        if not re.match(url_pattern, url):
            return False
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
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return False
        safe_pattern = "^[a-zA-Z0-9._/-]+$"
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
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                return False
        return True

    @classmethod
    def sanitize_html(cls, html_content: str, allowed_tags: list[str] | None=None) -> str:
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
        tag_pattern = "<(?!\\/?(" + "|".join(allowed_tags) + ")\x08)[^>]*>"
        sanitized = re.sub(tag_pattern, "", html_content, flags=re.IGNORECASE)
        attr_pattern = "\\s*(on\\w+|javascript:|vbscript:|data:)[^>]*"
        return re.sub(attr_pattern, "", sanitized, flags=re.IGNORECASE)

class SecureBaseModel(BaseModel):
    """Base model with security validation."""

    @validator("*", pre=True)
    def sanitize_strings(self, v):
        """Sanitize all string inputs."""
        if isinstance(v, str):
            return SecurityValidator.sanitize_string(v)
        return v

    @validator("*", pre=True)
    def validate_sql_injection(self, v):
        """Validate against SQL injection."""
        if isinstance(v, str) and (not SecurityValidator.validate_sql_input(v)):
            msg = "Input contains potentially dangerous SQL patterns"
            raise ValueError(msg)
        return v

class UserInputSchema(SecureBaseModel):
    """Schema for user input validation."""
    email: str | None = None
    name: str | None = None
    phone: str | None = None
    message: str | None = None

    @validator("email")
    def validate_email_field(self, v):
        err_msg = "Invalid email format"
        if v and (not SecurityValidator.validate_email(v)):
            raise ValueError(err_msg)
        return v

    @validator("phone")
    def validate_phone_field(self, v):
        err_msg = "Invalid phone number format"
        if v and (not SecurityValidator.validate_phone(v)):
            raise ValueError(err_msg)
        return v

    @validator("name", "message")
    def validate_length(self, v):
        err_msg = "Input too long"
        if v and len(v) > 1000:
            raise ValueError(err_msg)
        return v

def validate_and_sanitize_input(input_data: str | dict | list, schema_class: type | None=None) -> Any:
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
            return {SecurityValidator.sanitize_string(str(k)): SecurityValidator.sanitize_string(str(v)) for k, v in input_data.items()}
        if isinstance(input_data, list):
            return [SecurityValidator.sanitize_string(str(item)) for item in input_data]
        return input_data
    except Exception as e:
        logger.exception("Input validation failed: %s", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data") from e
