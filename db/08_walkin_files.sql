-- Walk-ins: managers can attach a photo of a paper application or a résumé (Salon Saia "photos" bucket, resumes/ folder).
-- Loopd-In already allows this in its lp-files bucket (managers only can open résumés there).
update storage.buckets set allowed_mime_types = (
  select array(select distinct unnest(coalesce(allowed_mime_types, array[]::text[]) || array['application/pdf','image/jpeg','image/png','image/webp','image/heic',
    'application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document'])))
  where id in ('photos', 'lp-files') and allowed_mime_types is not null;
drop policy if exists resumes_mgr on storage.objects;
create policy resumes_mgr on storage.objects for all to authenticated
  using (bucket_id = 'photos' and (storage.foldername(name))[1] = 'resumes' and print_role() = 'manager')
  with check (bucket_id = 'photos' and (storage.foldername(name))[1] = 'resumes' and print_role() = 'manager');
