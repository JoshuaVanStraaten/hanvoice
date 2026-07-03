from uuid import UUID

from app.core.errors import NotFoundError
from app.db.client import Database
from app.schemas.profiles import Profile, ProfileUpdate


async def get_profile(db: Database, user_id: UUID) -> Profile:
    row = await db.select_one("profiles", filters={"id": f"eq.{user_id}"})
    if row is None:
        # The signup trigger creates profiles, so this indicates a deleted user.
        raise NotFoundError("Profile not found.")
    return Profile.model_validate(row)


async def update_profile(db: Database, user_id: UUID, changes: ProfileUpdate) -> Profile:
    values = changes.model_dump(exclude_none=True)
    if not values:
        return await get_profile(db, user_id)
    rows = await db.update("profiles", values, filters={"id": f"eq.{user_id}"})
    if not rows:
        raise NotFoundError("Profile not found.")
    return Profile.model_validate(rows[0])
