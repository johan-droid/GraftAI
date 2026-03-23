from .base import DBModel
from typing import Optional

class AuthSession(DBModel):
    id: int
    user_id: int
    session_token: str
    expires_at: str
    created_at: Optional[str] = None

class AuditLog(DBModel):
    id: int
    user_id: int
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: str
