-- Atomic upsert-increment for daily_usage, called by the backend after every
-- metered AI operation. A plain PostgREST upsert cannot add to existing
-- counters; this function makes metering a single atomic statement.

create or replace function public.increment_daily_usage(
  p_user_id uuid,
  p_pronunciation integer default 0,
  p_turns integer default 0,
  p_tokens_in bigint default 0,
  p_tokens_out bigint default 0,
  p_tts_seconds integer default 0,
  p_handwriting integer default 0
)
returns public.daily_usage
language sql
set search_path = ''
as $$
  insert into public.daily_usage as du
    (user_id, usage_date, pronunciation_attempts, conversation_turns,
     llm_tokens_in, llm_tokens_out, tts_seconds, handwriting_checks)
  values
    (p_user_id, (now() at time zone 'utc')::date, p_pronunciation, p_turns,
     p_tokens_in, p_tokens_out, p_tts_seconds, p_handwriting)
  on conflict (user_id, usage_date) do update set
    pronunciation_attempts = du.pronunciation_attempts + excluded.pronunciation_attempts,
    conversation_turns     = du.conversation_turns     + excluded.conversation_turns,
    llm_tokens_in          = du.llm_tokens_in          + excluded.llm_tokens_in,
    llm_tokens_out         = du.llm_tokens_out         + excluded.llm_tokens_out,
    tts_seconds            = du.tts_seconds            + excluded.tts_seconds,
    handwriting_checks     = du.handwriting_checks     + excluded.handwriting_checks,
    updated_at             = now()
  returning du.*;
$$;

-- Metering is backend-only: clients must never be able to touch counters.
revoke execute on function public.increment_daily_usage(uuid, integer, integer, bigint, bigint, integer, integer)
  from public, anon, authenticated;
