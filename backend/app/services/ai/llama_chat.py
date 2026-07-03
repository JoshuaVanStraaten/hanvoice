"""Llama chat client for scenario conversations.

Implements the integration contract from
``prompts/scenarios/cafe_iced_americano_v1.md``:

- system prompt + alternating turns, windowed to the last 12;
- assistant history is replayed as the raw JSON the model produced (keeps it
  anchored to the format);
- strict 4-key validation with exactly one repair retry;
- on repeated failure, a canned in-character fallback so the learner's flow
  never breaks.
"""

import json
from typing import Any

import httpx
import structlog
from pydantic import ValidationError

from app.core.errors import ServiceUnavailableError
from app.schemas.conversation import BaristaTurn, ChatMessage, TokenUsage
from app.services.ai.base import post_with_retry

logger = structlog.get_logger(__name__)

_PROVIDER = "llama-chat"
_TRANSCRIPT_WINDOW = 12

FALLBACK_TURN = BaristaTurn(
    ai_response_hangul="죄송해요, 다시 한 번 말씀해 주시겠어요?",
    ai_response_romanized="joesonghaeyo, dasi han beon malsseumhae jusigesseoyo?",
    ai_response_english="Sorry, could you say that one more time?",
    contextual_correction="",
)

_REPAIR_MESSAGE = (
    "Your last reply was not valid JSON. Reply again with only the JSON object "
    "using exactly the 4 required keys."
)


class LlamaChatClient:
    def __init__(self, http: httpx.AsyncClient, api_key: str, url: str, model: str):
        self._http = http
        self._api_key = api_key
        self._url = url
        self._model = model

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def next_turn(
        self, system_prompt: str, transcript: list[ChatMessage]
    ) -> tuple[BaristaTurn, TokenUsage]:
        if not self.is_configured:
            raise ServiceUnavailableError("Conversation is not configured.")

        messages = self._build_messages(system_prompt, transcript)
        usage = TokenUsage()

        raw, first_usage = await self._complete(messages)
        usage.tokens_in += first_usage.tokens_in
        usage.tokens_out += first_usage.tokens_out

        turn = self._parse(raw)
        if turn is not None:
            return turn, usage

        logger.warning("llama_invalid_json_retrying", raw=raw[:200])
        repair_messages = [
            *messages,
            {"role": "assistant", "content": raw},
            {"role": "user", "content": _REPAIR_MESSAGE},
        ]
        raw, retry_usage = await self._complete(repair_messages)
        usage.tokens_in += retry_usage.tokens_in
        usage.tokens_out += retry_usage.tokens_out

        turn = self._parse(raw)
        if turn is not None:
            return turn, usage

        logger.error("llama_invalid_json_fallback", raw=raw[:500])
        return FALLBACK_TURN, usage

    def _build_messages(
        self, system_prompt: str, transcript: list[ChatMessage]
    ) -> list[dict[str, str]]:
        windowed = transcript[-_TRANSCRIPT_WINDOW:]
        return [
            {"role": "system", "content": system_prompt},
            *({"role": m.role, "content": m.content} for m in windowed),
        ]

    async def _complete(self, messages: list[dict[str, str]]) -> tuple[str, TokenUsage]:
        response = await post_with_retry(
            self._http,
            self._url,
            provider=_PROVIDER,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": messages,
                "temperature": 0.6,
                "max_tokens": 220,
            },
            timeout=45.0,
        )
        payload = response.json()
        content = str(payload["choices"][0]["message"]["content"])
        usage: dict[str, Any] = payload.get("usage") or {}
        return content, TokenUsage(
            tokens_in=int(usage.get("prompt_tokens", 0)),
            tokens_out=int(usage.get("completion_tokens", 0)),
        )

    @staticmethod
    def _parse(raw: str) -> BaristaTurn | None:
        text = raw.strip()
        # Tolerate accidental code fences without weakening key validation.
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        try:
            return BaristaTurn.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError):
            return None
