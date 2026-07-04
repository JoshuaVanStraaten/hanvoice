from typing import Annotated

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from app.api.deps import Billing, CurrentUser, Db
from app.core.errors import BadRequestError
from app.services.billing import CheckoutPlan

router = APIRouter(tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: CheckoutPlan


class CheckoutResponse(BaseModel):
    checkout_url: str


@router.post("/billing/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest, user: CurrentUser, billing: Billing
) -> CheckoutResponse:
    url = await billing.create_checkout_url(user.id, user.email, body.plan)
    return CheckoutResponse(checkout_url=url)


@router.post("/billing/webhook")
async def stripe_webhook(
    request: Request,
    db: Db,
    billing: Billing,
    stripe_signature: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    if not stripe_signature:
        raise BadRequestError("Missing Stripe-Signature header.")
    payload = await request.body()
    event = billing.verify_webhook(payload, stripe_signature)
    await billing.handle_event(db, event)
    return {"status": "processed"}
