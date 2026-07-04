# HanVoice — Session Handover

**Date:** 2026-07-04 · **Branch:** `feat/full-app` (branched from `main`)
**Mission:** Implement the entire production-ready HanVoice application per `prompt2.xml`, on top of the already-approved schema and barista prompt. Work is executed against the plan in `docs/superpowers/plans/2026-07-03-hanvoice-full-app.md` — **read that plan first; it locks in all architecture decisions, file layout, and the env-var contract.**

## What HanVoice is

Mobile-first PWA teaching beginners spoken Korean: tiny phrase chunks, Azure pronunciation scoring, AI café conversations (Nemotron ASR → Llama → TTS), Hangul handwriting checks (Nemotron-VL). React/TS/Tailwind frontend, FastAPI backend, Supabase (Postgres + Auth). Paid tiers: free / $69 lifetime Founder Pass / $14.99mo Premium, enforced by daily quotas.

## Approved artifacts (source of truth — do not rewrite)

- `supabase/migrations/20260703090000_initial_schema.sql` — 16 tables, full RLS. Security model: **clients never write scores/usage/billing**; only the backend (service-role key) does. Documented in `docs/schema.md`.
- `supabase/migrations/20260703120000_increment_daily_usage.sql` — atomic usage RPC (verified against throwaway Docker Postgres).
- `prompts/scenarios/cafe_iced_americano_v1.md` — barista prompt + integration contract (strict 4-key JSON, 12-turn window, one repair retry, canned fallback). Also seeded in `supabase/seed.sql`.
- The plan doc above.

## State: DONE

### Backend (M1–M5) — complete, committed, green

`cd backend && ./.venv/Scripts/python -m pytest -q` → **79 passed**; `ruff check .` and `mypy app` (strict) clean. Commits `97983e7`…`99b6c37`.

- `app/main.py` — `create_app()`, lifespan holds shared `httpx.AsyncClient` + `Database` + `Settings` (reachable via `request.state.*`).
- `app/core/` — `config.py` (all env vars; pydantic-settings), `errors.py` (AppError hierarchy → single `{"error":{"code","message"}}` envelope), `logging.py` (structlog + request-id middleware), `security.py` (Supabase HS256 JWT → `AuthenticatedUser`), `ratelimit.py` (in-process sliding window).
- `app/db/client.py` — thin async PostgREST client (select/insert/upsert/update/rpc), `DatabaseError` carries `db_status` (409 used for idempotency). `app/db/repositories/` — one module per domain.
- `app/services/` — `entitlements.py` (founder → live sub → free), `quota.py` (pure checks, 429 before AI spend), `usage.py` wrapper is in `db/repositories/usage.py` (`increment` via RPC), `goals.py` (keyword goal detection — backend, never the model), `progress.py` (rollups on write path; pass threshold 60), `conversation.py` (ConversationService: ASR→quota→Llama→goals→persist→best-effort TTS→meter), `billing.py` (Stripe checkout + webhooks; unconfigured ⇒ 503; **stripe v15: `event.data.object.to_dict()`**, StripeObject is no longer a dict).
- `app/services/ai/` — `base.py` (bounded retry: retryable 5xx twice ⇒ `AIServiceUnavailableError` 503; other 4xx/5xx ⇒ `AIServiceError` 502), `azure_pronunciation.py`, `nemotron_asr.py`, `llama_chat.py` (BaristaTurn `extra="forbid"`, repair retry, `FALLBACK_TURN`), `tts.py`, `nemotron_vision.py`.
- `app/api/routes/` — health, me (GET/PATCH), usage, content (lessons/scenarios), pronunciation (multipart, quota-gated), conversations (start / turns [multipart text-or-audio] / complete / get), handwriting (base64 PNG), progress, waitlist (anon, dup-safe), billing (checkout + webhook).
- Tests in `backend/tests/` use **respx** against `http://supabase.test` + fake AI hosts; `tests/factories.py` has row factories + `auth_headers()`. Env stubs live at the top of `conftest.py` (imported before app).

**Deliberate v1 scope decisions** (documented, revisit later): no raw audio/image persistence (analyze-and-discard; `audio_url`/`image_url` stay null), no Redis (in-process rate limit; daily quota in Postgres is the cross-instance authority), no background jobs needed yet.

### Frontend (M6 — in progress, ~60% of scaffold done, UNCOMMITTED)

`frontend/` exists with deps installed (React 19, Vite 8, Tailwind 4, TS 6, react-router-dom 7, TanStack Query 5, supabase-js 2, vite-plugin-pwa 1, vitest 4). Files written so far:

