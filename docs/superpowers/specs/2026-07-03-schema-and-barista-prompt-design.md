# HanVoice — Initial Database Schema & Barista Scenario Prompt (Design)

**Date:** 2026-07-03
**Status:** Approved by founder (delivery: SQL migration files in repo; full RLS included)
**Scope:** Task 1 (Supabase PostgreSQL schema) and Task 2 (café barista system prompt) from `prompt.xml`. Nothing else — no app code.

## Context

HanVoice is a mobile-first PWA teaching beginners conversational Korean via tiny phrase chunks, pronunciation scoring (Azure Pronunciation Assessment), AI conversation (Nemotron ASR → Llama-3 Instruct → Chatterbox/Magpie TTS), and Hangul handwriting checks (Nemotron-VL). Stack: React/TS frontend, FastAPI backend, Supabase (Postgres + Auth). Must support quotas and paid tiers (Founder Pass $69 lifetime, $14.99/mo subscription) at low infra cost.

## Decisions

### Approach

Normalized domain tables in a **single initial migration** (`supabase/migrations/<ts>_initial_schema.sql`). Rejected: JSONB-generic attempt tables (unqueryable scores, messy quotas) and per-domain migration splitting (ceremony for a greenfield repo — future changes get their own migrations).

Reference/content **seed data** split: `plans` rows live in the migration (schema can't function without them); demo lesson + café scenario content live in `supabase/seed.sql`.

### Key architectural choices

1. **Clients never write scores, usage, or billing rows.** All AI-scored artifacts (pronunciation/handwriting attempts, conversation messages), `daily_usage`, and billing tables are written exclusively by the FastAPI backend using the service-role key. RLS grants users `SELECT` on their own rows only. This prevents forged scores and self-reset quotas — the backbone of paid-tier enforcement.
2. **Quota limits are data, not code.** `plans` stores per-day limits (attempts, turns, tokens); changing a tier's limits is an UPDATE, not a deploy.
3. **`daily_usage` is one wide row per (user, day).** Quota check = single indexed read; metering = single atomic upsert/increment. Chosen over a narrow (user, day, metric, amount) design for simplicity and read cost at scale.
4. **System prompts are not client-readable.** Scenario metadata (`scenarios`) is readable; prompt text lives in `scenario_prompts` (versioned, service-role only) so users can't extract prompts via the Data API.
5. **PK strategy:** `uuid` (= `auth.users.id`) for `profiles`; `bigint generated always as identity` everywhere else (per Postgres best practice — sequential, compact; rows are shielded by RLS so sequential IDs leak nothing).
6. **RLS patterns:** enabled on every table; `(select auth.uid())` wrapping; `TO authenticated` + ownership predicate; `USING` + `WITH CHECK` on updates; index every column used in a policy predicate. `waitlist` is the sole anon-INSERT table.
7. **Media stays out of Postgres.** Audio and handwriting canvas images go to object storage; tables store URLs/paths only (JSONB reserved for genuinely unstructured model output like phoneme detail).

### Tables (16)

| Group | Tables |
|---|---|
| Identity | `profiles` (1:1 `auth.users`, auto-created by trigger) |
| Monetization | `plans`, `subscriptions`, `founder_pass_purchases`, `waitlist` |
| Usage/quotas | `daily_usage` |
| Content | `lessons`, `lesson_phrases`, `scenarios`, `scenario_prompts` |
| Activity | `pronunciation_attempts`, `handwriting_attempts`, `conversation_sessions`, `conversation_messages` |
| Progress | `lesson_progress`, `scenario_progress` |

Full column-level rationale ships in `docs/schema.md` (a Task 1 requirement).

### Task 2 — Barista prompt

Target model: **Llama-3 Instruct** (stated pipeline), so the prompt is few-shot-heavy and JSON-strict. Persona: “민지 (Minji)”, polite Seoul café barista, 해요체, ≤2 short sentences, one question at a time. Exact 4-key JSON schema (`ai_response_hangul`, `ai_response_romanized`, `ai_response_english`, `contextual_correction`), no markdown, no extra keys; `contextual_correction` is `""` unless the user made a contextual mistake (never grammar lectures unless asked). Revised Romanization. English input → stay in Korean, coach via correction field. Off-topic/injection → stay in character, still JSON. Delivered as `prompts/scenarios/cafe_iced_americano_v1.md` with FastAPI integration notes (pydantic validation, one repair retry); same text seeded into `scenario_prompts` v1.

## Verification

Migration is executed against a throwaway Dockerized Postgres with stubbed `auth` schema (`auth.users`, `auth.uid()`) and Supabase roles (`anon`, `authenticated`, `service_role`) to confirm it applies cleanly end-to-end.

## Out of scope

App code, Stripe webhook handlers, Supabase project provisioning, storage bucket policies, additional scenarios/lessons beyond seed samples.
