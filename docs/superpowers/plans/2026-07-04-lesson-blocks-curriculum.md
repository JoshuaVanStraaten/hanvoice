# Lesson Blocks & Hangul Curriculum Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Lessons into a real course — ordered mixed-kind content blocks (explain / speak / write / quiz) with per-block progress, plus a complete 8-lesson Hangul course authored as data.

**Architecture:** One new `lesson_blocks` table (`kind` + JSONB payload; speak blocks carry a required `phrase_id` FK so the existing pronunciation/TTS/analytics stack is reused unchanged) and a `lesson_block_progress` rollup source. `lesson_progress.phrases_completed` generalizes to `blocks_completed`. The lesson page becomes a block player. Spec: `docs/superpowers/specs/2026-07-04-lesson-blocks-curriculum-design.md`.

**Tech Stack:** Supabase Postgres (migration via MCP `apply_migration`, mirrored in `supabase/seed.sql`), FastAPI + Pydantic (respx-mocked tests), React + TanStack Query + Vitest.

**Verification commands** (all must be green before "done"):

- Backend: `backend/.venv/Scripts/python -m ruff check .` · `-m mypy .` · `-m pytest` (run from `backend/`)
- Frontend: `npm run lint` · `npm run typecheck` · `npm test` · `npm run build` (from `frontend/`)
- Live: Playwright walkthrough of the DoD path (M5).

---

## Milestone 1 — Schema: `lesson_blocks` migration, live + seed mirror

### Task 1.1: Write the migration

**Files:**
- Create: `supabase/migrations/20260704110000_lesson_blocks.sql`

- [ ] **Step 1: Write the migration file** (complete content):

```sql
-- Lessons become ordered sequences of mixed-kind content blocks so the
-- curriculum can teach (explain/write/quiz), not just drill phrases.
-- Speak blocks reference lesson_phrases so the whole existing pronunciation
-- stack (TTS locked to phrase ids, attempt analytics, rollups) is reused.

-- Display grouping for the lessons list ("Read & write Hangul" / "Speak").
alter table public.lessons add column section text not null default '';

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

alter table public.lesson_blocks enable row level security;

create index lesson_blocks_lesson_id_idx on public.lesson_blocks (lesson_id, sort_order);
create index lesson_blocks_phrase_id_idx on public.lesson_blocks (phrase_id);

create policy "Users can view blocks of published lessons"
  on public.lesson_blocks for select
  to authenticated
  using (
    exists (
      select 1 from public.lessons l
      where l.id = lesson_id and l.is_published
    )
  );

-- Per-user pass state per block. Backend-written only (no client write
-- policies): speak/write passes are verified against real scored attempts.
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

alter table public.lesson_block_progress enable row level security;

create index lesson_block_progress_block_idx on public.lesson_block_progress (block_id);

create trigger lesson_block_progress_set_updated_at
  before update on public.lesson_block_progress
  for each row execute function public.set_updated_at();

create policy "Users can view own block progress"
  on public.lesson_block_progress for select
  to authenticated
  using ((select auth.uid()) = user_id);

-- The rollup counts blocks now, not phrases.
alter table public.lesson_progress rename column phrases_completed to blocks_completed;

-- Existing phrase lessons become speaking units: one speak block per phrase,
-- and they move behind the Hangul course in the list. No-ops on a fresh
-- database (seed.sql handles fresh environments).
insert into public.lesson_blocks (lesson_id, kind, phrase_id, sort_order)
select lesson_id, 'speak', id, sort_order from public.lesson_phrases;

update public.lessons set section = 'Speak', sort_order = sort_order + 10;
```

- [ ] **Step 2: Apply to the live `hanvoice` project** (`mxibibkcaarltsbkomvm`) via MCP `apply_migration` with name `lesson_blocks`. Verify with `list_tables` (both tables present, `lessons.section` exists) and a `select kind, count(*) from lesson_blocks group by kind` (expect 25 speak).

- [ ] **Step 3: Run `get_advisors` (security)** — expect no new findings for the two tables.

### Task 1.2: Mirror in seed.sql

**Files:**
- Modify: `supabase/seed.sql`

- [ ] **Step 1:** Update the five existing lesson INSERTs: add `section` column value `'Speak'` and change `sort_order` 1–5 → 11–15.
- [ ] **Step 2:** Append at the end (after all phrase inserts):

