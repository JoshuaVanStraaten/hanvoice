from typing import Literal

from pydantic import BaseModel


class LessonProgressItem(BaseModel):
    lesson_id: int
    lesson_slug: str
    lesson_title: str
    status: Literal["in_progress", "completed"]
    blocks_completed: int
    block_count: int
    best_pronunciation_score: float | None = None


class ScenarioProgressItem(BaseModel):
    scenario_id: int
    scenario_slug: str
    scenario_title: str
    status: Literal["in_progress", "completed"]
    times_completed: int
    last_session_id: int | None = None


class ProgressResponse(BaseModel):
    lessons: list[LessonProgressItem]
    scenarios: list[ScenarioProgressItem]
