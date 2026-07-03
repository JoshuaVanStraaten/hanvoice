-- HanVoice — initial schema
-- Applies cleanly to a fresh Supabase project. Every table has RLS enabled.
-- Access model: users SELECT their own rows; the FastAPI backend (service_role)
-- performs all writes to scored/billable data so clients can never forge
-- scores, reset quotas, or edit billing state.

-- =============================================================================
-- Helper functions
-- =============================================================================

-- Keeps updated_at current on any table that has the column.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

revoke execute on function public.set_updated_at() from public, anon, authenticated;

-- =============================================================================
-- Identity
-- =============================================================================

-- App-level user data. 1:1 with auth.users (never add columns to auth.users).
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text not null default '',
  native_language text not null default 'en',
  onboarding_completed boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create trigger profiles_set_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

-- Auto-create a profile on signup. SECURITY DEFINER is required to insert
-- past RLS from the auth trigger context; execution is revoked from client
-- roles below. display_name from user_metadata is display-only, never used
-- for authorization.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, display_name)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'display_name', split_part(coalesce(new.email, ''), '@', 1))
  );
  return new;
end;
$$;

revoke execute on function public.handle_new_user() from public, anon, authenticated;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

create policy "Users can view own profile"
  on public.profiles for select
  to authenticated
  using ((select auth.uid()) = id);

create policy "Users can update own profile"
  on public.profiles for update
  to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

-- =============================================================================
-- Monetization
-- =============================================================================

