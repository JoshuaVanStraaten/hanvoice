import base64
import hashlib
import hmac
import json
import time
from typing import Any

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.errors import BadRequestError
from app.db.client import Database
from app.services.billing import BillingService
from tests.conftest import SUPABASE_REST
from tests.factories import TEST_USER_ID, auth_headers

# whsec_ + valid base64 so both key interpretations (literal string vs
# decoded standard-webhooks key) exist — see BillingService._candidate_keys.
WEBHOOK_SECRET = "whsec_dGVzdC1zaWduaW5nLWtleS0zMi1ieXRlcy1sb25nISE="
PRODUCT_FOUNDER = "prod-founder-test"
PRODUCT_PREMIUM = "prod-premium-test"
POLAR_API = "http://polar.test"


# --- Waitlist -----------------------------------------------------------------


@respx.mock
def test_waitlist_signup(client):
    insert = respx.mock.post(f"{SUPABASE_REST}/waitlist").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    response = client.post(
        "/api/waitlist", json={"email": "Fan@Example.com", "source": "tiktok"}
    )
    assert response.status_code == 201
    sent = json.loads(insert.calls[0].request.content)
    assert sent["email"] == "fan@example.com"  # normalized


@respx.mock
def test_waitlist_duplicate_looks_identical(client):
    respx.mock.post(f"{SUPABASE_REST}/waitlist").mock(
        return_value=httpx.Response(409, json={"code": "23505"})
    )
    resend = respx.mock.post("https://api.resend.com/emails").mock(
        return_value=httpx.Response(200, json={"id": "re_dup"})
    )
    response = client.post("/api/waitlist", json={"email": "fan@example.com"})
    assert response.status_code == 201
    assert not resend.called  # duplicates never re-email


@respx.mock
def test_waitlist_fresh_signup_sends_phrase_card_email(client):
    respx.mock.post(f"{SUPABASE_REST}/waitlist").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    resend = respx.mock.post("https://api.resend.com/emails").mock(
        return_value=httpx.Response(200, json={"id": "re_123"})
    )
    response = client.post(
        "/api/waitlist", json={"email": "Traveler@Example.com", "source": "tiktok"}
    )
    assert response.status_code == 201
    assert resend.called
    sent = json.loads(resend.calls[0].request.content)
    assert sent["to"] == ["traveler@example.com"]
    assert "phrase-card.html" in sent["html"]
    assert "SEOUL49" in sent["html"]


@respx.mock
def test_waitlist_email_failure_does_not_break_signup(client):
    respx.mock.post(f"{SUPABASE_REST}/waitlist").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    respx.mock.post("https://api.resend.com/emails").mock(
        return_value=httpx.Response(500, json={"error": "boom"})
    )
    response = client.post("/api/waitlist", json={"email": "fan2@example.com"})
    assert response.status_code == 201


def test_waitlist_invalid_email_is_422(client):
    assert client.post("/api/waitlist", json={"email": "not-an-email"}).status_code == 422


def test_waitlist_rate_limited_eventually(client):
    # In-process limiter allows 5/min per IP; TestClient always comes from the
    # same address, so a burst must hit 429 within a handful of requests.
    with respx.mock:
        respx.post(f"{SUPABASE_REST}/waitlist").mock(
            return_value=httpx.Response(201, json=[{"id": 1}])
        )
        statuses = [
            client.post("/api/waitlist", json={"email": f"a{i}@example.com"}).status_code
            for i in range(8)
        ]
    assert 429 in statuses


# --- Billing (Polar) -----------------------------------------------------------


def test_checkout_unconfigured_is_503(client):
    response = client.post(
        "/api/billing/checkout", json={"plan": "founder"}, headers=auth_headers()
    )
    assert response.status_code == 503


def test_webhook_missing_signature_is_400(client):
    response = client.post("/api/billing/webhook", content=b"{}")
    assert response.status_code == 400


