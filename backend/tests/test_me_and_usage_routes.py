import httpx
import respx

from tests.conftest import SUPABASE_REST
from tests.factories import auth_headers, plan_row, profile_row, usage_row


def mock_get(table: str, rows: list) -> None:
    respx.mock.get(f"{SUPABASE_REST}/{table}").mock(
        return_value=httpx.Response(200, json=rows)
    )


def test_me_requires_auth(client):
    response = client.get("/api/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


@respx.mock
def test_me_returns_profile_and_plan(client):
    mock_get("profiles", [profile_row()])
    mock_get("founder_pass_purchases", [])
    mock_get("subscriptions", [])
    mock_get("plans", [plan_row("free")])

    response = client.get("/api/me", headers=auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["display_name"] == "Josh"
    assert body["plan"]["id"] == "free"
    assert body["has_founder_pass"] is False


@respx.mock
def test_patch_me_updates_profile(client):
    updated = profile_row(display_name="Joshua")
    respx.mock.patch(f"{SUPABASE_REST}/profiles").mock(
        return_value=httpx.Response(200, json=[updated])
    )

    response = client.patch(
        "/api/me", json={"display_name": "Joshua"}, headers=auth_headers()
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Joshua"


def test_patch_me_rejects_blank_name(client):
    response = client.patch("/api/me", json={"display_name": ""}, headers=auth_headers())
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@respx.mock
def test_usage_today_zeros_when_no_row(client):
    mock_get("daily_usage", [])
    mock_get("founder_pass_purchases", [])
    mock_get("subscriptions", [])
    mock_get("plans", [plan_row("free")])

    response = client.get("/api/usage/today", headers=auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["usage"]["pronunciation_attempts"] == 0
    assert body["plan"]["daily_pronunciation_limit"] == 20


@respx.mock
def test_usage_today_returns_existing_counters(client):
    mock_get("daily_usage", [usage_row(pronunciation_attempts=7, conversation_turns=3)])
    mock_get("founder_pass_purchases", [])
    mock_get("subscriptions", [])
    mock_get("plans", [plan_row("free")])

    response = client.get("/api/usage/today", headers=auth_headers())

    assert response.json()["usage"]["pronunciation_attempts"] == 7
