from fastapi import APIRouter

from app.api.deps import CurrentUser, Db
from app.db.repositories import billing, profiles
from app.schemas.profiles import MeResponse, Profile, ProfileUpdate
from app.services.entitlements import resolve_plan

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeResponse)
async def get_me(user: CurrentUser, db: Db) -> MeResponse:
    profile = await profiles.get_profile(db, user.id)
    plan = await resolve_plan(db, user.id)
    founder_pass = await billing.get_founder_pass(db, user.id)
    return MeResponse(profile=profile, plan=plan, has_founder_pass=founder_pass is not None)


@router.patch("/me", response_model=Profile)
async def update_me(changes: ProfileUpdate, user: CurrentUser, db: Db) -> Profile:
    return await profiles.update_profile(db, user.id, changes)
