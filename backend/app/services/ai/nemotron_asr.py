"""NVIDIA Nemotron ASR client (OpenAI-compatible transcription endpoint)."""

import httpx

from app.core.errors import ServiceUnavailableError
from app.services.ai.base import AIServiceError, post_with_retry

_PROVIDER = "nemotron-asr"


class NemotronASRClient:
    def __init__(self, http: httpx.AsyncClient, api_key: str, url: str):
        self._http = http
        self._api_key = api_key
        self._url = url

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def transcribe(self, audio: bytes, content_type: str = "audio/webm") -> str:
        if not self.is_configured:
            raise ServiceUnavailableError("Speech recognition is not configured.")

        extension = content_type.split("/")[-1].split(";")[0] or "webm"
        response = await post_with_retry(
            self._http,
            self._url,
            provider=_PROVIDER,
            headers={"Authorization": f"Bearer {self._api_key}"},
            files={"file": (f"turn.{extension}", audio, content_type)},
            data={"language": "ko"},
            timeout=30.0,
        )
        payload = response.json()
        text = payload.get("text")
        if not isinstance(text, str):
            raise AIServiceError("ASR returned an unexpected payload.")
        return text.strip()
