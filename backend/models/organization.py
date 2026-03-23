from .base import DBModel
from typing import Optional

class Organization(DBModel):
    id: int
    name: str
    owner_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
