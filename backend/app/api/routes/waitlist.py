from fastapi import APIRouter, Depends

from app.api.deps import Db
from app.core.ratelimit import rate_limit_anonymous
from app.db.client import DatabaseError
from app.schemas.content import WaitlistRequest

router = APIRouter(tags=["waitlist"])


@router.post(
    "/waitlist",
    status_code=201,
    dependencies=[Depends(rate_limit_anonymous(max_requests=5, window_seconds=60))],
)
async def join_waitlist(body: WaitlistRequest, db: Db) -> dict[str, str]:
    try:
        await db.insert(
            "waitlist", {"email": body.email.lower(), "source": body.source}
        )
    except DatabaseError as exc:
        if exc.db_status != 409:
            raise
        # Duplicate signup: same outcome for the visitor, and indistinguishable
        # from a fresh one so the endpoint can't be used to probe emails.
    return {"status": "subscribed"}
