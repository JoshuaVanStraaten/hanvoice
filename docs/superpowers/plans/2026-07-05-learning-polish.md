# Learning-Experience Polish Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Audio on every teaching surface, silence-detection auto-stop recording, and a motion/identity visual overhaul of the block player.

**Architecture:** A block-scoped TTS endpoint validates requested text against the block's own payload through a fixed jamoâ†’carrier-syllable map (code, not data), with an in-process LRU in front of Azure TTS. Auto-stop is a pure silence-gate state machine fed by `useRecorder`'s existing rAF meter loop. The visual pass is CSS-first (tokens + keyframes), no animation library.

**Tech Stack:** FastAPI + respx tests; React 19 + Tailwind v4 tokens + vitest; Azure neural TTS (SunHi).

**Spec:** `docs/superpowers/specs/2026-07-05-learning-polish-design.md`

Run backend gates with `backend/.venv/Scripts/python -m pytest|ruff|mypy` (Windows venv).
Frontend gates: `npm run lint / typecheck / test / build` in `frontend/`.

---

### Task 1: Backend carrier map + allowed-text helper

**Files:**
- Create: `backend/app/services/audio_text.py`
- Test: `backend/tests/test_audio_text.py`

- [ ] **Step 1: Failing tests** â€” pin the carrier table and payload extraction:

```python
from app.services.audio_text import allowed_audio_texts, audio_text_for

def test_consonants_map_to_a_carrier_syllable():
    assert audio_text_for("ã„±") == "ê°€"
    assert audio_text_for("ã…") == "ë§ˆ"

def test_vowels_map_to_silent_ieung_carrier():
    assert audio_text_for("ã…") == "ì•„"
    assert audio_text_for("ã…¡") == "ìœ¼"

def test_full_syllables_pass_through():
    assert audio_text_for("í•œ") == "í•œ"

def test_explain_payload_collects_chars_and_examples_with_override():
    payload = {"segments": [
        {"type": "chars", "items": [{"ko": "ã„±"}, {"ko": "ã…ˆ", "audio": "ì¦ˆ"}]},
        {"type": "example", "items": [{"ko": "í•œêµ­"}]},
        {"type": "text", "body": "ignored"},
    ]}
    assert allowed_audio_texts("explain", payload) == {"ê°€", "ì¦ˆ", "í•œêµ­"}

def test_write_payload_uses_target_with_override():
    assert allowed_audio_texts("write", {"target": "ã„±"}) == {"ê°€"}
    assert allowed_audio_texts("write", {"target": "ã„±", "audio": "ê·¸"}) == {"ê·¸"}

def test_other_kinds_have_no_audio():
    assert allowed_audio_texts("quiz", {"question": "?"}) == set()
```

- [ ] **Step 2: Run, verify fail** (`ImportError`).
- [ ] **Step 3: Implement** â€” 14 consonants â†’ ã…-carrier (ê°€ë‚˜ë‹¤ë¼ë§ˆë°”ì‚¬ì•„ìžì°¨ì¹´íƒ€íŒŒí•˜), 10 vowels â†’ silent-ã…‡ carrier (ì•„ì–´ì˜¤ìš°ìœ¼ì´ + ì•¼ì—¬ìš”ìœ ), dict keyed by jamo; `audio_text_for(glyph) = CARRIER.get(glyph, glyph)`; `allowed_audio_texts(kind, payload)` walks explain segments (chars + example items, `item.audio` override) and write payloads (`payload.audio ?? carrier(target)`).
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** `feat(api): jamo carrier map + per-block allowed audio texts`

### Task 2: TTS LRU cache

**Files:**
- Create: `backend/app/services/tts_cache.py`
- Test: `backend/tests/test_tts_cache.py`

- [ ] **Step 1: Failing test** â€” fake TTS client with call counter; two calls for same text hit synth once; capacity evicts oldest; distinct texts synth separately.
- [ ] **Step 2â€“4:** `OrderedDict`-based module cache, `async def synthesize_cached(tts, text) -> bytes`, `_MAX_ENTRIES = 256`, `move_to_end` on hit, `clear_cache()` for tests. Wire `pronunciation.get_phrase_audio` through it too.
- [ ] **Step 5: Commit** `feat(api): in-process LRU for TTS synthesis`

