from pydantic import BaseModel, EmailStr, Field


class LessonPhrase(BaseModel):
    id: int
    hangul: str
    romanized: str
    english: str
    audio_url: str | None = None
    sort_order: int


class LessonSummary(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    sort_order: int
    phrase_count: int = 0


class LessonDetail(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    phrases: list[LessonPhrase]


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
