from typing import Annotated

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from app.api.deps import Billing, CurrentUser, Db
from app.core.errors import BadRequestError
from app.services.billing import CheckoutPlan, CheckoutSession

router = APIRouter(tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: CheckoutPlan


@router.post("/billing/checkout", response_model=CheckoutSession)
async def create_checkout(
    body: CheckoutRequest, user: CurrentUser, billing: Billing
) -> CheckoutSession:
    """Create a Polar checkout session and return its hosted URL."""
    return await billing.create_checkout(user.id, user.email, body.plan)


@router.post("/billing/webhook")
async def polar_webhook(
    request: Request,
    db: Db,
    billing: Billing,
    webhook_id: Annotated[str | None, Header()] = None,
    webhook_timestamp: Annotated[str | None, Header()] = None,
    webhook_signature: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    if not (webhook_id and webhook_timestamp and webhook_signature):
        raise BadRequestError("Missing webhook signature headers.")
    payload = await request.body()
    event = billing.verify_webhook(
        payload, webhook_id, webhook_timestamp, webhook_signature
    )
    await billing.handle_event(db, event)
    return {"status": "processed"}
