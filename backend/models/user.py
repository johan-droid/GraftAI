from pydantic import EmailStr, Field
from .base import DBModel
from typing import Optional

class User(DBModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    hashed_password: Optional[str] = None
    timezone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
