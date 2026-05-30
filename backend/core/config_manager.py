"""
Centralized Configuration Management

Provides unified configuration management with:
- Environment variable loading and validation
- Configuration schema validation
- Secret management integration
- Environment-specific overrides
- Hot reload capabilities
"""
import hashlib
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class ConfigSource(Enum):
    """Configuration source types"""
    ENVIRONMENT = "environment"
    FILE = "file"
    SECRETS_MANAGER = "secrets_manager"
    DATABASE = "database"
    REMOTE = "remote"

@dataclass
class ConfigSchema:
    """Configuration schema definition"""
    key: str
    type: type
    required: bool = True
    default: Any = None
    validator: Callable[[Any], bool] | None = None
    description: str = ""
    sensitive: bool = False
    source: ConfigSource = ConfigSource.ENVIRONMENT
    reloadable: bool = False

@dataclass
class ConfigValidationResult:
    """Configuration validation result"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    missing_required: list[str]
    invalid_types: list[str]

class ConfigValidator(ABC):
    """Abstract configuration validator"""

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate configuration value"""

    @abstractmethod
    def get_error_message(self, value: Any) -> str:
        """Get validation error message"""

class URLValidator(ConfigValidator):
    """URL configuration validator"""

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        url_pattern = re.compile("^(https?|postgres|mysql|redis)://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[A-Z]{2,6}\\.?|localhost|\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})(?::\\d+)?(?:/?|[/?]\\S+)$", re.IGNORECASE)
        return bool(url_pattern.match(value))

    def get_error_message(self, value: Any) -> str:
        return f"Invalid URL format: {value}"

class SecretKeyValidator(ConfigValidator):
    """Secret key validator"""

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        if len(value) < 32:
            return False
        weak_keys = ["super-secret-college-project-key-change-in-prod", "your-secret-key-here", "change-me-in-production", "default-secret-key"]
        return value not in weak_keys

    def get_error_message(self, value: Any) -> str:
        return "Secret key must be at least 32 characters and not use default values"

class PositiveIntegerValidator(ConfigValidator):
    """Positive integer validator"""

    def __init__(self, min_value: int=1, max_value: int | None=None):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Any) -> bool:
        try:
            int_value = int(value)
            if int_value < self.min_value:
                return False
            return not (self.max_value and int_value > self.max_value)
        except (ValueError, TypeError):
            return False

    def get_error_message(self, value: Any) -> str:
        if self.max_value:
            return f"Value must be an integer between {self.min_value} and {self.max_value}"
        return f"Value must be an integer greater than or equal to {self.min_value}"

