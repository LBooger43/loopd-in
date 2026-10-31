-- Loopd-In: every salon's data lives in lp_ tables, each row tied to one salon.
-- A person only ever sees rows for the salon they belong to (lp_my_salon()).

-- ---------- salons, plans, invite codes ----------
create table if not exists lp_salons (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  city text,
  plan text not null default 'team' check (plan in ('front_desk','team','owner')),
  settings jsonb not null default '{}'::jsonb,
  logo text,
  created_by text not null default lower(auth.jwt()->>'email'),
  created_at timestamptz not null default now()
);
create table if not exists lp_invite_codes (
  code text primary key,
  plan text not null default 'team' check (plan in ('front_desk','team','owner')),
  uses_left int not null default 1,
  note text,
  created_at timestamptz not null default now()
);
alter table lp_salons enable row level security;
alter table lp_invite_codes enable row level security;  -- no policies: only the sign-up function reads it

-- ---------- per-salon copies of every app table ----------
do $$ declare t text; begin
  foreach t in array array['staff','daily_log','followups','log_replies','incidents','resolutions','staff_notes','supply_items','supply_needs',
    'todos','manager_log','staff_writeups','announcements','messages','time_off','one_on_ones','goal_sheets','applicants','handbook_versions','push_subs'] loop
    execute format('create table if not exists %I (like public.%I including defaults including constraints including indexes)', 'lp_' || t, t);
    execute format('alter table %I add column if not exists salon_id uuid references lp_salons(id) on delete cascade', 'lp_' || t);
    execute format('alter table %I enable row level security', 'lp_' || t);
    execute format('create index if not exists %I on %I (salon_id)', 'lp_' || t || '_salon_idx', 'lp_' || t);
  end loop;
end $$;

-- staff: one row per person per salon (the same email can work at two salons)
do $$ declare c record; begin
  for c in select conname from pg_constraint where conrelid = 'lp_staff'::regclass and contype in ('p','u') loop
    execute format('alter table lp_staff drop constraint %I', c.conname);
  end loop;
end $$;
alter table lp_staff add primary key (salon_id, email);
alter table lp_staff add column if not exists created_at timestamptz not null default now();
do $$ declare c record; begin
  for c in select conname from pg_constraint where conrelid = 'lp_goal_sheets'::regclass and contype = 'u' loop
    execute format('alter table lp_goal_sheets drop constraint %I', c.conname);
  end loop;
end $$;
alter table lp_goal_sheets add constraint lp_goal_sheets_one_per_period unique (salon_id, created_by, kind, period);
alter table lp_goal_sheets add constraint lp_goal_sheets_oo_fk foreign key (one_on_one_id) references lp_one_on_ones(id) on delete set null;

-- ---------- who am I ----------
create or replace function lp_my_salon() returns uuid language sql stable security definer set search_path = public as $$
  select salon_id from lp_staff where lower(email) = lower(coalesce(auth.jwt()->>'email','')) order by created_at nulls last limit 1
$$;
create or replace function lp_my_role() returns text language sql stable security definer set search_path = public as $$
  select role from lp_staff where salon_id = lp_my_salon() and lower(email) = lower(coalesce(auth.jwt()->>'email',''))
$$;
create or replace function lp_is_staff() returns boolean language sql stable security definer set search_path = public as $$ select lp_my_role() is not null $$;
create or replace function lp_is_manager() returns boolean language sql stable security definer set search_path = public as $$ select lp_my_role() = 'manager' $$;
create or replace function lp_is_desk() returns boolean language sql stable security definer set search_path = public as $$ select lp_my_role() in ('manager','front_desk') $$;
create or replace function lp_me() returns text language sql stable as $$ select lower(coalesce(auth.jwt()->>'email','')) $$;
create or replace function lp_is_invited(p_email text) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from lp_staff where lower(email) = lower(trim(p_email)))
$$;
create or replace function lp_my_salon_info() returns json language sql stable security definer set search_path = public as $$
  select json_build_object('id', s.id, 'name', s.name, 'city', s.city, 'plan', s.plan, 'settings', s.settings, 'logo', s.logo) from lp_salons s where s.id = lp_my_salon()
