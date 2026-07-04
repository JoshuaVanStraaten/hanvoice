# Architecture

## System overview

```
┌──────────────┐     auth + RLS reads      ┌────────────────┐
│  React PWA   │ ─────────────────────────▶│    Supabase     │
│  (Vite,      │                            │  Postgres+Auth  │
│   Tailwind)  │      Bearer JWT            └────────▲───────┘
│              │ ──────────────┐                     │ service-role key
└──────────────┘               ▼                     │ (PostgREST)
                       ┌──────────────┐──────────────┘
                       │  FastAPI     │
                       │  backend     │──▶ Azure Speech (pronunciation, TTS)
                       └──────────────┘──▶ NVIDIA: ASR · Llama · Nemotron-VL
                               │
                               └─────────▶ Stripe (checkout + webhooks)
```

## Security model (the core invariant)

**Clients never write scores, usage, or billing rows.** The browser talks to Supabase
directly only for auth and RLS-guarded reads (own profile, public content, pricing).
Every write to scored or billable data goes through the backend, which uses the
service-role key. RLS on those tables has no insert/update policies for
`authenticated`, so a stolen anon key cannot forge progress or usage.

Auth: the frontend signs in with Supabase Auth; the backend verifies the access token
(HS256, `SUPABASE_JWT_SECRET`) in a dependency — no backend session state.

## The metered-route order

Every AI-backed route runs, in order:

**rate limit → resolve plan → quota check → AI call → persist → meter**

Quota failures (HTTP 429, `quota_exceeded`) happen *before* any AI spend. Metering
happens *after* persistence via an atomic `increment_daily_usage` RPC — one wide row
per user per day, and daily quota in Postgres is the cross-instance authority.

## Entitlements

Resolved per request in `services/entitlements.py`: founder pass row → `founder`
plan; else live subscription (`trialing|active|past_due`) → its plan; else `free`.
Plan limits are data (the `plans` table), so changing a tier's quota is an UPDATE,
not a deploy.

## AI clients

One class per provider in `app/services/ai/`, each taking a shared
`httpx.AsyncClient` + settings. Retryable 5xx are retried twice, then map to 503;
other upstream errors map to 502 — routes never see raw provider exceptions.

The Llama barista contract is strict: a 4-key JSON turn validated with
`extra="forbid"`, one repair retry on malformed output, then a canned in-character
fallback. Conversation goal tracking is backend keyword matching
(`services/goals.py`) — never delegated to the model. The transcript window is the
last 12 turns.

## Frontend

TanStack Query owns all server state (`hooks/queries.ts` is the single fetch
surface); React context only for the auth session. `lib/api.ts` attaches the
Supabase token and unwraps the backend's single error envelope
(`{"error": {"code", "message"}}`) into a typed `ApiError` — quota errors render
upgrade prompts, not retries.

Design system ("hanji & taegeuk"): paper base, ink text; **taegeuk red is reserved
for speaking actions** (the record ring, live states), blue for learning/navigation,
jade for strong scores. Tokens are Tailwind v4 `@theme` variables in `index.css`.

## Deliberate v1 scope

- **No raw audio/image persistence** — analyze-and-discard; `audio_url`/`image_url`
  stay null. Revisit if we need training data (with consent).
- **No Redis** — the rate limiter is in-process (single-instance deploys; the
  Postgres daily quota is the real cross-instance limit). Revisit when scaling out.
- **No background jobs** — TTS is best-effort inline; a failed synthesis degrades to
  text-only rather than queueing.
