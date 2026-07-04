"""Azure Pronunciation Assessment client (short-audio REST API).

The assessment config rides in the ``Pronunciation-Assessment`` header as
base64 JSON alongside the raw audio body. Korean = ``ko-KR``.
"""

import base64
import json
from typing import Any

import httpx
import structlog

from app.core.errors import ServiceUnavailableError
from app.schemas.pronunciation import PronunciationScores
from app.services.ai.base import AIServiceError, post_with_retry

_PROVIDER = "azure-pronunciation"

logger = structlog.get_logger(__name__)


def _normalize_word(word: dict[str, Any]) -> dict[str, Any]:
    """Both API shapes → the nested one the stored payload/frontend expect."""
    assessment = word.get("PronunciationAssessment", word)
    return {
        "Word": word.get("Word", ""),
        "PronunciationAssessment": {
            "AccuracyScore": assessment.get("AccuracyScore"),
            "ErrorType": assessment.get("ErrorType"),
        },
    }


class AzurePronunciationClient:
    def __init__(self, http: httpx.AsyncClient, key: str, region: str):
        self._http = http
        self._key = key
        self._region = region

    @property
    def is_configured(self) -> bool:
        return bool(self._key and self._region)

    async def assess(
        self, audio: bytes, reference_text: str, content_type: str = "audio/wav"
    ) -> PronunciationScores:
        if not self.is_configured:
            raise ServiceUnavailableError("Pronunciation assessment is not configured.")

        assessment_config = base64.b64encode(
            json.dumps(
                {
                    "ReferenceText": reference_text,
                    "GradingSystem": "HundredMark",
                    "Granularity": "Phoneme",
                    "Dimension": "Comprehensive",
                }
            ).encode()
        ).decode()

        url = (
            f"https://{self._region}.stt.speech.microsoft.com"
            "/speech/recognition/conversation/cognitiveservices/v1"
        )
        response = await post_with_retry(
            self._http,
            url,
            provider=_PROVIDER,
            # format=detailed is required: the default "simple" response has
            # no NBest array and silently drops the assessment scores.
            params={"language": "ko-KR", "format": "detailed"},
            headers={
                "Ocp-Apim-Subscription-Key": self._key,
                "Pronunciation-Assessment": assessment_config,
                "Content-Type": content_type,
                "Accept": "application/json",
            },
            content=audio,
            timeout=30.0,
        )
        return self._parse(response.json())

    @staticmethod
    def _parse(payload: dict[str, Any]) -> PronunciationScores:
        status = payload.get("RecognitionStatus")
        if status != "Success":
            logger.warning("azure_recognition_failed", status=status)
            raise AIServiceError(
                "We couldn't hear any speech in that recording — try again a bit louder."
            )
        try:
            best = payload["NBest"][0]
            # The short-audio v1 endpoint returns scores flat on the NBest
            # entry; newer API versions nest them under
            # "PronunciationAssessment". Accept both.
            scores = best.get("PronunciationAssessment", best)
            return PronunciationScores(
                accuracy=scores["AccuracyScore"],
                fluency=scores["FluencyScore"],
                completeness=scores["CompletenessScore"],
                overall=scores["PronScore"],
                recognized_text=best.get("Display", ""),
                words=[_normalize_word(word) for word in best.get("Words", [])],
            )
        except (KeyError, IndexError) as exc:
            logger.error("azure_payload_unexpected", keys=sorted(payload.keys()))
            raise AIServiceError("Azure returned an unexpected payload.") from exc