$$;

-- every new row is stamped with the salon of the person adding it
do $$ declare t text; begin
  foreach t in array array['staff','daily_log','followups','log_replies','incidents','resolutions','staff_notes','supply_items','supply_needs',
    'todos','manager_log','staff_writeups','announcements','messages','time_off','one_on_ones','goal_sheets','applicants','handbook_versions','push_subs'] loop
    execute format('alter table %I alter column salon_id set default lp_my_salon()', 'lp_' || t);
  end loop;
end $$;

-- ---------- starting a salon (beta invite codes) ----------
create or replace function lp_check_code(p_code text) returns text language sql stable security definer set search_path = public as $$
  select plan from lp_invite_codes where upper(code) = upper(trim(p_code)) and uses_left > 0
$$;
create or replace function lp_create_salon(p_code text, p_salon text, p_city text, p_name text) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_plan text; v_id uuid; v_me text := lp_me();
begin
  if v_me = '' then raise exception 'Sign in first.'; end if;
  if exists (select 1 from lp_staff where lower(email) = v_me) then raise exception 'ALREADY_IN_SALON'; end if;
  select plan into v_plan from lp_invite_codes where upper(code) = upper(trim(p_code)) and uses_left > 0 for update;
  if v_plan is null then raise exception 'BAD_CODE'; end if;
  update lp_invite_codes set uses_left = uses_left - 1 where upper(code) = upper(trim(p_code));
  insert into lp_salons (name, city, plan, created_by, settings) values (trim(p_salon), nullif(trim(p_city), ''), v_plan, v_me, jsonb_build_object('timeoff_limit', 2))
    returning id into v_id;
  insert into lp_staff (salon_id, email, name, role) values (v_id, v_me, trim(p_name), 'manager');
  return v_id;
end $$;
grant execute on function lp_check_code(text) to anon, authenticated;
grant execute on function lp_create_salon(text, text, text, text) to authenticated;
grant execute on function lp_is_invited(text) to anon, authenticated;

-- ---------- manager tools ----------
create or replace function lp_archive_entry(p_kind text, p_id uuid, p_restore boolean default false) returns boolean
language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if p_kind = 'd' then
    update lp_daily_log set deleted_at = case when p_restore then null else now() end, deleted_by = case when p_restore then null else lp_me() end
      where id = p_id and salon_id = lp_my_salon() and (lp_is_manager() or (lp_is_desk() and created_by = lp_me()));
  else
    update lp_incidents set deleted_at = case when p_restore then null else now() end, deleted_by = case when p_restore then null else lp_me() end
      where id = p_id and salon_id = lp_my_salon() and (lp_is_manager() or (lp_is_desk() and created_by = lp_me()));
  end if;
  get diagnostics n = row_count; return n > 0;
end $$;
create or replace function lp_reset_login(p_email text) returns void language plpgsql security definer set search_path = public, auth as $$
begin
  if not lp_is_manager() then raise exception 'Managers only.'; end if;
  if not exists (select 1 from lp_staff where salon_id = lp_my_salon() and lower(email) = lower(trim(p_email))) then raise exception 'Not on your team.'; end if;
  if exists (select 1 from lp_staff where lower(email) = lower(trim(p_email)) and salon_id <> lp_my_salon()) then raise exception 'They also work at another salon; they can reset their own password.'; end if;
  delete from auth.users where lower(email) = lower(trim(p_email));
end $$;
create or replace function lp_update_salon(p_name text, p_city text, p_settings jsonb, p_logo text) returns void language plpgsql security definer set search_path = public as $$
begin
  if not lp_is_manager() then raise exception 'Managers only.'; end if;
  update lp_salons set name = coalesce(nullif(trim(p_name), ''), name), city = nullif(trim(coalesce(p_city, '')), ''),
    settings = coalesce(p_settings, settings), logo = coalesce(p_logo, logo) where id = lp_my_salon();
