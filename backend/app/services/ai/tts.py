"""Text-to-speech client (Magpie/Chatterbox via OpenAI-compatible endpoint)."""

import httpx

from app.core.errors import ServiceUnavailableError
from app.services.ai.base import AIServiceError, post_with_retry

_PROVIDER = "tts"


class TTSClient:
    def __init__(self, http: httpx.AsyncClient, api_key: str, url: str, voice: str):
        self._http = http
        self._api_key = api_key
        self._url = url
        self._voice = voice

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def synthesize(self, text: str) -> bytes:
        if not self.is_configured:
            raise ServiceUnavailableError("Text-to-speech is not configured.")

        response = await post_with_retry(
            self._http,
            self._url,
            provider=_PROVIDER,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"input": text, "voice": self._voice, "response_format": "mp3"},
            timeout=30.0,
        )
        if not response.content:
            raise AIServiceError("TTS returned empty audio.")
        return response.content
