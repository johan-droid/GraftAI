"""
Secure configuration management for GraftAI backend.
Provides encrypted storage and validation for sensitive configuration.
"""
import base64
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class ConfigType(Enum):
    """Configuration value types."""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    JSON = "json"
    ENCRYPTED = "encrypted"

@dataclass
class ConfigField:
    """Configuration field definition."""
    key: str
    config_type: ConfigType
    required: bool = True
    default: Any | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    description: str | None = None
    is_secret: bool = False

class SecureConfig:
    """Secure configuration manager with encryption support."""

    def __init__(self, encryption_key: str | None=None):
        self.encryption_key = encryption_key
        self.cipher_suite: Fernet | None = None
        self.config_cache: dict[str, Any] = {}
        if encryption_key:
            try:
                kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"graftai_secure_config_salt", iterations=100000)
                key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
                self.cipher_suite = Fernet(key)
            except Exception as e:
                logger.exception("Failed to initialize encryption: %s", e)
                self.cipher_suite = None
        self.config_schema = {"DATABASE_URL": ConfigField(key="DATABASE_URL", config_type=ConfigType.ENCRYPTED, required=True, description="PostgreSQL connection string"), "REDIS_URL": ConfigField(key="REDIS_URL", config_type=ConfigType.STRING, required=True, default="redis://localhost:6379/0", description="Redis connection URL"), "SECRET_KEY": ConfigField(key="SECRET_KEY", config_type=ConfigType.ENCRYPTED, required=True, min_length=32, description="JWT secret key"), "JWT_SECRET": ConfigField(key="JWT_SECRET", config_type=ConfigType.ENCRYPTED, required=True, min_length=32, description="JWT signing secret"), "NEXTAUTH_SECRET": ConfigField(key="NEXTAUTH_SECRET", config_type=ConfigType.ENCRYPTED, required=True, min_length=32, description="NextAuth secret"), "GOOGLE_CLIENT_ID": ConfigField(key="GOOGLE_CLIENT_ID", config_type=ConfigType.ENCRYPTED, required=False, description="Google OAuth client ID"), "GOOGLE_CLIENT_SECRET": ConfigField(key="GOOGLE_CLIENT_SECRET", config_type=ConfigType.ENCRYPTED, required=False, description="Google OAuth client secret"), "MICROSOFT_CLIENT_ID": ConfigField(key="MICROSOFT_CLIENT_ID", config_type=ConfigType.ENCRYPTED, required=False, description="Microsoft OAuth client ID"), "MICROSOFT_CLIENT_SECRET": ConfigField(key="MICROSOFT_CLIENT_SECRET", config_type=ConfigType.ENCRYPTED, required=False, description="Microsoft OAuth client secret"), "OPENAI_API_KEY": ConfigField(key="OPENAI_API_KEY", config_type=ConfigType.ENCRYPTED, required=False, description="OpenAI API key"), "GROQ_API_KEY": ConfigField(key="GROQ_API_KEY", config_type=ConfigType.ENCRYPTED, required=False, description="Groq API key"), "PINECONE_API_KEY": ConfigField(key="PINECONE_API_KEY", config_type=ConfigType.ENCRYPTED, required=False, description="Pinecone API key"), "STRIPE_SECRET_KEY": ConfigField(key="STRIPE_SECRET_KEY", config_type=ConfigType.ENCRYPTED, required=False, description="Stripe secret key"), "STRIPE_WEBHOOK_SECRET": ConfigField(key="STRIPE_WEBHOOK_SECRET", config_type=ConfigType.ENCRYPTED, required=False, description="Stripe webhook secret"), "RAZORPAY_KEY_ID": ConfigField(key="RAZORPAY_KEY_ID", config_type=ConfigType.ENCRYPTED, required=False, description="Razorpay key ID"), "RAZORPAY_KEY_SECRET": ConfigField(key="RAZORPAY_KEY_SECRET", config_type=ConfigType.ENCRYPTED, required=False, description="Razorpay key secret"), "RESEND_API_KEY": ConfigField(key="RESEND_API_KEY", config_type=ConfigType.ENCRYPTED, required=False, description="Resend API key"), "SMTP_PASSWORD": ConfigField(key="SMTP_PASSWORD", config_type=ConfigType.ENCRYPTED, required=False, description="SMTP password"), "SENTRY_DSN": ConfigField(key="SENTRY_DSN", config_type=ConfigType.ENCRYPTED, required=False, description="Sentry DSN"), "ENV": ConfigField(key="ENV", config_type=ConfigType.STRING, required=True, default="development", pattern="^(development|staging|production)$", description="Environment"), "DEBUG": ConfigField(key="DEBUG", config_type=ConfigType.BOOLEAN, required=True, default=False, description="Debug mode"), "PORT": ConfigField(key="PORT", config_type=ConfigType.INTEGER, required=True, default=8000, description="Server port"), "BACKEND_URL": ConfigField(key="BACKEND_URL", config_type=ConfigType.STRING, required=True, default="http://localhost:8000", description="Backend URL"), "FRONTEND_URL": ConfigField(key="FRONTEND_URL", config_type=ConfigType.STRING, required=True, default="http://localhost:3000", description="Frontend URL")}

    def encrypt_value(self, value: str) -> str:
        """
        Encrypt a configuration value.

        Args:
            value: Value to encrypt

        Returns:
            str: Encrypted value (base64 encoded)
        """
        if not self.cipher_suite:
            msg = "Encryption not initialized"
            raise ValueError(msg)
        try:
            encrypted = self.cipher_suite.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.exception("Failed to encrypt value: %s", e)
            raise

    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypt a configuration value.

        Args:
            encrypted_value: Encrypted value (base64 encoded)

        Returns:
            str: Decrypted value
        """
        if not self.cipher_suite:
            msg = "Encryption not initialized"
            raise ValueError(msg)
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.exception("Failed to decrypt value: %s", e)
            raise

    def get_config_value(self, key: str, use_cache: bool=True) -> Any:
        """
        Get configuration value with validation and decryption.

        Args:
            key: Configuration key
            use_cache: Whether to use cached value

        Returns:
            Any: Configuration value

        Raises:
            ValueError: If configuration is invalid or missing
        """
        if use_cache and key in self.config_cache:
            return self.config_cache[key]
        if key not in self.config_schema:
            logger.warning("Unknown configuration key: %s", key)
            return os.getenv(key)
        field = self.config_schema[key]
        raw_value = os.getenv(key)
        if raw_value is None:
            if field.required and field.default is None:
                msg = f"Required configuration missing: {key}"
                raise ValueError(msg)
            raw_value = field.default
        if raw_value is None:
            return None
        if field.config_type == ConfigType.ENCRYPTED:
            try:
                if self.cipher_suite:
                    try:
                        base64.urlsafe_b64decode(raw_value.encode())
                        decrypted_value = self.decrypt_value(raw_value)
                    except Exception:
                        decrypted_value = raw_value
                    raw_value = decrypted_value
                else:
                    logger.warning("Encryption not available for secret: %s", key)
            except Exception as e:
                logger.exception("Failed to decrypt %s: %s", key, e)
                if field.required:
                    msg = f"Failed to decrypt required configuration: {key}"
                    raise ValueError(msg)
                return None
        validated_value = self._validate_and_convert(raw_value, field)
        if use_cache:
            self.config_cache[key] = validated_value
        return validated_value

    def _validate_and_convert(self, value: str, field: ConfigField) -> Any:
        """
        Validate and convert configuration value.

        Args:
            value: Raw value
            field: Configuration field definition

        Returns:
            Any: Validated and converted value

        Raises:
            ValueError: If validation fails
        """
        if field.config_type == ConfigType.BOOLEAN:
            if value.lower() in ("true", "1", "yes", "on"):
                return True
            if value.lower() in ("false", "0", "no", "off"):
                return False
            msg = f"Invalid boolean value for {field.key}: {value}"
            raise ValueError(msg)
        if field.config_type == ConfigType.INTEGER:
            try:
                int_value = int(value)
                if field.min_length is not None and int_value < field.min_length:
                    msg = f"Value for {field.key} is below minimum: {int_value} < {field.min_length}"
                    raise ValueError(msg)
                if field.max_length is not None and int_value > field.max_length:
                    msg = f"Value for {field.key} is above maximum: {int_value} > {field.max_length}"
                    raise ValueError(msg)
                return int_value
            except ValueError:
                msg = f"Invalid integer value for {field.key}: {value}"
                raise ValueError(msg)
        elif field.config_type == ConfigType.FLOAT:
            try:
                return float(value)
            except ValueError:
                msg = f"Invalid float value for {field.key}: {value}"
                raise ValueError(msg)
        elif field.config_type == ConfigType.JSON:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                msg = f"Invalid JSON value for {field.key}: {value}"
                raise ValueError(msg)
        else:
            if field.min_length is not None and len(value) < field.min_length:
                msg = f"Value for {field.key} is too short: {len(value)} < {field.min_length}"
                raise ValueError(msg)
            if field.max_length is not None and len(value) > field.max_length:
                msg = f"Value for {field.key} is too long: {len(value)} > {field.max_length}"
                raise ValueError(msg)
            if field.pattern:
                import re
                if not re.match(field.pattern, value):
                    msg = f"Value for {field.key} does not match pattern: {value}"
                    raise ValueError(msg)
            return value

    def set_config_value(self, key: str, value: Any, encrypt: bool=False) -> None:
        """
        Set configuration value with optional encryption.

        Args:
            key: Configuration key
            value: Value to set
            encrypt: Whether to encrypt the value
        """
        if key not in self.config_schema:
            logger.warning("Unknown configuration key: %s", key)
        str_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        if encrypt and self.cipher_suite:
            str_value = self.encrypt_value(str_value)
        os.environ[key] = str_value
        self.config_cache[key] = value

    def validate_all_config(self) -> dict[str, Any]:
        """
        Validate all required configuration.

        Returns:
            Dict containing validation results

        Raises:
            ValueError: If critical configuration is missing
        """
        results = {"valid": True, "errors": [], "warnings": [], "missing_secrets": [], "configured": []}
        for key, field in self.config_schema.items():
            try:
                value = self.get_config_value(key, use_cache=False)
                if value is not None:
                    results["configured"].append(key)
                    if field.is_secret and value in ["change-me-in-production", "your-secret-key", "REPLACE_ME", "dev-fallback-secret"]:
                        results["missing_secrets"].append(key)
                        results["warnings"].append(f"Using default secret for {key}")
            except ValueError as e:
                if field.required:
                    results["valid"] = False
                    results["errors"].append(str(e))
                else:
                    results["warnings"].append(f"Optional config missing: {key}")
        return results

    def get_security_report(self) -> dict[str, Any]:
        """
        Generate security configuration report.

        Returns:
            Dict containing security assessment
        """
        validation_results = self.validate_all_config()
        security_issues = []
        weak_patterns = ["test", "dev", "default", "example", "sample", "demo", "123", "abc", "password", "secret", "key"]
        for key in self.config_schema:
            if self.config_schema[key].is_secret:
                try:
                    value = self.get_config_value(key, use_cache=False)
                    if value:
                        for pattern in weak_patterns:
                            if pattern.lower() in str(value).lower():
                                security_issues.append(f"Weak pattern detected in {key}")
                                break
                except ValueError:
                    pass
        return {"validation": validation_results, "security_issues": security_issues, "encryption_enabled": self.cipher_suite is not None, "total_configs": len(self.config_schema), "required_configs": len([f for f in self.config_schema.values() if f.required]), "secret_configs": len([f for f in self.config_schema.values() if f.is_secret])}
_secure_config: SecureConfig | None = None

def get_secure_config(encryption_key: str | None=None) -> SecureConfig:
    """Get or create global secure config instance."""
    global _secure_config
    if _secure_config is None:
        if not encryption_key:
            encryption_key = os.getenv("CONFIG_ENCRYPTION_KEY")
        _secure_config = SecureConfig(encryption_key)
    return _secure_config

def reset_secure_config():
    """Reset global secure config instance (primarily for testing)."""
    global _secure_config
    _secure_config = None