end $$;
create or replace function lp_set_plan(p_plan text) returns void language plpgsql security definer set search_path = public as $$
begin
  if not lp_is_manager() then raise exception 'Managers only.'; end if;
  if p_plan not in ('front_desk','team','owner') then raise exception 'Unknown plan.'; end if;
  update lp_salons set plan = p_plan where id = lp_my_salon();   -- free to switch during the beta
end $$;
grant execute on function lp_archive_entry(text, uuid, boolean), lp_reset_login(text), lp_update_salon(text, text, jsonb, text), lp_set_plan(text),
  lp_my_role(), lp_my_salon(), lp_my_salon_info(), lp_is_staff(), lp_is_manager(), lp_is_desk() to authenticated;

-- ---------- time off: limit per role per day comes from the salon's settings ----------
create or replace function lp_time_off_guard() returns trigger language plpgsql security definer set search_path = public as $$
declare v_limit int; d date;
begin
  new.role := coalesce((select role from lp_staff where salon_id = new.salon_id and lower(email) = lower(new.created_by)), 'stylist');
  if new.role = 'manager' then return new; end if;
  select coalesce((settings->>'timeoff_limit')::int, 2) into v_limit from lp_salons where id = new.salon_id;
  d := new.off_from;
  while d < new.back_on loop
    if (select count(*) from lp_time_off o where o.salon_id = new.salon_id and o.role = new.role and o.status in ('pending','approved')
        and o.id <> new.id and o.off_from <= d and d < o.back_on) >= v_limit then
      raise exception 'TIMEOFF_LIMIT: %', d;
    end if;
    d := d + 1;
  end loop;
  return new;
end $$;
drop trigger if exists lp_time_off_guard on lp_time_off;
create trigger lp_time_off_guard before insert on lp_time_off for each row execute function lp_time_off_guard();

-- ---------- 1:1s: only managers change the details ----------
create or replace function lp_one_on_ones_guard() returns trigger language plpgsql as $$
begin
  if lp_is_manager() then return new; end if;
  if new.req_date is distinct from old.req_date or new.req_time is distinct from old.req_time or new.topic is distinct from old.topic
     or new.with_manager is distinct from old.with_manager or new.meet_date is distinct from old.meet_date or new.meet_time is distinct from old.meet_time
     or new.manager_note is distinct from old.manager_note or new.decided_by is distinct from old.decided_by or new.decided_at is distinct from old.decided_at
     or new.salon_id is distinct from old.salon_id then
    raise exception 'Only managers can change the details of a 1:1.';
  end if;
  if new.status = 'confirmed' and old.status <> 'proposed' then raise exception 'Only managers can confirm a 1:1.'; end if;
  return new;
end $$;
drop trigger if exists lp_one_on_ones_guard on lp_one_on_ones;
create trigger lp_one_on_ones_guard before update on lp_one_on_ones for each row execute function lp_one_on_ones_guard();

-- ---------- phone notifications ----------
create or replace function lp_save_push_sub(p_endpoint text, p_p256dh text, p_auth text, p_prefs jsonb, p_ua text) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not lp_is_staff() then raise exception 'not on the team'; end if;
  insert into lp_push_subs (salon_id, email, endpoint, p256dh, auth, prefs, ua) values (lp_my_salon(), lp_me(), p_endpoint, p_p256dh, p_auth, coalesce(p_prefs, '{}'::jsonb), p_ua)
  on conflict (endpoint) do update set salon_id = excluded.salon_id, email = excluded.email, p256dh = excluded.p256dh, auth = excluded.auth, prefs = excluded.prefs, ua = excluded.ua, updated_at = now();
end $$;
create or replace function lp_delete_push_sub(p_endpoint text) returns void language sql security definer set search_path = public as $$
  delete from lp_push_subs where endpoint = p_endpoint;
$$;
grant execute on function lp_save_push_sub(text, text, text, jsonb, text), lp_delete_push_sub(text) to authenticated;
