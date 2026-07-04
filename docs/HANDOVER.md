# HanVoice — Session Handover

**Updated:** 2026-07-04 (evening) · **Branch:** `main` · **Status: curriculum shipped — the app now teaches Korean from zero; verified live end-to-end.**

## What exists

The full application (M1–M10 of `docs/superpowers/plans/2026-07-03-hanvoice-full-app.md`)
plus the **real curriculum** (`docs/superpowers/plans/2026-07-04-lesson-blocks-curriculum.md`,
design in `docs/superpowers/specs/2026-07-04-lesson-blocks-curriculum-design.md`):
FastAPI backend (97 tests; ruff + strict mypy clean), React PWA frontend
(17 tests; eslint + tsc clean), Docker images smoke-tested, CI workflow written.
See `README.md`, `docs/architecture.md`, `docs/api.md`, `docs/deployment.md`, `docs/schema.md`.

**Curriculum architecture (new):** lessons are ordered `lesson_blocks`
(`explain | speak | write | quiz`, JSONB payload; speak blocks FK to
`lesson_phrases` so the whole pronunciation stack is reused). Per-block pass
state in `lesson_block_progress` (backend-written; speak/write pass only via
scored attempts ≥ 60, explain/quiz via `POST /lessons/blocks/{id}/complete`).
`lesson_progress.phrases_completed` → `blocks_completed`. The lesson page is a
stepper player that resumes at the first unpassed block; the standalone Write
tab still works (canvas extracted to `HangulCanvas`).

## Live environment

- **Supabase project `hanvoice`** (`mxibibkcaarltsbkomvm`, eu-west-1, free tier) —
  migrated + seeded. `frontend/.env` and `backend/.env` are wired (gitignored).
- **Content:** 13 lessons in two sections — **"Read & write Hangul"** (8 lessons,
  62 blocks: what-is-hangul → vowels → consonants → building syllables → more
  letters → batchim → sound changes → reading + 해요체) and **"Speak"** (the 5
  phrase lessons as speak-block units) — plus 1 conversation scenario (iced
  americano), barista prompt v1. Content is data — new lessons are an INSERT,
  no deploy. `supabase/seed.sql` mirrors the live content.
- **Azure Speech** (northeurope, F0): pronunciation scoring, STT for conversation
  turns, Korean neural TTS (SunHi). **NVIDIA**: Llama barista chat + Nemotron-VL
  handwriting vision. All verified live, in-browser and via API.
- **Test account:** `joshuavanstraaten100+hanvoice-test@gmail.com` /
  `hanvoice-test-1234` (email-confirmed via SQL; holds a manually-granted founder
  pass → 200/day quotas). The founder entitlement path is therefore live-tested.
- User's other Supabase project **pettlo-poc was paused** to free the free-tier
  slot — don't unpause/delete without asking.

## What's left (in rough priority order)

1. **Push to GitHub (NEXT)** — repo has no remote; CI has never actually run.
2. **Deploy** — per `docs/deployment.md`: backend container (Fly/Railway/Render),
   frontend static host (Vercel/Netlify), env vars at build time for `VITE_*`.
3. **Stripe** — create products/prices ($69 founder one-time, $14.99/mo premium),
   set the four STRIPE_* env vars, point the webhook at
   `/api/billing/webhook`. Until then billing routes 503 (by design).
4. **Production email** — Supabase's built-in SMTP is rate-limited (~3/hr);
   configure custom SMTP before real signups.
5. **Content depth** — more scenarios (only the café exists; the Talk tab is the
   marquee feature), audio for lesson phrases is generated on demand (could
   pre-generate + cache in Storage), double vowels (ㅐㅔㅘ…) and tense/aspirated
   consonants as Hangul course lessons 9-10, intro explain blocks for the five
   Speak lessons.
6. **v2 quality items** — stronger handwriting judge (8B Nemotron-VL is coarse;
   scores synthetic/mouse drawings near zero — one config line to swap; matters
   more now that write blocks gate lesson progress), phoneme-level pronunciation
   coaching (needs Azure streaming SDK instead of REST), streaks/gamification,
   romanization toggle as a profile setting, raw-audio persistence for progress
   review (consent + storage), `/api/progress` + `/api/lessons` do N+1 block
   queries per lesson (fine at 13 lessons; batch when content grows).

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
- **Run the backend with `PYTHONUTF8=1` on Windows.** structlog prints to the
  console; a log line containing Hangul (e.g. the vision-retry warning quoting
  the target char) crashes the *request* with UnicodeEncodeError on a cp1252
  console. Production containers (UTF-8) are unaffected. Also: port 8000 tends
  to hold a stale uvicorn from an earlier session — probe a new route (404 =
  stale) and kill it before testing new backend code.
- Local dev drive recipe (servers, test login, deterministic speak-block pass
  via Azure TTS WAV): `.claude/skills/verify/SKILL.md`.
