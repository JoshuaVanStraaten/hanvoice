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
