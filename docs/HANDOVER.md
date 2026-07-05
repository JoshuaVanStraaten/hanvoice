# HanVoice — Session Handover

**Updated:** 2026-07-05 · **Branch:** `main` · **Status: DEPLOYED. App live at https://hanvoice.vercel.app, API at https://hanvoice-api.fly.dev, CI green on GitHub. Next: Stripe — see item 1 below.**

## What exists

The full application (M1–M10 of `docs/superpowers/plans/2026-07-03-hanvoice-full-app.md`)
plus the **real curriculum** (`docs/superpowers/plans/2026-07-04-lesson-blocks-curriculum.md`,
design in `docs/superpowers/specs/2026-07-04-lesson-blocks-curriculum-design.md`):
FastAPI backend (112 tests; ruff + strict mypy clean), React PWA frontend
(37 tests; eslint + tsc clean), Docker images smoke-tested, CI workflow written.
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

- **Production (deployed 2026-07-05, full post-deploy checklist passed):**
  - Frontend: **https://hanvoice.vercel.app** (Vercel project `hanvoice`,
    `frontend/vercel.json` SPA rewrites; `VITE_*` vars set as production env —
    Vite bakes them at build, so changing one requires a redeploy).
  - Backend: **https://hanvoice-api.fly.dev** (Fly app `hanvoice-api`, region
    `lhr` — Dublin had no capacity; `backend/fly.toml`; single machine, single
    uvicorn worker, scale-to-zero when idle so first request after a lull is a
    cold start). Secrets: Supabase, Azure, NVIDIA + `APP_ENV`/`LOG_LEVEL` +
    `CORS_ORIGINS`/`FRONTEND_URL`=the Vercel origin. `STRIPE_*` unset → billing
    503s by design.
  - GitHub: **https://github.com/JoshuaVanStraaten/hanvoice** (private). CI
    green (first run needed `python -m pytest`, `fc06554`).
  - Verified live: login, cross-origin usage read (CORS), scored pronunciation
    attempt (79.6) metering usage, block teaching-audio endpoint, service
    worker active + installable manifest.
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

1. **Stripe (NEXT)** — create products/prices ($69 founder one-time, $14.99/mo
   premium), set the four STRIPE_* env vars as Fly secrets, point the webhook
   at `https://hanvoice-api.fly.dev/api/billing/webhook`. Until then billing
   routes 503 (by design).
2. **Production email** — Supabase's built-in SMTP is rate-limited (~3/hr);
   configure custom SMTP before real signups.
3. **Content depth** — more scenarios (only the café exists; the Talk tab is the
   marquee feature), audio for lesson phrases is generated on demand (could
   pre-generate + cache in Storage), double vowels (ㅐㅔㅘ…) and tense/aspirated
   consonants as Hangul course lessons 9-10, intro explain blocks for the five
   Speak lessons.
4. **Data nit (test account only):** lessons passed *before* the blocks
   migration (café essentials) have a completed `lesson_progress` rollup but no
   `lesson_block_progress` rows, so the player starts them at step 1 unpassed.
   Real users all start post-migration; backfill or ignore.
5. **v2 quality items** — stronger handwriting judge (8B Nemotron-VL is coarse;
   scores synthetic/mouse drawings near zero — one config line to swap; matters
   more now that write blocks gate lesson progress), phoneme-level pronunciation
   coaching (needs Azure streaming SDK instead of REST), streaks/gamification,
   romanization toggle as a profile setting, raw-audio persistence for progress
   review (consent + storage), `/api/progress` + `/api/lessons` do N+1 block
   queries per lesson (fine at 13 lessons; batch when content grows), main JS
   chunk is 593 kB gzip 171 kB (build warns; candidate for route-level code
   splitting once it's worth the complexity).

## Learning-experience polish pass (done, 2026-07-05)

Plan: `docs/superpowers/plans/2026-07-05-learning-polish.md` · design:
`docs/superpowers/specs/2026-07-05-learning-polish-design.md`. Three founder
asks from 2026-07-04 evening, all shipped and verified (112 backend / 37
frontend tests green):

- **Audio on every teaching surface.** `chars`/`write`/`example` payloads carry
  an optional `audio` field; a jamo carrier map (frontend `lib/hangulAudio.ts`,
  backend `services/audio_text.py` — keep in sync) resolves bare jamo to a
  spoken carrier syllable (ㄱ → 가, ㅏ → 아, shown as "in 가"). New
  block-scoped audio endpoint `GET /lessons/blocks/{id}/audio?text=…`
  (whitelisted against the block's own payload) + backend in-process LRU
  cache for TTS synthesis (`d875ba3`, `3258a47`). `AudioButton` component
  reused across explain/write/speak blocks. Silence-gate thresholds live in
  `lib/silenceGate.ts` (onset 0.15, silence 0.08, 2.5 s window; cap 4–12 s
  via `recordingCapMs`); silent takes are discarded, never scored.
- **Recording stops itself.** Silence-gate state machine in the recorder
  (`86a4b82`, `61a0c65`) — auto-stops and submits after sustained silence,
  visible state so it's never ambiguous, manual stop still works.
- **Visual identity + motion.** "Hanji" look (Myeongjo display face for Hangul,
  paper texture, motion design tokens — `4d908f7`), skeleton loaders shaped
  like their content instead of spinners (`40ce98c`), step-enter/list-stagger/
  score-ring count-up motion (`d56920f`), and the 도장 (dojang) red-seal stamp
  as the pass celebration (`276b413`).

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
- **Never pipe secrets into a CLI from Windows PowerShell 5.1** (`"value" |
  vercel env add …`) — the pipe prepended a UTF-8 BOM (U+FEFF) to every value,
  which Vite baked into the bundle and broke `fetch` with "String contains non
  ISO-8859-1 code point". Write the value to a file with
  `[IO.File]::WriteAllText` (BOM-less) and redirect via `cmd /c "… < file"`.
  Same class of bug: `Get-Content`/`Set-Content` round-trips mangle UTF-8
  files without BOM — use the agent Write/Edit tools for files with Hangul.
  Vercel "Sensitive" env vars pull back as empty strings — inspect the built
  bundle, not `vercel env pull`, when debugging baked values.
- **The PWA service worker serves the stale shell after a redeploy** — the old
  bundle keeps running until the SW updates in the background + next reload.
  When verifying a fresh deploy, unregister the SW / clear CacheStorage first,
  or you'll debug the previous build.
- Local dev drive recipe (servers, test login, deterministic speak-block pass
  via Azure TTS WAV): `.claude/skills/verify/SKILL.md`.
