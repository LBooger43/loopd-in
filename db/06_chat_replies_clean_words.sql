-- Team chat replies and reactions, and no swearing in team chat, announcements and daily log notes.
-- Part 1 is Salon Saia (public tables). Part 2 is Loopd-In (lp_ tables, one salon at a time).

-- ================= the word list (shared) =================
create or replace function swear_word(t text) returns text language sql immutable as $$
  select (regexp_match(coalesce(t, ''), '(f[u*@]+c?k\w*|\ysh[i1!*]t\w*|bullshit\w*|dipshit\w*|horseshit|\ybitch\w*|\yass(hole|holes|hat|es)\y|\yass\y(?!'')|jackass\w*|dumbass\w*|smartass\w*|\ybastards?\y|\y(god)?damn(ed|it)?\y|\ydickheads?\y|\ycocks?\y|\ypuss(y|ies)\y|\ycunts?\y|\ypiss(ed|ing|es)?\y|\ycrap(py|s)?\y|\ysluts?\y|\ywhores?\y|\ywtf\y|\ystfu\y)', 'i'))[1]
$$;
grant execute on function swear_word(text) to anon, authenticated;
create or replace function no_swearing() returns trigger language plpgsql as $$
declare w text := swear_word(to_jsonb(new)->>tg_argv[0]);
begin
  if w is not null and (tg_op = 'INSERT' or (to_jsonb(new)->>tg_argv[0]) is distinct from (to_jsonb(old)->>tg_argv[0])) then
    raise exception 'NO_SWEARING: %', w using errcode = 'P0001';
  end if;
  return new;
end $$;
do $$ declare x record; begin
  for x in select * from (values ('messages','body'),('announcements','body'),('daily_log','note'),('log_replies','note'),
                                  ('lp_messages','body'),('lp_announcements','body'),('lp_daily_log','note'),('lp_log_replies','note')) v(t, c) loop
    execute format('drop trigger if exists no_swearing on %I', x.t);
    execute format('create trigger no_swearing before insert or update on %I for each row execute function no_swearing(%L)', x.t, x.c);
  end loop;
end $$;

-- ================= Part 1: Salon Saia =================
alter table messages add column if not exists reply_to uuid references messages(id) on delete set null;
alter table messages add column if not exists reactions jsonb not null default '{}'::jsonb;
alter table announcements add column if not exists reactions jsonb not null default '{}'::jsonb;

-- tap an emoji to add it, tap again to take it back (anyone on the team, on any message)
create or replace function chat_react(p_kind text, p_id uuid, p_emoji text) returns void language plpgsql security definer set search_path = public as $$
declare me text := lower(coalesce(auth.jwt()->>'email', '')); cur jsonb; lst jsonb;
begin
  if not exists (select 1 from staff where lower(email) = me) then raise exception 'Not on the team.'; end if;
  if p_emoji not in ('👍','❤️','😂','🎉','🙏','👀') then raise exception 'Unknown reaction.'; end if;
  if p_kind = 'a' then select reactions into cur from announcements where id = p_id for update;
  else select reactions into cur from messages where id = p_id for update; end if;
  if not found then raise exception 'Message not found.'; end if;
  lst := coalesce(cur->p_emoji, '[]'::jsonb);
  lst := case when lst ? me then (select coalesce(jsonb_agg(v), '[]'::jsonb) from jsonb_array_elements_text(lst) v where v <> me) else lst || to_jsonb(me) end;
  cur := case when jsonb_array_length(lst) = 0 then coalesce(cur, '{}'::jsonb) - p_emoji else jsonb_set(coalesce(cur, '{}'::jsonb), array[p_emoji], lst) end;
  if p_kind = 'a' then update announcements set reactions = cur where id = p_id; else update messages set reactions = cur where id = p_id; end if;
end $$;
grant execute on function chat_react(text, uuid, text) to authenticated;

-- ================= Part 2: Loopd-In =================
alter table lp_messages add column if not exists reply_to uuid references lp_messages(id) on delete set null;
alter table lp_messages add column if not exists reactions jsonb not null default '{}'::jsonb;
alter table lp_announcements add column if not exists reactions jsonb not null default '{}'::jsonb;

create or replace function lp_chat_react(p_kind text, p_id uuid, p_emoji text) returns void language plpgsql security definer set search_path = public as $$
declare me text := lp_me(); cur jsonb; lst jsonb;
begin
  if not lp_is_staff() then raise exception 'Not on the team.'; end if;
  if p_emoji not in ('👍','❤️','😂','🎉','🙏','👀') then raise exception 'Unknown reaction.'; end if;
  if p_kind = 'a' then select reactions into cur from lp_announcements where id = p_id and salon_id = lp_my_salon() for update;
  else select reactions into cur from lp_messages where id = p_id and salon_id = lp_my_salon() for update; end if;
  if not found then raise exception 'Message not found.'; end if;
  lst := coalesce(cur->p_emoji, '[]'::jsonb);
  lst := case when lst ? me then (select coalesce(jsonb_agg(v), '[]'::jsonb) from jsonb_array_elements_text(lst) v where v <> me) else lst || to_jsonb(me) end;
  cur := case when jsonb_array_length(lst) = 0 then coalesce(cur, '{}'::jsonb) - p_emoji else jsonb_set(coalesce(cur, '{}'::jsonb), array[p_emoji], lst) end;
  if p_kind = 'a' then update lp_announcements set reactions = cur where id = p_id and salon_id = lp_my_salon();
  else update lp_messages set reactions = cur where id = p_id and salon_id = lp_my_salon(); end if;
end $$;
grant execute on function lp_chat_react(text, uuid, text) to authenticated;

-- a reply must point at a message in the same salon
create or replace function lp_reply_same_salon() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.reply_to is not null and not exists (select 1 from lp_messages where id = new.reply_to and salon_id = new.salon_id) then new.reply_to := null; end if;
  return new;
end $$;
drop trigger if exists lp_reply_same_salon on lp_messages;
create trigger lp_reply_same_salon before insert on lp_messages for each row execute function lp_reply_same_salon();
