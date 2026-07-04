from pydantic import BaseModel, Field


class HandwritingScores(BaseModel):
    """Nemotron-VL handwriting assessment, normalized to 0-100."""

    proportion_score: float = Field(ge=0, le=100)
    stroke_score: float = Field(ge=0, le=100)
    legibility_score: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)
    feedback: str = ""


class HandwritingAttemptRequest(BaseModel):
    target_text: str = Field(min_length=1, max_length=40)
    image_base64: str = Field(min_length=1, description="PNG data, base64 (no data: prefix)")
    block_id: int | None = Field(
        default=None, description="Write block this attempt answers, if inside a lesson"
    )


class HandwritingAttemptResponse(BaseModel):
    attempt_id: int
    target_text: str
    scores: HandwritingScores
    model_version: str
