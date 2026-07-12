# HanVoice — Speak Korean out loud

HanVoice is a mobile-first PWA that teaches beginners **spoken** Korean: tiny phrase
chunks scored by Azure pronunciation assessment, AI café conversations with Minji the
barista (Azure STT → Llama → Azure TTS), and Hangul handwriting checks (Nemotron-VL).
Free tier, $69 lifetime Founder Pass, or $14.99/mo Premium — enforced by daily quotas.

**Stack:** React 19 / TypeScript / Tailwind v4 / Vite PWA · FastAPI / Python 3.12 ·
Supabase (Postgres + Auth) · Paddle.

## Quickstart

Prereqs: Node 22+, Python 3.12+, a [Supabase](https://supabase.com) project.

```bash
# 1. Database — apply migrations + seed to your Supabase project
supabase link --project-ref <your-ref>
supabase db push
supabase seed run   # or run supabase/seed.sql in the SQL editor

# 2. Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # or bin/activate
pip install -e ".[dev]"
cp ../.env.example .env                             # fill in Supabase + AI keys
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
cp .env.example .env                                # fill in Supabase URL + anon key
npm run dev                                         # http://localhost:5173
```

Or run both with Docker: `cp .env.example .env`, fill it in, then `docker compose up --build`
(frontend at :8080, API at :8000).

## Environment variables

| Variable | Where | Required | Purpose |
|---|---|---|---|
| `SUPABASE_URL` | backend | ✅ | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | backend | ✅ | Server-side DB access (bypasses RLS — backend only) |
| `SUPABASE_JWT_SECRET` | backend | ✅ | Verifies user access tokens (HS256) |
| `AZURE_SPEECH_KEY` / `AZURE_SPEECH_REGION` | backend | for speech features | Pronunciation scoring, speech-to-text, Korean neural TTS |
| `NVIDIA_API_KEY` | backend | for conversations/writing | Llama chat, handwriting vision |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PRICE_*` | backend | optional | Billing (routes return 503 when unset) |
| `APP_ENV`, `LOG_LEVEL`, `CORS_ORIGINS`, `FRONTEND_URL` | backend | defaults | App config |
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` | frontend | ✅ | Client auth + public reads (baked in at build) |
| `VITE_API_URL` | frontend | optional | Backend origin; empty = same-origin `/api` (dev proxy) |

## Repository layout

```
backend/    FastAPI app — core/ (config, auth, errors), db/ (PostgREST client +
            repositories), services/ (entitlements, quota, AI clients), api/routes/
frontend/   Vite + React PWA — pages/, components/, hooks/, lib/ (api, types)
supabase/   migrations/ (schema + RLS + usage RPC), seed.sql
prompts/    approved scenario prompts (barista contract)
docs/       architecture, api, deployment, schema
```

## Verification

```bash
cd backend && ruff check . && mypy app && pytest        # 79 tests
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
```

## Docs

- [docs/architecture.md](docs/architecture.md) — system design and the security model
- [docs/api.md](docs/api.md) — endpoint reference (also live at `/docs` on the API)
- [docs/deployment.md](docs/deployment.md) — hosting options and CI/CD
- [docs/schema.md](docs/schema.md) — database schema and RLS rationale