def configured_service() -> BillingService:
    return BillingService(
        Settings(
            supabase_url="http://supabase.test",
            supabase_service_role_key="k",
            supabase_jwt_secret="s",
            polar_access_token="polar_oat_test",
            polar_webhook_secret=WEBHOOK_SECRET,
            polar_product_founder=PRODUCT_FOUNDER,
            polar_product_premium=PRODUCT_PREMIUM,
            polar_api_base=POLAR_API,
        )
    )


MSG_ID = "wh_msg_test_1"


def sign(
    payload: bytes,
    timestamp: int | None = None,
    key: bytes = WEBHOOK_SECRET.encode(),
) -> tuple[str, str, str]:
    """Return (webhook-id, webhook-timestamp, webhook-signature) headers."""
    ts = int(time.time()) if timestamp is None else timestamp
    signed = f"{MSG_ID}.{ts}.".encode() + payload
    digest = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    return MSG_ID, str(ts), f"v1,{digest}"


def polar_event(event_type: str, data: dict[str, Any]) -> bytes:
    return json.dumps(
        {
            "type": event_type,
            "timestamp": "2026-07-16T10:00:00.000000Z",
            "data": data,
        }
    ).encode()


def founder_order(product_id: str = PRODUCT_FOUNDER) -> bytes:
    return polar_event(
        "order.paid",
        {
            "id": "order-founder-test",
            "paid": True,
            "total_amount": 6900,
            "currency": "usd",
            "product_id": product_id,
            "subscription_id": None,
            "customer_id": "cust-test",
            "metadata": {"user_id": TEST_USER_ID, "plan": "founder"},
        },
    )


def premium_subscription(
    status: str = "active", cancel_at_period_end: bool = False
) -> bytes:
    return polar_event(
        "subscription.updated",
        {
            "id": "sub-premium-test",
            "status": status,
            "customer_id": "cust-test",
            "product_id": PRODUCT_PREMIUM,
            "metadata": {"user_id": TEST_USER_ID, "plan": "premium"},
            "current_period_start": "2026-07-16T10:00:00Z",
            "current_period_end": "2026-08-16T10:00:00Z",
            "cancel_at_period_end": cancel_at_period_end,
        },
    )


def verify(service: BillingService, payload: bytes, **kwargs: Any) -> dict[str, Any]:
    msg_id, ts, sig = sign(payload, **kwargs)
    return service.verify_webhook(payload, msg_id, ts, sig)


@respx.mock
async def test_checkout_creates_polar_session():
    service = configured_service()
    from uuid import UUID

    create = respx.mock.post(f"{POLAR_API}/v1/checkouts/").mock(
        return_value=httpx.Response(
            201, json={"id": "co_test", "url": "https://polar.sh/checkout/co_test"}
        )
    )
    session = await service.create_checkout(
        UUID(TEST_USER_ID), "learner@example.com", "founder"
    )
    assert session.url == "https://polar.sh/checkout/co_test"
    sent = json.loads(create.calls[0].request.content)
    assert sent["products"] == [PRODUCT_FOUNDER]
    assert sent["metadata"] == {"user_id": TEST_USER_ID, "plan": "founder"}
    assert sent["customer_email"] == "learner@example.com"
    assert sent["external_customer_id"] == TEST_USER_ID
    assert sent["success_url"].endswith("/subscription?checkout=success")
    auth = create.calls[0].request.headers["authorization"]
    assert auth == "Bearer polar_oat_test"


@respx.mock
async def test_checkout_provider_error_is_503():
    service = configured_service()
    from uuid import UUID

    respx.mock.post(f"{POLAR_API}/v1/checkouts/").mock(
        return_value=httpx.Response(422, json={"detail": "nope"})
    )
    from app.core.errors import ServiceUnavailableError

    with pytest.raises(ServiceUnavailableError):
        await service.create_checkout(UUID(TEST_USER_ID), None, "premium")


def test_webhook_rejects_bad_signature():
    service = configured_service()
    payload = founder_order()
    with pytest.raises(BadRequestError):
        service.verify_webhook(payload, MSG_ID, str(int(time.time())), "v1,deadbeef")


