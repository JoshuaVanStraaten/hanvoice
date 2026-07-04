"""Progress rollup maintenance.

Runs on the write path (after each block outcome) so the read path — home
screen, lesson list — stays a single indexed read of the rollup tables.
Blocks are the unit of progress; a lesson completes when every block passes.
"""

from uuid import UUID

from app.db.client import Database, JsonRow
from app.db.repositories import attempts, content
from app.db.repositories import progress as progress_repo

# A block counts as passed once a scored attempt reaches this overall score.
PASS_THRESHOLD = 60.0


async def mark_block_result(
    db: Database, user_id: UUID, block: JsonRow, *, score: float | None, passed: bool
) -> tuple[int, int, bool]:
    """Record one block outcome and refresh the lesson rollup.

    Never downgrades: a failed retry after a pass keeps the pass and the best
    score. Returns (blocks_completed, block_count, lesson_completed).
    """
    block_id = int(block["id"])
    existing = await progress_repo.get_block_progress(db, user_id, block_id)
    if existing is not None:
        passed = passed or bool(existing["passed"])
        prev_best = existing.get("best_score")
        if prev_best is not None:
            best = float(prev_best)
            score = best if score is None else max(best, score)
    await progress_repo.upsert_block_progress(
        db, user_id, block_id, passed=passed, best_score=score
    )
    return await _refresh_lesson_rollup(db, user_id, int(block["lesson_id"]))


async def _refresh_lesson_rollup(
    db: Database, user_id: UUID, lesson_id: int
) -> tuple[int, int, bool]:
    blocks = await content.list_lesson_blocks(db, lesson_id)
    block_ids = [int(b["id"]) for b in blocks]
    progress_rows = await progress_repo.list_block_progress(db, user_id, block_ids)
    blocks_completed = sum(1 for row in progress_rows if row["passed"])
    phrases = await content.list_lesson_phrases(db, lesson_id)
    best = await attempts.best_lesson_score(db, user_id, [int(p["id"]) for p in phrases])
    lesson_completed = bool(block_ids) and blocks_completed == len(block_ids)
    await progress_repo.upsert_lesson_progress(
        db,
        user_id,
        lesson_id,
        blocks_completed=blocks_completed,
        best_score=best,
        completed=lesson_completed,
    )
    return blocks_completed, len(block_ids), lesson_completed


async def update_after_pronunciation(
    db: Database, user_id: UUID, phrase: JsonRow, score: float
) -> None:
    """A scored phrase attempt passes every speak block that references it."""
    for block in await content.list_speak_blocks_for_phrase(db, int(phrase["id"])):
        await mark_block_result(
            db, user_id, block, score=score, passed=score >= PASS_THRESHOLD
        )


async def update_after_scenario_completion(
    db: Database, user_id: UUID, scenario_id: int, session_id: int
) -> None:
    existing = await progress_repo.get_scenario_progress(db, user_id, scenario_id)
    times_completed = (int(existing["times_completed"]) if existing else 0) + 1
    await progress_repo.upsert_scenario_progress(
        db,
        user_id,
        scenario_id,
        times_completed=times_completed,
        last_session_id=session_id,
        completed=True,
    )
