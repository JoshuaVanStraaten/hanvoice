# Lesson blocks & the Hangul curriculum — design

**Date:** 2026-07-04 · **Status:** approved (founder mission 2026-07-04; schema change approved-in-principle in HANDOVER.md)

## Problem

Lessons today are phrase drills: `lessons → lesson_phrases`, one speak card per phrase.
That can't *teach* — there is nowhere to put "here is how a syllable block works",
no writing step, no comprehension check, no ordering of ideas. The founder decision:
the curriculum is the product spine; scenarios/conversations are a practice feature.

## Goal

A lesson becomes an ordered sequence of **content blocks** of mixed kinds, and the
Lessons tab becomes a course that teaches Korean from zero — starting with a complete
Hangul course, with the existing phrase lessons slotting in afterwards as speaking
units. Content stays data: authoring = INSERTs, no deploys.

**Definition of done:** open the app → start "What is Hangul?" → read a short
explanation → practice writing ㅏ → learn ㄱ → build 가 → speak it — one continuous
guided path with progress tracked. Full verification green; live app demonstrably working.

**Non-goals:** CMS/admin UI, spaced repetition, hard lesson locking.

## Approaches considered

1. **Pure JSONB blocks** (the handover sketch as written): every block, including
   speak, carries its content in a JSONB payload. Rejected: the entire existing speak
   loop is keyed on `lesson_phrases.id` — the TTS endpoint is deliberately locked to
   phrase ids (bounds TTS spend), `pronunciation_attempts.phrase_id` powers per-phrase
   analytics, and the progress service walks phrases. Embedding speak text in payloads
   orphans all of that.
2. **Per-kind detail tables** (`explain_blocks`, `speak_blocks`, …): four tables and
   joins for content that is always read whole, in order. No integrity win worth the
   surface area.
3. **Hybrid (chosen):** one `lesson_blocks` table with `kind` + JSONB `payload`, plus
   a typed `phrase_id` FK that speak blocks are required (CHECK) to carry. Speak
   blocks reuse the phrase machinery unchanged; explain/write/quiz are payload-shaped.

## Schema (new migration, mirrored in seed.sql)

```sql
create table public.lesson_blocks (
  id bigint generated always as identity primary key,
  lesson_id bigint not null references public.lessons (id) on delete cascade,
  kind text not null check (kind in ('explain', 'speak', 'write', 'quiz')),
  phrase_id bigint references public.lesson_phrases (id) on delete cascade,
  payload jsonb not null default '{}'::jsonb,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  check (kind <> 'speak' or phrase_id is not null)
);
-- RLS: select-only for authenticated where the parent lesson is published
-- (same pattern as lesson_phrases). Index (lesson_id, sort_order).

create table public.lesson_block_progress (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  block_id bigint not null references public.lesson_blocks (id) on delete cascade,
  passed boolean not null default false,
  best_score numeric(5, 2) check (best_score between 0 and 100),
  passed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, block_id)
);
-- RLS: users select their own rows; writes are backend-only (service role).
```

Alterations:

- `lessons` gains `section text not null default ''` — a display group label
  ("Read & write Hangul", "Speak"). The lessons list renders section headers; this is
  what makes 13 lessons read as a course instead of a pile.
- `lesson_progress.phrases_completed` → renamed `blocks_completed` (semantics
  generalize; pre-launch with one test account, a rename is safe and honest —
  no compat column).
- **Backfill in the migration:** one `speak` block per existing `lesson_phrases` row
  (`sort_order` copied). On a fresh `db reset` the migration backfill is a no-op
  (runs before seed), so `seed.sql` ends with the same generic
  `insert … select from lesson_phrases` statement.

Speak targets for the Hangul course (가, 안, 가요 …) are **new `lesson_phrases` rows**
in their lessons — that is what keeps TTS, attempts analytics, and the speak loop working.

## Pass semantics per kind (the contract)

| kind | content (payload) | how it passes |
|---|---|---|
| `explain` | `{"segments": [...]}` (see below) | client POSTs complete on "Continue" — reading is inherently self-attested |
| `speak` | none (uses `phrase_id`) | existing `POST /pronunciation/attempts` gains optional `block_id`; backend verifies the block is a `speak` block whose `phrase_id` matches, marks passed at overall ≥ 60 (existing `PASS_THRESHOLD`) |
| `write` | `{"target": "ㅏ", "hint": "..."}` | existing `POST /handwriting/attempts` gains optional `block_id`; backend verifies kind + target match, marks passed at overall ≥ 60 |
| `quiz` | `{"question", "choices": [...], "answer": <index>, "explanation"}` | client checks locally (retry until right), POSTs complete on correct answer |

