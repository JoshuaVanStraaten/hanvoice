"""Polar billing integration — checkout sessions and webhook processing.

HanVoice sells through Polar as merchant of record. The backend creates a
checkout session server-side (``POST {polar_api_base}/v1/checkouts/`` with the
organization access token) and hands the hosted checkout URL to the frontend,
which redirects. When Polar isn't configured the service reports so and
billing routes return 503 — the rest of the app (and local development) works
without payment credentials.

Entitlement rows are only ever written from signature-verified webhook
events. ``metadata`` originates server-side at checkout creation (unlike the
old Paddle flow's client-set ``custom_data``), but every grant still
cross-checks the purchased product id against the plan as defense in depth.
"""

import base64
import contextlib
import hashlib
import hmac
import json
import time
from typing import Any, Literal
from uuid import UUID

import httpx
import structlog
from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import BadRequestError, ServiceUnavailableError
from app.db.client import Database, DatabaseError
from app.db.repositories import billing as billing_repo

logger = structlog.get_logger(__name__)

CheckoutPlan = Literal["premium", "founder"]

# Polar subscription statuses we store verbatim; anything else (incomplete,
# unpaid, revoked, unknown future statuses) maps to canceled so it never
# keeps entitlements.
_KNOWN_STATUSES = {"trialing", "active", "past_due", "canceled"}

# Replay window for webhook signatures (standard-webhooks recommends 5 min).
_SIGNATURE_TOLERANCE_SECONDS = 300

_CHECKOUT_TIMEOUT_SECONDS = 15.0


class CheckoutSession(BaseModel):
    """The hosted checkout URL the frontend redirects to."""

    url: str


