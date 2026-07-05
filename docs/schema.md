# HanVoice Database Schema

PostgreSQL schema for Supabase. Source of truth: [`supabase/migrations/20260703090000_initial_schema.sql`](../supabase/migrations/20260703090000_initial_schema.sql) plus [`supabase/migrations/20260704110000_lesson_blocks.sql`](../supabase/migrations/20260704110000_lesson_blocks.sql). Sample content: [`supabase/seed.sql`](../supabase/seed.sql).

## Security model (read this first)

Two write paths exist, and the distinction is the whole design:

1. **Client → Supabase (anon/authenticated key).** Users can read their own rows everywhere, update their own profile, and join the waitlist. That's it.
2. **FastAPI backend → Supabase (service-role key).** Everything else — scores, conversation transcripts, usage counters, billing state, progress rollups — is written only by the backend, because the backend is the only party we trust to have actually called Azure/Llama/Nemotron and metered the cost.

Consequences:

- A user cannot forge a 100% pronunciation score, reset today's quota, or grant themselves a founder pass, even with their own JWT and direct PostgREST access.
- RLS is enabled on **every** table, including backend-only ones (no policies = no client access).
- All policies use the audited fast pattern: `to authenticated using ((select auth.uid()) = user_id)` — the `select` wrapper makes Postgres evaluate `auth.uid()` once per query instead of once per row, and every column referenced in a policy is indexed.

Primary keys: `profiles` uses the `auth.users` uuid; all other tables use `bigint generated always as identity` (sequential, compact, index-friendly; RLS means sequential IDs expose nothing).

## Tables

### Identity

#### `profiles`
**Why it exists:** Supabase manages `auth.users` and you should never add app columns to it — it's owned by the auth service and can change between upgrades. `profiles` is the app-owned 1:1 extension (display name, native language, onboarding state), auto-created by a trigger the moment a user signs up, so application code can always assume it exists. This is the schema's answer to both "users" and "authentication integration": auth stays in `auth.users`, app data lives here, and every other table references the same uuid.

### Monetization

#### `plans`
**Why it exists:** Quota limits and prices are business levers that will change often (launch promos, tuning free-tier cost). Storing them as rows — `free`, `founder`, `premium`, each with per-day limits for pronunciation checks, conversation turns, LLM tokens, and handwriting checks — means adjusting a tier is an `UPDATE`, not a code deploy. Publicly readable (`is_active` only) so the landing page can render pricing without an API hop.

#### `subscriptions`
**Why it exists:** Mirrors the recurring-billing lifecycle from the payment provider (Stripe-shaped: status, period boundaries, `cancel_at_period_end`, provider IDs). Written only by backend webhook handlers; users can read their own. A partial unique index guarantees at most one live (trialing/active/past_due) subscription per user while preserving canceled history rows for support and analytics.

#### `founder_pass_purchases`
**Why it exists:** The $69 Lifetime Founder Pass is a one-time payment, not a subscription — different provider object, no renewal lifecycle, never expires. Modeling it as a fake "subscription" row would poison every renewal/dunning query. `UNIQUE(user_id)` enforces one pass per person. Entitlement resolution in the backend is: founder pass row → founder tier; else live subscription → its plan; else free.

#### `waitlist`
**Why it exists:** Phase-1 marketing needs email capture before accounts exist, so this can't hang off `auth.users`. The only table with an anonymous INSERT policy — and no client SELECT policy, so the list can't be scraped. Unique on `lower(email)` prevents duplicates; `source` tracks which campaign converted.

### Usage metering / quotas

#### `daily_usage`
**Why it exists:** Every AI feature costs real money per call, so paid tiers are only enforceable if usage is metered where it can't be tampered with. One wide row per `(user_id, usage_date)` with a counter per metric (attempts, turns, tokens in/out, TTS seconds, handwriting checks). The backend does one atomic upsert-increment per event and one indexed read to answer "is this user over their plan's limit today?" — O(1) regardless of history size. Client access is read-only, which doubles as the data source for a "daily usage" meter in the UI.

### Learning content (ours, read-only to users)

#### `lessons`
**Why it exists:** The curriculum container — "What is Hangul?", "Café essentials". In the database rather than code so new content ships instantly and `is_published` lets us stage drafts. Users see published lessons only. `section` is a display group label ("Read & write Hangul" / "Speak") that makes the lessons list read as a course.

#### `lesson_blocks`
**Why it exists:** A lesson that *teaches* is an ordered sequence of mixed steps, not a flat phrase list. One row per step: `kind` ∈ `explain | speak | write | quiz` with a JSONB `payload` for the kind-specific content (explain segments, write target + hint, quiz question/choices/answer). Speak blocks carry a **required `phrase_id` FK** instead of a payload — that is what lets them reuse the whole existing pronunciation stack (TTS locked to phrase ids, attempt analytics, best-score rollups) unchanged. Read-only to users via the parent lesson's `is_published`, like `lesson_phrases`.

