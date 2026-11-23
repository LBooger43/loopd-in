-- Loopd-In for Restaurants.
-- A business is a salon or a restaurant (lp_salons.settings->>'business_type'; missing = salon).
-- Restaurants get: shift notes (open / mid / close handoffs that roll up into the owner's recap),
-- opening and closing checklists in English and Spanish, and a temperature log.
-- Safe to run more than once.

-- ---------- starting a business: pick salon or restaurant ----------
create or replace function lp_create_salon(p_code text, p_salon text, p_city text, p_name text, p_kind text)
returns uuid language plpgsql security definer set search_path = public as $$
declare v_plan text; v_id uuid; v_me text := lp_me();
  v_kind text := case when lower(coalesce(p_kind, '')) = 'restaurant' then 'restaurant' else 'salon' end;
begin
  if v_me = '' then raise exception 'Sign in first.'; end if;
  if exists (select 1 from lp_staff where lower(email) = v_me) then raise exception 'ALREADY_IN_SALON'; end if;
  select plan into v_plan from lp_invite_codes where upper(code) = upper(trim(p_code)) and uses_left > 0 for update;
  if v_plan is null then raise exception 'BAD_CODE'; end if;
  update lp_invite_codes set uses_left = uses_left - 1 where upper(code) = upper(trim(p_code));
  insert into lp_salons (name, city, plan, created_by, settings)
    values (trim(p_salon), nullif(trim(p_city), ''), v_plan, v_me, jsonb_build_object('timeoff_limit', 2, 'business_type', v_kind))
    returning id into v_id;
  insert into lp_staff (salon_id, email, name, role) values (v_id, v_me, trim(p_name), 'manager');
  if v_kind = 'restaurant' then perform lp_seed_restaurant(v_id); end if;
  return v_id;
end $$;

-- ---------- shift notes ----------
create table if not exists lp_shift_notes (
  id uuid primary key default gen_random_uuid(),
  salon_id uuid not null default lp_my_salon() references lp_salons(id) on delete cascade,
  shift_date date not null default current_date,
  shift text not null default 'close' check (shift in ('open','mid','close')),
  sales numeric(10,2),
  labor_hours numeric(7,2),
  labor_pct numeric(5,2),
  comps numeric(10,2),
  tags text[] not null default '{}',
  callouts text,
  eighty_six text,
  guest_issue text,
  broke text,
  note_next text,
  flag_owner boolean not null default false,
  owner_done_at timestamptz,
  owner_done_by text,
  photo text,
  read_by text,
  read_at timestamptz,
  created_by text not null default lp_me(),
  created_at timestamptz not null default now()
);
create index if not exists lp_shift_notes_salon_idx on lp_shift_notes (salon_id, shift_date desc);

-- ---------- checklists ----------
create table if not exists lp_check_items (
  id uuid primary key default gen_random_uuid(),
  salon_id uuid not null default lp_my_salon() references lp_salons(id) on delete cascade,
  list text not null check (list in ('open','close')),
  area text not null default 'all' check (area in ('foh','boh','all')),
  label_en text not null,
  label_es text,
  sort int not null default 0,
  active boolean not null default true,
  created_at timestamptz not null default now()
);
create index if not exists lp_check_items_salon_idx on lp_check_items (salon_id, list, sort);

create table if not exists lp_check_done (
  id uuid primary key default gen_random_uuid(),
  salon_id uuid not null default lp_my_salon() references lp_salons(id) on delete cascade,
  item_id uuid not null references lp_check_items(id) on delete cascade,
  done_date date not null default current_date,
  done_by text not null default lp_me(),
  done_at timestamptz not null default now(),
  unique (item_id, done_date)
);
create index if not exists lp_check_done_salon_idx on lp_check_done (salon_id, done_date desc);

-- ---------- temperature log ----------
create table if not exists lp_temp_logs (
  id uuid primary key default gen_random_uuid(),
  salon_id uuid not null default lp_my_salon() references lp_salons(id) on delete cascade,
  unit text not null,
  kind text not null default 'cold' check (kind in ('cold','frozen','hot')),
  temp numeric(5,1) not null,
  logged_date date not null default current_date,
  logged_by text not null default lp_me(),
  logged_at timestamptz not null default now(),
  note text
);
create index if not exists lp_temp_logs_salon_idx on lp_temp_logs (salon_id, logged_at desc);

alter table lp_shift_notes enable row level security;
alter table lp_check_items enable row level security;
alter table lp_check_done enable row level security;
alter table lp_temp_logs enable row level security;

do $$ declare t text; p record; begin
  foreach t in array array['lp_shift_notes','lp_check_items','lp_check_done','lp_temp_logs'] loop
    for p in select policyname from pg_policies where schemaname = 'public' and tablename = t loop
      execute format('drop policy %I on %I', p.policyname, t);
    end loop;
  end loop;
end $$;

-- shift notes: shift leads (front desk role) and managers write and read them; managers delete
create policy sh_read on lp_shift_notes for select to authenticated using (salon_id = lp_my_salon() and lp_is_desk());
create policy sh_add on lp_shift_notes for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_desk() and created_by = lp_me());
create policy sh_edit on lp_shift_notes for update to authenticated using (salon_id = lp_my_salon() and lp_is_desk()) with check (salon_id = lp_my_salon());
create policy sh_del on lp_shift_notes for delete to authenticated using (salon_id = lp_my_salon() and lp_is_manager());

