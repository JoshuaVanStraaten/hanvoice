import uuid

import httpx
import pytest
import respx

from app.db.client import Database
from app.services.entitlements import resolve_plan
from tests.conftest import SUPABASE_REST
from tests.factories import founder_pass_row, plan_row, subscription_row

USER_ID = uuid.UUID("1b671a64-40d5-491e-99b0-da01ff1f3341")


@pytest.fixture
async def db():
    async with httpx.AsyncClient() as http:
        yield Database(http=http, base_url="http://supabase.test", service_role_key="k")


def mock_get(router: respx.MockRouter, table: str, rows: list) -> None:
    router.get(f"{SUPABASE_REST}/{table}").mock(
        return_value=httpx.Response(200, json=rows)
    )


@respx.mock
async def test_founder_pass_wins(db):
    mock_get(respx.mock, "founder_pass_purchases", [founder_pass_row()])
    mock_get(respx.mock, "plans", [plan_row("founder")])
    plan = await resolve_plan(db, USER_ID)
    assert plan.id == "founder"
    assert plan.daily_conversation_turn_limit == 150


@respx.mock
async def test_live_subscription_used_when_no_founder_pass(db):
    mock_get(respx.mock, "founder_pass_purchases", [])
    mock_get(respx.mock, "subscriptions", [subscription_row(plan_id="premium")])
    mock_get(respx.mock, "plans", [plan_row("premium")])
    plan = await resolve_plan(db, USER_ID)
    assert plan.id == "premium"


@respx.mock
async def test_defaults_to_free(db):
    mock_get(respx.mock, "founder_pass_purchases", [])
    mock_get(respx.mock, "subscriptions", [])
    mock_get(respx.mock, "plans", [plan_row("free")])
    plan = await resolve_plan(db, USER_ID)
    assert plan.id == "free"


@respx.mock
async def test_subscription_query_excludes_dead_statuses(db):
    mock_get(respx.mock, "founder_pass_purchases", [])
    subs_route = respx.mock.get(f"{SUPABASE_REST}/subscriptions").mock(
        return_value=httpx.Response(200, json=[])
    )
    mock_get(respx.mock, "plans", [plan_row("free")])

    await resolve_plan(db, USER_ID)

    params = subs_route.calls[0].request.url.params
    assert params["status"] == "in.(trialing,active,past_due)"
