-- Free beta lasts 60 days per salon. When it ends the salon is locked: everyone can still sign in and see
-- (and print) their information, but nothing new can be saved until the Loopd-In team extends it or (later) they pay.
-- Help requests, phone-alert settings and Loopd-In support view keep working while locked.

alter table lp_salons add column if not exists beta_ends_at timestamptz;
alter table lp_salons add column if not exists paid_until timestamptz;    -- for card payments later
alter table lp_salons alter column beta_ends_at set default now() + interval '60 days';
-- salons that started before end dates existed get 60 days from today
update lp_salons set beta_ends_at = now() + interval '60 days' where beta_ends_at is null;

create or replace function lp_salon_active(p_salon uuid) returns boolean language sql stable security definer set search_path = public as $$
  select coalesce((select (s.beta_ends_at is null or s.beta_ends_at > now()) or coalesce(s.paid_until > now(), false) from lp_salons s where s.id = p_salon), true)
$$;

-- every change to a locked salon's information stops here
create or replace function lp_locked_guard() returns trigger language plpgsql security definer set search_path = public as $$
declare sid uuid := case when tg_op = 'DELETE' then old.salon_id else new.salon_id end;
begin
  if pg_trigger_depth() > 1 or coalesce(auth.jwt()->>'email', '') = '' then   -- cascades, and the system itself
    return case when tg_op = 'DELETE' then old else new end;
  end if;
  if sid is not null and not lp_salon_active(sid) and lp_support_salon() is null then
    raise exception 'SALON_LOCKED' using errcode = 'P0001';
  end if;
  return case when tg_op = 'DELETE' then old else new end;
end $$;
do $$ declare t text; begin
  foreach t in array array['lp_staff','lp_daily_log','lp_followups','lp_log_replies','lp_incidents','lp_resolutions','lp_staff_notes','lp_supply_items',
    'lp_supply_needs','lp_todos','lp_manager_log','lp_staff_writeups','lp_announcements','lp_messages','lp_time_off','lp_one_on_ones','lp_goal_sheets',
    'lp_applicants','lp_handbook_versions','lp_print_jobs'] loop
    execute format('drop trigger if exists lp_locked_guard on %I', t);
    execute format('create trigger lp_locked_guard before insert or update or delete on %I for each row execute function lp_locked_guard()', t);
  end loop;
end $$;

-- the public apply page closes while a salon is locked
create or replace function lp_apply_salon(p_slug text) returns lp_salons language sql stable security definer set search_path = public as $$
  select * from lp_salons where slug = lower(trim(p_slug)) and plan = 'owner' and coalesce((settings->>'apply_open')::boolean, true) and lp_salon_active(id)
$$;

create or replace function lp_my_salon_info() returns json language sql stable security definer set search_path = public as $$
  select json_build_object('id', s.id, 'name', s.name, 'city', s.city, 'plan', s.plan, 'settings', s.settings, 'logo', s.logo, 'slug', s.slug,
    'support_until', s.support_until, 'support_view', lp_support_salon() is not null,
    'beta_ends_at', s.beta_ends_at, 'paid_until', s.paid_until, 'active', lp_salon_active(s.id))
  from lp_salons s where s.id = lp_my_salon()
$$;

-- admin: give more time (days > 0) or end the beta now (days = 0)
create or replace function lp_admin_set_beta(p_salon uuid, p_days int) returns timestamptz language plpgsql security definer set search_path = public as $$
declare v timestamptz;
begin
  if not lp_is_admin() then raise exception 'Not allowed.'; end if;
  update lp_salons set beta_ends_at = case when coalesce(p_days, 0) > 0 then greatest(coalesce(beta_ends_at, now()), now()) + make_interval(days => least(p_days, 365)) else now() end
  where id = p_salon returning beta_ends_at into v;
  return v;
end $$;

create or replace function lp_admin_salons() returns json language plpgsql stable security definer set search_path = public as $$
begin
  if not lp_is_admin() then raise exception 'Not allowed.'; end if;
  return coalesce((select json_agg(x order by x.created_at desc) from (
    select s.id, s.name, s.city, s.plan, s.slug, s.created_at, s.support_until, s.beta_ends_at, s.paid_until, lp_salon_active(s.id) as active,
      (select count(*) from lp_staff t where t.salon_id = s.id) as team,
      greatest((select max(created_at) from lp_daily_log d where d.salon_id = s.id),
               (select max(created_at) from lp_messages m where m.salon_id = s.id),
               (select max(created_at) from lp_time_off o where o.salon_id = s.id),
               (select max(submitted_at) from lp_applicants a where a.salon_id = s.id)) as last_active,
      (select count(*) from lp_support_tickets k where k.salon_id = s.id and k.status = 'open') as open_tickets,
      (select json_agg(json_build_object('started', v.started_at, 'ended', v.ended_at) order by v.started_at desc)
         from (select * from lp_support_visits v where v.salon_id = s.id order by started_at desc limit 5) v) as visits
    from lp_salons s) x), '[]'::json);
end $$;
