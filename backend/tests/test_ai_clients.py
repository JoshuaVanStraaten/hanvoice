"""AI provider client tests — success paths, provider failures, repair retries."""

import json

import httpx
import pytest
import respx

from app.core.errors import ServiceUnavailableError
from app.schemas.conversation import ChatMessage
from app.services.ai.azure_pronunciation import AzurePronunciationClient
from app.services.ai.base import AIServiceError, AIServiceUnavailableError
from app.services.ai.llama_chat import FALLBACK_TURN, LlamaChatClient
from app.services.ai.nemotron_asr import NemotronASRClient
from app.services.ai.nemotron_vision import NemotronVisionClient
from app.services.ai.tts import TTSClient

AZURE_URL = "https://koreacentral.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
LLM_URL = "http://nvidia.test/v1/chat/completions"
ASR_URL = "http://nvidia.test/v1/audio/transcriptions"
TTS_URL = "http://nvidia.test/v1/audio/speech"


@pytest.fixture
async def http():
    async with httpx.AsyncClient() as client:
        yield client


def azure_payload(status: str = "Success") -> dict:
    return {
        "RecognitionStatus": status,
        "NBest": [
            {
                "Display": "안녕하세요",
                "PronunciationAssessment": {
                    "AccuracyScore": 88.0,
                    "FluencyScore": 92.5,
                    "CompletenessScore": 100.0,
                    "PronScore": 90.1,
                },
                "Words": [
                    {"Word": "안녕하세요", "PronunciationAssessment": {"AccuracyScore": 88.0}}
                ],
            }
        ],
    }


def llm_payload(content: str, tokens_in: int = 100, tokens_out: int = 50) -> dict:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out},
    }


VALID_TURN_JSON = json.dumps(
    {
        "ai_response_hangul": "안녕하세요! 뭐 드릴까요?",
        "ai_response_romanized": "annyeonghaseyo! mwo deurilkkayo?",
        "ai_response_english": "Hello! What can I get you?",
        "contextual_correction": "",
    }
)


# --- Azure ------------------------------------------------------------------


@respx.mock
async def test_azure_parses_scores(http):
    respx.mock.post(AZURE_URL).mock(return_value=httpx.Response(200, json=azure_payload()))
    client = AzurePronunciationClient(http, key="k", region="koreacentral")

    scores = await client.assess(b"RIFF...", "안녕하세요")

    assert scores.overall == 90.1
    assert scores.recognized_text == "안녕하세요"
    assert scores.words[0]["Word"] == "안녕하세요"


@respx.mock
async def test_azure_no_speech_is_client_presentable_error(http):
    respx.mock.post(AZURE_URL).mock(
        return_value=httpx.Response(200, json={"RecognitionStatus": "NoMatch"})
    )
    client = AzurePronunciationClient(http, key="k", region="koreacentral")
    with pytest.raises(AIServiceError, match="couldn't hear"):
        await client.assess(b"...", "안녕하세요")


async def test_azure_unconfigured_raises_503(http):
    client = AzurePronunciationClient(http, key="", region="")
    with pytest.raises(ServiceUnavailableError):
        await client.assess(b"...", "안녕하세요")


@respx.mock
async def test_azure_retries_then_gives_up(http):
    route = respx.mock.post(AZURE_URL).mock(return_value=httpx.Response(503))
    client = AzurePronunciationClient(http, key="k", region="koreacentral")
    with pytest.raises(AIServiceUnavailableError):
        await client.assess(b"...", "안녕하세요")
    assert route.call_count == 2


# --- ASR ----------------------------------------------------------------------


@respx.mock
async def test_asr_returns_transcript(http):
    respx.mock.post(ASR_URL).mock(
        return_value=httpx.Response(200, json={"text": " 아이스 아메리카노 주세요 "})
    )
    client = NemotronASRClient(http, api_key="k", url=ASR_URL)
    assert await client.transcribe(b"audio") == "아이스 아메리카노 주세요"


@respx.mock
async def test_asr_bad_payload_raises(http):
    respx.mock.post(ASR_URL).mock(return_value=httpx.Response(200, json={"nope": 1}))
    client = NemotronASRClient(http, api_key="k", url=ASR_URL)
    with pytest.raises(AIServiceError):
        await client.transcribe(b"audio")


# --- Llama chat -----------------------------------------------------------------


@respx.mock
async def test_llama_valid_turn_first_try(http):
    respx.mock.post(LLM_URL).mock(
        return_value=httpx.Response(200, json=llm_payload(VALID_TURN_JSON))
    )
    client = LlamaChatClient(http, api_key="k", url=LLM_URL, model="llama")

    turn, usage = await client.next_turn("system", [ChatMessage(role="user", content="안녕하세요")])

    assert turn.ai_response_hangul.startswith("안녕하세요")
    assert usage.tokens_in == 100
    assert usage.tokens_out == 50


