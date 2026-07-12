"""Paddle Billing integration — checkout config and webhook processing.

HanVoice sells through Paddle as merchant of record. The frontend opens a
Paddle.js overlay checkout using config served by ``POST /billing/checkout``;
no Paddle API key is needed server-side. When Paddle isn't configured the
service reports so and billing routes return 503 — the rest of the app (and
local development) works without payment credentials.

Entitlement rows are only ever written from signature-verified webhook
events. Because the checkout is opened client-side, ``custom_data`` is
client-influenced — every grant cross-checks the purchased price id against
the plan before writing anything.
"""

import hashlib
import hmac
import json
import time
from typing import Any, Literal
from uuid import UUID

import structlog
from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import BadRequestError, ServiceUnavailableError
from app.db.client import Database, DatabaseError
from app.db.repositories import billing as billing_repo

logger = structlog.get_logger(__name__)

CheckoutPlan = Literal["premium", "founder"]

# Paddle subscription statuses we store verbatim; anything else (paused,
# unknown future statuses) maps to canceled so it never keeps entitlements.
_KNOWN_STATUSES = {"trialing", "active", "past_due", "canceled"}

# Replay window for webhook signatures. Paddle re-signs on every delivery
# attempt, so a generous-but-bounded window survives clock skew and slow
# proxies while still rejecting replayed captures.
_SIGNATURE_TOLERANCE_SECONDS = 60


class CheckoutConfig(BaseModel):
    """Everything Paddle.js needs to open the overlay checkout."""

    environment: Literal["sandbox", "production"]
    client_token: str
    price_id: str
    custom_data: dict[str, str]
    email: str | None
    success_url: str


class BillingService:
    def __init__(self, settings: Settings):
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(
            self._settings.paddle_client_token and self._settings.paddle_webhook_secret
        )

    def _require_configured(self) -> None:
        if not self.is_configured:
            raise ServiceUnavailableError("Payments are not enabled on this deployment.")

    def checkout_config(
        self, user_id: UUID, email: str | None, plan: CheckoutPlan
    ) -> CheckoutConfig:
        self._require_configured()
        price = (
            self._settings.paddle_price_founder
            if plan == "founder"
            else self._settings.paddle_price_premium
        )
        if not price:
            raise ServiceUnavailableError(f"The {plan} plan is not purchasable yet.")
        environment: Literal["sandbox", "production"] = (
            "production" if self._settings.paddle_env == "production" else "sandbox"
        )
        frontend = self._settings.frontend_url.rstrip("/")
        return CheckoutConfig(
            environment=environment,
            client_token=self._settings.paddle_client_token,
            price_id=price,
            custom_data={"user_id": str(user_id), "plan": plan},
            email=email,
            success_url=f"{frontend}/subscription?checkout=success",
        )

    def verify_webhook(self, payload: bytes, signature: str) -> dict[str, Any]:
        """Check the Paddle-Signature header (``ts=…;h1=…``) and parse the event.

        Signed payload is ``{ts}:{raw_body}`` HMAC-SHA256'd with the endpoint's
        webhook secret; see developer.paddle.com/webhooks/signature-verification.
        """
        self._require_configured()
        parts = dict(
            part.split("=", 1) for part in signature.split(";") if "=" in part
        )
        ts, h1 = parts.get("ts"), parts.get("h1")
        if not ts or not h1 or not ts.isdigit():
            raise BadRequestError("Invalid webhook signature.")
        if abs(time.time() - int(ts)) > _SIGNATURE_TOLERANCE_SECONDS:
            raise BadRequestError("Webhook timestamp outside tolerance.")
        expected = hmac.new(
            self._settings.paddle_webhook_secret.encode(),
            ts.encode() + b":" + payload,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, h1):
            raise BadRequestError("Invalid webhook signature.")
        try:
            event: dict[str, Any] = json.loads(payload)
        except ValueError as exc:
            raise BadRequestError("Webhook payload is not valid JSON.") from exc
        return event

    async def handle_event(self, db: Database, event: dict[str, Any]) -> None:
        event_type = str(event.get("event_type", ""))
        data: dict[str, Any] = event.get("data") or {}
        if event_type == "transaction.completed":
            await self._handle_transaction_completed(db, data)
        elif event_type.startswith("subscription."):
            await self._handle_subscription_change(db, data)
        else:
            logger.info("paddle_event_ignored", event_type=event_type)

    def _price_ids(self, data: dict[str, Any]) -> set[str]:
        return {
            str(item.get("price", {}).get("id"))
            for item in data.get("items") or []
            if isinstance(item, dict)
        }

    async def _handle_transaction_completed(
        self, db: Database, data: dict[str, Any]
    ) -> None:
        if data.get("subscription_id"):
            return  # recurring payments are handled by subscription.* events
        custom = data.get("custom_data") or {}
        if custom.get("plan") != "founder":
            logger.warning("paddle_unknown_payment", transaction_id=data.get("id"))
            return
        # custom_data is set by the client-opened checkout — the price actually
        # paid for is the source of truth, not the plan label.
        if self._settings.paddle_price_founder not in self._price_ids(data):
            logger.warning(
                "paddle_plan_price_mismatch",
                transaction_id=data.get("id"),
                prices=sorted(self._price_ids(data)),
            )
            return
        user_id = UUID(str(custom["user_id"]))
        totals = (data.get("details") or {}).get("totals") or {}
        try:
            amount = int(totals.get("total") or 6900)
        except ValueError:
            amount = 6900
        try:
            await billing_repo.record_founder_pass(
                db,
                user_id,
                provider_payment_id=str(data["id"]),
                amount_usd_cents=amount,
            )
        except DatabaseError as exc:
            if exc.db_status == 409:
                logger.info("founder_pass_already_recorded", user_id=str(user_id))
                return  # webhook retry — already processed
            raise

    async def _handle_subscription_change(
        self, db: Database, data: dict[str, Any]
    ) -> None:
        custom = data.get("custom_data") or {}
        user_id = custom.get("user_id")
        if not user_id:
            logger.warning("paddle_subscription_missing_user", sub_id=data.get("id"))
            return
        if self._settings.paddle_price_premium not in self._price_ids(data):
            logger.warning(
                "paddle_plan_price_mismatch",
                sub_id=data.get("id"),
                prices=sorted(self._price_ids(data)),
            )
            return
        status = str(data.get("status"))
        if status not in _KNOWN_STATUSES:
            status = "canceled"
        scheduled = data.get("scheduled_change") or {}
        period = data.get("current_billing_period") or {}
        await billing_repo.upsert_subscription_by_provider_id(
            db,
            str(data["id"]),
            {
                "user_id": str(UUID(str(user_id))),
                "plan_id": "premium",
                "status": status,
                "provider": "paddle",
                "provider_customer_id": data.get("customer_id"),
                "cancel_at_period_end": scheduled.get("action") in ("cancel", "pause"),
                "current_period_start": period.get("starts_at"),
                "current_period_end": period.get("ends_at"),
            },
        )
