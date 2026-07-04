from typing import Any

from pydantic import BaseModel, Field


class PronunciationScores(BaseModel):
    """Azure Pronunciation Assessment result, normalized to 0-100."""

    accuracy: float = Field(ge=0, le=100)
    fluency: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)
    overall: float = Field(ge=0, le=100)
    recognized_text: str = ""
    words: list[dict[str, Any]] = Field(default_factory=list)


class PronunciationAttemptResponse(BaseModel):
    attempt_id: int
    target_text: str
    scores: PronunciationScores
