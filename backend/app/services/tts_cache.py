"""In-process LRU in front of Azure TTS.

Teaching audio is a tiny closed vocabulary (carrier syllables, phrase text),
so one process-wide dict turns almost every listen into a cache hit. Bytes
per entry are ~10-30 KB of mp3; 256 entries is comfortably the whole
curriculum with room to grow. Per-process only — with one uvicorn worker
(deployment requirement for the rate limiter) that is the whole app.
"""

from collections import OrderedDict

from app.services.ai.tts import TTSClient

_MAX_ENTRIES = 256
_cache: OrderedDict[str, bytes] = OrderedDict()


async def synthesize_cached(tts: TTSClient, text: str) -> bytes:
    cached = _cache.get(text)
    if cached is not None:
        _cache.move_to_end(text)
        return cached
    audio = await tts.synthesize(text)
    _cache[text] = audio
    if len(_cache) > _MAX_ENTRIES:
        _cache.popitem(last=False)
    return audio


def clear_cache() -> None:
    _cache.clear()