### Task 3: Block audio endpoint

**Files:**
- Modify: `backend/app/api/routes/content.py`
- Test: `backend/tests/test_lesson_blocks.py` (append)

- [ ] **Step 1: Failing tests** (respx; TTS_URL as in `test_pronunciation_route.py`):

```python
@respx.mock
def test_block_audio_synthesizes_carrier_for_write_target(client):
    mock_get("lesson_blocks", [block_row(1, "write", payload={"target": "ã„±", "hint": "â€¦"})])
    mock_get("lessons", [lesson_row()])
    tts = respx.mock.post(TTS_URL).mock(return_value=httpx.Response(200, content=b"ID3mp3"))
    response = client.get("/api/lessons/blocks/1/audio?text=ê°€", headers=auth_headers())
    assert response.status_code == 200
    assert "ê°€" in tts.calls[0].request.content.decode()

@respx.mock
def test_block_audio_rejects_text_not_in_block(client):  # 400, no TTS call
@respx.mock
def test_block_audio_unpublished_lesson_404(client):
@respx.mock
def test_block_audio_repeat_request_hits_cache(client):  # tts.call_count == 1 after 2 GETs
```

(Autouse-clear the TTS cache between tests via a conftest fixture.)

- [ ] **Step 2â€“4:** Route `GET /lessons/blocks/{block_id}/audio` (rate_limit 30/60s, `Tts` dep): get_block â†’ get_published_lesson_by_id â†’ `text` query param must be in `allowed_audio_texts(kind, payload)` else `BadRequestError` â†’ `synthesize_cached` â†’ `{"audio_base64": â€¦}`. Not quota-metered.
- [ ] **Step 5: Commit** `feat(api): block-scoped audio endpoint for teaching surfaces`

### Task 4: Frontend carrier map mirror

**Files:**
- Create: `frontend/src/lib/hangulAudio.ts`
- Test: `frontend/src/lib/hangulAudio.test.ts`

- [ ] Steps: failing tests mirroring Task 1 cases (`audioTextFor("ã„±") === "ê°€"`, override param wins, pass-through) + `isCarrier(glyph)` (true when played text â‰  glyph, drives "in ê°€" microcopy). Implement the same 24-entry table. Commit `feat(web): hangul carrier map for teaching audio`.

### Task 5: AudioButton + audio on explain/write surfaces

**Files:**
- Create: `frontend/src/components/AudioButton.tsx` (generalized from `ListenButton`)
- Modify: `frontend/src/components/blocks/SpeakBlock.tsx` (use AudioButton), `ExplainBlock.tsx`, `WriteBlock.tsx`, `frontend/src/lib/types.ts` (optional `audio` on `ExplainCharItem`/`ExplainExampleItem`/`WritePayload`; blocks pass `blockId` down)
- Test: `frontend/src/components/blocks/blocks.test.tsx` (extend)

- [ ] **Step 1: Failing tests** â€” chars card renders a speaker with `aria-label="Hear ã„± (sounds like ê°€)"`; clicking fetches `/lessons/blocks/7/audio?text=ê°€` once, second click plays from cache (mock `apiGet`, stub `Audio`); write block renders speaker for target; example rows render speakers.
- [ ] **Step 2â€“4:** `AudioButton({ label, fetchAudio })` holds the fetched-base64 cache + pending state (lifted from ListenButton, visual identical); SpeakBlock passes phrase fetcher; Explain/Write pass block fetcher `audioTextFor(item.ko, item.audio)`; microcopy `in ê°€` under card glyph when `isCarrier`. Explain cards keep layout (button under glyph); write block speaker sits beside the target text.
- [ ] **Step 5: Commit** `feat(web): hear every glyph â€” audio buttons on explain and write blocks`

### Task 6: Silence gate (pure logic)

**Files:**
- Create: `frontend/src/lib/silenceGate.ts`
- Test: `frontend/src/lib/silenceGate.test.ts`

