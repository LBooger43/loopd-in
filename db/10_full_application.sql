-- Full job application on each salon's apply page (like a paper/Jotform application):
-- address, availability, driving, education, up to 4 jobs, 3 references, and a typed signature.
-- Background questions (criminal record, controlled substances) show only when the salon turns them on.

create or replace function lp_apply_info(p_slug text) returns json language sql stable security definer set search_path = public as $$
  select json_build_object('id', s.id, 'name', s.name, 'city', s.city, 'logo', s.logo,
    'positions', coalesce(s.settings->'apply_positions', '["Stylist","Assistant","Front desk"]'::jsonb),
    'intro', s.settings->>'apply_intro',
    'background', coalesce((s.settings->>'apply_background')::boolean, false))
  from lp_apply_salon(p_slug) s where s.id is not null
$$;

create or replace function lp_apply(p_slug text, p jsonb) returns boolean language plpgsql security definer set search_path = public, storage as $$
declare s lp_salons; v_email text; v_resume text; v_ans jsonb; v_more jsonb;
begin
  s := lp_apply_salon(p_slug);
  if s.id is null then raise exception 'APPLY_CLOSED'; end if;
  if coalesce((p->>'ms')::int, 0) < 4000 then raise exception 'TOO_FAST'; end if;
  if coalesce(trim(p->>'name'), '') = '' or (coalesce(trim(p->>'phone'), '') = '' and coalesce(trim(p->>'email'), '') = '') then raise exception 'MISSING'; end if;
  -- the rest of the application: short text answers only, with simple names
  v_more := coalesce((select jsonb_object_agg(key, left(value #>> '{}', 3000)) from (
      select key, value from jsonb_each(case when jsonb_typeof(p->'answers') = 'object' then p->'answers' else '{}'::jsonb end)
      where key ~ '^[a-z0-9_]{1,40}$' and key not in ('resume_file','resume_name','source')
        and jsonb_typeof(value) in ('string','number','boolean') and coalesce(value #>> '{}', '') <> '' limit 200) x), '{}'::jsonb);
  if coalesce(trim(v_more->>'signature'), '') = '' or v_more->>'agree' is distinct from 'Yes' then raise exception 'SIGNATURE'; end if;
  v_email := lower(nullif(trim(p->>'email'), ''));
  if (select count(*) from lp_applicants where salon_id = s.id and submission_id like 'web-%' and submitted_at > now() - interval '1 hour') >= 25 then raise exception 'BUSY'; end if;
  if v_email is not null and exists (select 1 from lp_applicants where salon_id = s.id and lower(email) = v_email and submitted_at > now() - interval '1 day') then raise exception 'ALREADY'; end if;
  v_resume := nullif(p->>'resume_file', '');
  if v_resume is not null and (v_resume !~ '^resumes/[A-Za-z0-9._-]+$'
      or not exists (select 1 from storage.objects o where o.bucket_id = 'lp-files' and o.name = s.id || '/' || v_resume and o.created_at > now() - interval '1 hour')) then
    v_resume := null;
  end if;
  v_ans := v_more || jsonb_strip_nulls(jsonb_build_object(
    'license', left(p->>'license', 200), 'experience', left(p->>'experience', 200), 'availability', left(p->>'availability', 500),
    'start', left(p->>'start', 100), 'instagram', left(p->>'instagram', 100), 'heard', left(p->>'heard', 200), 'about', left(p->>'about', 3000),
    'resume_file', v_resume, 'resume_name', case when v_resume is null then null else left(p->>'resume_name', 150) end));
  insert into lp_applicants (salon_id, name, position, phone, email, answers, submission_id, status, log, submitted_at)
  values (s.id, left(trim(p->>'name'), 100), nullif(left(trim(p->>'position'), 100), ''), nullif(left(trim(p->>'phone'), 40), ''), v_email,
          v_ans, 'web-' || gen_random_uuid(), 'new', '[]'::jsonb, now());
  return true;
end $$;
grant execute on function lp_apply_info(text), lp_apply(text, jsonb) to anon, authenticated;