```sql
-- Every phrase is a speak block; on a fresh database the migration backfill
-- ran before seed and found nothing, so seed creates them here.
insert into public.lesson_blocks (lesson_id, kind, phrase_id, sort_order)
select lesson_id, 'speak', id, sort_order from public.lesson_phrases;
```

(The Hangul course content itself is Milestone 4 and gets its own seed section.)

- [ ] **Step 3: Commit** — `git commit -m "feat(db): lesson_blocks + block progress migration, seed mirror"`

---

## Milestone 2 — Backend: blocks API + per-block progress

### Task 2.1: Factories & content repo

**Files:**
- Modify: `backend/tests/factories.py`, `backend/app/db/repositories/content.py`

- [ ] **Step 1: Add factories**:

```python
def block_row(block_id: int = 1, kind: str = "explain", **overrides: Any) -> dict[str, Any]:
    return {
        "id": block_id,
        "lesson_id": 1,
        "kind": kind,
        "phrase_id": None,
        "payload": {"segments": [{"type": "text", "body": "Hangul is an alphabet."}]},
        "sort_order": block_id,
        **overrides,
    }


def block_progress_row(block_id: int = 1, **overrides: Any) -> dict[str, Any]:
    return {
        "id": 1,
        "user_id": TEST_USER_ID,
        "block_id": block_id,
        "passed": True,
        "best_score": None,
        "passed_at": "2026-07-04T10:00:00+00:00",
        **overrides,
    }
```

Also update `lesson_row` to include `"section": ""`.

- [ ] **Step 2: Repo functions** in `content.py`:

```python
async def list_lesson_blocks(db: Database, lesson_id: int) -> list[JsonRow]:
    return await db.select(
        "lesson_blocks",
        columns="id,lesson_id,kind,phrase_id,payload,sort_order",
        filters={"lesson_id": f"eq.{lesson_id}"},
        order="sort_order.asc",
    )


async def get_block(db: Database, block_id: int) -> JsonRow:
    row = await db.select_one(
        "lesson_blocks",
        columns="id,lesson_id,kind,phrase_id,payload",
        filters={"id": f"eq.{block_id}"},
    )
    if row is None:
        raise NotFoundError("Block not found.")
    return row


async def list_speak_blocks_for_phrase(db: Database, phrase_id: int) -> list[JsonRow]:
    return await db.select(
        "lesson_blocks",
        columns="id,lesson_id,kind,phrase_id",
        filters={"phrase_id": f"eq.{phrase_id}", "kind": "eq.speak"},
    )
```

`list_published_lessons` gains `section` in its column list.

### Task 2.2: Progress repo & service (block semantics)

**Files:**
- Modify: `backend/app/db/repositories/progress.py`, `backend/app/services/progress.py`

- [ ] **Step 1: Progress repo** — rename `phrases_completed` kwarg/field to `blocks_completed`; add:

```python
async def upsert_block_progress(
    db: Database, user_id: UUID, block_id: int, *, passed: bool, best_score: float | None
) -> None:
    values: JsonRow = {
        "user_id": str(user_id),
        "block_id": block_id,
        "passed": passed,
        "best_score": best_score,
    }
    if passed:
        values["passed_at"] = datetime.now(UTC).isoformat()
    await db.upsert("lesson_block_progress", values, on_conflict="user_id,block_id")


async def list_block_progress(
    db: Database, user_id: UUID, block_ids: list[int]
) -> list[JsonRow]:
    if not block_ids:
        return []
    return await db.select(
        "lesson_block_progress",
        filters={
            "user_id": f"eq.{user_id}",
            "block_id": f"in.({','.join(str(b) for b in block_ids)})",
        },
    )
```

Guard in `upsert_block_progress`: never downgrade — read existing row first; keep `passed=True` and the max `best_score` (a failed retry after a pass must not unpass a block).

- [ ] **Step 2: Progress service** — replace `update_after_pronunciation` with block-centric functions:

