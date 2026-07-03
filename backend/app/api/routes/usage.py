from fastapi import APIRouter

from app.api.deps import CurrentUser, Db
from app.db.repositories import usage as usage_repo
from app.schemas.usage import UsageTodayResponse
from app.services.entitlements import resolve_plan

router = APIRouter(tags=["usage"])


@router.get("/usage/today", response_model=UsageTodayResponse)
async def usage_today(user: CurrentUser, db: Db) -> UsageTodayResponse:
    counters = await usage_repo.get_today(db, user.id)
    plan = await resolve_plan(db, user.id)
    return UsageTodayResponse(usage=counters, plan=plan)
