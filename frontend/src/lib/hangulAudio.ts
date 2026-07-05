/** What a taught glyph *sounds like*. Bare jamo aren't pronounceable alone,
 * so teaching audio speaks a carrier syllable: consonants ride ㅏ (ㄱ → 가,
 * the 가나다 drill), vowels ride the silent ㅇ (ㅏ → 아). Full syllables pass
 * through. Mirrors the backend map in `app/services/audio_text.py` — the
 * backend only synthesizes texts derived by this same rule, so the two tables
 * must stay in sync. Payload `audio` overrides win. */

const CARRIER: Record<string, string> = {
  // 14 basic consonants → ㅏ-carrier syllables
  ㄱ: "가", ㄴ: "나", ㄷ: "다", ㄹ: "라", ㅁ: "마",
  ㅂ: "바", ㅅ: "사", ㅇ: "아", ㅈ: "자", ㅊ: "차",
  ㅋ: "카", ㅌ: "타", ㅍ: "파", ㅎ: "하",
  // 10 basic vowels → silent-ㅇ carrier syllables
  ㅏ: "아", ㅑ: "야", ㅓ: "어", ㅕ: "여", ㅗ: "오",
  ㅛ: "요", ㅜ: "우", ㅠ: "유", ㅡ: "으", ㅣ: "이",
};

/** The text the backend should speak for a taught glyph. */
export function audioTextFor(glyph: string, override?: string): string {
  return override || CARRIER[glyph] || glyph;
}

/** True when the played audio differs from the glyph (drives "in 가" copy). */
export function isCarrier(glyph: string, override?: string): boolean {
  return audioTextFor(glyph, override) !== glyph;
}