-- Tier definitions with quota limits as data: changing a tier's daily limits
-- is an UPDATE, not a deploy. Backend reads these to enforce quotas.
create table public.plans (
  id text primary key,
  name text not null,
  price_usd_cents integer not null default 0 check (price_usd_cents >= 0),
  billing_period text not null check (billing_period in ('none', 'monthly', 'lifetime')),
  daily_pronunciation_limit integer not null check (daily_pronunciation_limit >= 0),
  daily_conversation_turn_limit integer not null check (daily_conversation_turn_limit >= 0),
  daily_llm_token_limit integer not null check (daily_llm_token_limit >= 0),
  daily_handwriting_limit integer not null check (daily_handwriting_limit >= 0),
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.plans enable row level security;

-- Pricing is public marketing data (landing page reads it pre-signup).
create policy "Anyone can view active plans"
  on public.plans for select
  to anon, authenticated
  using (is_active);

insert into public.plans
  (id, name, price_usd_cents, billing_period,
   daily_pronunciation_limit, daily_conversation_turn_limit,
   daily_llm_token_limit, daily_handwriting_limit)
values
  ('free',    'Free',                 0, 'none',     20,  10,  20000, 10),
  ('founder', 'Lifetime Founder Pass', 6900, 'lifetime', 200, 150, 300000, 100),
  ('premium', 'Premium',            1499, 'monthly',  200, 150, 300000, 100);

-- Recurring billing state mirrored from the payment provider via backend
-- webhooks. Kept separate from founder passes: different lifecycle
-- (recurring vs one-time) and different provider objects.
create table public.subscriptions (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  plan_id text not null references public.plans (id),
  status text not null check (status in ('trialing', 'active', 'past_due', 'canceled', 'incomplete')),
  provider text not null default 'stripe',
  provider_customer_id text,
  provider_subscription_id text unique,
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.subscriptions enable row level security;

create index subscriptions_user_id_idx on public.subscriptions (user_id);
-- At most one live subscription per user.
create unique index subscriptions_one_live_per_user_idx
  on public.subscriptions (user_id)
  where status in ('trialing', 'active', 'past_due');

create trigger subscriptions_set_updated_at
  before update on public.subscriptions
  for each row execute function public.set_updated_at();

create policy "Users can view own subscriptions"
  on public.subscriptions for select
  to authenticated
  using ((select auth.uid()) = user_id);

-- One-time $69 lifetime purchases, written by the backend after payment
-- confirmation. UNIQUE(user_id): a founder pass can only be bought once.
create table public.founder_pass_purchases (
  id bigint generated always as identity primary key,
  user_id uuid not null unique references auth.users (id) on delete cascade,
  provider text not null default 'stripe',
  provider_payment_id text unique,
  amount_usd_cents integer not null default 6900 check (amount_usd_cents > 0),
  purchased_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

alter table public.founder_pass_purchases enable row level security;

create policy "Users can view own founder pass"
  on public.founder_pass_purchases for select
  to authenticated
  using ((select auth.uid()) = user_id);

-- Pre-launch email capture from the landing page. The only table anonymous
-- visitors can write to; nobody but the backend can read it.
create table public.waitlist (
  id bigint generated always as identity primary key,
  email text not null,
  source text,
  created_at timestamptz not null default now()
);

alter table public.waitlist enable row level security;

create unique index waitlist_email_idx on public.waitlist (lower(email));

create policy "Anyone can join the waitlist"
  on public.waitlist for insert
  to anon, authenticated
  with check (true);

-- =============================================================================
-- Usage metering / quotas
-- =============================================================================

-- One wide row per user per UTC day. Quota check = one indexed read;
-- metering = one atomic upsert by the backend. This table is what keeps
-- AI spend bounded per tier.
create table public.daily_usage (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  usage_date date not null default ((now() at time zone 'utc')::date),
  pronunciation_attempts integer not null default 0 check (pronunciation_attempts >= 0),
  conversation_turns integer not null default 0 check (conversation_turns >= 0),
  llm_tokens_in bigint not null default 0 check (llm_tokens_in >= 0),
  llm_tokens_out bigint not null default 0 check (llm_tokens_out >= 0),
  tts_seconds integer not null default 0 check (tts_seconds >= 0),
  handwriting_checks integer not null default 0 check (handwriting_checks >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, usage_date)
);

alter table public.daily_usage enable row level security;

create trigger daily_usage_set_updated_at
  before update on public.daily_usage
  for each row execute function public.set_updated_at();

create policy "Users can view own usage"
  on public.daily_usage for select
  to authenticated
  using ((select auth.uid()) = user_id);

-- =============================================================================
-- Learning content (authored by us, read-only to users)
-- =============================================================================

-- A themed pack of phrase chunks ("Café essentials"). Content lives in the
-- DB so new lessons ship without a deploy.
create table public.lessons (
  id bigint generated always as identity primary key,
  slug text not null unique,
  title text not null,
  description text not null default '',
  sort_order integer not null default 0,
  is_published boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.lessons enable row level security;

create trigger lessons_set_updated_at
  before update on public.lessons
  for each row execute function public.set_updated_at();

create policy "Users can view published lessons"
  on public.lessons for select
  to authenticated
  using (is_published);

-- The tiny conversational chunks themselves — the core teaching unit.
create table public.lesson_phrases (
  id bigint generated always as identity primary key,
  lesson_id bigint not null references public.lessons (id) on delete cascade,
  hangul text not null,
  romanized text not null,
  english text not null,
  audio_url text,
  sort_order integer not null default 0,
  created_at timestamptz not null default now()
);

alter table public.lesson_phrases enable row level security;

create index lesson_phrases_lesson_id_idx on public.lesson_phrases (lesson_id, sort_order);

create policy "Users can view phrases of published lessons"
  on public.lesson_phrases for select
  to authenticated
  using (
    exists (
      select 1 from public.lessons l
      where l.id = lesson_id and l.is_published
    )
  );

-- Conversation scenario metadata ("Order an iced Americano"). The client
-- reads this; the system prompt deliberately does NOT live here.
create table public.scenarios (
  id bigint generated always as identity primary key,
  slug text not null unique,
  title text not null,
  description text not null default '',
  completion_goals jsonb not null default '[]'::jsonb,
  difficulty smallint not null default 1 check (difficulty between 1 and 5),
  sort_order integer not null default 0,
  is_published boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.scenarios enable row level security;

create trigger scenarios_set_updated_at
  before update on public.scenarios
  for each row execute function public.set_updated_at();

create policy "Users can view published scenarios"
  on public.scenarios for select
  to authenticated
  using (is_published);

-- Versioned system prompts, split out of scenarios so RLS can keep them
-- backend-only: prompts are IP and users must not be able to pull them
-- through the Data API. No client policies on purpose.
create table public.scenario_prompts (
  id bigint generated always as identity primary key,
  scenario_id bigint not null references public.scenarios (id) on delete cascade,
  version integer not null default 1,
  system_prompt text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (scenario_id, version)
);

alter table public.scenario_prompts enable row level security;

-- Defense in depth on top of "no policies = no access".
revoke all on public.scenario_prompts from anon, authenticated;

-- =============================================================================
-- Learner activity (written only by the backend)
-- =============================================================================

-- One row per Azure Pronunciation Assessment call: the raw material for
-- progress charts, streaks, and the "AI roasts my Korean" marketing clips.
create table public.pronunciation_attempts (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  phrase_id bigint references public.lesson_phrases (id) on delete set null,
  target_text text not null,
  accuracy_score numeric(5, 2) check (accuracy_score between 0 and 100),
  fluency_score numeric(5, 2) check (fluency_score between 0 and 100),
  completeness_score numeric(5, 2) check (completeness_score between 0 and 100),
  overall_score numeric(5, 2) check (overall_score between 0 and 100),
  phoneme_detail jsonb,
  audio_url text,
  created_at timestamptz not null default now()
);

alter table public.pronunciation_attempts enable row level security;

create index pronunciation_attempts_user_idx
  on public.pronunciation_attempts (user_id, created_at desc);
create index pronunciation_attempts_phrase_idx
  on public.pronunciation_attempts (phrase_id);

create policy "Users can view own pronunciation attempts"
  on public.pronunciation_attempts for select
  to authenticated
  using ((select auth.uid()) = user_id);

-- One row per Nemotron-VL handwriting evaluation. Canvas images go to
-- object storage; only the path is stored here.
create table public.handwriting_attempts (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  target_text text not null,
  image_url text,
  proportion_score numeric(5, 2) check (proportion_score between 0 and 100),
  stroke_score numeric(5, 2) check (stroke_score between 0 and 100),
  legibility_score numeric(5, 2) check (legibility_score between 0 and 100),
  overall_score numeric(5, 2) check (overall_score between 0 and 100),
  feedback jsonb,
  model_version text,
  created_at timestamptz not null default now()
);

alter table public.handwriting_attempts enable row level security;

create index handwriting_attempts_user_idx
  on public.handwriting_attempts (user_id, created_at desc);

create policy "Users can view own handwriting attempts"
  on public.handwriting_attempts for select
  to authenticated
  using ((select auth.uid()) = user_id);

-- One AI conversation run of a scenario. Groups messages and tracks which
-- completion goals were hit.
create table public.conversation_sessions (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  scenario_id bigint not null references public.scenarios (id),
  status text not null default 'active' check (status in ('active', 'completed', 'abandoned')),
  goals_completed jsonb not null default '[]'::jsonb,
  started_at timestamptz not null default now(),
  ended_at timestamptz
);

alter table public.conversation_sessions enable row level security;

create index conversation_sessions_user_idx
  on public.conversation_sessions (user_id, started_at desc);
create index conversation_sessions_scenario_idx
  on public.conversation_sessions (scenario_id);

create policy "Users can view own conversation sessions"
  on public.conversation_sessions for select
  to authenticated
  using ((select auth.uid()) = user_id);

-- Full transcript, one row per turn. Assistant rows mirror the model's JSON
-- schema (hangul / romanized / english / correction); user rows store the
-- ASR transcript in `hangul`.
create table public.conversation_messages (
  id bigint generated always as identity primary key,
  session_id bigint not null references public.conversation_sessions (id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  hangul text not null default '',
  romanized text,
  english text,
  contextual_correction text,
  created_at timestamptz not null default now()
);

alter table public.conversation_messages enable row level security;

create index conversation_messages_session_idx
  on public.conversation_messages (session_id, id);

create policy "Users can view messages of own sessions"
  on public.conversation_messages for select
  to authenticated
  using (
    exists (
      select 1 from public.conversation_sessions s
      where s.id = session_id and s.user_id = (select auth.uid())
    )
  );

-- =============================================================================
-- Progress
-- =============================================================================

-- Per-user rollup per lesson so the home screen renders from one indexed
-- read instead of aggregating attempts.
create table public.lesson_progress (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  lesson_id bigint not null references public.lessons (id) on delete cascade,
  status text not null default 'in_progress' check (status in ('in_progress', 'completed')),
  phrases_completed integer not null default 0 check (phrases_completed >= 0),
  best_pronunciation_score numeric(5, 2) check (best_pronunciation_score between 0 and 100),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, lesson_id)
);

alter table public.lesson_progress enable row level security;

create index lesson_progress_lesson_idx on public.lesson_progress (lesson_id);

create trigger lesson_progress_set_updated_at
  before update on public.lesson_progress
  for each row execute function public.set_updated_at();

create policy "Users can view own lesson progress"
  on public.lesson_progress for select
  to authenticated
  using ((select auth.uid()) = user_id);

-- Same rollup for scenarios (times completed, whether goals were all hit).
create table public.scenario_progress (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  scenario_id bigint not null references public.scenarios (id) on delete cascade,
  status text not null default 'in_progress' check (status in ('in_progress', 'completed')),
  times_completed integer not null default 0 check (times_completed >= 0),
  last_session_id bigint references public.conversation_sessions (id) on delete set null,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, scenario_id)
);

alter table public.scenario_progress enable row level security;

create index scenario_progress_scenario_idx on public.scenario_progress (scenario_id);
create index scenario_progress_last_session_idx on public.scenario_progress (last_session_id);

create trigger scenario_progress_set_updated_at
  before update on public.scenario_progress
  for each row execute function public.set_updated_at();

create policy "Users can view own scenario progress"
  on public.scenario_progress for select
  to authenticated
  using ((select auth.uid()) = user_id);
