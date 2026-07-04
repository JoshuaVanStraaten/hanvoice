from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class LessonPhrase(BaseModel):
    id: int
    hangul: str
    romanized: str
    english: str
    audio_url: str | None = None
    sort_order: int


class LessonBlock(BaseModel):
    """One step of a lesson. `payload` shape depends on `kind` (see docs/schema.md);
    speak blocks carry their phrase instead of a payload."""

    id: int
    kind: Literal["explain", "speak", "write", "quiz"]
    payload: dict[str, Any] = Field(default_factory=dict)
    phrase: LessonPhrase | None = None
    sort_order: int
    passed: bool = False


class LessonSummary(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    section: str = ""
    sort_order: int
    block_count: int = 0


class LessonDetail(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    section: str = ""
    blocks: list[LessonBlock]


class BlockCompleteResponse(BaseModel):
    block_id: int
    passed: bool
    blocks_completed: int
    block_count: int
    lesson_completed: bool


class ScenarioSummary(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    difficulty: int
    completion_goals: list[str]
    sort_order: int


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str | None = Field(default=None, max_length=80)