- `package.json` (scripts: dev/build/typecheck/lint/format/test), `vite.config.ts` (react + tailwind + VitePWA manifest + `/api` proxy → :8000 + vitest jsdom config), `tsconfig.json` (strict), `eslint.config.js`, `.prettierrc`, `index.html`
- `src/index.css` — design tokens (see below)
- `src/lib/types.ts` (mirrors backend schemas), `src/lib/supabase.ts`, `src/lib/api.ts` (`ApiError`, apiGet/Post/Patch/PostForm, attaches Supabase token)
- `src/context/AuthContext.tsx` (session restore, signIn/signUp/signOut/resetPassword)
- `src/hooks/queries.ts` (useMe, useUsageToday, useLessons, useLesson, useScenarios, useProgress, useUpdateProfile, useCheckout, useActivityInvalidation)
- `src/components/ui.tsx` (Button [primary/speak/quiet], Card, Spinner, ErrorNote [quota-aware], ScoreRing, MeterBar)
- `public/icons/icon-192.png`, `icon-512.png` (generated taegeuk placeholder)

**Design system ("hanji & taegeuk")**: paper `#F6F4EF` base, ink `#23262C`; taegeuk **red `#C73E3A` = speaking actions only** (record button, live states), **blue `#2C4E8A` = learning/nav**, jade `#3E8E7E` = strong scores. Hangul as display type (`.hangul-display`). Signature element: red "speak ring" record button (`.speak-ring-active` breathing animation, reduced-motion respected). Tokens are Tailwind v4 `@theme` vars in `index.css` (`bg-taegeuk-red`, `border-line`, etc.).

## State: TODO (in order)

1. **Finish M6 scaffold**: `src/test/setup.ts` (jest-dom import), `src/main.tsx` (QueryClientProvider + AuthProvider + RouterProvider), `src/App.tsx`/`routes.tsx` (router: public Landing/Login/Signup; protected shell), `src/components/RequireAuth.tsx`, `src/components/AppShell.tsx` (top bar + bottom tab nav: Home, Lessons, Talk, Write, Profile; safe-area padding). Also `frontend/.env.example` (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL). Verify with `npm run typecheck && npm run lint && npm run build`. Commit.
2. **M7 core pages**: Landing (pricing from anon supabase read of `plans`, waitlist form → POST /api/waitlist), Login/Signup/reset, Dashboard (usage MeterBars, continue-lesson card, scenario card, progress section).
3. **M8 features**: `hooks/useRecorder.ts` (MediaRecorder → webm blob), LessonDetail (phrase cards + record → `apiPostForm("/pronunciation/attempts")` → ScoreRings + per-word feedback), Talk (scenario list) + Conversation page (start → chat bubbles with hangul + toggleable romanized/english + correction chips; mic or text per turn; play `audio_base64`; goal checklist; completed state), Writing (canvas with pointer events, undo/clear, export PNG ≤2MB → POST /api/handwriting/attempts), Settings/Profile (PATCH /me, sign out), Subscription (plan cards, `useCheckout`, handles `?checkout=success|canceled`, shows current plan/founder badge from useMe). Add a few vitest tests (api error unwrapping, ScoreRing/MeterBar render, goal chip logic).
4. **M9 infra**: `backend/Dockerfile` (multi-stage, non-root, uvicorn), `frontend/Dockerfile` (build → nginx SPA fallback), `docker-compose.yml`, root `.env.example`, `.github/workflows/ci.yml` (backend: ruff+mypy+pytest; frontend: lint+typecheck+test+build).
5. **M10 docs**: README (quickstart, env table), `docs/architecture.md`, `docs/api.md`, `docs/deployment.md`. Update plan checkboxes.
6. **Finish**: full verification, then merge `feat/full-app` → `main` (user works directly in this checkout; no worktrees — repo is in OneDrive).

## Commands & gotchas

- Backend venv: `backend/.venv` — invoke as `./.venv/Scripts/python -m pytest|ruff|mypy` from `backend/`.
- Frontend: plain `npm run <script>` from `frontend/`.
- Windows + Git Bash; git prints LF/CRLF warnings — harmless, ignore.
- `pyproject.toml` mypy is strict; ruff line-length 100 (watch long Korean-string lines and en-dashes in docstrings — RUF002).
- Route order everywhere: **rate limit → resolve plan → quota check → AI call → persist → meter** (quota errors must cost nothing).
- Conversation route resolves plan *before* the service loads the session — tests for 404/409 paths still need plan-resolution mocks (`mock_common()` in `tests/test_conversation_routes.py`).
- respx: mock every Supabase table a request touches or you get `AllMockedAssertionError` → 500s.
- The user prompt style: acts as founder; you are technical co-founder. Make decisions, explain briefly, don't ask unless product strategy is affected. Response format per `prompt2.xml`: milestone → objective → decisions → files → explanation → next milestone.
