-- "Also works front desk": a stylist keeps the Stylist role (and counts as a stylist for time off)
-- but gets the front desk tabs: Daily log, Incidents, Supplies and To print.

-- ================= Part 1: Salon Saia =================
alter table staff add column if not exists also_desk boolean not null default false;
create or replace function is_desk() returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from staff where lower(email) = lower(coalesce(auth.jwt()->>'email', ''))
                 and (role in ('manager','front_desk') or (role = 'stylist' and also_desk)))
$$;
-- print queue rules use the same check
drop policy if exists pj_read on print_jobs;
drop policy if exists pj_desk_done on print_jobs;
create policy pj_read on print_jobs for select to authenticated using (is_desk());
create policy pj_desk_done on print_jobs for update to authenticated using (is_desk() and status = 'pending') with check (is_desk() and status = 'printed');
drop policy if exists print_read on storage.objects;
create policy print_read on storage.objects for select to authenticated using (bucket_id = 'photos' and (storage.foldername(name))[1] = 'print' and is_desk());

-- ================= Part 2: Loopd-In =================
alter table lp_staff add column if not exists also_desk boolean not null default false;
create or replace function lp_is_desk() returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from lp_staff where lower(email) = lp_me() and salon_id = lp_my_salon()
                 and (role in ('manager','front_desk') or (role = 'stylist' and also_desk)))
$$;
