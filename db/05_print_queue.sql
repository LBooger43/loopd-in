-- Print queue: managers send flyers and ads (PDFs or images, e.g. from Canva); front desk prints them and checks them off.
-- Part 1 is Salon Saia (public tables, "photos" bucket). Part 2 is Loopd-In (lp_ tables, "lp-files" bucket, one salon at a time).

-- ================= Part 1: Salon Saia =================
create table if not exists print_jobs (
  id uuid primary key default gen_random_uuid(),
  title text not null check (length(title) between 1 and 120),
  file_path text not null,
  file_name text,
  file_type text,
  copies int not null default 1 check (copies between 1 and 1000),
  paper text,
  due_kind text not null default 'open' check (due_kind in ('open','day','any')),
  due_date date,
  note text check (length(note) <= 1000),
  status text not null default 'pending' check (status in ('pending','printed','cancelled')),
  printed_by text,
  printed_at timestamptz,
  created_by text not null default lower(auth.jwt()->>'email'),
  created_at timestamptz not null default now()
);
alter table print_jobs enable row level security;

create or replace function print_role() returns text language sql stable security definer set search_path = public as $$
  select role from staff where lower(email) = lower(coalesce(auth.jwt()->>'email', '')) limit 1
$$;
grant execute on function print_role() to authenticated;

-- front desk may only mark a job printed; managers may do anything
create or replace function print_jobs_guard() returns trigger language plpgsql security definer set search_path = public as $$
declare r text := print_role();
begin
  if new.status = 'printed' and old.status is distinct from 'printed' then
    new.printed_by := lower(coalesce(auth.jwt()->>'email', '')); new.printed_at := now();
  elsif new.status = 'pending' then
    new.printed_by := null; new.printed_at := null;
  end if;
  if coalesce(r, '') <> 'manager' then
    if not (old.status = 'pending' and new.status = 'printed'
            and (new.title, new.file_path, new.copies, coalesce(new.paper,''), new.due_kind, coalesce(new.due_date,'1900-01-01'::date), coalesce(new.note,''), new.created_by)
              = (old.title, old.file_path, old.copies, coalesce(old.paper,''), old.due_kind, coalesce(old.due_date,'1900-01-01'::date), coalesce(old.note,''), old.created_by)) then
      raise exception 'Front desk can only mark a job printed.';
    end if;
  end if;
  return new;
end $$;
drop trigger if exists print_jobs_guard on print_jobs;
create trigger print_jobs_guard before update on print_jobs for each row execute function print_jobs_guard();

drop policy if exists pj_read on print_jobs;
drop policy if exists pj_mgr on print_jobs;
drop policy if exists pj_desk_done on print_jobs;
create policy pj_read on print_jobs for select to authenticated using (print_role() in ('manager','front_desk'));
create policy pj_mgr on print_jobs for all to authenticated using (print_role() = 'manager') with check (print_role() = 'manager');
create policy pj_desk_done on print_jobs for update to authenticated using (print_role() = 'front_desk' and status = 'pending') with check (print_role() = 'front_desk' and status = 'printed');

-- files go in photos/print/…; managers add and remove, front desk opens them
update storage.buckets set allowed_mime_types = (
  select array(select distinct unnest(coalesce(allowed_mime_types, array[]::text[]) || array['application/pdf','image/jpeg','image/png','image/webp','image/heic'])))
  where id = 'photos' and allowed_mime_types is not null;
drop policy if exists print_add on storage.objects;
drop policy if exists print_read on storage.objects;
drop policy if exists print_del on storage.objects;
create policy print_add on storage.objects for insert to authenticated with check (bucket_id = 'photos' and (storage.foldername(name))[1] = 'print' and print_role() = 'manager');
create policy print_read on storage.objects for select to authenticated using (bucket_id = 'photos' and (storage.foldername(name))[1] = 'print' and print_role() in ('manager','front_desk'));
create policy print_del on storage.objects for delete to authenticated using (bucket_id = 'photos' and (storage.foldername(name))[1] = 'print' and print_role() = 'manager');

do $$ begin alter publication supabase_realtime add table print_jobs; exception when others then null; end $$;
drop trigger if exists push_ins on print_jobs;
create trigger push_ins after insert on print_jobs for each row execute function notify_push();

-- ================= Part 2: Loopd-In =================
create table if not exists lp_print_jobs (like public.print_jobs including defaults including constraints including indexes);
alter table lp_print_jobs add column if not exists salon_id uuid references lp_salons(id) on delete cascade;
alter table lp_print_jobs alter column salon_id set default lp_my_salon();
alter table lp_print_jobs enable row level security;

create or replace function lp_print_jobs_guard() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.salon_id is distinct from old.salon_id then raise exception 'Not allowed.'; end if;
  if new.status = 'printed' and old.status is distinct from 'printed' then
    new.printed_by := lp_me(); new.printed_at := now();
  elsif new.status = 'pending' then
    new.printed_by := null; new.printed_at := null;
  end if;
  if not lp_is_manager() then
    if not (old.status = 'pending' and new.status = 'printed'
            and (new.title, new.file_path, new.copies, coalesce(new.paper,''), new.due_kind, coalesce(new.due_date,'1900-01-01'::date), coalesce(new.note,''), new.created_by)
              = (old.title, old.file_path, old.copies, coalesce(old.paper,''), old.due_kind, coalesce(old.due_date,'1900-01-01'::date), coalesce(old.note,''), old.created_by)) then
      raise exception 'Front desk can only mark a job printed.';
    end if;
  end if;
  return new;
end $$;
drop trigger if exists lp_print_jobs_guard on lp_print_jobs;
create trigger lp_print_jobs_guard before update on lp_print_jobs for each row execute function lp_print_jobs_guard();

drop policy if exists pj_read on lp_print_jobs;
drop policy if exists pj_mgr on lp_print_jobs;
drop policy if exists pj_desk_done on lp_print_jobs;
create policy pj_read on lp_print_jobs for select to authenticated using (salon_id = lp_my_salon() and lp_is_desk());
create policy pj_mgr on lp_print_jobs for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy pj_desk_done on lp_print_jobs for update to authenticated using (salon_id = lp_my_salon() and lp_is_desk() and status = 'pending')
  with check (salon_id = lp_my_salon() and lp_is_desk() and status = 'printed');

-- print files are added by managers only (everything else in the salon folder keeps its rule)
drop policy if exists lp_files_add on storage.objects;
create policy lp_files_add on storage.objects for insert to authenticated
  with check (bucket_id = 'lp-files' and (storage.foldername(name))[1] = lp_my_salon()::text and lp_is_staff()
    and ((storage.foldername(name))[2] not in ('handbook','logo','writeups','mgrlog','print') or lp_is_manager()));

do $$ begin alter publication supabase_realtime add table lp_print_jobs; exception when others then null; end $$;
drop trigger if exists lp_push_ins on lp_print_jobs;
create trigger lp_push_ins after insert on lp_print_jobs for each row execute function lp_notify_push();
