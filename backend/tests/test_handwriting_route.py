import base64
import json

import httpx
import respx

from tests.conftest import SUPABASE_REST
from tests.factories import auth_headers, plan_row, usage_row

VISION_URL = "http://nvidia.test/vision"

# Smallest thing that passes the PNG magic check.
FAKE_PNG_B64 = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"fakepixels").decode()

VERDICT = {
    "proportion_score": 70,
    "stroke_score": 65,
    "legibility_score": 80,
    "overall_score": 72,
    "feedback": "Nice spacing — make the final consonant smaller.",
}


def mock_get(table: str, rows: list) -> None:
    respx.mock.get(f"{SUPABASE_REST}/{table}").mock(
        return_value=httpx.Response(200, json=rows)
    )


@respx.mock
def test_handwriting_happy_path(client):
    mock_get("founder_pass_purchases", [])
    mock_get("subscriptions", [])
    mock_get("plans", [plan_row("free")])
    mock_get("daily_usage", [])
    respx.mock.post(VISION_URL).mock(
        return_value=httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(VERDICT)}}]}
        )
    )
    respx.mock.post(f"{SUPABASE_REST}/handwriting_attempts").mock(
        return_value=httpx.Response(201, json=[{"id": 5}])
    )
    respx.mock.post(f"{SUPABASE_REST}/rpc/increment_daily_usage").mock(
        return_value=httpx.Response(200, json=usage_row(handwriting_checks=1))
    )

    response = client.post(
        "/api/handwriting/attempts",
        headers=auth_headers(),
        json={"target_text": "안녕", "image_base64": FAKE_PNG_B64},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["attempt_id"] == 5
    assert body["scores"]["overall_score"] == 72


def test_invalid_base64_is_400(client):
    response = client.post(
        "/api/handwriting/attempts",
        headers=auth_headers(),
        json={"target_text": "안녕", "image_base64": "not-base64!!!"},
    )
    assert response.status_code == 400


def test_non_png_is_400(client):
    jpeg = base64.b64encode(b"\xff\xd8\xffJFIFdata").decode()
    response = client.post(
        "/api/handwriting/attempts",
        headers=auth_headers(),
        json={"target_text": "안녕", "image_base64": jpeg},
    )
    assert response.status_code == 400


@respx.mock
def test_handwriting_quota_gate(client):
    mock_get("founder_pass_purchases", [])
    mock_get("subscriptions", [])
    mock_get("plans", [plan_row("free")])
    mock_get("daily_usage", [usage_row(handwriting_checks=10)])
    vision = respx.mock.post(VISION_URL)

    response = client.post(
        "/api/handwriting/attempts",
        headers=auth_headers(),
        json={"target_text": "안녕", "image_base64": FAKE_PNG_B64},
    )

    assert response.status_code == 429
    assert vision.call_count == 0
