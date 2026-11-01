-- Loopd-In: each salon's public job application page (apply.html?s=<slug>), with résumé upload.
-- Anyone can open an Owner-plan salon's page and apply; nobody outside the salon can read applicants or résumés.

-- ---------- a short public web name for every salon ----------
alter table lp_salons add column if not exists slug text;
create or replace function lp_slugify(p text) returns text language sql immutable as $$
  select coalesce(nullif(trim(both '-' from regexp_replace(lower(coalesce(p, '')), '[^a-z0-9]+', '-', 'g')), ''), 'salon')
$$;
create or replace function lp_salon_slug() returns trigger language plpgsql security definer set search_path = public as $$
declare base text; cand text; n int := 1;
begin
  if new.slug is not null and new.slug <> '' then return new; end if;
  base := left(lp_slugify(new.name), 40); cand := base;
  while exists (select 1 from lp_salons where slug = cand and id <> new.id) loop n := n + 1; cand := base || '-' || n; end loop;
  new.slug := cand; return new;
end $$;
drop trigger if exists lp_salon_slug on lp_salons;
create trigger lp_salon_slug before insert or update of slug on lp_salons for each row execute function lp_salon_slug();
update lp_salons set slug = null where slug is null;          -- fills in salons made before today
create unique index if not exists lp_salons_slug_key on lp_salons (slug);

create or replace function lp_my_salon_info() returns json language sql stable security definer set search_path = public as $$
  select json_build_object('id', s.id, 'name', s.name, 'city', s.city, 'plan', s.plan, 'settings', s.settings, 'logo', s.logo, 'slug', s.slug)
  from lp_salons s where s.id = lp_my_salon()
$$;

-- ---------- what the public page may see ----------
create or replace function lp_apply_salon(p_slug text) returns lp_salons language sql stable security definer set search_path = public as $$
  select * from lp_salons where slug = lower(trim(p_slug)) and plan = 'owner' and coalesce((settings->>'apply_open')::boolean, true)
$$;
create or replace function lp_apply_info(p_slug text) returns json language sql stable security definer set search_path = public as $$
  select json_build_object('id', s.id, 'name', s.name, 'city', s.city, 'logo', s.logo,
    'positions', coalesce(s.settings->'apply_positions', '["Stylist","Assistant","Front desk"]'::jsonb),
    'intro', s.settings->>'apply_intro')
  from lp_apply_salon(p_slug) s where s.id is not null
$$;

-- ---------- sending an application ----------
create or replace function lp_apply(p_slug text, p jsonb) returns boolean language plpgsql security definer set search_path = public, storage as $$
declare s lp_salons; v_email text; v_resume text; v_ans jsonb;
begin
  s := lp_apply_salon(p_slug);
  if s.id is null then raise exception 'APPLY_CLOSED'; end if;
  if coalesce((p->>'ms')::int, 0) < 4000 then raise exception 'TOO_FAST'; end if;          -- people take longer than 4 seconds
  if coalesce(trim(p->>'name'), '') = '' or (coalesce(trim(p->>'phone'), '') = '' and coalesce(trim(p->>'email'), '') = '') then raise exception 'MISSING'; end if;
  v_email := lower(nullif(trim(p->>'email'), ''));
  if (select count(*) from lp_applicants where salon_id = s.id and submission_id like 'web-%' and submitted_at > now() - interval '1 hour') >= 25 then raise exception 'BUSY'; end if;
  if v_email is not null and exists (select 1 from lp_applicants where salon_id = s.id and lower(email) = v_email and submitted_at > now() - interval '1 day') then raise exception 'ALREADY'; end if;
  -- the résumé must be a file that was just uploaded into this salon's résumé folder
  v_resume := nullif(p->>'resume_file', '');
  if v_resume is not null and (v_resume !~ '^resumes/[A-Za-z0-9._-]+$'
      or not exists (select 1 from storage.objects o where o.bucket_id = 'lp-files' and o.name = s.id || '/' || v_resume and o.created_at > now() - interval '1 hour')) then
    v_resume := null;
  end if;
  v_ans := jsonb_strip_nulls(jsonb_build_object(
    'license', left(p->>'license', 200), 'experience', left(p->>'experience', 200), 'availability', left(p->>'availability', 500),
    'start', left(p->>'start', 100), 'instagram', left(p->>'instagram', 100), 'heard', left(p->>'heard', 200), 'about', left(p->>'about', 3000),
    'resume_file', v_resume, 'resume_name', case when v_resume is null then null else left(p->>'resume_name', 150) end));
  insert into lp_applicants (salon_id, name, position, phone, email, answers, submission_id, status, log, submitted_at)
  values (s.id, left(trim(p->>'name'), 100), nullif(left(trim(p->>'position'), 100), ''), nullif(left(trim(p->>'phone'), 40), ''), v_email,
          v_ans, 'web-' || gen_random_uuid(), 'new', '[]'::jsonb, now());
  return true;
end $$;
grant execute on function lp_apply_info(text), lp_apply(text, jsonb) to anon, authenticated;
revoke execute on function lp_apply_salon(text) from public, anon, authenticated;

create or replace function lp_apply_open(p_folder text) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from lp_salons where id::text = p_folder and plan = 'owner' and coalesce((settings->>'apply_open')::boolean, true))
$$;
grant execute on function lp_apply_open(text) to anon, authenticated;

-- ---------- files ----------
-- résumés can be PDF, Word or a photo
update storage.buckets set allowed_mime_types = array['image/jpeg','image/png','image/webp','image/heic','application/pdf',
  'application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document'] where id = 'lp-files';
-- applicants can drop a résumé into an open salon's résumé folder (add only: they can't see, replace or remove anything)
drop policy if exists lp_files_apply on storage.objects;
create policy lp_files_apply on storage.objects for insert to anon, authenticated
  with check (bucket_id = 'lp-files' and (storage.foldername(name))[2] = 'resumes' and lp_apply_open((storage.foldername(name))[1]));
-- the apply page shows the salon's logo
drop policy if exists lp_files_logo_public on storage.objects;
create policy lp_files_logo_public on storage.objects for select to anon
  using (bucket_id = 'lp-files' and (storage.foldername(name))[2] = 'logo');
-- inside the salon, only managers can open résumés
drop policy if exists lp_files_read on storage.objects;
create policy lp_files_read on storage.objects for select to authenticated
  using (bucket_id = 'lp-files' and (storage.foldername(name))[1] = lp_my_salon()::text and lp_is_staff()
    and ((storage.foldername(name))[2] is distinct from 'resumes' or lp_is_manager()));
