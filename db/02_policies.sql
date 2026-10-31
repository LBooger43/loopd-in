-- Loopd-In permission rules. Every rule starts with "this row is from my salon".
-- S = my salon; M = manager; D = manager or front desk; A = anyone on the team; ME = rows I wrote.
do $$ declare t text; p record; begin
  foreach t in array array['lp_staff','lp_daily_log','lp_followups','lp_log_replies','lp_incidents','lp_resolutions','lp_staff_notes','lp_supply_items','lp_supply_needs',
    'lp_todos','lp_manager_log','lp_staff_writeups','lp_announcements','lp_messages','lp_time_off','lp_one_on_ones','lp_goal_sheets','lp_applicants','lp_handbook_versions','lp_push_subs','lp_salons'] loop
    for p in select policyname from pg_policies where schemaname = 'public' and tablename = t loop
      execute format('drop policy %I on %I', p.policyname, t);
    end loop;
  end loop;
end $$;

-- the salon itself: members read it; changes go through lp_update_salon / lp_set_plan
create policy s_read on lp_salons for select to authenticated using (id = lp_my_salon());

-- team list: everyone sees the team; managers add, change and remove people
create policy t_read on lp_staff for select to authenticated using (salon_id = lp_my_salon() and lp_is_staff());
create policy t_mgr on lp_staff for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());

-- daily log: front desk and managers
create policy dl_read on lp_daily_log for select to authenticated using (salon_id = lp_my_salon() and lp_is_desk());
create policy dl_add on lp_daily_log for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_desk() and created_by = lp_me());
create policy dl_edit on lp_daily_log for update to authenticated using (salon_id = lp_my_salon() and (lp_is_manager() or (lp_is_desk() and created_by = lp_me())))
  with check (salon_id = lp_my_salon());
create policy dl_del on lp_daily_log for delete to authenticated using (salon_id = lp_my_salon() and lp_is_manager());
create policy fu_read on lp_followups for select to authenticated using (salon_id = lp_my_salon() and lp_is_desk());
create policy fu_mgr on lp_followups for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy rp_read on lp_log_replies for select to authenticated using (salon_id = lp_my_salon() and lp_is_desk());
create policy rp_add on lp_log_replies for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_desk() and created_by = lp_me());
create policy rp_edit on lp_log_replies for update to authenticated using (salon_id = lp_my_salon() and created_by = lp_me()) with check (salon_id = lp_my_salon() and created_by = lp_me());
create policy rp_del on lp_log_replies for delete to authenticated using (salon_id = lp_my_salon() and (lp_is_manager() or created_by = lp_me()));

-- client incidents: front desk and managers
create policy in_read on lp_incidents for select to authenticated using (salon_id = lp_my_salon() and lp_is_desk());
create policy in_add on lp_incidents for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_desk() and created_by = lp_me());
create policy in_edit on lp_incidents for update to authenticated using (salon_id = lp_my_salon() and (lp_is_manager() or (lp_is_desk() and created_by = lp_me())))
  with check (salon_id = lp_my_salon());
create policy in_del on lp_incidents for delete to authenticated using (salon_id = lp_my_salon() and lp_is_manager());
create policy rs_read on lp_resolutions for select to authenticated using (salon_id = lp_my_salon() and lp_is_desk());
create policy rs_mgr on lp_resolutions for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());

-- managers only
create policy sn_mgr on lp_staff_notes for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy ml_mgr on lp_manager_log for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy wu_mgr on lp_staff_writeups for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy ap_mgr on lp_applicants for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy hv_mgr on lp_handbook_versions for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());

-- supplies: front desk and managers use the list; managers edit the item catalog
create policy si_read on lp_supply_items for select to authenticated using (salon_id = lp_my_salon() and lp_is_desk());
create policy si_mgr on lp_supply_items for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy sq_read on lp_supply_needs for select to authenticated using (salon_id = lp_my_salon() and lp_is_desk());
create policy sq_add on lp_supply_needs for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_desk());
create policy sq_edit on lp_supply_needs for update to authenticated using (salon_id = lp_my_salon() and lp_is_desk()) with check (salon_id = lp_my_salon() and lp_is_desk());
create policy sq_del on lp_supply_needs for delete to authenticated using (salon_id = lp_my_salon() and (lp_is_manager() or requested_by = lp_me()));

-- to-do list: managers run it; anyone can report an issue and see their own reports
create policy td_mgr on lp_todos for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy td_own_read on lp_todos for select to authenticated using (salon_id = lp_my_salon() and created_by = lp_me());
create policy td_report on lp_todos for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_staff() and created_by = lp_me() and reported = true);

