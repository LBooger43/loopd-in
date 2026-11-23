-- Applicants: allow the "Saved for later" status (check-back date is kept in interview_at).
begin;
alter table applicants drop constraint applicants_status_check;
alter table applicants add constraint applicants_status_check check (status = any (array['new','no_answer','voicemail','spoke','interview','hired','later','not_a_fit']));
alter table lp_applicants drop constraint applicants_status_check;
alter table lp_applicants add constraint applicants_status_check check (status = any (array['new','no_answer','voicemail','spoke','interview','hired','later','not_a_fit']));
commit;