-- checklist items: the whole team sees them; managers edit the list
create policy ci_read on lp_check_items for select to authenticated using (salon_id = lp_my_salon() and lp_is_staff());
create policy ci_mgr on lp_check_items for all to authenticated using (salon_id = lp_my_salon() and lp_is_manager()) with check (salon_id = lp_my_salon() and lp_is_manager());

-- check-offs: anyone on the team checks items off; you can undo your own, managers can undo any
create policy cd_read on lp_check_done for select to authenticated using (salon_id = lp_my_salon() and lp_is_staff());
create policy cd_add on lp_check_done for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_staff() and done_by = lp_me());
create policy cd_del on lp_check_done for delete to authenticated using (salon_id = lp_my_salon() and (lp_is_manager() or done_by = lp_me()));

-- temperatures: anyone on the team logs and reads them; managers delete mistakes
create policy tl_read on lp_temp_logs for select to authenticated using (salon_id = lp_my_salon() and lp_is_staff());
create policy tl_add on lp_temp_logs for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_staff() and logged_by = lp_me());
create policy tl_del on lp_temp_logs for delete to authenticated using (salon_id = lp_my_salon() and lp_is_manager());

-- locked (beta over) salons can't save; live updates on every phone
do $$ declare t text; begin
  foreach t in array array['lp_shift_notes','lp_check_items','lp_check_done','lp_temp_logs'] loop
    execute format('drop trigger if exists lp_locked_guard on %I', t);
    execute format('create trigger lp_locked_guard before insert or update or delete on %I for each row execute function lp_locked_guard()', t);
    begin execute format('alter publication supabase_realtime add table %I', t); exception when others then null; end;
  end loop;
end $$;

-- ---------- starter checklists (English + Spanish) ----------
create or replace function lp_seed_restaurant(p_salon uuid) returns void language plpgsql security definer set search_path = public as $$
begin
  if exists (select 1 from lp_check_items where salon_id = p_salon) then return; end if;
  insert into lp_check_items (salon_id, list, area, label_en, label_es, sort) values
    (p_salon, 'open', 'boh', 'Walk-in, reach-ins and freezer temps logged', 'Temperaturas de cámara fría, refrigeradores y congelador anotadas', 10),
    (p_salon, 'open', 'boh', 'Line set up and stocked', 'Línea lista y surtida', 20),
    (p_salon, 'open', 'boh', 'Prep list checked', 'Lista de preparación revisada', 30),
    (p_salon, 'open', 'boh', 'Sanitizer buckets set at every station', 'Cubetas de desinfectante en cada estación', 40),
    (p_salon, 'open', 'foh', 'Dining room and restrooms checked', 'Comedor y baños revisados', 50),
    (p_salon, 'open', 'foh', 'Specials and 86 list shared with the team', 'Especiales y lista de 86 compartidos con el equipo', 60),
    (p_salon, 'open', 'foh', 'Bar set up, ice filled', 'Barra lista, hielo lleno', 70),
    (p_salon, 'close', 'boh', 'Fryers filtered and covered', 'Freidoras filtradas y tapadas', 10),
    (p_salon, 'close', 'boh', 'Flat-top scraped and oiled', 'Plancha raspada y aceitada', 20),
    (p_salon, 'close', 'boh', 'Food labeled, dated and put away', 'Comida etiquetada, fechada y guardada', 30),
    (p_salon, 'close', 'boh', 'Walk-in temp logged', 'Temperatura de la cámara fría anotada', 40),
    (p_salon, 'close', 'boh', 'Floors swept and mopped', 'Pisos barridos y trapeados', 50),
    (p_salon, 'close', 'boh', 'Trash taken out', 'Basura sacada', 60),
    (p_salon, 'close', 'foh', 'Bar restocked, taps covered', 'Barra surtida, llaves cubiertas', 70),
    (p_salon, 'close', 'foh', 'Tables and booths wiped, set for tomorrow', 'Mesas y gabinetes limpios, listos para mañana', 80),
    (p_salon, 'close', 'all', 'Cash drop done', 'Depósito de efectivo hecho', 90),
    (p_salon, 'close', 'all', 'Back door locked, alarm set', 'Puerta trasera cerrada con llave, alarma puesta', 100);
end $$;
revoke all on function lp_seed_restaurant(uuid) from public, anon, authenticated;

-- ---------- managers: switch business type (seeds the starter checklists the first time) ----------
create or replace function lp_set_business_type(p_kind text) returns void language plpgsql security definer set search_path = public as $$
declare v_kind text := case when lower(coalesce(p_kind, '')) = 'restaurant' then 'restaurant' else 'salon' end;
begin
  if not lp_is_manager() then raise exception 'Only managers can change this.'; end if;
  update lp_salons set settings = coalesce(settings, '{}'::jsonb) || jsonb_build_object('business_type', v_kind) where id = lp_my_salon();
  if v_kind = 'restaurant' then perform lp_seed_restaurant(lp_my_salon()); end if;
end $$;

grant execute on function lp_create_salon(text, text, text, text, text) to authenticated;
grant execute on function lp_set_business_type(text) to authenticated;
