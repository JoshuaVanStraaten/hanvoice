import json

import httpx
import respx

from tests.conftest import SUPABASE_REST
from tests.factories import (
    auth_headers,
    message_row,
    plan_row,
    prompt_row,
    scenario_row,
    session_row,
    usage_row,
)

LLM_URL = "http://nvidia.test/llm"
TTS_URL = "https://koreacentral.tts.speech.microsoft.com/cognitiveservices/v1"
ASR_URL = "http://nvidia.test/asr"

VALID_TURN = {
    "ai_response_hangul": "네! 사이즈는 어떤 걸로 드릴까요?",
    "ai_response_romanized": "ne! saijeuneun eotteon geollo deurilkkayo?",
    "ai_response_english": "Sure! What size would you like?",
    "contextual_correction": "",
}


def mock_get(table: str, rows: list) -> respx.Route:
    return respx.mock.get(f"{SUPABASE_REST}/{table}").mock(
        return_value=httpx.Response(200, json=rows)
    )


def mock_common(usage: dict | None = None) -> None:
    mock_get("founder_pass_purchases", [])
    mock_get("subscriptions", [])
    mock_get("plans", [plan_row("free")])
    mock_get("daily_usage", [usage] if usage else [])
    respx.mock.post(f"{SUPABASE_REST}/rpc/increment_daily_usage").mock(
        return_value=httpx.Response(200, json=usage_row())
    )
    respx.mock.post(LLM_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(VALID_TURN)}}],
                "usage": {"prompt_tokens": 90, "completion_tokens": 45},
            },
        )
    )
    respx.mock.post(TTS_URL).mock(return_value=httpx.Response(200, content=b"mp3" * 100))


@respx.mock
def test_start_conversation(client):
    mock_common()
    mock_get("scenarios", [scenario_row()])
    mock_get("scenario_prompts", [prompt_row()])
    respx.mock.post(f"{SUPABASE_REST}/conversation_sessions").mock(
        return_value=httpx.Response(201, json=[session_row()])
    )
    respx.mock.post(f"{SUPABASE_REST}/conversation_messages").mock(
        return_value=httpx.Response(201, json=[message_row()])
    )

    response = client.post(
        "/api/conversations",
        json={"scenario_slug": "cafe-iced-americano"},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session"]["status"] == "active"
    assert body["opening_message"]["role"] == "assistant"
    assert body["audio_base64"]  # TTS configured in tests


@respx.mock
def test_turn_detects_goals_and_stores_messages(client):
    mock_common()
    mock_get("conversation_sessions", [session_row(goals_completed=["greeted"])])
    mock_get("scenarios", [scenario_row()])
    mock_get("scenario_prompts", [prompt_row()])
    mock_get("conversation_messages", [message_row()])
    message_insert = respx.mock.post(f"{SUPABASE_REST}/conversation_messages")
    message_insert.side_effect = [
        httpx.Response(
            201, json=[message_row(2, role="user", hangul="아이스 아메리카노 주세요")]
        ),
        httpx.Response(
            201, json=[message_row(3, hangul=VALID_TURN["ai_response_hangul"])]
        ),
    ]
    session_patch = respx.mock.patch(f"{SUPABASE_REST}/conversation_sessions").mock(
        return_value=httpx.Response(200, json=[session_row()])
    )

    response = client.post(
        "/api/conversations/1/turns",
        headers=auth_headers(),
        data={"text": "아이스 아메리카노 주세요"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body["goals_completed"]) == {"greeted", "ordered_drink", "stated_size_or_temp"}
    assert body["scenario_completed"] is False
    assert body["assistant_message"]["hangul"].startswith("네!")
    assert message_insert.call_count == 2
    patched = json.loads(session_patch.calls[0].request.content)
    assert "ordered_drink" in patched["goals_completed"]


@respx.mock
def test_final_goal_completes_scenario_and_updates_progress(client):
    mock_common()
    nearly_done = ["greeted", "ordered_drink", "stated_size_or_temp", "paid"]
    mock_get("conversation_sessions", [session_row(goals_completed=nearly_done)])
    mock_get("scenarios", [scenario_row()])
    mock_get("scenario_prompts", [prompt_row()])
    mock_get("conversation_messages", [])
    respx.mock.post(f"{SUPABASE_REST}/conversation_messages").mock(
        return_value=httpx.Response(201, json=[message_row()])
    )
    session_patch = respx.mock.patch(f"{SUPABASE_REST}/conversation_sessions").mock(
        return_value=httpx.Response(200, json=[session_row(status="completed")])
    )
    mock_get("scenario_progress", [])
    progress_upsert = respx.mock.post(f"{SUPABASE_REST}/scenario_progress").mock(
        return_value=httpx.Response(201, json=[{"id": 1}])
    )

    response = client.post(
        "/api/conversations/1/turns",
        headers=auth_headers(),
        data={"text": "감사합니다!"},
    )

    body = response.json()
    assert body["scenario_completed"] is True
    patched = json.loads(session_patch.calls[0].request.content)
    assert patched["status"] == "completed"
    upserted = json.loads(progress_upsert.calls[0].request.content)
    assert upserted["times_completed"] == 1
    assert upserted["status"] == "completed"


@respx.mock
def test_turn_transcribes_audio_via_asr(client):
    mock_common()
    mock_get("conversation_sessions", [session_row()])
    mock_get("scenarios", [scenario_row()])
    mock_get("scenario_prompts", [prompt_row()])
    mock_get("conversation_messages", [])
    respx.mock.post(ASR_URL).mock(
        return_value=httpx.Response(200, json={"text": "카드로 할게요"})
    )
    respx.mock.post(f"{SUPABASE_REST}/conversation_messages").mock(
        return_value=httpx.Response(201, json=[message_row()])
    )
    respx.mock.patch(f"{SUPABASE_REST}/conversation_sessions").mock(
        return_value=httpx.Response(200, json=[session_row()])
    )

    response = client.post(
        "/api/conversations/1/turns",
        headers=auth_headers(),
        files={"audio": ("turn.webm", b"webmbytes", "audio/webm")},
    )

    assert response.status_code == 200
    assert "paid" in response.json()["goals_completed"]


@respx.mock
def test_foreign_session_is_404(client):
    mock_common()
    mock_get("conversation_sessions", [])
    response = client.post(
        "/api/conversations/999/turns", headers=auth_headers(), data={"text": "안녕"}
    )
    assert response.status_code == 404


@respx.mock
def test_ended_session_is_409(client):
    mock_common()
    mock_get("conversation_sessions", [session_row(status="completed")])
    response = client.post(
        "/api/conversations/1/turns", headers=auth_headers(), data={"text": "안녕"}
    )
    assert response.status_code == 409


@respx.mock
def test_empty_turn_is_400(client):
    mock_common()
    mock_get("conversation_sessions", [session_row()])
    mock_get("scenarios", [scenario_row()])
    mock_get("scenario_prompts", [prompt_row()])
    response = client.post(
        "/api/conversations/1/turns", headers=auth_headers(), data={"text": "   "}
    )
    assert response.status_code == 400
