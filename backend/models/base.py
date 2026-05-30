import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class DBModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

def generate_uuid() -> str:
    return str(uuid.uuid4())
