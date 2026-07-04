"""Reads for authored content (lessons, phrases, scenarios, prompts).

Published-only filtering happens here so no route can accidentally leak
drafts. Scenario prompt text never leaves the backend.
"""

from app.core.errors import NotFoundError
from app.db.client import Database, JsonRow


async def list_published_lessons(db: Database) -> list[JsonRow]:
    return await db.select(
        "lessons",
        columns="id,slug,title,description,section,sort_order",
        filters={"is_published": "eq.true"},
        order="sort_order.asc",
    )


async def get_published_lesson(db: Database, slug: str) -> JsonRow:
    row = await db.select_one(
        "lessons",
        columns="id,slug,title,description,section",
        filters={"slug": f"eq.{slug}", "is_published": "eq.true"},
    )
    if row is None:
        raise NotFoundError("Lesson not found.")
    return row


async def get_published_lesson_by_id(db: Database, lesson_id: int) -> JsonRow:
    row = await db.select_one(
        "lessons",
        columns="id,slug,title,section",
        filters={"id": f"eq.{lesson_id}", "is_published": "eq.true"},
    )
    if row is None:
        raise NotFoundError("Lesson not found.")
    return row


async def list_lesson_blocks(db: Database, lesson_id: int) -> list[JsonRow]:
    return await db.select(
        "lesson_blocks",
        columns="id,lesson_id,kind,phrase_id,payload,sort_order",
        filters={"lesson_id": f"eq.{lesson_id}"},
        order="sort_order.asc",
    )


async def get_block(db: Database, block_id: int) -> JsonRow:
    row = await db.select_one(
        "lesson_blocks",
        columns="id,lesson_id,kind,phrase_id,payload",
        filters={"id": f"eq.{block_id}"},
    )
    if row is None:
        raise NotFoundError("Block not found.")
    return row


async def list_speak_blocks_for_phrase(db: Database, phrase_id: int) -> list[JsonRow]:
    return await db.select(
        "lesson_blocks",
        columns="id,lesson_id,kind,phrase_id",
        filters={"phrase_id": f"eq.{phrase_id}", "kind": "eq.speak"},
    )


async def list_lesson_phrases(db: Database, lesson_id: int) -> list[JsonRow]:
    return await db.select(
        "lesson_phrases",
        columns="id,lesson_id,hangul,romanized,english,audio_url,sort_order",
        filters={"lesson_id": f"eq.{lesson_id}"},
        order="sort_order.asc",
    )


async def get_phrase(db: Database, phrase_id: int) -> JsonRow:
    row = await db.select_one(
        "lesson_phrases",
        columns="id,lesson_id,hangul",
        filters={"id": f"eq.{phrase_id}"},
    )
    if row is None:
        raise NotFoundError("Phrase not found.")
    return row


async def list_published_scenarios(db: Database) -> list[JsonRow]:
    return await db.select(
        "scenarios",
        columns="id,slug,title,description,difficulty,completion_goals,sort_order",
        filters={"is_published": "eq.true"},
        order="sort_order.asc",
    )


async def get_published_scenario(db: Database, slug: str) -> JsonRow:
    row = await db.select_one(
        "scenarios",
        columns="id,slug,title,description,difficulty,completion_goals",
        filters={"slug": f"eq.{slug}", "is_published": "eq.true"},
    )
    if row is None:
        raise NotFoundError("Scenario not found.")
    return row


async def get_scenario_by_id(db: Database, scenario_id: int) -> JsonRow:
    row = await db.select_one(
        "scenarios",
        columns="id,slug,title,completion_goals",
        filters={"id": f"eq.{scenario_id}"},
    )
    if row is None:
        raise NotFoundError("Scenario not found.")
    return row


async def get_active_prompt(db: Database, scenario_id: int) -> JsonRow:
    """Latest active prompt version for a scenario — service-role only data."""
    rows = await db.select(
        "scenario_prompts",
        columns="id,version,system_prompt",
        filters={"scenario_id": f"eq.{scenario_id}", "is_active": "eq.true"},
        order="version.desc",
        limit=1,
    )
    if not rows:
        raise NotFoundError("This scenario has no active prompt.")
    return rows[0]
