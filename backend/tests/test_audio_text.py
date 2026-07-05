"""The jamo carrier map and per-block audio whitelisting.

Bare jamo aren't pronounceable alone, so teaching audio speaks a carrier
syllable (ㄱ → 가, ㅏ → 아). The allowed-texts helper is what keeps the TTS
endpoint bounded to authored content.
"""

from app.services.audio_text import allowed_audio_texts, audio_text_for


def test_consonants_map_to_a_carrier_syllable():
    assert audio_text_for("ㄱ") == "가"
    assert audio_text_for("ㅁ") == "마"
    assert audio_text_for("ㅎ") == "하"


def test_vowels_map_to_silent_ieung_carrier():
    assert audio_text_for("ㅏ") == "아"
    assert audio_text_for("ㅡ") == "으"
    assert audio_text_for("ㅣ") == "이"


def test_full_syllables_pass_through():
    assert audio_text_for("한") == "한"
    assert audio_text_for("한국") == "한국"


def test_explain_payload_collects_chars_and_examples_with_override():
    payload = {
        "segments": [
            {"type": "chars", "items": [{"ko": "ㄱ"}, {"ko": "ㅈ", "audio": "즈"}]},
            {"type": "example", "items": [{"ko": "한국"}]},
            {"type": "text", "body": "ignored"},
        ]
    }
    assert allowed_audio_texts("explain", payload) == {"가", "즈", "한국"}


def test_write_payload_uses_target_with_override():
    assert allowed_audio_texts("write", {"target": "ㄱ"}) == {"가"}
    assert allowed_audio_texts("write", {"target": "ㄱ", "audio": "그"}) == {"그"}


def test_other_kinds_have_no_audio():
    assert allowed_audio_texts("quiz", {"question": "?"}) == set()
    assert allowed_audio_texts("speak", {}) == set()


def test_malformed_payloads_yield_nothing():
    assert allowed_audio_texts("explain", {}) == set()
    assert allowed_audio_texts("explain", {"segments": [{"type": "chars"}]}) == set()
    assert allowed_audio_texts("write", {}) == set()
