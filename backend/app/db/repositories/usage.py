from datetime import UTC, datetime
from uuid import UUID

from app.db.client import Database
from app.schemas.usage import UsageCounters


def _today_utc() -> str:
    return datetime.now(UTC).date().isoformat()


async def get_today(db: Database, user_id: UUID) -> UsageCounters:
    row = await db.select_one(
        "daily_usage",
        filters={"user_id": f"eq.{user_id}", "usage_date": f"eq.{_today_utc()}"},
    )
    if row is None:
        return UsageCounters(usage_date=datetime.now(UTC).date())
    return UsageCounters.model_validate(row)


async def increment(
    db: Database,
    user_id: UUID,
    *,
    pronunciation: int = 0,
    turns: int = 0,
    tokens_in: int = 0,
    tokens_out: int = 0,
    tts_seconds: int = 0,
    handwriting: int = 0,
) -> UsageCounters:
    """Atomic upsert-increment via the ``increment_daily_usage`` RPC."""
    row = await db.rpc(
        "increment_daily_usage",
        {
            "p_user_id": str(user_id),
            "p_pronunciation": pronunciation,
            "p_turns": turns,
            "p_tokens_in": tokens_in,
            "p_tokens_out": tokens_out,
            "p_tts_seconds": tts_seconds,
            "p_handwriting": handwriting,
        },
    )
    return UsageCounters.model_validate(row)
