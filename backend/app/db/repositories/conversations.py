"""Reads/writes for conversation sessions and messages."""

from datetime import UTC, datetime
from uuid import UUID

from app.core.errors import NotFoundError
from app.db.client import Database, JsonRow


async def create_session(db: Database, user_id: UUID, scenario_id: int) -> JsonRow:
    rows = await db.insert(
        "conversation_sessions",
        {"user_id": str(user_id), "scenario_id": scenario_id},
    )
    return rows[0]


async def get_own_session(db: Database, user_id: UUID, session_id: int) -> JsonRow:
    """Ownership is enforced here — a foreign session id is indistinguishable
    from a missing one (404, never 403, so ids can't be probed)."""
    row = await db.select_one(
        "conversation_sessions",
        filters={"id": f"eq.{session_id}", "user_id": f"eq.{user_id}"},
    )
    if row is None:
        raise NotFoundError("Conversation not found.")
    return row


async def update_session(db: Database, session_id: int, values: JsonRow) -> JsonRow:
    rows = await db.update(
        "conversation_sessions", values, filters={"id": f"eq.{session_id}"}
    )
    return rows[0]


async def end_session(db: Database, session_id: int, status: str) -> JsonRow:
    return await update_session(
        db,
        session_id,
        {"status": status, "ended_at": datetime.now(UTC).isoformat()},
    )


async def insert_message(db: Database, session_id: int, values: JsonRow) -> JsonRow:
    rows = await db.insert("conversation_messages", {"session_id": session_id, **values})
    return rows[0]


async def list_messages(db: Database, session_id: int) -> list[JsonRow]:
    return await db.select(
        "conversation_messages",
        filters={"session_id": f"eq.{session_id}"},
        order="id.asc",
    )
