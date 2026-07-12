from typing import Annotated

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from app.api.deps import Billing, CurrentUser, Db
from app.core.errors import BadRequestError
from app.services.billing import CheckoutConfig, CheckoutPlan

router = APIRouter(tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: CheckoutPlan


@router.post("/billing/checkout", response_model=CheckoutConfig)
async def create_checkout(
    body: CheckoutRequest, user: CurrentUser, billing: Billing
) -> CheckoutConfig:
    """Serve the config the frontend needs to open a Paddle.js overlay checkout."""
    return billing.checkout_config(user.id, user.email, body.plan)


@router.post("/billing/webhook")
async def paddle_webhook(
    request: Request,
    db: Db,
    billing: Billing,
    paddle_signature: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    if not paddle_signature:
        raise BadRequestError("Missing Paddle-Signature header.")
    payload = await request.body()
    event = billing.verify_webhook(payload, paddle_signature)
    await billing.handle_event(db, event)
    return {"status": "processed"}