Payload shapes (documented, not constrained — content is trusted, authored by us):
- `explain`: `{"segments": [{"type": "text|tip", "body"}, {"type": "chars", "items": [{ko, label?, note?, audio?}]}, {"type": "example", "items": [{ko, roman?, en?, audio?}]}]}`
- `write`: `{"target": "ㅏ", "hint": "...", "audio"?: "..."}`
- `quiz`: `{"question", "choices": [...], "answer": <index>, "explanation"}`

Every taught glyph is audible via `GET /lessons/blocks/{id}/audio?text=…`. The
optional `audio` field overrides what TTS speaks for an item; without it, bare
jamo fall back to a fixed carrier-syllable map in code (consonants ride ㅏ:
ㄱ → 가; vowels ride silent ㅇ: ㅏ → 아) and anything else is spoken as-is. The
endpoint only accepts texts derivable from the block's own payload by that
rule, so TTS spend stays bounded by authored content.

#### `lesson_phrases`
**Why it exists:** The speakable chunk ("물 주세요", or a single syllable like "가" in the Hangul course), so it gets its own table: hangul, romanization, English, reference-audio URL, ordered within a lesson. Pronunciation attempts point back at the phrase they practiced, which is what makes "your 아 improved this week" analytics possible. Every phrase is referenced by at least one speak block.

#### `scenarios`
**Why it exists:** Client-facing metadata for immersive conversations ("Order an iced Americano in a Seoul café"): title, description, difficulty, and `completion_goals` (a JSON list like `["greeted", "ordered_drink", "paid"]`) that the backend checks off during the conversation to decide when the scenario is passed.

#### `scenario_prompts`
**Why it exists:** Deliberately split from `scenarios` because RLS is row-level, not column-level: if the system prompt were a column on `scenarios`, any authenticated user could read our prompt IP through the Data API. This table has no client policies at all (service-role only) and is versioned — `(scenario_id, version)` — so prompts can be iterated, A/B tested, and rolled back, and every conversation can be traced to the exact prompt version that produced it.

### Learner activity (backend-written)

#### `pronunciation_attempts`
**Why it exists:** One row per Azure Pronunciation Assessment call: accuracy, fluency, completeness, overall (the exact scores Azure returns), plus per-phoneme detail as JSONB — kept unstructured because Azure's phoneme payload is deep, variable, and only ever consumed whole by the UI. Audio lives in object storage (`audio_url`), never in Postgres. This history powers progress charts, streaks, and the Phase-1 "AI roasts my pronunciation" content.

#### `handwriting_attempts`
**Why it exists:** Same pattern for Nemotron-VL handwriting checks, with the scores the vision model is asked for (proportions, stroke placement, legibility). Canvas images are uploaded to storage and referenced by path — base64 blobs in the database would bloat it and slow every backup. `model_version` is recorded because vision-model scores aren't comparable across model upgrades.

#### `conversation_sessions`
**Why it exists:** Groups one run of a scenario: who, which scenario, active/completed/abandoned, and which completion goals were hit. Sessions are what make "resume conversation", per-scenario attempt counts, and session-level analytics (where do beginners give up?) possible.

#### `conversation_messages`
**Why it exists:** The full transcript, one row per turn. Assistant rows store exactly the four fields of the model's JSON contract (hangul / romanized / english / contextual_correction); user rows store the ASR transcript. This is what the backend replays to the LLM as context, what the user reviews afterwards, and the raw material for improving prompts. Ownership is enforced through the parent session's `user_id`.

### Progress

#### `lesson_block_progress`
**Why it exists:** Blocks are the unit of pass/fail, so pass state lives per `(user, block)`: `passed`, `best_score`, `passed_at`. Written only by the backend — explain/quiz complete via `POST /lessons/blocks/{id}/complete` (self-attested by design; reading can't be verified), while speak/write are marked only when a backend-scored attempt clears the 60 threshold, so a user still cannot forge a score. Never downgrades: a failed retry after a pass keeps the pass and the best score.

#### `lesson_progress`
**Why it exists:** The home screen needs "3 of 9 steps done, best score 82" for every lesson at render time. Computing that by aggregating block progress on every load gets slower forever; this per-`(user, lesson)` rollup (`blocks_completed`, renamed from `phrases_completed` in the lesson_blocks migration), updated by the backend after each block outcome, keeps it one indexed read. `best_pronunciation_score` still derives from phrase attempts only.

#### `scenario_progress`
**Why it exists:** Same rollup for scenarios — status, `times_completed`, link to the most recent session — driving the scenario map UI and the key activation metric: *did this user complete a conversation in week one?*

## Conventions

- `created_at`/`updated_at` are `timestamptz`; `updated_at` maintained by a shared `set_updated_at()` trigger.
- Scores are `numeric(5,2)` constrained to 0–100, matching provider score ranges.
- JSONB only where the payload is genuinely unstructured model output (`phoneme_detail`, `feedback`, `goals_completed`); everything queried or constrained is a typed column.
- Media (audio, images) always in object storage, referenced by URL/path.

## Deliberately deferred (YAGNI)

Streak/gamification tables (derivable from `daily_usage` until product demands more), a generic `events` analytics table (use a product-analytics tool), table partitioning of attempt tables (revisit past tens of millions of rows), and storage bucket policies (separate task alongside the upload code).
