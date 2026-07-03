"""Progress rollup maintenance.

Runs on the write path (after each scored attempt) so the read path — home
screen, lesson list — stays a single indexed read of the rollup tables.
"""

from uuid import UUID

from app.db.client import Database, JsonRow
from app.db.repositories import attempts, content
from app.db.repositories import progress as progress_repo

# A phrase counts as "completed" once any attempt reaches this overall score.
PASS_THRESHOLD = 60.0


async def update_after_pronunciation(db: Database, user_id: UUID, phrase: JsonRow) -> None:
    lesson_id = int(phrase["lesson_id"])
    phrases = await content.list_lesson_phrases(db, lesson_id)
    phrase_ids = [int(p["id"]) for p in phrases]

    passed = await attempts.list_passed_phrase_ids(db, user_id, phrase_ids, PASS_THRESHOLD)
    best = await attempts.best_lesson_score(db, user_id, phrase_ids)

    await progress_repo.upsert_lesson_progress(
        db,
        user_id,
        lesson_id,
        phrases_completed=len(passed),
        best_score=best,
        completed=bool(phrase_ids) and len(passed) == len(phrase_ids),
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