class BillingService:
    def __init__(self, settings: Settings):
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(
            self._settings.polar_access_token and self._settings.polar_webhook_secret
        )

    def _require_configured(self) -> None:
        if not self.is_configured:
            raise ServiceUnavailableError("Payments are not enabled on this deployment.")

    def _product_for(self, plan: CheckoutPlan) -> str:
        product = (
            self._settings.polar_product_founder
            if plan == "founder"
            else self._settings.polar_product_premium
        )
        if not product:
            raise ServiceUnavailableError(f"The {plan} plan is not purchasable yet.")
        return product

    async def create_checkout(
        self, user_id: UUID, email: str | None, plan: CheckoutPlan
    ) -> CheckoutSession:
        self._require_configured()
        product = self._product_for(plan)
        frontend = self._settings.frontend_url.rstrip("/")
        body: dict[str, Any] = {
            "products": [product],
            "metadata": {"user_id": str(user_id), "plan": plan},
            "external_customer_id": str(user_id),
            "success_url": f"{frontend}/subscription?checkout=success",
        }
        if email:
            body["customer_email"] = email
        try:
            async with httpx.AsyncClient(timeout=_CHECKOUT_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{self._settings.polar_api_base}/v1/checkouts/",
                    headers={
                        "Authorization": f"Bearer {self._settings.polar_access_token}"
                    },
                    json=body,
                )
        except httpx.HTTPError as exc:
            logger.error("polar_checkout_unreachable", error=str(exc))
            raise ServiceUnavailableError(
                "The payment provider is unreachable. Please try again."
            ) from exc
        if response.status_code != 201:
            logger.error(
                "polar_checkout_failed",
                status=response.status_code,
                body=response.text[:500],
            )
            raise ServiceUnavailableError(
                "The payment provider rejected the checkout. Please try again."
            )
        url = response.json().get("url")
        if not url:
            raise ServiceUnavailableError(
                "The payment provider returned no checkout URL."
            )
        return CheckoutSession(url=str(url))

    def _candidate_keys(self) -> list[bytes]:
        """Both plausible HMAC keys for the configured secret.

        Polar's docs sign with the literal secret string; the
        standard-webhooks spec says the key is the base64-decoded part after
        ``whsec_``. Accepting either keeps us correct across Polar versions —
        both candidates still derive solely from our secret.
        """
        secret = self._settings.polar_webhook_secret
        keys = [secret.encode()]
        stripped = secret.removeprefix("whsec_")
        # If the secret isn't base64, the literal-string key stands alone.
        with contextlib.suppress(ValueError):
            keys.append(base64.b64decode(stripped + "=" * (-len(stripped) % 4)))
        return keys

    def verify_webhook(
        self, payload: bytes, msg_id: str, timestamp: str, signature: str
    ) -> dict[str, Any]:
        """Verify standard-webhooks headers and parse the event.

        Signed content is ``{id}.{timestamp}.{raw_body}`` HMAC-SHA256'd; the
        ``webhook-signature`` header holds space-separated ``v1,<base64>``
        entries. See polar.sh/docs/integrate/webhooks/delivery.
        """
        self._require_configured()
        if not timestamp.isdigit():
            raise BadRequestError("Invalid webhook timestamp.")
        if abs(time.time() - int(timestamp)) > _SIGNATURE_TOLERANCE_SECONDS:
            raise BadRequestError("Webhook timestamp outside tolerance.")
        signed = msg_id.encode() + b"." + timestamp.encode() + b"." + payload
        given = {
            part.split(",", 1)[1]
            for part in signature.split()
            if part.startswith("v1,")
        }
        expected = {
            base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
            for key in self._candidate_keys()
        }
        if not any(
            hmac.compare_digest(e, g) for e in expected for g in given
        ):
            raise BadRequestError("Invalid webhook signature.")
        try:
            event: dict[str, Any] = json.loads(payload)
        except ValueError as exc:
            raise BadRequestError("Webhook payload is not valid JSON.") from exc
        return event

    async def handle_event(self, db: Database, event: dict[str, Any]) -> None:
        event_type = str(event.get("type", ""))
        data: dict[str, Any] = event.get("data") or {}
        if event_type == "order.paid":
            await self._handle_order_paid(db, data)
        elif event_type.startswith("subscription."):
            await self._handle_subscription_change(db, data)
        else:
            logger.info("polar_event_ignored", event_type=event_type)

    async def _handle_order_paid(self, db: Database, data: dict[str, Any]) -> None:
        if data.get("subscription_id"):
            return  # recurring payments are handled by subscription.* events
        metadata = data.get("metadata") or {}
        if metadata.get("plan") != "founder":
            logger.warning("polar_unknown_payment", order_id=data.get("id"))
            return
        # metadata is server-set at checkout creation, but the product
        # actually paid for stays the source of truth, not the plan label.
        if str(data.get("product_id")) != self._settings.polar_product_founder:
            logger.warning(
                "polar_plan_product_mismatch",
                order_id=data.get("id"),
                product_id=data.get("product_id"),
            )
            return
        user_id = UUID(str(metadata["user_id"]))
        try:
            amount = int(data.get("total_amount") or 6900)
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
        metadata = data.get("metadata") or {}
        user_id = metadata.get("user_id")
        if not user_id:
            logger.warning("polar_subscription_missing_user", sub_id=data.get("id"))
            return
        if str(data.get("product_id")) != self._settings.polar_product_premium:
            logger.warning(
                "polar_plan_product_mismatch",
                sub_id=data.get("id"),
                product_id=data.get("product_id"),
            )
            return
        status = str(data.get("status"))
        if status not in _KNOWN_STATUSES:
            status = "canceled"
        await billing_repo.upsert_subscription_by_provider_id(
            db,
            str(data["id"]),
            {
                "user_id": str(UUID(str(user_id))),
                "plan_id": "premium",
                "status": status,
                "provider": "polar",
                "provider_customer_id": data.get("customer_id"),
                "cancel_at_period_end": bool(data.get("cancel_at_period_end")),
                "current_period_start": data.get("current_period_start"),
                "current_period_end": data.get("current_period_end"),
            },
        )
