-- Google OAuth signups carry the user's name as `full_name` (or `name`) in
-- raw_user_meta_data, not our email-signup `display_name` key. Extend the
-- profile-creation fallback chain so OAuth users get a real display name
-- instead of their email prefix. Display-only, never used for authorization.
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
    coalesce(
      new.raw_user_meta_data ->> 'display_name',
      new.raw_user_meta_data ->> 'full_name',
      new.raw_user_meta_data ->> 'name',
      split_part(coalesce(new.email, ''), '@', 1)
    )
  );
  return new;
end;
$$;