```python
async def mark_block_result(
    db: Database, user_id: UUID, block: JsonRow, *, score: float | None, passed: bool
) -> None:
    """Record a block outcome and refresh the lesson rollup."""
    await progress_repo.upsert_block_progress(
        db, user_id, int(block["id"]), passed=passed, best_score=score
    )
    await _refresh_lesson_rollup(db, user_id, int(block["lesson_id"]))


async def _refresh_lesson_rollup(db: Database, user_id: UUID, lesson_id: int) -> None:
    blocks = await content.list_lesson_blocks(db, lesson_id)
    block_ids = [int(b["id"]) for b in blocks]
    rows = await progress_repo.list_block_progress(db, user_id, block_ids)
    passed = sum(1 for r in rows if r["passed"])
    phrases = await content.list_lesson_phrases(db, lesson_id)
    best = await attempts.best_lesson_score(db, user_id, [int(p["id"]) for p in phrases])
    await progress_repo.upsert_lesson_progress(
        db, user_id, lesson_id,
        blocks_completed=passed, best_score=best,
        completed=bool(block_ids) and passed == len(block_ids),
    )


async def update_after_pronunciation(
    db: Database, user_id: UUID, phrase: JsonRow, score: float
) -> None:
    """A scored phrase attempt passes every speak block that references it."""
    for block in await content.list_speak_blocks_for_phrase(db, int(phrase["id"])):
        await mark_block_result(
            db, user_id, block, score=score, passed=score >= PASS_THRESHOLD
        )
```

The pronunciation route keeps calling `update_after_pronunciation` (now passing `scores.overall`) — **no external API change for speak**; the backend resolves the speak block(s) from the phrase.

### Task 2.3: Content routes — blocks in lesson detail + complete endpoint

**Files:**
- Modify: `backend/app/schemas/content.py`, `backend/app/api/routes/content.py`
- Test: `backend/tests/test_content_routes.py`, create `backend/tests/test_lesson_blocks.py`

- [ ] **Step 1: Failing tests** (`test_lesson_blocks.py`): lesson detail returns ordered blocks with `passed` flags (mock `lesson_blocks`, `lesson_block_progress`, `lesson_phrases`); speak blocks embed their phrase; `POST /api/lessons/blocks/1/complete` on an `explain` block returns 200 and upserts progress + rollup; complete on a `speak` block → 400; unknown block → 404; unpublished lesson → 404. Update `test_content_routes.py`: `block_count` replaces `phrase_count`.
- [ ] **Step 2: Run tests, verify they fail.**
- [ ] **Step 3: Schemas:**

```python
class LessonBlock(BaseModel):
    id: int
    kind: Literal["explain", "speak", "write", "quiz"]
    payload: dict[str, Any] = Field(default_factory=dict)
    phrase: LessonPhrase | None = None
    sort_order: int
    passed: bool = False


class LessonSummary(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    section: str = ""
    sort_order: int
    block_count: int = 0


class LessonDetail(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    section: str = ""
    blocks: list[LessonBlock]


class BlockCompleteResponse(BaseModel):
    block_id: int
    passed: bool
    blocks_completed: int
    block_count: int
    lesson_completed: bool
```

- [ ] **Step 4: Routes:** `list_lessons` counts blocks; `get_lesson` assembles blocks + phrase embeds (one `lesson_phrases` fetch, dict by id) + the caller's `list_block_progress`; new:

```python
@router.post("/lessons/blocks/{block_id}/complete", response_model=BlockCompleteResponse)
async def complete_block(block_id: int, user: CurrentUser, db: Db) -> BlockCompleteResponse:
    block = await content.get_block(db, block_id)
    lesson = await content.get_published_lesson_by_id(db, int(block["lesson_id"]))
    if block["kind"] not in ("explain", "quiz"):
        raise BadRequestError("This block is completed by a scored attempt, not directly.")
    await progress_service.mark_block_result(db, user.id, block, score=None, passed=True)
    ...  # re-read rollup for the response counts
```

