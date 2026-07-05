# Learning-experience polish pass — design

**Date:** 2026-07-05 · **Status:** approved (founder delegated decisions 2026-07-04)
**Scope:** HANDOVER item 1 — three sub-features on the shipped block player. A polish
pass, not a rebuild.

## 1. Audio on every teaching surface

### Pedagogy decision: demo syllables, not letter names

A lesson-1 learner needs the *sound* a letter makes, not its Korean name. Letter
names (ㄱ = 기역) are meta-vocabulary that mislead a beginner about the sound.
So:

- **Consonants** play their ㅏ-carrier syllable: ㄱ → 가, ㄴ → 나, ㅁ → 마 …
  (the standard 가나다 drill order).
- **Vowels** play their silent-ㅇ carrier: ㅏ → 아, ㅓ → 어, ㅡ → 으 …
- **Real syllables and words** (한, 국, 물 …) play as-is.
- When the played text differs from the glyph, the card shows microcopy
  (“in 가”) so the learner knows they’re hearing a carrier syllable.

The jamo → carrier map is a **fixed table in code** (closed set: 24 basic jamo
now, doubles/tense later). Payloads may carry an optional `audio` string that
overrides the map (`{"ko":"ㄱ","audio":"그"}`) for future authored content.
**No data migration needed** — the shipped 62 blocks work through the map and
pass-through.

### API: block-scoped TTS, same bounding as phrases

`GET /api/lessons/blocks/{block_id}/audio?text=<hangul>` → `{"audio_base64": …}`

- Backend loads the block (must belong to a published lesson) and computes the
  block’s **allowed audio set** from its payload:
  - explain: every chars item and example item → `item.audio ?? JAMO_CARRIER[ko] ?? ko`
  - write: `payload.audio ?? JAMO_CARRIER[target] ?? target`
- `text` must be an exact member of that set, else 400. TTS spend stays bounded
  by authored content — the endpoint never synthesizes free text.
- Rate limit 30/min (same as phrase audio); **not quota-metered** — listening is
  learning.
- **In-process LRU cache** (text → mp3 bytes, ~256 entries) in front of the TTS
  client: the whole curriculum uses ~40 distinct strings, so effectively every
  request after warm-up is free. (Phrase audio keeps its existing path;
  the cache wraps synthesis so both benefit.)

Backend mirror of the jamo map lives in `app/services/audio_text.py` (single
source for route validation); frontend mirror in `frontend/src/lib/hangulAudio.ts`
(computes what to request + the “in 가” microcopy). The two must agree — a
backend test pins the table.

### Frontend surfaces

- Generalize `ListenButton` (SpeakBlock) into a shared `components/AudioButton`
  that takes a fetcher + cache key; SpeakBlock keeps its phrase endpoint.
- **Explain chars cards**: speaker button under each glyph.
- **Explain example rows**: speaker button per row (reading practice is
  a teaching surface too — lesson 8 is all examples).
- **Write block**: speaker next to the target glyph (“hear what you’re writing”).
- Failures stay quiet (as today): audio is enrichment, the text remains.

## 2. Auto-stop recording

### Behaviour

State machine inside `useRecorder`’s existing rAF meter loop (no new audio
plumbing):

- `armed` → recording started, no speech yet. If the hard cap passes with no
  speech ever detected: stop, **discard** (don’t submit — a silent clip would
  waste a scored attempt and quota), surface “We didn’t hear anything — try again.”
- `hearing` → level ≥ **0.15** (speech onset). Any loud frame resets the
  silence clock.
- `finishing` → level < **0.08** continuously; after **2.5 s** of silence
  auto-stop fires and the blob is delivered via a new `onAutoStop(blob)` option —
  SpeakBlock routes it into the same submit mutation as manual stop.
- **Hard cap** scaled to the target: callers pass `maxDurationMs`; SpeakBlock
  uses `4000 + 1600 × (syllable count − 1)`, clamped to [4 s, 12 s]. The
  absolute 30 s ceiling stays. At the cap, if speech was heard → stop + submit.

Thresholds (0.15/0.08, 2.5 s) are constants with a comment — tuned during the
live walkthrough; founder delegated exact values.

### UI (never feels haunted)

`useRecorder` exposes `phase` (`idle | armed | hearing | finishing`) and
`silenceProgress` (0–1 through the 2.5 s window). Under the record ring:

- armed: “Listening — speak now”
- hearing: “Got it — pause when you’re done”
- finishing: shrinking arc on the ring + “Finishing…”
- Manual affordance stays: ring remains tappable, caption keeps “tap to stop”.
- Reduced motion: text states only, no arc animation.

## 3. Visual overhaul — “alive and unmistakably Korean”

CSS-first (no animation library; bundle stays lean). Executed under the
frontend-design skill. Elements:

- **Motion**: block step enter transition (directional slide + fade keyed on
  step index), score rings draw in with a count-up, staggered reveals on lists.
- **Pass celebration**: a **dojang** — the Korean red seal stamp — thumps onto
  the card on 통과, with a subtle paper-settle. Distinctly Korean; no confetti.
- **Skeletons** replace the three-dot spinner on lessons / lesson player /
  dashboard / progress loads (shaped like the content they become).
- **Identity**: subtle hanji paper texture on the app background; a self-hosted
  Korean **serif display face** (subset-split woff2, e.g. Noto Serif KR via
  fontsource) for `hangul-display` moments so the glyphs learners study have
  calligraphic presence; refined lesson cards and header.
- `prefers-reduced-motion` honoured on every animation. Dark mode explicitly
  **out of scope** this pass (future item).

## Testing

- **Backend**: route tests — allowed text passes, free text 400s, unpublished
  lesson 404s, jamo table pinned, cache hit skips the TTS client (fake client
  call-count).
- **Frontend**: silence-gate logic extracted as a pure helper
  (`lib/silenceGate.ts`) and unit-tested (onset, reset on loud frame, fire at
  2.5 s, no-speech discard); AudioButton fetch-once caching; skeleton renders.
- **Live walkthrough** (verify skill): hear ㅏ/ㄱ/한 from lesson 1–2 cards,
  write-block audio, record with auto-stop on a real mic pass, celebration and
  skeletons observed, reduced-motion spot check.

## Out of scope

Dark mode; pre-generated audio in Storage (HANDOVER item 6); phoneme-level
coaching; romanization toggle.
