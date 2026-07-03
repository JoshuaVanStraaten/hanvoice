"""Stripe integration — checkout creation and webhook processing.

All Stripe knowledge lives here. When Stripe isn't configured the service
reports so and billing routes return 503 — the rest of the app (and local
development) works without payment credentials. Database rows are only ever
written from verified webhook events, never from client-initiated requests.
"""

from typing import Any, Literal
from uuid import UUID

import anyio.to_thread
import stripe
import structlog

from app.core.config import Settings
from app.core.errors import BadRequestError, ServiceUnavailableError
from app.db.client import Database, DatabaseError
from app.db.repositories import billing as billing_repo

logger = structlog.get_logger(__name__)

CheckoutPlan = Literal["premium", "founder"]

# Stripe subscription statuses we store verbatim; anything else maps to canceled.
_KNOWN_STATUSES = {"trialing", "active", "past_due", "canceled", "incomplete"}


class BillingService:
    def __init__(self, settings: Settings):
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self._settings.stripe_secret_key and self._settings.stripe_webhook_secret)

    def _require_configured(self) -> None:
        if not self.is_configured:
            raise ServiceUnavailableError("Payments are not enabled on this deployment.")

    async def create_checkout_url(
        self, user_id: UUID, email: str | None, plan: CheckoutPlan
    ) -> str:
        self._require_configured()
        frontend = self._settings.frontend_url.rstrip("/")

        if plan == "founder":
            price = self._settings.stripe_price_founder
            mode = "payment"
        else:
            price = self._settings.stripe_price_premium
            mode = "subscription"
        if not price:
            raise ServiceUnavailableError(f"The {plan} plan is not purchasable yet.")

        params: dict[str, Any] = {
            "mode": mode,
            "line_items": [{"price": price, "quantity": 1}],
            "client_reference_id": str(user_id),
            "metadata": {"plan": plan, "user_id": str(user_id)},
            "success_url": f"{frontend}/subscription?checkout=success",
            "cancel_url": f"{frontend}/subscription?checkout=canceled",
        }
        if email:
            params["customer_email"] = email
        if mode == "subscription":
            params["subscription_data"] = {"metadata": {"user_id": str(user_id)}}

        def _create() -> str:
            session = stripe.checkout.Session.create(
                api_key=self._settings.stripe_secret_key, **params
            )
            if not session.url:
                raise ServiceUnavailableError("Stripe did not return a checkout URL.")
            return session.url

        return await anyio.to_thread.run_sync(_create)

    def verify_webhook(self, payload: bytes, signature: str) -> stripe.Event:
        self._require_configured()
        try:
            event: stripe.Event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
                payload, signature, self._settings.stripe_webhook_secret
            )
            return event
        except (ValueError, stripe.SignatureVerificationError) as exc:
            raise BadRequestError("Invalid webhook signature.") from exc

    async def handle_event(self, db: Database, event: stripe.Event) -> None:
        # StripeObject stopped being a dict subclass in stripe-python v15;
        # normalize once so handlers work with plain dicts.
        data = event.data.object.to_dict()
        if event.type == "checkout.session.completed":
            await self._handle_checkout_completed(db, data)
        elif event.type in (
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ):
            await self._handle_subscription_change(db, data)
        else:
            logger.info("stripe_event_ignored", event_type=event.type)

    async def _handle_checkout_completed(self, db: Database, session: dict[str, Any]) -> None:
        if session.get("mode") != "payment":
            return  # subscriptions are handled by customer.subscription.* events
        metadata = session.get("metadata") or {}
        if metadata.get("plan") != "founder":
            logger.warning("stripe_unknown_payment", session_id=session.get("id"))
            return
        user_id = UUID(str(session["client_reference_id"]))
        try:
            await billing_repo.record_founder_pass(
                db,
                user_id,
                provider_payment_id=str(session.get("payment_intent")),
                amount_usd_cents=int(session.get("amount_total") or 6900),
            )
        except DatabaseError as exc:
            if exc.db_status == 409:
                logger.info("founder_pass_already_recorded", user_id=str(user_id))
                return  # webhook retry — already processed
            raise

    async def _handle_subscription_change(
        self, db: Database, subscription: dict[str, Any]
    ) -> None:
        metadata = subscription.get("metadata") or {}
        user_id = metadata.get("user_id")
        if not user_id:
            logger.warning("stripe_subscription_missing_user", sub_id=subscription.get("id"))
            return
        status = str(subscription.get("status"))
        if status not in _KNOWN_STATUSES:
            status = "canceled"
        await billing_repo.upsert_subscription_by_provider_id(
            db,
            str(subscription["id"]),
            {
                "user_id": str(UUID(str(user_id))),
                "plan_id": "premium",
                "status": status,
                "provider": "stripe",
                "provider_customer_id": subscription.get("customer"),
                "cancel_at_period_end": bool(subscription.get("cancel_at_period_end", False)),
                "current_period_start": _epoch_to_iso(subscription.get("current_period_start")),
                "current_period_end": _epoch_to_iso(subscription.get("current_period_end")),
            },
        )


def _epoch_to_iso(value: object) -> str | None:
    if not isinstance(value, int | float):
        return None
    from datetime import UTC, datetime

    return datetime.fromtimestamp(value, tz=UTC).isoformat()