- [ ] **Step 1: Failing tests** â€” feed `(level, timestampMs)` samples:
  - stays `armed` below onset (0.15);
  - `hearing` on onset; loud frame resets silence clock;
  - `finishing` with `silenceProgress` growing once level < 0.08;
  - emits `fire` after 2500 ms continuous silence;
  - emits `capDiscard` at maxDurationMs when speech never detected;
  - emits `capFire` at maxDurationMs when speech was detected.
- [ ] **Step 2â€“4:** `createSilenceGate({ maxDurationMs })` returning `{ sample(level, now): GateEvent | null, phase, silenceProgress }`; constants `ONSET = 0.15`, `SILENCE = 0.08`, `SILENCE_WINDOW_MS = 2500` exported for UI copy/tests.
- [ ] **Step 5: Commit** `feat(web): silence-gate state machine for auto-stop`

### Task 7: useRecorder + RecordButton + SpeakBlock auto-stop

**Files:**
- Modify: `frontend/src/hooks/useRecorder.ts`, `frontend/src/components/RecordButton.tsx`, `frontend/src/components/blocks/SpeakBlock.tsx`
- Test: `frontend/src/components/blocks/blocks.test.tsx` (behavioural: auto-submit shown states)

- [ ] **Steps:** `start(options?: { maxDurationMs?, onAutoStop?, onSilentDiscard? })`; gate sampled inside the meter rAF tick; expose `phase` + `silenceProgress`. Hard cap replaces the fixed 30 s timeout (still clamped â‰¤ 30 s). SpeakBlock: `maxDurationMs = clamp(4000 + 1600 Ã— (syllablesâˆ’1), 4000, 12000)` where syllables = Hangul-block count of `phrase.hangul`; `onAutoStop` feeds the existing mutation; `onSilentDiscard` shows "We didn't hear anything â€” try again." RecordButton caption per phase ("Listening â€” speak now" / "Got it â€” pause when you're done" / "Finishingâ€¦" + countdown arc via SVG stroke, `prefers-reduced-motion` â†’ text only). Manual tap-to-stop unchanged.
- [ ] **Commit** `feat(web): recordings stop themselves â€” silence auto-stop with visible state`

### Task 8: Visual overhaul (frontend-design skill governs execution)

**Files:** `frontend/src/index.css` (tokens, keyframes, texture), `frontend/package.json` (fontsource serif display face), `frontend/src/components/ui.tsx` (Skeleton, animated ScoreRing), `frontend/src/components/blocks/*` (celebration), `frontend/src/pages/*` (skeletons, step transition), small new `frontend/src/components/Dojang.tsx`.

- [ ] **8a â€” Identity:** self-hosted Korean serif display face (subset woff2) applied to `.hangul-display`; hanji texture (layered CSS gradients/noise) on `html`; refined card/header polish. Commit.
- [ ] **8b â€” Skeletons:** `Skeleton` primitive + content-shaped loading states for lessons list, lesson player, dashboard, progress; replace `Spinner` at page level (keep Spinner for inline scoring). Test: skeleton renders while pending. Commit.
- [ ] **8c â€” Motion:** step enter transition (directional slide+fade on block index change), ScoreRing stroke draw-in + count-up, list stagger. All gated by `prefers-reduced-motion`. Commit.
- [ ] **8d â€” Dojang pass celebration:** red seal stamp (í†µê³¼) thumps onto the card on pass (speak/write/lesson-complete), paper-settle shadow; reduced-motion â†’ static stamp. Commit.

### Task 9: Gates + docs

- [ ] Backend: ruff + mypy + pytest all green. Frontend: eslint + tsc + vitest + build green.
- [ ] Update `docs/api.md` (new endpoint), `docs/schema.md` (optional `audio` payload field).
- [ ] Commit `docs: block audio endpoint + payload audio field`

### Task 10: Live walkthrough (verify skill)

- [ ] Drive servers per `.claude/skills/verify/SKILL.md`: hear ã…/ã„±/í•œ from lesson 1â€“2 cards; write-block audio; deterministic speak pass via TTS WAV â†’ confirm auto-stop states + dojang; skeletons on cold loads; reduced-motion spot check. Tune silence thresholds if the walkthrough contradicts them.
- [ ] Update `docs/HANDOVER.md` (item 1 done).
