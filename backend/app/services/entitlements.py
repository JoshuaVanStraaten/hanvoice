"""Plan resolution — the single source of truth for what a user is entitled to.

Order matters and is part of the approved schema design:
founder pass (lifetime, never expires) → live subscription → free.
"""

from uuid import UUID

from app.db.client import Database
from app.db.repositories import billing, plans
from app.schemas.plans import Plan

FOUNDER_PLAN_ID = "founder"
FREE_PLAN_ID = "free"


async def resolve_plan(db: Database, user_id: UUID) -> Plan:
    if await billing.get_founder_pass(db, user_id) is not None:
        return await plans.get_plan(db, FOUNDER_PLAN_ID)

    subscription = await billing.get_live_subscription(db, user_id)
    if subscription is not None:
        return await plans.get_plan(db, str(subscription["plan_id"]))

    return await plans.get_plan(db, FREE_PLAN_ID)
