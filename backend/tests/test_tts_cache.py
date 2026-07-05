"""The in-process TTS LRU: the whole curriculum speaks ~40 distinct strings,
so after warm-up almost every listen is free."""

import asyncio

from app.services import tts_cache


class FakeTts:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def synthesize(self, text: str) -> bytes:
        self.calls.append(text)
        return f"mp3:{text}".encode()


def synth(tts: FakeTts, text: str) -> bytes:
    return asyncio.run(tts_cache.synthesize_cached(tts, text))  # type: ignore[arg-type]


def test_repeat_text_synthesizes_once():
    tts_cache.clear_cache()
    tts = FakeTts()
    first = synth(tts, "가")
    second = synth(tts, "가")
    assert first == second == "mp3:가".encode()
    assert tts.calls == ["가"]


def test_distinct_texts_synthesize_separately():
    tts_cache.clear_cache()
    tts = FakeTts()
    synth(tts, "가")
    synth(tts, "나")
    assert tts.calls == ["가", "나"]


def test_capacity_evicts_least_recently_used(monkeypatch):
    tts_cache.clear_cache()
    monkeypatch.setattr(tts_cache, "_MAX_ENTRIES", 2)
    tts = FakeTts()
    synth(tts, "가")
    synth(tts, "나")
    synth(tts, "가")  # refresh 가 — 나 is now the oldest
    synth(tts, "다")  # evicts 나
    synth(tts, "가")  # still cached
    synth(tts, "나")  # gone — synthesized again
    assert tts.calls == ["가", "나", "다", "나"]