(`get_published_lesson_by_id` is a small new repo function mirroring `get_published_lesson` with an id filter — 404s for unpublished, so drafts can't be completed.)

- [ ] **Step 5: Handwriting route** — request schema gains `block_id: int | None = None`; after scoring, if given: fetch block, require `kind == 'write'`, require `payload["target"] == body.target_text` (400 otherwise), then `mark_block_result(..., score=scores.overall_score, passed=scores.overall_score >= 60)`. Pronunciation route: change the `update_after_pronunciation` call to pass `scores.overall`.
- [ ] **Step 6: Progress route/schema** — `LessonProgressItem.phrases_completed/phrase_count` → `blocks_completed/block_count`; route counts blocks instead of phrases.
- [ ] **Step 7: Run the full backend gate** (ruff, mypy, pytest) — all green.
- [ ] **Step 8: Commit** — `feat(api): lesson blocks, per-block progress, complete endpoint`.

---

## Milestone 3 — Frontend: lesson player

### Task 3.1: Types & hooks

**Files:**
- Modify: `frontend/src/lib/types.ts`, `frontend/src/hooks/queries.ts`

- [ ] **Step 1:** Mirror the backend: `LessonBlock` (discriminated by `kind`, with typed payloads `ExplainPayload {segments}`, `WritePayload {target, hint}`, `QuizPayload {question, choices, answer, explanation}`), `LessonSummary.section/block_count`, `LessonDetail.blocks`, progress items `blocks_completed/block_count`. Add `useCompleteBlock` mutation posting `/lessons/blocks/{id}/complete`, invalidating `["lesson", slug]` + progress on success.

### Task 3.2: Extract `HangulCanvas` from WritingPage

**Files:**
- Create: `frontend/src/components/HangulCanvas.tsx`
- Modify: `frontend/src/pages/WritingPage.tsx`

- [ ] **Step 1:** Move the canvas + guide + strokes + undo/clear/guide-toggle + PNG export into `<HangulCanvas target={string} onSubmit={(png: string) => void} submitting={bool} />` (all existing drawing code moves verbatim; the 12px-stroke and white-composite gotchas travel with it). WritingPage keeps its target picker and result display, submits without `block_id`. Existing behavior unchanged.

### Task 3.3: Block player page

**Files:**
- Create: `frontend/src/components/blocks/ExplainBlock.tsx`, `SpeakBlock.tsx`, `WriteBlock.tsx`, `QuizBlock.tsx`
- Rewrite: `frontend/src/pages/LessonDetailPage.tsx`
- Test: `frontend/src/components/blocks/blocks.test.tsx`

- [ ] **Step 1: Failing tests:** explain renders segments (text/chars/example/tip) and fires `onPassed` on Continue; quiz disables Continue until the right choice, shows explanation, fires `onPassed`; player resumes at first unpassed block and advances.
- [ ] **Step 2: Implement.** Player skeleton:

```tsx
const blocks = lesson.data.blocks;
const firstUnpassed = blocks.findIndex((b) => !b.passed);
const [index, setIndex] = useState(firstUnpassed === -1 ? 0 : firstUnpassed);
// progress dots header; block body by kind; each block calls onPassed →
// completeBlock (explain/quiz) or is marked server-side (speak/write) →
// invalidate + setIndex(i + 1); finish screen when past the last block.
```

SpeakBlock reuses the existing phrase-card loop (RecordButton, `AttemptResult`, ListenButton — move those helpers out of the old page into `SpeakBlock.tsx`); passing is detected from `attempt.scores.overall >= 60` and the refetched lesson. WriteBlock = `HangulCanvas` + score rings, posts with `block_id`. Explain text segments support `**bold**` only.

- [ ] **Step 3:** LessonsPage: group by `section`, meter = blocks; DashboardPage check (it may reference phrase counts — align).
- [ ] **Step 4:** Full frontend gate (lint, typecheck, test, build) green.
- [ ] **Step 5: Commit** — `feat(web): lesson block player`.

---

## Milestone 4 — Content: the Hangul course (INSERTs, live + seed)

Authoring rules: every lesson `is_published = true`, section `'Read & write Hangul'`, sort_order 1–8. Speak targets are new `lesson_phrases` rows in their own lesson (romanized + english gloss included) with a matching `speak` block; never a bare consonant. Write targets come from the six vowels / five consonants the Write tab already teaches. Explain prose is written at execution time against this manifest (short — 2–4 segments per explain block, beginner tone, no linguistics jargon).

- [ ] **Step 1:** Author `supabase/seed_hangul_course.sql`-style content **directly in `seed.sql`** (new section between the scenario and lessons 2–5) and execute the same statements against live via MCP `execute_sql`, per lesson:

| # | slug · title | blocks (ordered) |
|---|---|---|
| 1 | `what-is-hangul` · What is Hangul? | explain (Sejong, 24 letters, designed to be learned in days) · explain (blocks = syllables, chars: 한 국) · quiz (Hangul is → "an alphabet whose letters stack into syllable blocks") · explain (letters draw the mouth, chars: ㄱ ㄴ ㅁ) · quiz (each block = one syllable) · explain (course roadmap + tip) |
| 2 | `first-vowels` · Your first vowels | explain (vertical vowels, chars: ㅏ ㅓ) · write ㅏ · write ㅓ · explain (horizontal vowels, chars: ㅗ ㅜ) · write ㅗ · quiz (which is "a" → ㅏ) · explain (chars: ㅡ ㅣ) · write ㅣ · quiz (ㅜ sounds like → "oo") |
| 3 | `first-consonants` · Your first consonants | explain (shape mimics mouth, chars: ㄱ ㄴ) · write ㄱ · write ㄴ · explain (chars: ㄷ ㄹ ㅁ) · write ㅁ · quiz (ㅁ → m) · quiz (ㄱ → g/k) |
| 4 | `building-syllables` · Building syllables | explain (C+V side/stack: 가 vs 고) · write 가 · **speak 가** · explain (silent ㅇ: 아 어 오) · speak 아 · quiz (write "na" → 나) · speak 나 · quiz (오 = "o", ㅇ silent) · explain (you can already read!) |
| 5 | `more-letters` · More consonants & the y-vowels | explain (chars: ㅂ ㅅ) · write ㅅ · explain (chars: ㅇ ㅈ ㅎ) · quiz (ㅈ → j) · explain (y-vowels double the tick, chars: ㅑ ㅕ ㅛ ㅠ) · quiz (ㅕ → yeo) · speak 야 · write 요 · speak 요 |
| 6 | `batchim` · Batchim — the final floor | explain (안 = ㅇ+ㅏ+ㄴ, chars: 안 밥 강) · quiz (안 decomposition) · write 안 · speak 안 · explain (7 representative sounds, lite) · speak 밥 · quiz (final ㅇ → "ng") |
| 7 | `sound-changes` · Why words sound different | explain (linking: 밥이 → 바비, examples) · quiz (밥이 → "ba-bi") · explain (nasalization: 합니다 → 함니다, example 감사합니다) · quiz (합니다 → "ham-ni-da") · speak 감사합니다 · explain (tip: your ear learns rules, not tables) |
| 8 | `read-and-say-it` · Read it, say it politely | explain (real words, chars: 커피 서울 김치) · quiz (커피 → coffee) · quiz (서울 → Seoul) · speak 커피 · explain (해요체: end in 요, examples 가요/와요/해요) · quiz (polite ending → 요) · speak 가요 · **speak 커피 주세요** (bridge to Café essentials) · explain (wrap: on to the Speak section) |

Payload shapes exactly as in the spec. Quiz `answer` is the index into `choices` (4 choices each, plausible distractors, one-sentence `explanation`).

- [ ] **Step 2:** Verify live: `select l.slug, count(b.id) from lessons l join lesson_blocks b ... group by 1 order by min(l.sort_order)` matches the manifest; app lesson list shows both sections.
- [ ] **Step 3:** Commit — `feat(content): complete Hangul course (8 lessons, ~60 blocks)`.

---

## Milestone 5 — Verification, live walkthrough, handover

- [ ] **Step 1:** Full backend + frontend gates (commands at top) — paste outputs.
- [ ] **Step 2:** Run backend + frontend locally; Playwright as the test account through the DoD path: open Lessons → "What is Hangul?" → read explain → (lesson 2) write ㅏ → (lesson 3) learn ㄱ → (lesson 4) build 가 → speak 가 → confirm progress meters advance and block passes persist across reload.
- [ ] **Step 3:** Update `docs/HANDOVER.md` (item 1 done, new schema noted, what's next: GitHub push) and `docs/schema.md` (two new tables + rename).
- [ ] **Step 4:** Final commit.

## Self-review notes

- Spec coverage: schema (M1), pass semantics incl. server-verified speak/write (M2), player + canvas extraction (M3), 8-lesson course incl. DoD path in lessons 1–4 (M4), live verification + docs (M5). ✓
- The pronunciation API is deliberately unchanged (block resolution by `phrase_id` server-side) — one less client contract.
- `lesson_progress.best_pronunciation_score` still derives from phrase attempts only; explain/quiz/write never affect it. ✓
