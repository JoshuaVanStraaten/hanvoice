"""Nemotron-VL handwriting assessment.

Sends the learner's canvas (PNG, base64 data URI) with the target Hangul and
asks for a strict JSON verdict. Same resilience pattern as the chat client:
strict parse, one repair retry, then a typed error (handwriting has no
in-character fallback — the UI shows a friendly retry message on 502).
"""

import json

import httpx
import structlog
from pydantic import ValidationError

from app.core.errors import ServiceUnavailableError
from app.schemas.handwriting import HandwritingScores
from app.services.ai.base import AIServiceError, post_with_retry

logger = structlog.get_logger(__name__)

_PROVIDER = "nemotron-vision"

_INSTRUCTION = """You are a strict but encouraging Korean handwriting teacher.
The image shows a learner's handwritten attempt at: {target}

Score it 0-100 on three dimensions and give one short, friendly feedback sentence.
Reply with ONLY a JSON object, no markdown, exactly these keys:
{{"proportion_score": 0, "stroke_score": 0, "legibility_score": 0,
"overall_score": 0, "feedback": ""}}

- proportion_score: are the syllable blocks balanced and evenly sized?
- stroke_score: are strokes placed and shaped correctly?
- legibility_score: could a Korean reader recognize the text?
- overall_score: your overall impression.
- feedback: ONE sentence, specific and encouraging, in English.
If the image does not show an attempt at the target text, score legibility 0 and say so kindly."""

_REPAIR_MESSAGE = (
    "Your last reply was not valid JSON. Reply again with only the JSON object "
    "and exactly the 5 required keys."
)


class NemotronVisionClient:
    def __init__(self, http: httpx.AsyncClient, api_key: str, url: str, model: str):
        self._http = http
        self._api_key = api_key
        self._url = url
        self._model = model

    @property
    def model_version(self) -> str:
        return self._model

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def assess_handwriting(
        self, image_base64: str, target_text: str
    ) -> HandwritingScores:
        if not self.is_configured:
            raise ServiceUnavailableError("Handwriting assessment is not configured.")

        user_content = [
            {"type": "text", "text": _INSTRUCTION.format(target=target_text)},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"},
            },
        ]
        messages: list[dict[str, object]] = [{"role": "user", "content": user_content}]

        raw = await self._complete(messages)
        scores = self._parse(raw)
        if scores is not None:
            return scores

        logger.warning("vision_invalid_json_retrying", raw=raw[:200])
        messages += [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": _REPAIR_MESSAGE},
        ]
        raw = await self._complete(messages)
        scores = self._parse(raw)
        if scores is not None:
            return scores

        logger.error("vision_invalid_json_giving_up", raw=raw[:500])
        raise AIServiceError("Handwriting assessment failed — please try again.")

    async def _complete(self, messages: list[dict[str, object]]) -> str:
        response = await post_with_retry(
            self._http,
            self._url,
            provider=_PROVIDER,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 300,
            },
            timeout=45.0,
        )
        return str(response.json()["choices"][0]["message"]["content"])

    @staticmethod
    def _parse(raw: str) -> HandwritingScores | None:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        try:
            return HandwritingScores.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError):
            return None
