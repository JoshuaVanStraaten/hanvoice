import base64

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, Db, Tts
from app.core.errors import BadRequestError
from app.core.ratelimit import rate_limit
from app.db.repositories import content
from app.db.repositories import progress as progress_repo
from app.schemas.content import (
    BlockCompleteResponse,
    LessonBlock,
    LessonDetail,
    LessonPhrase,
    LessonSummary,
    ScenarioSummary,
)
from app.services import progress as progress_service
from app.services import tts_cache
from app.services.audio_text import allowed_audio_texts

router = APIRouter(tags=["content"])


@router.get("/lessons", response_model=list[LessonSummary])
async def list_lessons(user: CurrentUser, db: Db) -> list[LessonSummary]:
    lessons = await content.list_published_lessons(db)
    summaries = []
    for row in lessons:
        blocks = await content.list_lesson_blocks(db, int(row["id"]))
        summaries.append(LessonSummary(**row, block_count=len(blocks)))
    return summaries


@router.get("/lessons/{slug}", response_model=LessonDetail)
async def get_lesson(slug: str, user: CurrentUser, db: Db) -> LessonDetail:
    lesson = await content.get_published_lesson(db, slug)
    blocks = await content.list_lesson_blocks(db, int(lesson["id"]))
    phrases = {
        int(p["id"]): p
        for p in await content.list_lesson_phrases(db, int(lesson["id"]))
    }
    progress_rows = await progress_repo.list_block_progress(
        db, user.id, [int(b["id"]) for b in blocks]
    )
    passed_ids = {int(row["block_id"]) for row in progress_rows if row["passed"]}

    items = []
    for block in blocks:
        phrase = phrases.get(int(block["phrase_id"])) if block.get("phrase_id") else None
        items.append(
            LessonBlock(
                id=int(block["id"]),
                kind=block["kind"],
                payload=block.get("payload") or {},
                phrase=LessonPhrase.model_validate(phrase) if phrase else None,
                sort_order=int(block["sort_order"]),
                passed=int(block["id"]) in passed_ids,
            )
        )
    return LessonDetail(**lesson, blocks=items)


@router.post("/lessons/blocks/{block_id}/complete", response_model=BlockCompleteResponse)
async def complete_block(
    block_id: int, user: CurrentUser, db: Db
) -> BlockCompleteResponse:
    """Marks a self-attested block (explain/quiz) as passed.

    Speak and write blocks are deliberately excluded: those pass only when the
    backend scores a real attempt, so progress can't be forged.
    """
    block = await content.get_block(db, block_id)
    await content.get_published_lesson_by_id(db, int(block["lesson_id"]))
    if block["kind"] not in ("explain", "quiz"):
        raise BadRequestError("This block is completed by a scored attempt, not directly.")
    blocks_completed, block_count, lesson_completed = await progress_service.mark_block_result(
        db, user.id, block, score=None, passed=True
    )
    return BlockCompleteResponse(
        block_id=block_id,
        passed=True,
        blocks_completed=blocks_completed,
        block_count=block_count,
        lesson_completed=lesson_completed,
    )


@router.get(
    "/lessons/blocks/{block_id}/audio",
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
async def get_block_audio(
    block_id: int,
    user: CurrentUser,
    db: Db,
    tts: Tts,
    text: str = Query(max_length=50),
) -> dict[str, str]:
    """Teaching audio for a glyph on this block, synthesized on demand.

    Like phrase audio, the spend is bounded by our own content: ``text`` must
    be one of the strings this block's payload is allowed to speak (carrier
    syllables for bare jamo — see ``audio_text_for``). Not quota-metered:
    listening is learning.
    """
    block = await content.get_block(db, block_id)
    await content.get_published_lesson_by_id(db, int(block["lesson_id"]))
    allowed = allowed_audio_texts(str(block["kind"]), block.get("payload") or {})
    if text not in allowed:
        raise BadRequestError("This block has no such audio.")
    audio = await tts_cache.synthesize_cached(tts, text)
    return {"audio_base64": base64.b64encode(audio).decode()}


@router.get("/scenarios", response_model=list[ScenarioSummary])
async def list_scenarios(user: CurrentUser, db: Db) -> list[ScenarioSummary]:
    rows = await content.list_published_scenarios(db)
    return [ScenarioSummary.model_validate(row) for row in rows]
