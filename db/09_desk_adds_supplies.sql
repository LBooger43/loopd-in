-- Front desk (and stylists who also work front desk) can add a new item to the Running low list, e.g. Cleaning → Dryer sheets.
-- Taking items off the list stays with managers.
drop policy if exists si_desk_add on supply_items;
create policy si_desk_add on supply_items for insert to authenticated with check (is_desk());
drop policy if exists si_desk_add on lp_supply_items;
create policy si_desk_add on lp_supply_items for insert to authenticated with check (salon_id = lp_my_salon() and lp_is_desk());