-- announcements: everyone reads, managers post; team chat: everyone
create policy an_read on lp_announcements for select to authenticated using (salon_id = lp_my_salon() and lp_is_staff());
create policy an_mgr on lp_announcements for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy ms_read on lp_messages for select to authenticated using (salon_id = lp_my_salon() and lp_is_staff());
create policy ms_add on lp_messages for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_staff() and created_by = lp_me());
create policy ms_del on lp_messages for delete to authenticated using (salon_id = lp_my_salon() and (lp_is_manager() or created_by = lp_me()));

-- time off: managers see all; everyone requests and cancels their own
create policy to_mgr on lp_time_off for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy to_own_read on lp_time_off for select to authenticated using (salon_id = lp_my_salon() and created_by = lp_me());
create policy to_own_add on lp_time_off for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_staff() and created_by = lp_me() and status = 'pending');
create policy to_own_cancel on lp_time_off for update to authenticated using (salon_id = lp_my_salon() and created_by = lp_me() and status = 'pending')
  with check (salon_id = lp_my_salon() and created_by = lp_me() and status = 'cancelled');

-- 1:1s and goal sheets: managers see all; everyone sees and works on their own
create policy oo_mgr on lp_one_on_ones for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy oo_own_read on lp_one_on_ones for select to authenticated using (salon_id = lp_my_salon() and created_by = lp_me());
create policy oo_own_add on lp_one_on_ones for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_staff() and created_by = lp_me() and status = 'pending');
create policy oo_own_update on lp_one_on_ones for update to authenticated using (salon_id = lp_my_salon() and created_by = lp_me() and status in ('pending','proposed','confirmed'))
  with check (salon_id = lp_my_salon() and created_by = lp_me() and status in ('cancelled','confirmed'));
create policy gs_mgr on lp_goal_sheets for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());
create policy gs_own_read on lp_goal_sheets for select to authenticated using (salon_id = lp_my_salon() and created_by = lp_me());
create policy gs_own_add on lp_goal_sheets for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_staff() and created_by = lp_me());
create policy gs_own_edit on lp_goal_sheets for update to authenticated using (salon_id = lp_my_salon() and created_by = lp_me()) with check (salon_id = lp_my_salon() and created_by = lp_me());

-- phone notification sign-ups: your own only
create policy ps_own on lp_push_subs for all to authenticated using (email = lp_me()) with check (email = lp_me());

-- ---------- files: each salon has its own folder in the lp-files bucket ----------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
  values ('lp-files', 'lp-files', false, 10485760, array['image/jpeg','image/png','image/webp','application/pdf'])
  on conflict (id) do nothing;
drop policy if exists lp_files_read on storage.objects;
drop policy if exists lp_files_add on storage.objects;
drop policy if exists lp_files_del on storage.objects;
create policy lp_files_read on storage.objects for select to authenticated
  using (bucket_id = 'lp-files' and (storage.foldername(name))[1] = lp_my_salon()::text and lp_is_staff());
create policy lp_files_add on storage.objects for insert to authenticated
  with check (bucket_id = 'lp-files' and (storage.foldername(name))[1] = lp_my_salon()::text and lp_is_staff()
    and ((storage.foldername(name))[2] not in ('handbook','logo','writeups','mgrlog') or lp_is_manager()));
create policy lp_files_del on storage.objects for delete to authenticated
  using (bucket_id = 'lp-files' and (storage.foldername(name))[1] = lp_my_salon()::text and lp_is_manager());

-- live updates in the app
do $$ declare t text; begin
  foreach t in array array['lp_staff','lp_daily_log','lp_followups','lp_log_replies','lp_incidents','lp_resolutions','lp_staff_notes','lp_supply_items','lp_supply_needs',
    'lp_todos','lp_manager_log','lp_staff_writeups','lp_announcements','lp_messages','lp_time_off','lp_one_on_ones','lp_goal_sheets','lp_applicants','lp_salons'] loop
    begin execute format('alter publication supabase_realtime add table %I', t); exception when others then null; end;
  end loop;
end $$;

-- first beta invite codes (one per plan, a few uses each); more can be added any time
insert into lp_invite_codes (code, plan, uses_left, note) values
  ('BETA-DESK', 'front_desk', 5, 'Beta: Front Desk plan'),
  ('BETA-TEAM', 'team', 5, 'Beta: Team plan'),
  ('BETA-OWNER', 'owner', 5, 'Beta: Owner plan')
on conflict (code) do nothing;
