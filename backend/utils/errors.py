class CalendarError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.name = "CalendarError"


class BookingConflictError(ValueError):
    def __init__(self, message: str = "Booking conflict"):
        super().__init__(message)
        self.name = "BookingConflictError"


class TimezoneError(ValueError):
    def __init__(self, message: str):
        super().__init__(message)
        self.name = "TimezoneError"


class ExternalServiceError(Exception):
    def __init__(self, service: str, status_code: int, message: str):
        super().__init__(message)
        self.service = service
        self.status_code = status_code
        self.name = "ExternalServiceError"


class ValidationError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.name = "ValidationError"


def categorize_error(error: Exception) -> str:
    if getattr(error, "name", "") == "BookingConflictError":
        return "conflict"
    if getattr(error, "name", "") == "TimezoneError":
        return "validation"
    if getattr(error, "name", "") == "ValidationError":
        return "validation"
    if getattr(error, "name", "") == "ExternalServiceError":
        return "external"
    if getattr(error, "code", "").startswith("P"):
        return "database"
    return "unknown"


def http_status_for_error(error: Exception) -> int:
    category = categorize_error(error)
    if category == "conflict":
        return 409
    if category == "validation":
        return 400
    if category == "external":
        return 502
    if category == "database":
        return 500
    return 500
