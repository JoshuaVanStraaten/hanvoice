"""What a teaching glyph *sounds like*, and which texts a block may speak.

Bare jamo aren't pronounceable alone, so cards teach with carrier syllables:
consonants ride ㅏ (ㄱ → 가, the 가나다 drill), vowels ride the silent ㅇ
(ㅏ → 아). Letter names (기역, 니은) are deliberately not used — a beginner
needs the sound, not the name. Full syllables and words pass through.

``allowed_audio_texts`` is the whitelist that keeps the block audio endpoint
bounded to authored content: it derives every speakable string from the
block's own payload, so free text can never reach TTS. Payload items may set
``audio`` to override the map (future content; today's seed needs none).
"""

from typing import Any

_CARRIER: dict[str, str] = {
    # 14 basic consonants → ㅏ-carrier syllables
    "ㄱ": "가", "ㄴ": "나", "ㄷ": "다", "ㄹ": "라", "ㅁ": "마",
    "ㅂ": "바", "ㅅ": "사", "ㅇ": "아", "ㅈ": "자", "ㅊ": "차",
    "ㅋ": "카", "ㅌ": "타", "ㅍ": "파", "ㅎ": "하",
    # 10 basic vowels → silent-ㅇ carrier syllables
    "ㅏ": "아", "ㅑ": "야", "ㅓ": "어", "ㅕ": "여", "ㅗ": "오",
    "ㅛ": "요", "ㅜ": "우", "ㅠ": "유", "ㅡ": "으", "ㅣ": "이",
}


def audio_text_for(glyph: str, override: str | None = None) -> str:
    """The text TTS should speak for a taught glyph."""
    if override:
        return override
    return _CARRIER.get(glyph, glyph)


def _item_text(item: Any, key: str) -> str | None:
    if not isinstance(item, dict):
        return None
    glyph = item.get(key)
    if not isinstance(glyph, str) or not glyph:
        return None
    override = item.get("audio")
    return audio_text_for(glyph, override if isinstance(override, str) else None)


def allowed_audio_texts(kind: str, payload: dict[str, Any]) -> set[str]:
    """Every text this block is allowed to synthesize."""
    texts: set[str] = set()
    if kind == "explain":
        segments = payload.get("segments")
        for segment in segments if isinstance(segments, list) else []:
            if not isinstance(segment, dict):
                continue
            if segment.get("type") in ("chars", "example"):
                items = segment.get("items")
                for item in items if isinstance(items, list) else []:
                    text = _item_text(item, "ko")
                    if text:
                        texts.add(text)
    elif kind == "write":
        text = _item_text(payload, "target")
        if text:
            texts.add(text)
    return texts
