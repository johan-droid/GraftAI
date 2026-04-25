import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.getenv("LOG_DIR", "logs")
SERVICE_NAME = os.getenv("SERVICE_NAME", "graftai-backend")
IS_PRODUCTION = (
    os.getenv("NODE_ENV") == "production" or os.getenv("PYTHON_ENV") == "production"
)


class JsonFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        # Sensitive fields to mask in logs
        self.sensitive_fields = {
            "password",
            "token",
            "authorization",
            "cookie",
            "api_key",
            "secret",
            "refresh_token",
            "access_token",
            "oauth_token",
            "session_id",
            "csrf_token",
        }

    def _mask_sensitive_value(self, value: str) -> str:
        """Mask sensitive values in log output."""
        if not value or not isinstance(value, str):
            return value
        if len(value) <= 8:
            return "********"
        return value[:4] + "****" + value[-4:]

    def _sanitize_dict(self, data: dict) -> dict:
        """Recursively sanitize dictionary to mask sensitive fields."""
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.sensitive_fields):
                sanitized[key] = self._mask_sensitive_value(str(value))
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    def format(self, record: logging.LogRecord) -> str:
        record_dict = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": SERVICE_NAME,
            "message": record.getMessage(),
        }

        if record.exc_info:
            record_dict["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            record_dict.update(self._sanitize_dict(record.extra))

        # Include structured fields on the record if present
        for key in [
            "event",
            "user_id",
            "booking_id",
            "webhook_id",
            "service",
            "status_code",
        ]:
            if hasattr(record, key):
                record_dict[key] = getattr(record, key)

        return json.dumps(record_dict, default=str)


def _ensure_log_dir() -> None:
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except OSError:
        pass


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(LOG_LEVEL)
    _ensure_log_dir()

    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "error.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(error_handler)

    combined_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "combined.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    combined_handler.setLevel(LOG_LEVEL)
    combined_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(combined_handler)

    if not IS_PRODUCTION:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
