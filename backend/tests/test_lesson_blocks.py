"""Lesson blocks: detail payloads, the complete endpoint, and block-aware
scoring routes. Blocks are the curriculum's unit of progress."""

import base64
import json
import uuid

import httpx
import respx

from tests.conftest import SUPABASE_REST
from tests.factories import (
    auth_headers,
    block_progress_row,
    block_row,
    lesson_row,
    phrase_row,
    plan_row,
    usage_row,
)

VISION_URL = "http://nvidia.test/vision"
TTS_URL = "https://koreacentral.tts.speech.microsoft.com/cognitiveservices/v1"
FAKE_PNG_B64 = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"fakepixels").decode()


def mock_get(table: str, rows: list) -> respx.Route:
    return respx.mock.get(f"{SUPABASE_REST}/{table}").mock(
        return_value=httpx.Response(200, json=rows)
    )


def mock_post(table: str, rows: list) -> respx.Route:
    return respx.mock.post(f"{SUPABASE_REST}/{table}").mock(
        return_value=httpx.Response(201, json=rows)
    )


@respx.mock
def test_lesson_detail_returns_ordered_blocks_with_pass_state(client):
    mock_get("lessons", [lesson_row()])
    mock_get(
        "lesson_blocks",
        [
            block_row(1, "explain"),
            block_row(2, "speak", phrase_id=1, payload={}),
            block_row(
                3,
                "quiz",
                payload={
                    "question": "Hangul is…",
                    "choices": ["an alphabet", "pictographs"],
                    "answer": 0,
                    "explanation": "Letters stack into syllable blocks.",
                },
            ),
        ],
    )
    mock_get("lesson_phrases", [phrase_row()])
    mock_get("lesson_block_progress", [block_progress_row(1)])

    response = client.get("/api/lessons/cafe-essentials", headers=auth_headers())

    assert response.status_code == 200
    blocks = response.json()["blocks"]
    assert [b["kind"] for b in blocks] == ["explain", "speak", "quiz"]
    assert blocks[0]["passed"] is True
    assert blocks[1]["passed"] is False
    assert blocks[1]["phrase"]["hangul"] == "아이스 아메리카노 주세요"
    assert blocks[0]["phrase"] is None
    assert blocks[2]["payload"]["choices"] == ["an alphabet", "pictographs"]


