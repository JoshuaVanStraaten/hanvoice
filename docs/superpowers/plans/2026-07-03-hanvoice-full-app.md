# HanVoice Full Application Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Adaptation note:** The governing spec (`prompt2.xml`) directs the implementer to generate every file completely *during implementation*, iterating milestone-by-milestone. This plan therefore locks in architecture, file structure, interfaces, and task order — the level where consistency bugs are born — rather than duplicating the full source of every file. Key contracts (types, signatures, env vars) are spelled out exactly so later milestones match earlier ones.

**Goal:** Ship the complete, deployable HanVoice application — React/TS/Tailwind PWA frontend, FastAPI backend, Supabase database (already migrated), and five AI integrations — per `prompt2.xml`, on top of the approved schema (`supabase/migrations/20260703090000_initial_schema.sql`, documented in `docs/schema.md`) and the approved barista prompt (`prompts/scenarios/cafe_iced_americano_v1.md`).

**Architecture:** Monorepo with `backend/` (FastAPI) and `frontend/` (Vite + React PWA). The client talks to Supabase directly only for auth and RLS-guarded reads; **every write to scored/billable data goes through the backend** using the service-role key (the approved security model). AI providers are wrapped in small client classes behind protocols so they can be mocked in tests and swapped without touching routes.

**Tech Stack:** React 18, TypeScript (strict), TailwindCSS v4, Vite, vite-plugin-pwa, react-router v7, TanStack Query v5, @supabase/supabase-js v2 · FastAPI, Python 3.12, Pydantic v2, pydantic-settings, httpx, PyJWT, structlog · pytest + respx, Vitest + Testing Library · Docker, docker-compose, GitHub Actions · ruff, mypy, ESLint, Prettier.

---

## Locked architectural decisions

1. **Backend DB access:** a thin async PostgREST client (`backend/app/db/client.py`) over `httpx`, authenticated with the service-role key. Chosen over `supabase-py` for explicit control of timeouts/retries and trivial mocking with `respx`. All table access goes through repository functions — routes never build PostgREST queries.
2. **Auth:** the frontend authenticates with Supabase Auth (`@supabase/supabase-js`); the backend verifies the Supabase access token (HS256, `SUPABASE_JWT_SECRET`) in a FastAPI dependency `get_current_user() -> AuthenticatedUser(id: UUID, email: str | None)`. No session state in the backend.
3. **Entitlement resolution (backend, per approved schema doc):** founder pass row → `founder` plan; else live subscription (`trialing|active|past_due`) → its plan; else `free`. Implemented once in `app/services/entitlements.py`, cached per-request only.
4. **Quota flow:** every metered endpoint calls `quota.check_and_reserve(user_id, metric, plan)` before the AI call and `usage.record(...)` after. `daily_usage` is written via PostgREST upsert with `on_conflict=user_id,usage_date` and increment done by an RPC-free read-modify-write guarded by optimistic retry (single wide row per approved schema).
5. **AI clients** (`app/services/ai/`): one module per provider, each a class taking `httpx.AsyncClient` + settings; all raise a common `AIServiceError` hierarchy. Llama chat responses are validated by a strict Pydantic model (`extra="forbid"`, 4 keys) with one repair retry and the canned in-character fallback, exactly as the approved prompt's integration notes specify.
6. **Conversation goal tracking** is backend code (`app/services/goals.py`), keyword/pattern-based per scenario `completion_goals`, never delegated to the model (per integration notes).
7. **Rate limiting:** in-process token bucket keyed by user id (falls back to IP for anon), applied via dependency to expensive routes. No Redis at this scale (single-instance deploys; revisit when horizontally scaled).
8. **Media storage:** audio/canvas uploads go to Supabase Storage from the backend (service role) under `audio/{user_id}/...` and `handwriting/{user_id}/...`; DB rows store the path.
9. **Frontend state:** TanStack Query for server state, React context only for auth/session. No global state library.
10. **Billing:** Stripe Checkout (subscription + one-time founder pass) with a webhook endpoint that writes `subscriptions` / `founder_pass_purchases`. Stripe calls are isolated in `app/services/billing.py` so the app runs without Stripe configured (billing routes return 503 with a clear message when unconfigured).

## Repository layout (target)

