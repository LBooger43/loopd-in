-- Loopd-In support: Help requests from salons, an admin (Loopd-In owner) inbox, and support access that a salon's
-- owner switches on for a set time. While it's on, the admin can open that salon as a manager; every visit is logged.

-- ---------- who runs Loopd-In ----------
create table if not exists lp_platform_admins (
  email text primary key,
  viewing_salon uuid references lp_salons(id) on delete set null,
  visit_id uuid
);
alter table lp_platform_admins enable row level security;   -- no policies: only the functions below touch it
insert into lp_platform_admins (email) values ('leifpbooger@gmail.com') on conflict do nothing;

create or replace function lp_is_admin() returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from lp_platform_admins where email = lower(coalesce(auth.jwt()->>'email', '')))
$$;

-- ---------- support access (switched on by the salon's owner) ----------
alter table lp_salons add column if not exists support_until timestamptz;

-- the salon the admin is looking at right now, only while that salon's access is switched on
create or replace function lp_support_salon() returns uuid language sql stable security definer set search_path = public as $$
  select a.viewing_salon from lp_platform_admins a join lp_salons s on s.id = a.viewing_salon
  where a.email = lower(coalesce(auth.jwt()->>'email', '')) and s.support_until > now()
$$;

-- membership: an admin in support view counts as a manager of that one salon, nothing more
create or replace function lp_my_salon() returns uuid language sql stable security definer set search_path = public as $$
  select coalesce(lp_support_salon(),
    (select salon_id from lp_staff where lower(email) = lower(coalesce(auth.jwt()->>'email','')) order by created_at nulls last limit 1))
$$;
create or replace function lp_my_role() returns text language sql stable security definer set search_path = public as $$
  select case when lp_support_salon() is not null then 'manager'
    else (select role from lp_staff where salon_id = lp_my_salon() and lower(email) = lower(coalesce(auth.jwt()->>'email',''))) end
$$;
create or replace function lp_is_desk() returns boolean language sql stable security definer set search_path = public as $$
  select lp_support_salon() is not null
      or exists (select 1 from lp_staff where lower(email) = lp_me() and salon_id = lp_my_salon()
                 and (role in ('manager','front_desk') or (role = 'stylist' and also_desk)))
$$;
-- a real manager of the salon (support view doesn't count), for things only the owner may decide
create or replace function lp_is_real_manager() returns boolean language sql stable security definer set search_path = public as $$
  select lp_support_salon() is null and exists (select 1 from lp_staff where lower(email) = lp_me() and salon_id = lp_my_salon() and role = 'manager')
$$;

create or replace function lp_my_salon_info() returns json language sql stable security definer set search_path = public as $$
  select json_build_object('id', s.id, 'name', s.name, 'city', s.city, 'plan', s.plan, 'settings', s.settings, 'logo', s.logo, 'slug', s.slug,
    'support_until', s.support_until, 'support_view', lp_support_salon() is not null)
  from lp_salons s where s.id = lp_my_salon()
$$;

create table if not exists lp_support_visits (
  id uuid primary key default gen_random_uuid(),
  salon_id uuid not null references lp_salons(id) on delete cascade,
  admin_email text not null,
  started_at timestamptz not null default now(),
  ended_at timestamptz
);
alter table lp_support_visits enable row level security;
drop policy if exists sv_read on lp_support_visits;
create policy sv_read on lp_support_visits for select to authenticated using ((salon_id = lp_my_salon() and lp_is_manager()) or lp_is_admin());

-- owner: allow support for some hours (0 = turn it off now)
create or replace function lp_grant_support(p_hours int) returns timestamptz language plpgsql security definer set search_path = public as $$
declare v timestamptz;
begin
  if not lp_is_real_manager() then raise exception 'Only the salon''s managers can change support access.'; end if;
  v := case when coalesce(p_hours, 0) > 0 then now() + make_interval(hours => least(p_hours, 24 * 14)) else null end;
  update lp_salons set support_until = v where id = lp_my_salon();
  if v is null then
    update lp_support_visits set ended_at = now() where salon_id = lp_my_salon() and ended_at is null;
    update lp_platform_admins set viewing_salon = null, visit_id = null where viewing_salon = lp_my_salon();
  end if;
  return v;
end $$;

-- admin: open / leave a salon
create or replace function lp_admin_enter(p_salon uuid) returns void language plpgsql security definer set search_path = public as $$
declare me text := lower(coalesce(auth.jwt()->>'email', '')); vid uuid;
begin
  if not lp_is_admin() then raise exception 'Not allowed.'; end if;
  if not exists (select 1 from lp_salons where id = p_salon and support_until > now()) then raise exception 'NO_ACCESS'; end if;
  update lp_support_visits set ended_at = now() where admin_email = me and ended_at is null;
  insert into lp_support_visits (salon_id, admin_email) values (p_salon, me) returning id into vid;
  update lp_platform_admins set viewing_salon = p_salon, visit_id = vid where email = me;
end $$;
create or replace function lp_admin_exit() returns void language plpgsql security definer set search_path = public as $$
declare me text := lower(coalesce(auth.jwt()->>'email', ''));
begin
  if not lp_is_admin() then return; end if;
  update lp_support_visits set ended_at = now() where admin_email = me and ended_at is null;
  update lp_platform_admins set viewing_salon = null, visit_id = null where email = me;
end $$;

-- ---------- Help requests ----------
create table if not exists lp_support_tickets (
  id uuid primary key default gen_random_uuid(),
  salon_id uuid not null default lp_my_salon() references lp_salons(id) on delete cascade,
  created_by text not null default lower(coalesce(auth.jwt()->>'email', '')),
  message text not null check (length(message) between 1 and 4000),
  context jsonb not null default '{}'::jsonb,
  screenshot text,
  status text not null default 'open' check (status in ('open','closed')),
  reply text,
  replied_at timestamptz,
  created_at timestamptz not null default now()
);
alter table lp_support_tickets enable row level security;
drop policy if exists st_add on lp_support_tickets;
drop policy if exists st_read on lp_support_tickets;
drop policy if exists st_admin on lp_support_tickets;
create policy st_add on lp_support_tickets for insert to authenticated
  with check (salon_id = lp_my_salon() and lp_is_staff() and created_by = lp_me() and status = 'open' and reply is null);
create policy st_read on lp_support_tickets for select to authenticated
  using ((salon_id = lp_my_salon() and (created_by = lp_me() or lp_is_manager())) or lp_is_admin());
create policy st_admin on lp_support_tickets for update to authenticated using (lp_is_admin()) with check (lp_is_admin());
do $$ begin alter publication supabase_realtime add table lp_support_tickets; exception when others then null; end $$;

-- admin: every salon at a glance
create or replace function lp_admin_salons() returns json language plpgsql stable security definer set search_path = public as $$
begin
  if not lp_is_admin() then raise exception 'Not allowed.'; end if;
  return coalesce((select json_agg(x order by x.created_at desc) from (
    select s.id, s.name, s.city, s.plan, s.slug, s.created_at, s.support_until,
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

-- screenshots: the person sending it can add one to their salon's support folder; the admin can open them
drop policy if exists lp_files_support_admin on storage.objects;
create policy lp_files_support_admin on storage.objects for select to authenticated
  using (bucket_id = 'lp-files' and (storage.foldername(name))[2] = 'support' and lp_is_admin());

-- phone alerts: new Help requests go to the admin; replies go back to the person who asked
drop trigger if exists lp_push_ins on lp_support_tickets;
create trigger lp_push_ins after insert on lp_support_tickets for each row execute function lp_notify_push();
drop trigger if exists lp_push_upd on lp_support_tickets;
create trigger lp_push_upd after update on lp_support_tickets for each row when (old.reply is distinct from new.reply) execute function lp_notify_push();
