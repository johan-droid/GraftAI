from .base import DBModel
from typing import Optional


class Preference(DBModel):
    id: int
    user_id: int
    key: str
    value: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
