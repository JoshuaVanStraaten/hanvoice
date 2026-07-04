"""Azure speech-to-text for conversation turns.

Same short-audio endpoint the pronunciation client uses, without the
assessment header. Chosen over NVIDIA ASR for v1: NVIDIA's speech models are
served gRPC-only (Riva), while this is one REST call on the key we already
hold, and Azure's Korean recognition is strong.
"""

from typing import Any

import httpx
import structlog

from app.core.errors import ServiceUnavailableError
from app.services.ai.base import AIServiceError, post_with_retry

_PROVIDER = "azure-stt"

logger = structlog.get_logger(__name__)


class AzureSTTClient:
    def __init__(self, http: httpx.AsyncClient, key: str, region: str):
        self._http = http
        self._key = key
        self._region = region

    @property
    def is_configured(self) -> bool:
        return bool(self._key and self._region)

    async def transcribe(self, audio: bytes, content_type: str = "audio/wav") -> str:
        if not self.is_configured:
            raise ServiceUnavailableError("Speech recognition is not configured.")

        url = (
            f"https://{self._region}.stt.speech.microsoft.com"
            "/speech/recognition/conversation/cognitiveservices/v1"
        )
        response = await post_with_retry(
            self._http,
            url,
            provider=_PROVIDER,
            params={"language": "ko-KR"},
            headers={
                "Ocp-Apim-Subscription-Key": self._key,
                "Content-Type": content_type,
                "Accept": "application/json",
            },
            content=audio,
            timeout=30.0,
        )
        payload: dict[str, Any] = response.json()
        status = payload.get("RecognitionStatus")
        if status != "Success":
            logger.warning("azure_stt_no_match", status=status)
            raise AIServiceError(
                "We couldn't make out any speech — try again a bit closer to the mic."
            )
        text = payload.get("DisplayText")
        if not isinstance(text, str) or not text.strip():
            raise AIServiceError("Speech recognition returned an unexpected payload.")
        return text.strip()