def test_webhook_rejects_stale_timestamp():
    service = configured_service()
    payload = founder_order()
    stale = int(time.time()) - 3600
    msg_id, ts, sig = sign(payload, timestamp=stale)
    with pytest.raises(BadRequestError):
        service.verify_webhook(payload, msg_id, ts, sig)


def test_webhook_accepts_spec_decoded_key():
    # The standard-webhooks spec signs with base64-decode of the part after
    # whsec_; Polar's docs sign with the literal secret. Both must verify.
    service = configured_service()
    payload = founder_order()
    decoded = base64.b64decode(WEBHOOK_SECRET.removeprefix("whsec_"))
    event = verify(service, payload, key=decoded)
    assert event["type"] == "order.paid"


@respx.mock
async def test_founder_order_records_pass():
    service = configured_service()
    event = verify(service, founder_order())

    insert = respx.mock.post(f"{SUPABASE_REST}/founder_pass_purchases").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)

    sent = json.loads(insert.calls[0].request.content)
    assert sent["user_id"] == TEST_USER_ID
    assert sent["provider_payment_id"] == "order-founder-test"
    assert sent["provider"] == "polar"
    assert sent["amount_usd_cents"] == 6900


@respx.mock
async def test_founder_webhook_retry_is_idempotent():
    service = configured_service()
    event = verify(service, founder_order())

    respx.mock.post(f"{SUPABASE_REST}/founder_pass_purchases").mock(
        return_value=httpx.Response(409, json={"code": "23505"})
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)  # must not raise


@respx.mock
async def test_founder_grant_requires_matching_product():
    # The purchased product stays the source of truth over the plan label —
    # a founder-labeled order for the premium product must not grant a pass.
    service = configured_service()
    event = verify(service, founder_order(product_id=PRODUCT_PREMIUM))

    insert = respx.mock.post(f"{SUPABASE_REST}/founder_pass_purchases").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)

    assert not insert.called


@respx.mock
async def test_subscription_order_is_left_to_subscription_events():
    service = configured_service()
    payload = polar_event(
        "order.paid",
        {
            "id": "order-sub-renewal",
            "paid": True,
            "total_amount": 1499,
            "currency": "usd",
            "product_id": PRODUCT_PREMIUM,
            "subscription_id": "sub-premium-test",
            "customer_id": "cust-test",
            "metadata": {"user_id": TEST_USER_ID, "plan": "premium"},
        },
    )
    event = verify(service, payload)

    insert = respx.mock.post(f"{SUPABASE_REST}/founder_pass_purchases").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)

    assert not insert.called


@respx.mock
async def test_subscription_update_upserts_row():
    service = configured_service()
    event = verify(service, premium_subscription())

    upsert = respx.mock.post(f"{SUPABASE_REST}/subscriptions").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)

    sent = json.loads(upsert.calls[0].request.content)
    assert sent["provider_subscription_id"] == "sub-premium-test"
    assert sent["provider"] == "polar"
    assert sent["status"] == "active"
    assert sent["plan_id"] == "premium"
    assert sent["user_id"] == TEST_USER_ID
    assert sent["cancel_at_period_end"] is False
    assert sent["current_period_end"] == "2026-08-16T10:00:00Z"


@respx.mock
async def test_subscription_cancel_at_period_end_flag():
    service = configured_service()
    event = verify(service, premium_subscription(cancel_at_period_end=True))

    upsert = respx.mock.post(f"{SUPABASE_REST}/subscriptions").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)

    sent = json.loads(upsert.calls[0].request.content)
    assert sent["cancel_at_period_end"] is True
    assert sent["status"] == "active"


@respx.mock
async def test_subscription_unknown_status_maps_to_canceled():
    # "revoked"/"unpaid"/"incomplete" are Polar statuses our schema doesn't
    # store; none of them may keep premium entitlements.
    service = configured_service()
    event = verify(service, premium_subscription(status="revoked"))

    upsert = respx.mock.post(f"{SUPABASE_REST}/subscriptions").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)

    sent = json.loads(upsert.calls[0].request.content)
    assert sent["status"] == "canceled"
