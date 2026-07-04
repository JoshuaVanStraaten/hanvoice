"""Text-to-speech via Azure neural voices.

Azure was chosen over NVIDIA's Magpie for v1: Magpie is served gRPC-only
(Riva), while Azure TTS is one REST call on the same key we already hold for
pronunciation assessment, with strong Korean neural voices.
"""

from xml.sax.saxutils import escape

import httpx

from app.core.errors import ServiceUnavailableError
from app.services.ai.base import AIServiceError, post_with_retry

_PROVIDER = "tts"
_OUTPUT_FORMAT = "audio-24khz-48kbitrate-mono-mp3"


class TTSClient:
    def __init__(self, http: httpx.AsyncClient, key: str, region: str, voice: str):
        self._http = http
        self._key = key
        self._region = region
        self._voice = voice

    @property
    def is_configured(self) -> bool:
        return bool(self._key and self._region)

    async def synthesize(self, text: str) -> bytes:
        if not self.is_configured:
            raise ServiceUnavailableError("Text-to-speech is not configured.")

        ssml = (
            f"<speak version='1.0' xml:lang='ko-KR'>"
            f"<voice name='{self._voice}'>{escape(text)}</voice>"
            f"</speak>"
        )
        response = await post_with_retry(
            self._http,
            f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/v1",
            provider=_PROVIDER,
            headers={
                "Ocp-Apim-Subscription-Key": self._key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": _OUTPUT_FORMAT,
                "User-Agent": "hanvoice-backend",
            },
            content=ssml.encode("utf-8"),
            timeout=30.0,
        )
        if not response.content:
            raise AIServiceError("TTS returned empty audio.")
        return response.content
