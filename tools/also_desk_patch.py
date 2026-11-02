"""'Also works front desk' checkbox for stylists (Salon Saia's and Loopd-In's index.html; the demo is built from Salon Saia's)."""
import pathlib, sys

def patch(s: str) -> str:
    if 'data-also=' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    rep('const isDesk = () => effRole() === "manager" || effRole() === "front_desk";',
        'const isDesk = () => effRole() === "manager" || effRole() === "front_desk" || (!previewRole && !!me && me.role === "stylist" && !!me.also_desk);')
    rep('const { data: row } = await sb.from("staff").select("name").eq("email", email).maybeSingle();',
        'const { data: row } = await sb.from("staff").select("name,also_desk").eq("email", email).maybeSingle();\n  me.also_desk = !!(row && row.also_desk);')
    rep('  team = r[0].data || []; daily = r[1].data || [];',
        '  team = r[0].data || []; daily = r[1].data || [];\n  { const mine = team.find(x => x.email === me.email); if (mine && !!mine.also_desk !== !!me.also_desk) { me.also_desk = !!mine.also_desk; applyRole(); } }')
    rep('me && (me.role === "manager" || me.role === "front_desk") ? await sb.from("print_jobs")',
        'me && (me.role === "manager" || me.role === "front_desk" || me.also_desk) ? await sb.from("print_jobs")')
    # team list: role tag shows both jobs; checkbox next to the access menu for stylists
    rep('<span class="tag">${roleName(p.role)}</span></div>',
        '<span class="tag">${roleName(p.role)}${p.role === "stylist" && p.also_desk ? " + Front desk" : ""}</span></div>')
    rep('''</select><button class="link" data-tact="reset" data-email="${esc(p.email)}">Reset password</button>''',
        '''</select>${p.role === "stylist" ? `<label style="flex-direction:row;align-items:center;gap:6px;font-weight:500;font-size:.85rem;color:var(--ink)"><input type="checkbox" data-also="${esc(p.email)}" ${p.also_desk ? "checked" : ""} style="width:18px;height:18px;min-height:0"> Also works front desk</label>` : ""}<button class="link" data-tact="reset" data-email="${esc(p.email)}">Reset password</button>''')
    rep('''  const sel = e.target.closest("[data-role-email]"); if (!sel || !isMgr()) return;''',
        '''  const also = e.target.closest("[data-also]");
  if (also && isMgr()) {
    const { error } = await sb.from("staff").update({ also_desk: also.checked }).eq("email", also.dataset.also);
    if (error) { also.checked = !also.checked; return alert(friendly(error)); }
    $("foot").textContent = also.checked ? "They'll see the front desk tabs next time they open the app." : "Front desk tabs removed for them.";
    return loadAll();
  }
  const sel = e.target.closest("[data-role-email]"); if (!sel || !isMgr()) return;''')
    return s

if __name__ == '__main__':
    for p in sys.argv[1:]:
        p = pathlib.Path(p); p.write_text(patch(p.read_text())); print('patched', p)