```
backend/
  pyproject.toml            # deps + ruff + mypy + pytest config
  app/
    main.py                 # create_app() factory, middleware, router mounting
    core/config.py          # Settings (pydantic-settings), env contract
    core/logging.py         # structlog setup, request-id middleware
    core/errors.py          # AppError hierarchy + exception handlers
    core/security.py        # JWT verification, get_current_user dependency
    core/ratelimit.py       # token-bucket dependency
    db/client.py            # PostgREST thin client (service role)
    db/repositories/        # profiles.py, plans.py, usage.py, content.py,
                            # attempts.py, conversations.py, progress.py, billing.py
    schemas/                # Pydantic request/response models per domain
    services/
      entitlements.py       # resolve_plan(user_id) -> Plan
      quota.py              # QuotaExceeded, check(user, metric)
      usage.py              # record increments
      goals.py              # completion-goal detection
      billing.py            # Stripe wrapper
      ai/
        base.py             # AIServiceError, shared retry helper
        azure_pronunciation.py
        nemotron_asr.py
        llama_chat.py       # + BaristaTurn pydantic contract + repair retry
        tts.py              # Chatterbox/Magpie client
        nemotron_vision.py  # handwriting assessment
    api/
      deps.py               # shared dependencies (db, user, services)
      routes/               # health, profiles, lessons, scenarios, pronunciation,
                            # conversations, handwriting, progress, usage,
                            # waitlist, billing
  tests/                    # mirrors app/ ; respx for HTTP mocks
frontend/
  package.json, vite.config.ts, tsconfig.json, index.html
  src/
    main.tsx, App.tsx, routes.tsx
    lib/supabase.ts         # supabase-js client
    lib/api.ts              # typed fetch wrapper (attaches access token)
    lib/types.ts            # API types mirroring backend schemas
    context/AuthContext.tsx
    components/             # ui/ primitives + feature components
    pages/                  # Landing, Login, Signup, Dashboard, Lessons,
                            # LessonDetail (pronunciation), Conversation,
                            # Writing, Progress, Settings, Subscription
    hooks/                  # useRecorder, useApi queries
docker-compose.yml, backend/Dockerfile, frontend/Dockerfile
.github/workflows/ci.yml
docs/architecture.md, docs/api.md, docs/deployment.md, README.md
```

## Environment contract (single source: `backend/app/core/config.py` + `.env.example`)

```
SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET, SUPABASE_ANON_KEY
AZURE_SPEECH_KEY, AZURE_SPEECH_REGION
NVIDIA_API_KEY, NVIDIA_ASR_URL, NVIDIA_LLM_URL, NVIDIA_LLM_MODEL, NVIDIA_TTS_URL, NVIDIA_VISION_URL, NVIDIA_VISION_MODEL
STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_PREMIUM, STRIPE_PRICE_FOUNDER (all optional)
APP_ENV, LOG_LEVEL, CORS_ORIGINS, FRONTEND_URL
frontend: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL
```

## Milestones and tasks

### M1 — Backend foundation
- [x] `backend/pyproject.toml` (fastapi, uvicorn, httpx, pydantic-settings, pyjwt, structlog, stripe; dev: pytest, pytest-asyncio, respx, ruff, mypy)
- [x] `app/core/config.py` Settings with the env contract above; test that missing required vars fail loudly
- [x] `app/core/errors.py` `AppError(status, code, message)` + handlers returning `{"error": {"code", "message"}}`
- [x] `app/core/logging.py` structlog JSON logs + request-id middleware
- [x] `app/main.py` `create_app()`; `GET /api/health` returns `{"status": "ok"}`; CORS from settings
- [x] Tests: health endpoint, error envelope shape. Run `pytest`, commit.

### M2 — DB client + auth
- [x] `db/client.py`: `Database.select/insert/upsert/update/rpc` (typed thin wrappers, service-role headers, raises `DatabaseError`)
- [x] `core/security.py`: verify HS256 JWT (aud `authenticated`), `get_current_user` dependency; tests for expired/garbage/valid tokens
- [x] Repositories for profiles + plans; `GET /api/me` (profile + resolved plan) route. Tests with respx. Commit.

### M3 — Entitlements, quota, usage (pure TDD — this is the money logic)
- [x] `services/entitlements.py`: founder → subscription → free resolution; tests cover all branches incl. expired subscription
- [x] `services/quota.py`: `ensure_within_quota(usage_row, plan, metric)` raises `QuotaExceeded` (→ HTTP 429 with `quota_exceeded` code)
- [x] `services/usage.py`: `record(user_id, **increments)` upsert-increment; `GET /api/usage/today` route. Commit.