@respx.mock
def test_complete_explain_block_updates_rollup(client):
    mock_get("lessons", [lesson_row()])
    mock_get("lesson_blocks", [block_row(1, "explain"), block_row(2, "quiz")])
    mock_get("lesson_block_progress", [block_progress_row(1)])
    block_upsert = mock_post("lesson_block_progress", [block_progress_row(1)])
    mock_get("lesson_phrases", [])
    rollup = mock_post("lesson_progress", [{"id": 1}])

    response = client.post("/api/lessons/blocks/1/complete", headers=auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["blocks_completed"] == 1
    assert body["block_count"] == 2
    assert body["lesson_completed"] is False
    assert block_upsert.call_count == 1
    assert rollup.call_count == 1


@respx.mock
def test_complete_speak_block_is_rejected(client):
    mock_get("lessons", [lesson_row()])
    mock_get("lesson_blocks", [block_row(1, "speak", phrase_id=1)])

    response = client.post("/api/lessons/blocks/1/complete", headers=auth_headers())

    assert response.status_code == 400


@respx.mock
def test_complete_unknown_block_404(client):
    mock_get("lesson_blocks", [])
    response = client.post("/api/lessons/blocks/999/complete", headers=auth_headers())
    assert response.status_code == 404


@respx.mock
def test_complete_block_of_unpublished_lesson_404(client):
    mock_get("lesson_blocks", [block_row(1, "explain")])
    mock_get("lessons", [])  # published-only filter finds nothing

    response = client.post("/api/lessons/blocks/1/complete", headers=auth_headers())

    assert response.status_code == 404


VERDICT = {
    "proportion_score": 70,
    "stroke_score": 65,
    "legibility_score": 80,
    "overall_score": 72,
    "feedback": "Nice spacing.",
}


def _mock_handwriting_scoring() -> None:
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


@respx.mock
def test_handwriting_with_block_id_marks_block_passed(client):
    _mock_handwriting_scoring()
    mock_get("lessons", [lesson_row()])
    mock_get("lesson_blocks", [block_row(4, "write", payload={"target": "안", "hint": ""})])
    mock_get("lesson_block_progress", [])
    block_upsert = mock_post("lesson_block_progress", [block_progress_row(4)])
    mock_get("lesson_phrases", [])
    mock_post("lesson_progress", [{"id": 1}])

    # Fresh user id: the in-process rate limiter is keyed per user and shared
    # across tests in the same window.
    response = client.post(
        "/api/handwriting/attempts",
        headers=auth_headers(str(uuid.uuid4())),
        json={"target_text": "안", "image_base64": FAKE_PNG_B64, "block_id": 4},
    )

    assert response.status_code == 200
    assert block_upsert.call_count == 1
    sent = json.loads(block_upsert.calls[0].request.content)
    assert sent["passed"] is True
    assert sent["best_score"] == 72


@respx.mock
def test_handwriting_block_target_mismatch_400_before_vision(client):
    mock_get("lessons", [lesson_row()])
    mock_get("lesson_blocks", [block_row(4, "write", payload={"target": "안", "hint": ""})])
    vision = respx.mock.post(VISION_URL)

    response = client.post(
        "/api/handwriting/attempts",
        headers=auth_headers(str(uuid.uuid4())),
        json={"target_text": "녕", "image_base64": FAKE_PNG_B64, "block_id": 4},
    )

    assert response.status_code == 400
    assert vision.call_count == 0


@respx.mock
def test_handwriting_block_must_be_write_kind(client):
    mock_get("lessons", [lesson_row()])
    mock_get("lesson_blocks", [block_row(1, "explain")])

    response = client.post(
        "/api/handwriting/attempts",
        headers=auth_headers(str(uuid.uuid4())),
        json={"target_text": "안", "image_base64": FAKE_PNG_B64, "block_id": 1},
    )

    assert response.status_code == 400


@respx.mock
def test_block_audio_synthesizes_carrier_for_write_target(client):
    mock_get("lesson_blocks", [block_row(1, "write", payload={"target": "ㄱ"})])
    mock_get("lessons", [lesson_row()])
    tts = respx.mock.post(TTS_URL).mock(
        return_value=httpx.Response(200, content=b"ID3mp3bytes")
    )

    response = client.get(
        "/api/lessons/blocks/1/audio", params={"text": "가"}, headers=auth_headers()
    )

    assert response.status_code == 200
    assert base64.b64decode(response.json()["audio_base64"]) == b"ID3mp3bytes"
    assert "가" in tts.calls[0].request.content.decode()


@respx.mock
def test_block_audio_allows_explain_chars_and_examples(client):
    payload = {
        "segments": [
            {"type": "chars", "items": [{"ko": "ㅏ"}]},
            {"type": "example", "items": [{"ko": "한국"}]},
        ]
    }
    mock_get("lesson_blocks", [block_row(1, "explain", payload=payload)])
    mock_get("lessons", [lesson_row()])
    tts = respx.mock.post(TTS_URL).mock(
        return_value=httpx.Response(200, content=b"ID3mp3bytes")
    )

    for text in ("아", "한국"):
        response = client.get(
            "/api/lessons/blocks/1/audio", params={"text": text}, headers=auth_headers()
        )
        assert response.status_code == 200
    assert tts.call_count == 2


@respx.mock
def test_block_audio_rejects_text_not_in_block(client):
    mock_get("lesson_blocks", [block_row(1, "write", payload={"target": "ㄱ"})])
    mock_get("lessons", [lesson_row()])
    tts = respx.mock.post(TTS_URL)

    response = client.get(
        "/api/lessons/blocks/1/audio",
        params={"text": "아무 말이나"},
        headers=auth_headers(),
    )

    assert response.status_code == 400
    assert tts.call_count == 0


@respx.mock
def test_block_audio_unpublished_lesson_404(client):
    mock_get("lesson_blocks", [block_row(1, "write", payload={"target": "ㄱ"})])
    mock_get("lessons", [])

    response = client.get(
        "/api/lessons/blocks/1/audio", params={"text": "가"}, headers=auth_headers()
    )

    assert response.status_code == 404


@respx.mock
def test_block_audio_repeat_request_hits_cache(client):
    mock_get("lesson_blocks", [block_row(1, "write", payload={"target": "ㄱ"})])
    mock_get("lessons", [lesson_row()])
    tts = respx.mock.post(TTS_URL).mock(
        return_value=httpx.Response(200, content=b"ID3mp3bytes")
    )

    for _ in range(2):
        response = client.get(
            "/api/lessons/blocks/1/audio", params={"text": "가"}, headers=auth_headers()
        )
        assert response.status_code == 200

    assert tts.call_count == 1
