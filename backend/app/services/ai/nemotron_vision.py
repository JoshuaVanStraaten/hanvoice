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

_INSTRUCTION = """You are a Korean handwriting examiner. The image shows a beginner's attempt at
writing: {target} (drawn with a mouse or fingertip, so wobble is expected and
not penalized).

Work in two steps.

STEP 1 — Look carefully. The target {target} is composed of specific jamo
(consonants/vowels). For each jamo of the target, decide whether a stroke
group in the image plausibly matches it: its SHAPE (circle vs line vs angle)
and its POSITION in the syllable block both matter.

STEP 2 — Score 0-100 based only on what you actually observed:
- legibility_score: what fraction of the target's jamo are recognizably
  present in roughly correct positions? All present = 80+. Half = about 50.
  None recognizable = below 20.
- stroke_score: are the individual strokes the right kinds of shapes?
- proportion_score: is the layout of components balanced like the target?
- overall_score: weigh legibility most.

Reply with ONLY a JSON object, no markdown. Keys, in this order:
components_seen (string), proportion_score (integer 0-100),
stroke_score (integer 0-100), legibility_score (integer 0-100),
overall_score (integer 0-100), feedback (string).
Never copy example numbers — every score must come from your own observation.

- components_seen: one short sentence listing which jamo of {target} you can
  and cannot find in the image.
- feedback: ONE friendly English sentence naming the most important fix.
Honest scores help the learner: do not inflate, and do not give identical
scores to different drawings."""

_REPAIR_MESSAGE = (
    "Your last reply was not valid JSON. Reply again with only the JSON object "
    "and exactly the required keys (components_seen, proportion_score, "
    "stroke_score, legibility_score, overall_score, feedback)."
)

_ZERO_RETRY_MESSAGE = (
    "You scored every dimension 0, which contradicts your own observation. "
    "Look at the image again and score each dimension honestly per the rubric: "
    "any recognizable stroke earns points, and only an empty canvas scores 0. "
    "Reply with only the JSON object."
)


def _all_zero(scores: HandwritingScores) -> bool:
    return (
        scores.proportion_score == 0
        and scores.stroke_score == 0
        and scores.legibility_score == 0
        and scores.overall_score == 0
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

        last_scores: HandwritingScores | None = None
        for attempt in (1, 2):
            raw = await self._complete(messages)
            scores = self._parse(raw)
            if scores is not None and not _all_zero(scores):
                return scores
            last_scores = scores
            if attempt == 1:
                # Two observed lapse modes: non-JSON replies, and the model
                # echoing zeros instead of scoring. One nudge fixes most.
                nudge = _REPAIR_MESSAGE if scores is None else _ZERO_RETRY_MESSAGE
                logger.warning(
                    "vision_retrying",
                    reason="invalid_json" if scores is None else "all_zero",
                    raw=raw[:200],
                )
                messages += [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": nudge},
                ]

        if last_scores is not None:
            # Still all zeros after a retry — accept it; an empty canvas or
            # pure scribble can legitimately score nothing.
            return last_scores
        logger.error("vision_invalid_json_giving_up")
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
                "temperature": 0.0,
                "max_tokens": 400,
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
