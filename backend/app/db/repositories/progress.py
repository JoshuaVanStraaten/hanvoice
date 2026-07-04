"""Reads/writes for the per-user progress rollup tables."""

from datetime import UTC, datetime
from uuid import UUID

from app.db.client import Database, JsonRow


async def upsert_lesson_progress(
    db: Database,
    user_id: UUID,
    lesson_id: int,
    *,
    blocks_completed: int,
    best_score: float | None,
    completed: bool,
) -> None:
    values: JsonRow = {
        "user_id": str(user_id),
        "lesson_id": lesson_id,
        "blocks_completed": blocks_completed,
        "best_pronunciation_score": best_score,
        "status": "completed" if completed else "in_progress",
    }
    if completed:
        values["completed_at"] = datetime.now(UTC).isoformat()
    await db.upsert("lesson_progress", values, on_conflict="user_id,lesson_id")


async def get_block_progress(
    db: Database, user_id: UUID, block_id: int
) -> JsonRow | None:
    return await db.select_one(
        "lesson_block_progress",
        filters={"user_id": f"eq.{user_id}", "block_id": f"eq.{block_id}"},
    )


async def upsert_block_progress(
    db: Database,
    user_id: UUID,
    block_id: int,
    *,
    passed: bool,
    best_score: float | None,
) -> None:
    values: JsonRow = {
        "user_id": str(user_id),
        "block_id": block_id,
        "passed": passed,
        "best_score": best_score,
    }
    if passed:
        values["passed_at"] = datetime.now(UTC).isoformat()
    await db.upsert("lesson_block_progress", values, on_conflict="user_id,block_id")


async def list_block_progress(
    db: Database, user_id: UUID, block_ids: list[int]
) -> list[JsonRow]:
    if not block_ids:
        return []
    return await db.select(
        "lesson_block_progress",
        filters={
            "user_id": f"eq.{user_id}",
            "block_id": f"in.({','.join(str(b) for b in block_ids)})",
        },
    )


async def get_scenario_progress(
    db: Database, user_id: UUID, scenario_id: int
) -> JsonRow | None:
    return await db.select_one(
        "scenario_progress",
        filters={"user_id": f"eq.{user_id}", "scenario_id": f"eq.{scenario_id}"},
    )


async def upsert_scenario_progress(
    db: Database,
    user_id: UUID,
    scenario_id: int,
    *,
    times_completed: int,
    last_session_id: int,
    completed: bool,
) -> None:
    values: JsonRow = {
        "user_id": str(user_id),
        "scenario_id": scenario_id,
        "times_completed": times_completed,
        "last_session_id": last_session_id,
        "status": "completed" if completed else "in_progress",
    }
    if completed:
        values["completed_at"] = datetime.now(UTC).isoformat()
    await db.upsert("scenario_progress", values, on_conflict="user_id,scenario_id")


async def list_lesson_progress(db: Database, user_id: UUID) -> list[JsonRow]:
    return await db.select("lesson_progress", filters={"user_id": f"eq.{user_id}"})


async def list_scenario_progress(db: Database, user_id: UUID) -> list[JsonRow]:
    return await db.select("scenario_progress", filters={"user_id": f"eq.{user_id}"})
