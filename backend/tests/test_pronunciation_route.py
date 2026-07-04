import httpx
import respx

from tests.conftest import SUPABASE_REST
from tests.factories import auth_headers, phrase_row, plan_row, usage_row

AZURE_URL = (
    "https://koreacentral.stt.speech.microsoft.com"
    "/speech/recognition/conversation/cognitiveservices/v1"
)


def mock_get(table: str, rows: list) -> respx.Route:
    return respx.mock.get(f"{SUPABASE_REST}/{table}").mock(
        return_value=httpx.Response(200, json=rows)
    )


def mock_post(table: str, rows: list) -> respx.Route:
    return respx.mock.post(f"{SUPABASE_REST}/{table}").mock(
        return_value=httpx.Response(201, json=rows)
    )


def azure_success() -> dict:
    return {
        "RecognitionStatus": "Success",
        "NBest": [
            {
                "Display": "아이스 아메리카노 주세요",
                "PronunciationAssessment": {
                    "AccuracyScore": 85.0,
                    "FluencyScore": 90.0,
                    "CompletenessScore": 100.0,
                    "PronScore": 87.5,
                },
                "Words": [],
            }
        ],
    }


def mock_plan_resolution() -> None:
    mock_get("founder_pass_purchases", [])
    mock_get("subscriptions", [])
    mock_get("plans", [plan_row("free")])


@respx.mock
def test_pronunciation_attempt_happy_path(client):
    mock_get("lesson_phrases", [phrase_row()])
    mock_plan_resolution()
    mock_get("daily_usage", [])
    azure = respx.mock.post(AZURE_URL).mock(
        return_value=httpx.Response(200, json=azure_success())
    )
    attempt_insert = mock_post("pronunciation_attempts", [{"id": 11}])
    respx.mock.post(f"{SUPABASE_REST}/rpc/increment_daily_usage").mock(
        return_value=httpx.Response(200, json=usage_row(pronunciation_attempts=1))
    )
    # Progress rollup reads attempts and upserts lesson_progress.
    mock_get("pronunciation_attempts", [{"phrase_id": 1, "overall_score": 87.5}])
    mock_post("lesson_progress", [{"id": 1}])

    response = client.post(
        "/api/pronunciation/attempts",
        headers=auth_headers(),
        files={"audio": ("take.wav", b"RIFFfakewav", "audio/wav")},
        data={"phrase_id": "1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["attempt_id"] == 11
    assert body["scores"]["overall"] == 87.5
    assert azure.call_count == 1
    assert attempt_insert.call_count == 1


@respx.mock
def test_quota_exceeded_never_calls_azure(client):
    mock_get("lesson_phrases", [phrase_row()])
    mock_plan_resolution()
    mock_get("daily_usage", [usage_row(pronunciation_attempts=20)])
    azure = respx.mock.post(AZURE_URL).mock(
        return_value=httpx.Response(200, json=azure_success())
    )

    response = client.post(
        "/api/pronunciation/attempts",
        headers=auth_headers(),
        files={"audio": ("take.wav", b"RIFF", "audio/wav")},
        data={"phrase_id": "1"},
    )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "quota_exceeded"
    assert azure.call_count == 0


def test_rejects_unsupported_content_type(client):
    response = client.post(
        "/api/pronunciation/attempts",
        headers=auth_headers(),
        files={"audio": ("take.txt", b"hello", "text/plain")},
        data={"target_text": "안녕하세요"},
    )
    assert response.status_code == 400


def test_requires_phrase_or_target(client):
    response = client.post(
        "/api/pronunciation/attempts",
        headers=auth_headers(),
        files={"audio": ("take.wav", b"RIFF", "audio/wav")},
    )
    assert response.status_code == 400


TTS_URL = "https://koreacentral.tts.speech.microsoft.com/cognitiveservices/v1"


@respx.mock
def test_phrase_audio_returns_base64_tts(client):
    mock_get("lesson_phrases", [phrase_row()])
    tts = respx.mock.post(TTS_URL).mock(
        return_value=httpx.Response(200, content=b"ID3mp3bytes")
    )
    response = client.get("/api/pronunciation/phrases/1/audio", headers=auth_headers())
    assert response.status_code == 200
    import base64

    assert base64.b64decode(response.json()["audio_base64"]) == b"ID3mp3bytes"
    assert "아이스 아메리카노 주세요" in tts.calls[0].request.content.decode()


@respx.mock
def test_phrase_audio_unknown_phrase_404(client):
    mock_get("lesson_phrases", [])
    response = client.get("/api/pronunciation/phrases/999/audio", headers=auth_headers())
    assert response.status_code == 404