class EmailValidator(ConfigValidator):
    """Email address validator"""

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        email_pattern = re.compile("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
        return bool(email_pattern.match(value))

    def get_error_message(self, value: Any) -> str:
        return f"Invalid email format: {value}"

class ConfigManager:
    """Centralized configuration manager"""

    def __init__(self, env: Environment=Environment.DEVELOPMENT):
        self.env = env
        self.config_cache: dict[str, Any] = {}
        self.config_schemas: dict[str, ConfigSchema] = {}
        self.config_sources: dict[ConfigSource, Any] = {}
        self.validation_cache: dict[str, ConfigValidationResult] = {}
        self.reload_callbacks: list[Callable[[str, Any], None]] = []
        self._setup_default_schemas()
        self._load_config_sources()

    def _setup_default_schemas(self):
        """Setup default configuration schemas"""
        schemas = [ConfigSchema(key="DATABASE_URL", type=str, required=True, validator=URLValidator(), description="Primary database connection URL", sensitive=True, source=ConfigSource.ENVIRONMENT), ConfigSchema(key="DATABASE_READ_REPLICA_URLS", type=list, required=False, default=[], description="Read replica database URLs", sensitive=True, source=ConfigSource.ENVIRONMENT), ConfigSchema(key="DATABASE_POOL_SIZE", type=int, required=False, default=20, validator=PositiveIntegerValidator(1, 100), description="Database connection pool size", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="REDIS_URL", type=str, required=True, validator=URLValidator(), description="Redis connection URL", sensitive=True, source=ConfigSource.ENVIRONMENT), ConfigSchema(key="REDIS_POOL_SIZE", type=int, required=False, default=10, validator=PositiveIntegerValidator(1, 50), description="Redis connection pool size", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="SECRET_KEY", type=str, required=True, validator=SecretKeyValidator(), description="Application secret key", sensitive=True, source=ConfigSource.ENVIRONMENT), ConfigSchema(key="JWT_SECRET_KEY", type=str, required=True, validator=SecretKeyValidator(), description="JWT signing secret key", sensitive=True, source=ConfigSource.ENVIRONMENT), ConfigSchema(key="ENCRYPTION_KEY", type=str, required=False, description="Data encryption key", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="ENV", type=str, required=False, default=self.env.value, description="Application environment", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="DEBUG", type=bool, required=False, default=self.env == Environment.DEVELOPMENT, description="Debug mode", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="LOG_LEVEL", type=str, required=False, default="INFO", description="Logging level", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="API_RATE_LIMIT", type=int, required=False, default=100, validator=PositiveIntegerValidator(1, 1000), description="API rate limit per minute", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="API_TIMEOUT", type=int, required=False, default=30, validator=PositiveIntegerValidator(1, 300), description="API request timeout in seconds", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="GROQ_API_KEY", type=str, required=False, description="Groq API key", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="OPENAI_API_KEY", type=str, required=False, description="OpenAI API key", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="PINECONE_API_KEY", type=str, required=False, description="Pinecone API key", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="FRONTEND_URL", type=str, required=True, validator=URLValidator(), description="Frontend application URL", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="NEXT_PUBLIC_API_URL", type=str, required=True, validator=URLValidator(), description="Public API URL", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="STRIPE_SECRET_KEY", type=str, required=False, description="Stripe secret key", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="RAZORPAY_KEY_ID", type=str, required=False, description="Razorpay key ID", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="RAZORPAY_KEY_SECRET", type=str, required=False, description="Razorpay key secret", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="SENTRY_DSN", type=str, required=False, description="Sentry DSN", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="PROMETHEUS_PORT", type=int, required=False, default=9090, validator=PositiveIntegerValidator(1024, 65535), description="Prometheus metrics port", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="SMTP_HOST", type=str, required=False, description="SMTP server host", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="SMTP_PORT", type=int, required=False, default=587, validator=PositiveIntegerValidator(1, 65535), description="SMTP server port", source=ConfigSource.ENVIRONMENT), ConfigSchema(key="SMTP_USERNAME", type=str, required=False, description="SMTP username", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="SMTP_PASSWORD", type=str, required=False, description="SMTP password", sensitive=True, source=ConfigSource.SECRETS_MANAGER), ConfigSchema(key="FROM_EMAIL", type=str, required=False, validator=EmailValidator(), description="From email address", source=ConfigSource.ENVIRONMENT)]
        for schema in schemas:
            self.config_schemas[schema.key] = schema

    def _load_config_sources(self):
        """Load configuration sources"""
        self.config_sources[ConfigSource.ENVIRONMENT] = os.environ
        self.config_sources[ConfigSource.FILE] = {}
        self.config_sources[ConfigSource.SECRETS_MANAGER] = {}
        self.config_sources[ConfigSource.DATABASE] = {}
        self.config_sources[ConfigSource.REMOTE] = {}

    def get(self, key: str, default: Any=None) -> Any:
        """Get configuration value with caching and validation"""
        if key in self.config_cache:
            return self.config_cache[key]
        schema = self.config_schemas.get(key)
        if not schema:
            value = os.getenv(key, default)
            self.config_cache[key] = value
            return value
        value = self._load_from_sources(key, schema)
        if value is None:
            value = schema.default
        if value is not None and schema.validator:
            if not schema.validator.validate(value):
                error_msg = schema.validator.get_error_message(value)
                logger.error("Configuration validation failed for %s: %s", key, error_msg)
                if schema.required:
                    msg = f"Required configuration {key} is invalid: {error_msg}"
                    raise ValueError(msg)
                value = schema.default
        self.config_cache[key] = value
        return value

    def _load_from_sources(self, key: str, schema: ConfigSchema) -> Any:
        """Load configuration from sources in precedence order"""
        sources_order = [ConfigSource.ENVIRONMENT, ConfigSource.FILE, ConfigSource.SECRETS_MANAGER, ConfigSource.DATABASE, ConfigSource.REMOTE]
        for source in sources_order:
            value = self._load_from_source(source, key)
            if value is not None:
                return value
        return None

    def _load_from_source(self, source: ConfigSource, key: str) -> Any:
        """Load configuration from specific source"""
        if source == ConfigSource.ENVIRONMENT:
            return self._load_from_environment(key)
        if source == ConfigSource.FILE:
            return self._load_from_file(key)
        if source == ConfigSource.SECRETS_MANAGER:
            return self._load_from_secrets_manager(key)
        if source == ConfigSource.DATABASE:
            return self._load_from_database(key)
        if source == ConfigSource.REMOTE:
            return self._load_from_remote(key)
        return None

    def _load_from_environment(self, key: str) -> Any:
        """Load from environment variables"""
        return os.getenv(key)

    def _load_from_file(self, key: str) -> Any:
        """Load from configuration files"""
        config_files = [f".env.{self.env.value}", f".env.{self.env.value}.local", "config.yaml", "config.json", f"config.{self.env.value}.yaml", f"config.{self.env.value}.json"]
        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    if config_file.endswith((".yaml", ".yml")):
                        with open(config_file) as f:
                            config_data = yaml.safe_load(f)
                    else:
                        with open(config_file) as f:
                            config_data = json.load(f)
                    if key in config_data:
                        return config_data[key]
                except Exception as e:
                    logger.exception("Error loading config file %s: %s", config_file, e)
        return None

    def _load_from_secrets_manager(self, key: str) -> Any:
        """Load from secrets manager"""
        return None

    def _load_from_database(self, key: str) -> Any:
        """Load from database configuration"""
        return None

    def _load_from_remote(self, key: str) -> Any:
        """Load from remote configuration service"""
        return None

    def set(self, key: str, value: Any, persist: bool=False):
        """Set configuration value"""
        schema = self.config_schemas.get(key)
        if schema and schema.validator and (not schema.validator.validate(value)):
            error_msg = schema.validator.get_error_message(value)
            msg = f"Invalid value for {key}: {error_msg}"
            raise ValueError(msg)
        self.config_cache.get(key)
        self.config_cache[key] = value
        if persist:
            self._persist_value(key, value, schema)
        for callback in self.reload_callbacks:
            try:
                callback(key, value)
            except Exception as e:
                logger.exception("Error in config reload callback: %s", e)
        logger.info("Configuration updated: %s = %s", key, "[REDACTED]" if schema and schema.sensitive else value)

    def _persist_value(self, key: str, value: Any, schema: ConfigSchema | None):
        """Persist configuration value"""
        if not schema:
            return
        if schema.source == ConfigSource.ENVIRONMENT:
            os.environ[key] = str(value)

    def validate_all(self) -> ConfigValidationResult:
        """Validate all configuration"""
        errors = []
        warnings = []
        missing_required = []
        invalid_types = []
        for key, schema in self.config_schemas.items():
            try:
                value = self.get(key)
                if schema.required and value is None:
                    missing_required.append(key)
                    continue
                if value is not None and (not isinstance(value, schema.type)):
                    invalid_types.append(f"{key}: expected {schema.type.__name__}, got {type(value).__name__}")
                    continue
                if value is not None and schema.validator:
                    if not schema.validator.validate(value):
                        errors.append(f"{key}: {schema.validator.get_error_message(value)}")
                        continue
            except Exception as e:
                errors.append(f"{key}: {e!s}")
        is_valid = len(errors) == 0 and len(missing_required) == 0 and (len(invalid_types) == 0)
        result = ConfigValidationResult(is_valid=is_valid, errors=errors, warnings=warnings, missing_required=missing_required, invalid_types=invalid_types)
        cache_key = f"validation_{hashlib.md5(json.dumps([s.key for s in self.config_schemas.values()]).encode()).hexdigest()}"
        self.validation_cache[cache_key] = result
        return result

    def get_sensitive_config(self) -> dict[str, Any]:
        """Get sensitive configuration (for debugging, use with caution)"""
        sensitive_config = {}
        for key, schema in self.config_schemas.items():
            if schema.sensitive:
                value = self.get(key)
                if value:
                    if len(str(value)) > 8:
                        masked = f"{str(value)[:4]}...{str(value)[-4:]}"
                    else:
                        masked = "***"
                    sensitive_config[key] = masked
        return sensitive_config

    def get_environment_config(self) -> dict[str, Any]:
        """Get environment-specific configuration"""
        env_config = {}
        for key, schema in self.config_schemas.items():
            value = self.get(key)
            if value is not None:
                if schema.sensitive:
                    env_config[key] = "[REDACTED]"
                else:
                    env_config[key] = value
        return env_config

    def add_reload_callback(self, callback: Callable[[str, Any], None]):
        """Add callback for configuration reloads"""
        self.reload_callbacks.append(callback)

    def remove_reload_callback(self, callback: Callable[[str, Any], None]):
        """Remove reload callback"""
        if callback in self.reload_callbacks:
            self.reload_callbacks.remove(callback)

    def reload_config(self, keys: list[str] | None=None):
        """Reload configuration from sources"""
        if keys is None:
            keys = list(self.config_schemas.keys())
        for key in keys:
            if key in self.config_cache:
                del self.config_cache[key]
        logger.info("Reloaded configuration for %s keys", len(keys))

    def get_config_hash(self) -> str:
        """Get hash of current configuration for change detection"""
        config_data = {}
        for key in sorted(self.config_schemas.keys()):
            value = self.get(key)
            if value is not None:
                if self.config_schemas[key].sensitive:
                    config_data[key] = "[REDACTED]"
                else:
                    config_data[key] = str(value)
        return hashlib.sha256(json.dumps(config_data, sort_keys=True).encode()).hexdigest()

    async def watch_for_changes(self):
        """Watch for configuration changes (placeholder)"""
config_manager = ConfigManager()

def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    return config_manager

def get_config(key: str, default: Any=None) -> Any:
    """Get configuration value"""
    return config_manager.get(key, default)

def get_database_url() -> str:
    """Get database URL"""
    return config_manager.get("DATABASE_URL")

def get_redis_url() -> str:
    """Get Redis URL"""
    return config_manager.get("REDIS_URL")

def get_secret_key() -> str:
    """Get application secret key"""
    return config_manager.get("SECRET_KEY")

def is_production() -> bool:
    """Check if running in production"""
    return config_manager.get("ENV") == Environment.PRODUCTION.value

def is_debug() -> bool:
    """Check if debug mode is enabled"""
    return config_manager.get("DEBUG", False)

def validate_config_before_start(func):
    """Decorator to validate configuration before starting"""

    def wrapper(*args, **kwargs):
        validation_result = config_manager.validate_all()
        if not validation_result.is_valid:
            error_messages = []
            if validation_result.missing_required:
                error_messages.append(f"Missing required configuration: {', '.join(validation_result.missing_required)}")
            if validation_result.invalid_types:
                error_messages.append(f"Invalid types: {', '.join(validation_result.invalid_types)}")
            if validation_result.errors:
                error_messages.append(f"Validation errors: {', '.join(validation_result.errors)}")
            raise RuntimeError("Configuration validation failed:\n" + "\n".join(error_messages))
        return func(*args, **kwargs)
    return wrapper

def initialize_config():
    """Initialize configuration manager"""
    env_name = os.getenv("ENV", "development").lower()
    try:
        env = Environment(env_name)
    except ValueError:
        logger.warning("Invalid environment %s, defaulting to development", env_name)
        env = Environment.DEVELOPMENT
    global config_manager
    config_manager = ConfigManager(env)
    validation_result = config_manager.validate_all()
    if not validation_result.is_valid:
        logger.error("Configuration validation failed:")
        for error in validation_result.errors:
            logger.error("  - %s", error)
        for missing in validation_result.missing_required:
            logger.error("  - Missing required: %s", missing)
        for invalid in validation_result.invalid_types:
            logger.error("  - Invalid type: %s", invalid)
    logger.info("Configuration initialized for %s environment", env.value)
    return config_manager