### M4 — AI clients (each: client class + respx tests for success/timeout/4xx/5xx)
- [x] `ai/base.py` — `AIServiceError`, `AIServiceUnavailable`, bounded-retry helper
- [x] `ai/azure_pronunciation.py` — `assess(audio_wav: bytes, reference_text: str) -> PronunciationScores` (accuracy/fluency/completeness/overall + phoneme JSON)
- [x] `ai/nemotron_asr.py` — `transcribe(audio: bytes) -> str`
- [x] `ai/llama_chat.py` — `BaristaTurn` model (4 keys, `extra="forbid"`); `next_turn(system_prompt, transcript) -> tuple[BaristaTurn, TokenUsage]`; repair retry + canned fallback per integration notes; window last 12 turns
- [x] `ai/tts.py` — `synthesize(text: str) -> bytes` (audio/mpeg)
- [x] `ai/nemotron_vision.py` — `assess_handwriting(image_png: bytes, target: str) -> HandwritingScores`. Commit per client.

### M5 — Feature routes (each: schema + repository + route + tests)
- [x] Content: `GET /api/lessons`, `GET /api/lessons/{slug}` (with phrases), `GET /api/scenarios`
- [x] Pronunciation: `POST /api/pronunciation/attempts` (multipart audio + phrase_id/target) → quota check → Azure → store attempt → update `lesson_progress` → return scores
- [x] Conversations: `POST /api/conversations` (start; loads active scenario prompt, returns Minji's opener), `POST /api/conversations/{id}/turns` (multipart audio or text → ASR → quota → Llama → goals → TTS → store both messages → return turn payload + audio), `POST /api/conversations/{id}/complete`
- [x] Handwriting: `POST /api/handwriting/attempts` (base64 PNG + target) → quota → vision → store
- [x] Progress: `GET /api/progress` (lesson + scenario rollups)
- [x] Waitlist: `POST /api/waitlist` (anon, validated email)
- [x] Billing: `POST /api/billing/checkout` (premium|founder), `POST /api/billing/webhook` (signature-verified; writes subscriptions/founder passes)
- [x] Rate limiting on pronunciation/turn/handwriting routes. Commit per route group.

### M6 — Frontend scaffold
- [x] Vite + React + TS strict + Tailwind v4 + vite-plugin-pwa (manifest: HanVoice, standalone, icons) + ESLint/Prettier + Vitest
- [x] `lib/supabase.ts`, `AuthContext` (session, signIn/signUp/signOut), `lib/api.ts` (typed fetch attaching token, unwraps error envelope), router with protected routes. Commit.

### M7 — Frontend core
- [x] Landing page (pricing from `plans` via anon supabase read, waitlist form)
- [x] Login/Signup/PasswordReset pages
- [x] App shell: mobile-first bottom nav (Home, Lessons, Talk, Write, Profile), top bar, safe-area handling
- [x] Dashboard: today's usage meter, continue-lesson card, scenario card. Commit per page group.

### M8 — Frontend features
- [x] Lessons list + LessonDetail: phrase cards, `useRecorder` (MediaRecorder → wav/webm), record → POST attempt → score display with per-word feedback
- [x] Conversation: start scenario → chat UI (hangul + toggleable romanization/english, correction chips), mic button per turn, TTS audio playback
- [x] Writing: HTML5 canvas (touch + pointer), stroke clear/undo, submit → scores + feedback
- [x] Progress page: streaks from usage, per-lesson bars, scenario completion
- [x] Settings: profile edit, romanization toggle, sign out; Subscription page: plan comparison, checkout buttons, current-plan state. Commit per feature.

### M9 — Infra
- [x] `backend/Dockerfile` (multi-stage, uvicorn, non-root), `frontend/Dockerfile` (build → nginx with SPA fallback + caching headers), `docker-compose.yml` (backend + frontend, env passthrough), `.env.example`
- [x] `.github/workflows/ci.yml`: backend (ruff, mypy, pytest) + frontend (eslint, tsc, vitest, build) jobs. Commit.

### M10 — Docs
- [x] `README.md` (what/why, quickstart, env table), `docs/architecture.md`, `docs/api.md` (endpoint reference; note FastAPI /docs), `docs/deployment.md` (Supabase + Fly/Railway/Render + Vercel/Netlify options, CI/CD recommendation). Final commit.

## Verification per milestone
Backend: `cd backend && ruff check . && mypy app && pytest`. Frontend: `cd frontend && npm run lint && npm run typecheck && npm test && npm run build`. Every commit leaves the repo green.
