-- Loopd-In: phone notification triggers (sent with prefix lp_ so they only reach that salon's team),
-- and a starter supplies list for every new salon.
create or replace function lp_notify_push() returns trigger language plpgsql security definer set search_path = public, extensions as $$
declare rec jsonb := to_jsonb(new) - 'answers';
begin
  perform net.http_post(
    url := 'https://nalechcrehlzgghtcnog.supabase.co/functions/v1/notify?key=__NOTIFY_KEY__',  -- real key filled in when run; never committed
    body := jsonb_build_object('prefix', 'lp_', 'table', tg_table_name, 'type', tg_op, 'record', rec,
                               'old_record', case when tg_op = 'UPDATE' then to_jsonb(old) - 'answers' else null end),
    headers := '{"Content-Type": "application/json"}'::jsonb);
  return new;
exception when others then return new;
end $$;
do $$ declare t text; begin
  foreach t in array array['lp_time_off','lp_one_on_ones','lp_todos','lp_applicants','lp_announcements','lp_incidents','lp_messages','lp_handbook_versions'] loop
    execute format('drop trigger if exists lp_push_ins on %I', t);
    execute format('create trigger lp_push_ins after insert on %I for each row execute function lp_notify_push()', t);
  end loop;
  foreach t in array array['lp_time_off','lp_one_on_ones'] loop
    execute format('drop trigger if exists lp_push_upd on %I', t);
    execute format('create trigger lp_push_upd after update on %I for each row when (old.status is distinct from new.status) execute function lp_notify_push()', t);
  end loop;
end $$;

-- new salons start with a typical supplies list they can edit
create or replace function lp_starter_supplies() returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into lp_supply_items (salon_id, category, name, sort, active)
  select new.id, c, n, row_number() over (), true from (values
    ('Color','Developer 20 vol'),('Color','Developer 30 vol'),('Color','Lightener'),('Color','Foils'),('Color','Gloss / toner'),
    ('Back bar','Shampoo'),('Back bar','Conditioner'),('Back bar','Neck strips'),
    ('Front desk','Receipt paper'),('Front desk','Coffee'),('Front desk','Bottled water'),
    ('Cleaning','Disinfectant'),('Cleaning','Paper towels'),('Cleaning','Trash bags')) v(c, n);
  return new;
end $$;
drop trigger if exists lp_starter_supplies on lp_salons;
create trigger lp_starter_supplies after insert on lp_salons for each row execute function lp_starter_supplies();
