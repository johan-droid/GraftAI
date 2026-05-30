from __future__ import annotations

import html
import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from datetime import datetime
SLUG_PATTERN = re.compile("^[a-z0-9-]+$")

def _generate_slug(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub("[^a-z0-9]+", "-", slug).strip("-")
    return slug or "event-type"

class EventTypeBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    slug: str | None = None
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int = Field(default=30, ge=15, le=480)
    buffer_minutes: int = Field(default=0, ge=0, le=120)
    location: str | None = Field(default=None, max_length=255)
    color: str = Field(default="#3b82f6")
    is_hidden: bool = Field(default=False)
    is_default: bool = Field(default=False)
    model_config = ConfigDict(from_attributes=True)

    @field_validator("name", "description", "location", mode="before")
    @classmethod
    def sanitize_html(cls, v: str | None) -> str | None:
        """Neutralizes malicious script tags into harmless plain text."""
        if v is None:
            return v
        return html.escape(v.strip())

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not SLUG_PATTERN.match(value):
            msg = "slug may only contain lowercase letters, numbers, and hyphens"
            raise ValueError(msg)
        return value

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if not re.fullmatch("^#[0-9A-Fa-f]{6}$", value):
            msg = "color must be a valid hex value like #1a2b3c"
            raise ValueError(msg)
        return value

    @model_validator(mode="before")
    @classmethod
    def auto_generate_slug(cls, values: dict) -> dict:
        if values.get("slug") is None and values.get("name"):
            values["slug"] = _generate_slug(values["name"])
        return values

class EventTypeCreate(EventTypeBase):
    pass

class EventTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=120)
    slug: str | None = None
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    buffer_minutes: int | None = Field(default=None, ge=0, le=120)
    location: str | None = Field(default=None, max_length=255)
    color: str | None = None
    is_hidden: bool | None = None
    is_default: bool | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not SLUG_PATTERN.match(value):
            msg = "slug may only contain lowercase letters, numbers, and hyphens"
            raise ValueError(msg)
        return value

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not re.fullmatch("^#[0-9A-Fa-f]{6}$", value):
            msg = "color must be a valid hex value like #1a2b3c"
            raise ValueError(msg)
        return value

class EventTypeResponse(EventTypeBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
