from __future__ import annotations
import pytz
import re
from typing import Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")


class ProfileBase(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = None
    phone: str | None = Field(default=None, max_length=32)
    timezone: str = Field(default="UTC")
    time_format: Literal["12h", "24h"] = Field(default="12h")
    default_calendar_id: str | None = None
    theme: Literal["light", "dark", "system"] = Field(default="system")
    brand_color_light: str = Field(default="#3b82f6")
    brand_color_dark: str = Field(default="#1e40af")
    booking_layout: Literal["daily", "weekly", "monthly"] = Field(default="monthly")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("brand_color_light", "brand_color_dark")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not HEX_COLOR_PATTERN.match(value):
            raise ValueError("brand colors must be 6-digit hex values like #1a2b3c")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value or value not in pytz.all_timezones:
            raise ValueError(
                "timezone must be a valid IANA timezone like America/New_York or UTC"
            )
        return value


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    timezone: str | None = Field(default=None)
    time_format: Literal["12h", "24h"] | None = None
    theme: Literal["light", "dark", "system"] | None = None
    brand_color_light: str | None = None
    brand_color_dark: str | None = None
    booking_layout: Literal["daily", "weekly", "monthly"] | None = None


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    onboarding_completed: bool
    completed_steps: list[str]
    created_at: datetime
    updated_at: datetime
