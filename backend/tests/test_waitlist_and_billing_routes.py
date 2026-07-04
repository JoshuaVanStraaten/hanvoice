import hashlib
import hmac
import json
import time

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.errors import BadRequestError
from app.db.client import Database
from app.services.billing import BillingService
from tests.conftest import SUPABASE_REST
from tests.factories import TEST_USER_ID, auth_headers

WEBHOOK_SECRET = "whsec_testsecret"


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
    response = client.post("/api/waitlist", json={"email": "fan@example.com"})
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


# --- Billing --------------------------------------------------------------------


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
            stripe_secret_key="sk_test_x",
            stripe_webhook_secret=WEBHOOK_SECRET,
        )
    )


def sign(payload: bytes) -> str:
    timestamp = int(time.time())
    signature = hmac.new(
        WEBHOOK_SECRET.encode(), f"{timestamp}.{payload.decode()}".encode(), hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def founder_checkout_event() -> bytes:
    return json.dumps(
        {
            "id": "evt_1",
            "object": "event",
            "api_version": "2024-06-20",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_1",
                    "object": "checkout.session",
                    "mode": "payment",
                    "client_reference_id": TEST_USER_ID,
                    "payment_intent": "pi_123",
                    "amount_total": 6900,
                    "metadata": {"plan": "founder", "user_id": TEST_USER_ID},
                }
            },
        }
    ).encode()


def test_webhook_rejects_bad_signature():
    service = configured_service()
    with pytest.raises(BadRequestError):
        service.verify_webhook(founder_checkout_event(), "t=1,v1=deadbeef")


@respx.mock
async def test_founder_checkout_records_pass():
    service = configured_service()
    payload = founder_checkout_event()
    event = service.verify_webhook(payload, sign(payload))

    insert = respx.mock.post(f"{SUPABASE_REST}/founder_pass_purchases").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)

    sent = json.loads(insert.calls[0].request.content)
    assert sent["user_id"] == TEST_USER_ID
    assert sent["provider_payment_id"] == "pi_123"


@respx.mock
async def test_founder_webhook_retry_is_idempotent():
    service = configured_service()
    payload = founder_checkout_event()
    event = service.verify_webhook(payload, sign(payload))

    respx.mock.post(f"{SUPABASE_REST}/founder_pass_purchases").mock(
        return_value=httpx.Response(409, json={"code": "23505"})
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)  # must not raise


@respx.mock
async def test_subscription_update_upserts_row():
    service = configured_service()
    payload = json.dumps(
        {
            "id": "evt_2",
            "object": "event",
            "api_version": "2024-06-20",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_123",
                    "object": "subscription",
                    "status": "active",
                    "customer": "cus_9",
                    "cancel_at_period_end": False,
                    "current_period_start": 1780000000,
                    "current_period_end": 1782600000,
                    "metadata": {"user_id": TEST_USER_ID},
                }
            },
        }
    ).encode()
    event = service.verify_webhook(payload, sign(payload))

    upsert = respx.mock.post(f"{SUPABASE_REST}/subscriptions").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )
    async with httpx.AsyncClient() as http:
        db = Database(http=http, base_url="http://supabase.test", service_role_key="k")
        await service.handle_event(db, event)

    sent = json.loads(upsert.calls[0].request.content)
    assert sent["provider_subscription_id"] == "sub_123"
    assert sent["status"] == "active"
    assert sent["plan_id"] == "premium"
