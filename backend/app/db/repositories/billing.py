"""Reads/writes for subscriptions and founder passes.

Rows here are written only from verified payment-provider webhook handling —
never from user-initiated requests directly.
"""

from typing import Any
from uuid import UUID

from app.db.client import Database, JsonRow

LIVE_SUBSCRIPTION_STATUSES = ("trialing", "active", "past_due")


async def get_founder_pass(db: Database, user_id: UUID) -> JsonRow | None:
    return await db.select_one(
        "founder_pass_purchases", filters={"user_id": f"eq.{user_id}"}
    )


async def get_live_subscription(db: Database, user_id: UUID) -> JsonRow | None:
    return await db.select_one(
        "subscriptions",
        filters={
            "user_id": f"eq.{user_id}",
            "status": f"in.({','.join(LIVE_SUBSCRIPTION_STATUSES)})",
        },
    )


async def record_founder_pass(
    db: Database, user_id: UUID, provider_payment_id: str, amount_usd_cents: int
) -> None:
    await db.insert(
        "founder_pass_purchases",
        {
            "user_id": str(user_id),
            "provider": "polar",
            "provider_payment_id": provider_payment_id,
            "amount_usd_cents": amount_usd_cents,
        },
    )


async def upsert_subscription_by_provider_id(
    db: Database, provider_subscription_id: str, values: dict[str, Any]
) -> None:
    await db.upsert(
        "subscriptions",
        {"provider_subscription_id": provider_subscription_id, **values},
        on_conflict="provider_subscription_id",
    )