Speak/write completion stays **server-verified** — a user still cannot forge a score,
consistent with the schema's security model. Quiz answers being client-readable is
accepted: they are not IP, and cheating on your own learning is self-defeating.

`explain` payload segments (structured JSON, no markdown dependency):

```json
{"segments": [
  {"type": "text",    "body": "Plain prose. **bold** supported."},
  {"type": "chars",   "items": [{"ko": "ㅏ", "label": "a", "note": "open 'ah', as in father"}]},
  {"type": "example", "items": [{"ko": "가요", "roman": "gayo", "en": "I go"}]},
  {"type": "tip",     "body": "One-liner callout."}
]}
```

`chars` renders big-glyph jamo/syllable cards; `example` renders ko/roman/en rows;
this is why a constrained structure beats freeform markdown for teaching Hangul.

## API surface

- `GET /lessons` — summaries gain `section` and `block_count` (replaces `phrase_count`).
- `GET /lessons/{slug}` — returns ordered `blocks` (id, kind, payload, phrase
  embedded for speak blocks) **plus the caller's per-block `passed` state**, so the
  player can resume at the first unpassed block.
- `POST /lessons/blocks/{block_id}/complete` — explain/quiz only (400 for
  speak/write); upserts block progress, updates the lesson rollup.
- `POST /pronunciation/attempts` and `POST /handwriting/attempts` — optional
  `block_id`; on pass, upsert block progress + lesson rollup.
- `GET /progress` — lesson items report `blocks_completed` / `block_count`.

Rollup: `blocks_completed` = count of passed blocks in the lesson; lesson `completed`
when all blocks passed; `best_pronunciation_score` unchanged (still from phrase attempts).

## Frontend

- **LessonsPage** — groups lessons by `section` with headers; meter shows blocks
  passed; "Continue" affordance points at the next unfinished lesson. Soft guidance,
  no hard locks (frustration > discipline for a beginner app; also YAGNI).
- **LessonDetailPage** — becomes a block player: one block at a time, progress dots,
  Continue advances, resumes at first unpassed block. Speak blocks reuse the existing
  phrase card loop (RecordButton + scoring UI); write blocks reuse the canvas.
- **Canvas extraction** — the drawing canvas + guide + scoring moves from
  `WritingPage` into a shared `HangulCanvas` component; the standalone Write tab
  keeps working as free practice.

## Curriculum content (authored as INSERTs, live + seed.sql mirror)

Section **"Read & write Hangul"** (new lessons 1–8), then section **"Speak"**
(existing 5 phrase lessons re-ordered after, each backfilled with speak blocks):

1. **What is Hangul?** — blocks/jamo concept, why it's learnable in a week; quizzes.
2. **First vowels** — ㅏㅓㅗㅜㅡㅣ: mouth-shape explains, write ㅏ ㅓ ㅗ, quizzes.
3. **First consonants** — ㄱㄴㄷㄹㅁ: shape-mimics-mouth explains, write ㄱ ㄴ ㅁ, quizzes.
4. **Building syllables** — L+V stacking (가 vs 고), silent ㅇ; write 가; **speak 가,
   아, 나** (the DoD path lives here); quizzes.
5. **More consonants & vowels** — ㅂㅅㅇㅈㅎ, ㅑㅕㅛㅠ (y-vowels); writes, quizzes, speaks.
6. **Batchim** — final consonants, the 7 representative sounds (lite); write 안; speak 안, 밥.
7. **Sound changes (lite)** — linking (밥이 → 바비) and nasalization (합니다 → 함니다);
   quizzes; speak 감사합니다.
8. **Reading practice + 해요체 intro** — read real words (커피, 서울, 김치), the 요
   politeness ending; reading quizzes; speak 가요, 커피 주세요.

Azure scores single syllables noisily; accepted at threshold 60 (targets are chosen
to be pronounceable units — syllables and words, never bare consonants).

## Testing

- Backend: route tests for block listing (published-only), complete endpoint
  (kind gating, rollup math), block-aware pronunciation/handwriting attempts
  (pass/fail marks progress correctly). Same fake-DB pattern as existing 89 tests.
- Frontend: player component tests (block rendering per kind, advance/resume logic),
  quiz interaction; existing suites stay green.
- Live: Playwright walkthrough of the DoD path on the running app.
