import uuid

from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, ConfigDict

# SQLAlchemy Base for database models
Base = declarative_base()


# Pydantic Base for API schemas
class DBModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def generate_uuid() -> str:
    return str(uuid.uuid4())
