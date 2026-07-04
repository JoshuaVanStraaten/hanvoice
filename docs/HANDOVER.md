# HanVoice — Session Handover

**Updated:** 2026-07-04 · **Branch:** `main` · **Status: feature-complete and running live locally, all five AI paths verified end-to-end.**

## What exists

The full application (M1–M10 of `docs/superpowers/plans/2026-07-03-hanvoice-full-app.md`)
is implemented, tested, and merged: FastAPI backend (89 tests; ruff + strict mypy
clean), React PWA frontend (15 tests; eslint + tsc clean), Docker images
smoke-tested, CI workflow written. See `README.md`, `docs/architecture.md`,
`docs/api.md`, `docs/deployment.md`, `docs/schema.md`.

## Live environment

- **Supabase project `hanvoice`** (`mxibibkcaarltsbkomvm`, eu-west-1, free tier) —
  migrated + seeded. `frontend/.env` and `backend/.env` are wired (gitignored).
- **Content:** 5 lessons × 5 phrases (café, first meetings, restaurant, getting
  around, money), 1 conversation scenario (iced americano), barista prompt v1.
  Content is data — new lessons are an INSERT, no deploy. `supabase/seed.sql`
  mirrors the live content.
- **Azure Speech** (northeurope, F0): pronunciation scoring, STT for conversation
  turns, Korean neural TTS (SunHi). **NVIDIA**: Llama barista chat + Nemotron-VL
  handwriting vision. All verified live, in-browser and via API.
- **Test account:** `joshuavanstraaten100+hanvoice-test@gmail.com` /
  `hanvoice-test-1234` (email-confirmed via SQL; holds a manually-granted founder
  pass → 200/day quotas). The founder entitlement path is therefore live-tested.
- User's other Supabase project **pettlo-poc was paused** to free the free-tier
  slot — don't unpause/delete without asking.

## What's left (in rough priority order)

1. **Real curriculum (NEXT — before the GitHub push).** Founder decision
   2026-07-04: lessons must actually *teach*, not just drill phrases —
   scenarios/conversations are a practice **feature**, the curriculum is the
   product spine. Direction:
   - **Curriculum arc:** how Hangul works (blocks, jamo) → vowels → consonants
     → syllable building → batchim (final consonants) → beginner sound-change
     rules (linking, nasalization — lite) → reading practice → politeness
     (해요체) intro → then the existing phrase lessons slot in as speaking units.
   - **Architectural implication:** the current `lessons → lesson_phrases`
     model only supports phrase drills. Lessons need ordered *content blocks*
     of mixed types — explanation (rich text), speak (existing pronunciation
     loop), write (existing canvas, given jamo/syllable targets), and a light
     read/quiz type. Likely a new migration (e.g. `lesson_blocks` with a
     `kind` + JSONB payload, RLS read-only like other content) + a
     LessonDetail renderer that walks blocks. Keep content as data (authoring
     = INSERTs, no deploys); keep the pass/progress semantics per block type.
   - **Non-goals for this pass:** no CMS/admin UI, no spaced repetition —
     curriculum structure + the Hangul course content itself.
   - Brainstorm → plan → execute per the superpowers workflow; the schema
     change is approved-in-principle but the design deserves a plan doc.
2. **Push to GitHub** — repo has no remote; CI has never actually run.
3. **Deploy** — per `docs/deployment.md`: backend container (Fly/Railway/Render),
   frontend static host (Vercel/Netlify), env vars at build time for `VITE_*`.
4. **Stripe** — create products/prices ($69 founder one-time, $14.99/mo premium),
   set the four STRIPE_* env vars, point the webhook at
   `/api/billing/webhook`. Until then billing routes 503 (by design).
5. **Production email** — Supabase's built-in SMTP is rate-limited (~3/hr);
   configure custom SMTP before real signups.
6. **Content depth** — more scenarios (only the café exists; the Talk tab is the
   marquee feature), audio for lesson phrases is generated on demand (could
   pre-generate + cache in Storage), more lessons.
7. **v2 quality items** — stronger handwriting judge (8B Nemotron-VL is coarse;
   one config line to swap), phoneme-level pronunciation coaching (needs Azure
   streaming SDK instead of REST), streaks/gamification, romanization toggle as
   a profile setting, raw-audio persistence for progress review (consent + storage).

## Gotchas (hard-won, don't relearn)

- **Supabase signs ES256 now:** legacy HS256 secret verifies nothing; backend
  fetches JWKS (`core/security.py`, `199855f`). HS256 kept for tests.
- **NVIDIA's REST API has no speech models** — ASR/TTS are gRPC/Riva only. That's
  why speech is all-Azure (`1005ff4`, `3e5a14f`). Vision model id must be
  `nvidia/llama-3.1-nemotron-nano-vl-8b-v1` (check `/v1/models` first).
- **Azure short-audio API:** needs `format=detailed` query param; returns scores
  flat on `NBest[0]` (parser accepts both shapes, `5d69701`). Only accepts
  WAV/OGG — browser recordings are converted to 16kHz WAV client-side
  (`26aefcf`, `lib/audio.ts`).
- **VLM handwriting judging is fragile** (`9231a6c`): thin strokes vanish in the
  model's downscale (canvas draws 12px), JSON templates with example `0`s get
  echoed as scores (prompt lists keys without numbers + demands an observation
  sentence first), all-zero results retry once with a nudge.
- **Vite env vars are baked at build**; a module-level throw on missing env got
  the whole app dead-code-eliminated once (`3426705`) — keep env assertions lazy.
- Windows/OneDrive checkout: LF/CRLF git warnings are harmless. Backend venv:
  `backend/.venv/Scripts/python -m pytest|ruff|mypy`. Route order everywhere:
  rate limit → resolve plan → quota → AI call → persist → meter.
