"""Writes for scored attempts — service-role only by design."""

from typing import Any
from uuid import UUID

from app.db.client import Database, JsonRow
from app.schemas.handwriting import HandwritingScores
from app.schemas.pronunciation import PronunciationScores


async def insert_pronunciation_attempt(
    db: Database,
    user_id: UUID,
    target_text: str,
    scores: PronunciationScores,
    phrase_id: int | None,
) -> JsonRow:
    rows = await db.insert(
        "pronunciation_attempts",
        {
            "user_id": str(user_id),
            "phrase_id": phrase_id,
            "target_text": target_text,
            "accuracy_score": scores.accuracy,
            "fluency_score": scores.fluency,
            "completeness_score": scores.completeness,
            "overall_score": scores.overall,
            "phoneme_detail": {"recognized_text": scores.recognized_text, "words": scores.words},
        },
    )
    return rows[0]


async def insert_handwriting_attempt(
    db: Database,
    user_id: UUID,
    target_text: str,
    scores: HandwritingScores,
    model_version: str,
) -> JsonRow:
    rows = await db.insert(
        "handwriting_attempts",
        {
            "user_id": str(user_id),
            "target_text": target_text,
            "proportion_score": scores.proportion_score,
            "stroke_score": scores.stroke_score,
            "legibility_score": scores.legibility_score,
            "overall_score": scores.overall_score,
            "feedback": {"text": scores.feedback},
            "model_version": model_version,
        },
    )
    return rows[0]


async def best_lesson_score(
    db: Database, user_id: UUID, phrase_ids: list[int]
) -> float | None:
    if not phrase_ids:
        return None
    rows = await db.select(
        "pronunciation_attempts",
        columns="overall_score",
        filters={
            "user_id": f"eq.{user_id}",
            "phrase_id": f"in.({','.join(str(p) for p in phrase_ids)})",
            "overall_score": "not.is.null",
        },
        order="overall_score.desc",
        limit=1,
    )
    if not rows:
        return None
    value: Any = rows[0]["overall_score"]
    return float(value)