@respx.mock
async def test_llama_repairs_invalid_json_once(http):
    route = respx.mock.post(LLM_URL)
    route.side_effect = [
        httpx.Response(200, json=llm_payload("Sure! Here is my reply:")),
        httpx.Response(200, json=llm_payload(VALID_TURN_JSON)),
    ]
    client = LlamaChatClient(http, api_key="k", url=LLM_URL, model="llama")

    turn, usage = await client.next_turn("system", [ChatMessage(role="user", content="hi")])

    assert turn.ai_response_english == "Hello! What can I get you?"
    assert usage.tokens_in == 200  # both calls metered
    repair_body = json.loads(route.calls[1].request.content)
    assert repair_body["messages"][-1]["content"].startswith("Your last reply was not valid JSON")


@respx.mock
async def test_llama_falls_back_in_character_after_two_failures(http):
    respx.mock.post(LLM_URL).mock(
        return_value=httpx.Response(200, json=llm_payload("still not json"))
    )
    client = LlamaChatClient(http, api_key="k", url=LLM_URL, model="llama")

    turn, _ = await client.next_turn("system", [ChatMessage(role="user", content="hi")])

    assert turn == FALLBACK_TURN


@respx.mock
async def test_llama_rejects_extra_keys_via_repair(http):
    bad = json.dumps({**json.loads(VALID_TURN_JSON), "extra_key": "x"})
    route = respx.mock.post(LLM_URL)
    route.side_effect = [
        httpx.Response(200, json=llm_payload(bad)),
        httpx.Response(200, json=llm_payload(VALID_TURN_JSON)),
    ]
    client = LlamaChatClient(http, api_key="k", url=LLM_URL, model="llama")

    turn, _ = await client.next_turn("system", [ChatMessage(role="user", content="hi")])
    assert turn.contextual_correction == ""
    assert route.call_count == 2


@respx.mock
async def test_llama_windows_transcript_to_12_turns(http):
    route = respx.mock.post(LLM_URL).mock(
        return_value=httpx.Response(200, json=llm_payload(VALID_TURN_JSON))
    )
    client = LlamaChatClient(http, api_key="k", url=LLM_URL, model="llama")
    transcript = [
        ChatMessage(role="user" if i % 2 == 0 else "assistant", content=f"turn {i}")
        for i in range(30)
    ]

    await client.next_turn("system", transcript)

    body = json.loads(route.calls[0].request.content)
    assert len(body["messages"]) == 13  # system + last 12
    assert body["messages"][1]["content"] == "turn 18"


# --- TTS ---------------------------------------------------------------------


@respx.mock
async def test_tts_returns_audio_bytes(http):
    respx.mock.post(TTS_URL).mock(
        return_value=httpx.Response(200, content=b"ID3mp3bytes")
    )
    client = TTSClient(http, api_key="k", url=TTS_URL, voice="ko-female")
    assert await client.synthesize("안녕하세요") == b"ID3mp3bytes"


@respx.mock
async def test_tts_empty_audio_raises(http):
    respx.mock.post(TTS_URL).mock(return_value=httpx.Response(200, content=b""))
    client = TTSClient(http, api_key="k", url=TTS_URL, voice="ko-female")
    with pytest.raises(AIServiceError):
        await client.synthesize("안녕하세요")


# --- Vision --------------------------------------------------------------------


@respx.mock
async def test_vision_parses_scores(http):
    verdict = json.dumps(
        {
            "proportion_score": 70,
            "stroke_score": 65,
            "legibility_score": 80,
            "overall_score": 72,
            "feedback": "Nice balance — make the ㅇ rounder.",
        }
    )
    respx.mock.post(LLM_URL).mock(return_value=httpx.Response(200, json=llm_payload(verdict)))
    client = NemotronVisionClient(http, api_key="k", url=LLM_URL, model="nemotron-vl")

    scores = await client.assess_handwriting("aGk=", "안녕")

    assert scores.overall_score == 72
    assert "rounder" in scores.feedback


@respx.mock
async def test_vision_gives_up_after_repair_fails(http):
    respx.mock.post(LLM_URL).mock(
        return_value=httpx.Response(200, json=llm_payload("I think it looks great!"))
    )
    client = NemotronVisionClient(http, api_key="k", url=LLM_URL, model="nemotron-vl")
    with pytest.raises(AIServiceError):
        await client.assess_handwriting("aGk=", "안녕")
