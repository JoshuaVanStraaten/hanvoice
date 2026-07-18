from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.deps import AppSettings, Db
from app.core.ratelimit import rate_limit_anonymous
from app.db.client import DatabaseError
from app.schemas.content import WaitlistRequest
from app.services.waitlist_email import send_phrase_card_email

router = APIRouter(tags=["waitlist"])


@router.post(
    "/waitlist",
    status_code=201,
    dependencies=[Depends(rate_limit_anonymous(max_requests=5, window_seconds=60))],
)
async def join_waitlist(
    body: WaitlistRequest,
    db: Db,
    settings: AppSettings,
    background: BackgroundTasks,
) -> dict[str, str]:
    email = body.email.lower()
    try:
        await db.insert("waitlist", {"email": email, "source": body.source})
    except DatabaseError as exc:
        if exc.db_status != 409:
            raise
        # Duplicate signup: same outcome for the visitor, and indistinguishable
        # from a fresh one so the endpoint can't be used to probe emails. No
        # email either — re-sending would reveal the difference and spam them.
        return {"status": "subscribed"}
    background.add_task(send_phrase_card_email, settings, email)
    return {"status": "subscribed"}
