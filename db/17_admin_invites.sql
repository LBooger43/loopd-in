-- Admin: see every invite code, who it was for, and whether that salon has signed up yet.
-- Also lets the admin make a new one-time code or turn a code off, without opening Supabase.

-- remember which code each salon used to sign up
alter table lp_salons add column if not exists invite_code text;

create or replace function lp_create_salon(p_code text, p_salon text, p_city text, p_name text) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_plan text; v_code text; v_id uuid; v_me text := lp_me();
begin
  if v_me = '' then raise exception 'Sign in first.'; end if;
  if exists (select 1 from lp_staff where lower(email) = v_me) then raise exception 'ALREADY_IN_SALON'; end if;
  select plan, code into v_plan, v_code from lp_invite_codes where upper(code) = upper(trim(p_code)) and uses_left > 0 for update;
  if v_plan is null then raise exception 'BAD_CODE'; end if;
  update lp_invite_codes set uses_left = uses_left - 1 where code = v_code;
  insert into lp_salons (name, city, plan, created_by, settings, invite_code)
    values (trim(p_salon), nullif(trim(p_city), ''), v_plan, v_me, jsonb_build_object('timeoff_limit', 2), v_code)
    returning id into v_id;
  insert into lp_staff (salon_id, email, name, role) values (v_id, v_me, trim(p_name), 'manager');
  return v_id;
end $$;
grant execute on function lp_create_salon(text, text, text, text) to authenticated;

-- every code, newest first, with the salons that signed up with it
create or replace function lp_admin_invites() returns json language plpgsql stable security definer set search_path = public as $$
begin
  if not lp_is_admin() then raise exception 'Not allowed.'; end if;
  return coalesce((select json_agg(x order by x.created_at desc) from (
    select c.code, c.plan, c.uses_left, c.note, c.created_at,
      (select json_agg(json_build_object('id', s.id, 'name', s.name, 'city', s.city, 'created_at', s.created_at, 'beta_ends_at', s.beta_ends_at) order by s.created_at)
         from lp_salons s where upper(s.invite_code) = upper(c.code)) as salons
    from lp_invite_codes c) x), '[]'::json);
end $$;
grant execute on function lp_admin_invites() to authenticated;

-- make a new code (one use by default)
create or replace function lp_admin_create_invite(p_code text, p_plan text, p_note text, p_uses int default 1) returns text
language plpgsql security definer set search_path = public as $$
declare v text := upper(regexp_replace(trim(coalesce(p_code, '')), '\s+', '-', 'g'));
begin
  if not lp_is_admin() then raise exception 'Not allowed.'; end if;
  if v !~ '^[A-Z0-9-]{4,30}$' then raise exception 'BAD_FORMAT'; end if;
  if p_plan not in ('front_desk', 'team', 'owner') then raise exception 'BAD_PLAN'; end if;
  if exists (select 1 from lp_invite_codes where upper(code) = v) then raise exception 'CODE_TAKEN'; end if;
  insert into lp_invite_codes (code, plan, uses_left, note) values (v, p_plan, greatest(1, least(coalesce(p_uses, 1), 50)), nullif(trim(p_note), ''));
  return v;
end $$;
grant execute on function lp_admin_create_invite(text, text, text, int) to authenticated;

-- turn a code off (0 uses left) — salons already signed up are not affected
create or replace function lp_admin_turn_off_invite(p_code text) returns boolean
language plpgsql security definer set search_path = public as $$
begin
  if not lp_is_admin() then raise exception 'Not allowed.'; end if;
  update lp_invite_codes set uses_left = 0 where upper(code) = upper(trim(p_code));
  return found;
end $$;
grant execute on function lp_admin_turn_off_invite(text) to authenticated;
