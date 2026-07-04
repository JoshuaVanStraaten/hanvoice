from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.plans import Plan


class Profile(BaseModel):
    id: UUID
    display_name: str
    native_language: str
    onboarding_completed: bool
    created_at: datetime


class ProfileUpdate(BaseModel):
    """Client-editable profile fields only."""

    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    native_language: str | None = Field(default=None, min_length=2, max_length=16)
    onboarding_completed: bool | None = None


class MeResponse(BaseModel):
    profile: Profile
    plan: Plan
    has_founder_pass: bool
