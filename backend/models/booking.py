from .base import DBModel
from typing import Optional


class Booking(DBModel):
    id: int
    user_id: int
    organization_id: int
    start_time: str
    end_time: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
