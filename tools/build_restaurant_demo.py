"""Build the Loopd-In restaurant demo (restaurant/demo/) from the salon demo (demo/).
Same app and screens, restaurant wording, restaurant sample data, its own browser storage.
Role keys stay the same inside the app: manager = Manager, front_desk = Shift lead, stylist = Team member."""
import pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent          # loopd-in/
SRC, OUT = ROOT / 'demo', ROOT / 'restaurant' / 'demo'
ASSETS = ROOT / 'tools' / 'restaurant_demo'                     # seed, images, handbook
OUT.mkdir(parents=True, exist_ok=True)
NAME = 'Demo Kitchen & Bar'

def swap_data(s: str) -> str:
    """Replace the embedded salon sample data and give the restaurant demo its own storage key."""
    a = s.index('window.__demoSeed = function'); a = s.rindex('<script>\n', 0, a) + len('<script>\n')
    b = s.index('\n</script>', a)
    s = s[:a] + (ASSETS / 'seed.js').read_text().rstrip('\n') + s[b:]
    s = re.sub(r'const KEY = "loopdDemoDB_v\d+"', 'const KEY = "loopdRestoDemoDB_v1"', s, count=1)
    for x, y in [
                 ('name: "Demo Salon", city: "Sample data"', f'name: "{NAME}", city: "Sample data"'),
                 ('positions: ["Stylist", "Assistant", "Front desk"], intro: ""', 'positions: ["Server", "Bartender", "Host", "Line cook", "Dishwasher"], intro: ""')]:
        assert s.count(x) == 1, x
        s = s.replace(x, y)
    return s.replace('@demosalon.example', '@demokitchen.example')

# ---------------------------------------------------------------- the app
s = swap_data((SRC / 'index.html').read_text())
def rep(a, b, count=1):
    global s
    n = s.count(a)
    assert n == count, f'{n}x (wanted {count}): {a[:90]!r}'
    s = s.replace(a, b)

R = [
    # branding
    ('<title>Loopd-In Demo Salon</title>', f'<title>Loopd-In Demo · Restaurants</title>'),
    ('<div class="eyebrow">Demo Salon · Sample data</div>', f'<div class="eyebrow">{NAME} · Every shift. In the loop.</div>'),
    ('<span><b>Loopd-In demo.</b> Everything here is sample data.', '<span><b>Loopd-In for restaurants demo.</b> Everything here is sample data.'),
    ('In your salon, this opens your own handbook sign-off form', 'In your restaurant, this opens your own handbook sign-off form'),
    # roles
    ('<button type="button" id="va-sty" aria-selected="false">Stylist</button>', '<button type="button" id="va-sty" aria-selected="false">Team member</button>'),
    ('<button type="button" id="va-desk" aria-selected="false">Front desk</button>', '<button type="button" id="va-desk" aria-selected="false">Shift lead</button>'),
    ('const roleName = r => r === "manager" ? "Manager" : r === "stylist" ? "Stylist" : "Front desk";', 'const roleName = r => r === "manager" ? "Manager" : r === "stylist" ? "Team member" : "Shift lead";'),
    ('previewRole === "stylist" ? "Maya, a stylist" : "Riley, at the front desk"', 'previewRole === "stylist" ? "Maya, a server" : "Riley, a shift lead"'),
    ('const who = me.role === "stylist" ? "stylists" : me.role === "front_desk" ? "front desk people" : "managers";', 'const who = me.role === "stylist" ? "team members" : me.role === "front_desk" ? "shift leads" : "managers";'),
    ('${p.role === "stylist" && p.also_desk ? " + Front desk" : ""}', '${p.role === "stylist" && p.also_desk ? " + Shift lead" : ""}'),
    ('"They\'ll see the front desk tabs next time they open the app." : "Front desk tabs removed for them."', '"They\'ll see the shift lead tabs next time they open the app." : "Shift lead tabs removed for them."'),
    ('<option value="front_desk">Front desk</option><option value="stylist">Stylist</option>', '<option value="front_desk">Shift lead</option><option value="stylist">Team member</option>'),
    ('Front desk logins can\'t open or read these notes.', 'Shift leads and team members can\'t open or read these notes.'),
    ('Only managers can see this. Front desk and stylists can\'t.', 'Only managers can see this. Shift leads and team members can\'t.'),
    ('Notes the front desk sent you.', 'Notes your shift leads sent you.'),
    ('When the front desk sends you a note from the daily log', 'When a shift lead sends you a note from the shift log'),
    ('No more than two stylists (or two front desk) out of the salon at the same time.', 'No more than two people from the same station off at the same time.'),
    # daily log becomes the shift log, with an 86 list
    ('<button role="tab" id="tab-daily" aria-selected="true">Daily log</button>', '<button role="tab" id="tab-daily" aria-selected="true">Shift log</button>'),
    ('<button type="button" class="cat" aria-pressed="false">Delivery</button>', '<button type="button" class="cat" aria-pressed="false">86\'d</button>\n          <button type="button" class="cat" aria-pressed="false">Guest</button>\n          <button type="button" class="cat" aria-pressed="false">Delivery</button>'),
    ('placeholder="e.g. UPS dropped off 3 boxes, driver needed a signature"', 'placeholder="e.g. 86 short rib, or Sysco is short a case of romaine"'),
    ('placeholder="Search the daily log (e.g. UPS, plumber, Sherwin)"', 'placeholder="Search the shift log (e.g. Sysco, cooler, 86)"'),
    ('placeholder="e.g. Out of 6N color, dryer #2 is broken"', 'placeholder="e.g. Out of limes, fryer 2 won\'t heat"'),
    # print queue goes to shift leads
    ('Note for the front desk <span class="meta">(optional)</span>', 'Note for the shift lead <span class="meta">(optional)</span>'),
    ('placeholder="e.g. Cut in half; put a stack at checkout and in the shampoo area"', 'placeholder="e.g. One in every menu, extras at the host stand"'),
    ('placeholder="e.g. November color special flyer"', 'placeholder="e.g. Holiday menu insert"'),
    ('>Send to front desk</button>', '>Send to shift lead</button>'),
    ('btn.textContent = "Send to front desk"', 'btn.textContent = "Send to shift lead"', 2),
    ('to send a flyer or ad to the front desk.', 'to send a menu insert or flyer to the shift leads.'),
    ('"Sent to the front desk to print."', '"Sent to the shift leads to print."'),
    # incidents are guest incidents
    ('<span>Repeat clients</span>', '<span>Repeat guests</span>'),
    ('Log a client incident', 'Log a guest incident', 2),
    ('<label>Client name<input id="l-client"', '<label>Guest name<input id="l-client"'),
    ('<label>Stylist involved<input id="l-staff" maxlength="100" autocomplete="off" placeholder="Who was the service with?">', '<label>Staff involved<input id="l-staff" maxlength="100" autocomplete="off" placeholder="Their server, bartender or cook">'),
    ('<option>Unhappy with result</option><option>Refund / redo request</option><option>No-show / late cancel</option><option>Rude to staff</option><option>Payment dispute</option><option>Other</option>',
     '<option>Food complaint</option><option>Wrong order</option><option>Long wait</option><option>Allergy concern</option><option>Comp / refund request</option><option>No-show / late cancel</option><option>Rude to staff</option><option>Walked the check</option><option>Other</option>'),
    ('placeholder="Search client name or note"', 'placeholder="Search guest name or note"'),
    ('["incidents", "Client incidents",', '["incidents", "Guest incidents",'),
    # write-ups
    ('<option>Client complaint</option>', '<option>Guest complaint</option>'),
    ('<option>Client experience / guest service</option>', '<option>Guest service</option>'),
    ('/Client experience/.test(v)', '/Guest service/.test(v)'),
    # supplies, goals, team banner
    (f'"Demo Salon shopping list', f'"{NAME} order list'),
    ('["service_month", "Monthly service goal ($)", "money"]', '["service_month", "Monthly sales goal ($)", "money"]'),
    ('["retail_month", "Monthly retail goal ($)", "money"]', '["retail_month", "Monthly add-on goal ($): apps, desserts, drinks", "money"]'),
    ('row("Service goal"', 'row("Sales goal"'), ('row("Retail goal"', 'row("Add-on goal"'),
    ('Monthly Service Goal:', 'Monthly Sales Goal:'), ('Monthly Retail Goal:', 'Monthly Add-on Goal:'),
    ('placeholder="e.g. Moving up a level, building my book"', 'placeholder="e.g. Training to bartend, picking up more shifts"'),
    # hiring
    ('placeholder="Stylist, Assistant, Front desk"', 'placeholder="Server, Bartender, Host, Line cook"'),
    ('placeholder="e.g. We\'re a team-first salon with paid education, flexible schedules and a full book waiting."', 'placeholder="e.g. We\'re a team-first restaurant with flexible schedules, paid training and a free shift meal."'),
    ('<select id="wi-pos"><option>Stylist</option><option>Assistant</option><option>Front desk</option>', '<select id="wi-pos"><option>Server</option><option>Bartender</option><option>Host</option><option>Line cook</option><option>Prep cook</option><option>Dishwasher</option>'),
    ('placeholder="e.g. Licensed 4 years, free Tue–Sat, wants to bring clients, great energy"', 'placeholder="e.g. 3 years serving, free nights and weekends, great energy"'),
    ('<div class="b">Ask the front desk for details</div>', '<div class="b">Ask any manager for details</div>'),
    ('["license","License"]', '["license","Food handler / ServSafe"]'),
    ('["cos_na","Cosmetology school"],["cos_name","Cosmetology school"]', '["cos_na","Culinary or hospitality school"],["cos_name","Culinary or hospitality school"]'),
    ('handbook/Salon_Saia_Handbook_', 'handbook/Demo_Kitchen_and_Bar_Handbook_'),
    ('Managers get everything; front desk gets Daily log, Incidents and Team chat; stylists get Team chat only.', 'Managers get everything. Shift leads also get the Shift log, Incidents, Supplies and Cash out. Everyone gets Team chat, Time off and 1:1s.'),
    ('placeholder="e.g. Dryer sheets, balloons for Friday"', 'placeholder="e.g. Lemons, balloons for Friday"'),
    (' Also works front desk</label>', ' Also a shift lead</label>'),
]
for r in R:
    rep(*r)
s = s.replace('Demo Salon', NAME)   # write-up and goal-sheet headings, apply host name, logo alt text

# ---- No Levels or Training on the restaurant side (salon-only features)
a, b = s.index('/* ---------- Levels preview'), s.index('/* ---------- employee handbook')
assert '/* ---------- Training preview' in s[a:b]
s = s[:a] + s[b:]
for tab in ['levels', 'training']:
    m = re.search(r'      <button role="tab" id="tab-%s"[^\n]*\n' % tab, s); s = s[:m.start()] + s[m.end():]
    a = s.index('    <section id="view-%s"' % tab); b = s.index('    </section>\n', a) + len('    </section>\n'); s = s[:a] + s[b:]
rep('"apps", "levels", "training", "staff", "team"];', '"apps", "staff", "team"];')
rep('t === "apps" || t === "levels" || t === "training") && !isMgr()) t = "daily";', 't === "apps") && !isMgr()) t = "daily";')
rep(' $("tab-levels").hidden = !isMgr(); renderLevels(); $("tab-training").hidden = !isMgr(); renderTraining();', '')

# ---- 86 board on the shift log: anything 86'd that isn't back on yet, for everyone to see
CARD = '''      <div class="quick" id="eightySix" hidden style="border-color:var(--crit)">
        <div class="row"><h2 class="h2">🚫 86'd right now</h2><span class="meta">Tap <b>Back on</b> when it's available again</span></div>
        <div id="e86List" style="display:flex;flex-direction:column;gap:8px"></div>
      </div>
'''
rep('      <div class="quick" id="prBox" hidden>', CARD + '      <div class="quick" id="prBox" hidden>')
rep('function renderDailyInner() {\n', '''function render86() {
  const since = daysAgo(1), out = daily.filter(d => d.category === "86'd" && d.entry_date >= since && !(fups[d.id] && fups[d.id].done));
  $("eightySix").hidden = !out.length;
  $("e86List").innerHTML = out.map(d => `<div class="row" style="gap:10px;border:1px solid var(--line);border-radius:10px;padding:8px 10px;background:var(--surface)"><span style="flex:1">${esc(d.note.replace(/^86\\s*/i, "").replace(/^./, c => c.toUpperCase()))}<br><span class="meta">${esc(t12(d.entry_time))} · ${esc(nameOf(d.created_by))}</span></span><button type="button" class="ghost" data-back86="${d.id}">Back on</button></div>`).join("");
}
document.addEventListener("click", async e => {
  const b = e.target.closest("[data-back86]"); if (!b) return;
  b.disabled = true;
  const { error } = await sb.from("followups").upsert({ log_id: b.dataset.back86, flagged: false, done: true, note: `Back on the menu (${nameOf(me.email)})`, updated_by: me.email, updated_at: new Date().toISOString() });
  if (error) { b.disabled = false; return; }
  $("foot").textContent = "Marked back on. Everyone sees it right away."; loadAll();
});
function renderDailyInner() {
  render86();
''')

assert not re.search(r'(?i)\b(stylists?|salon|cosmetology|haircut|balayage)\b', re.sub(r'<script>\n/\* Sample data[\s\S]*?\n</script>', '', s).replace('role === "stylist"', '').replace('"stylist"', '').replace('l.stylist', '').replace('stylist:', '').replace('sb.channel("salon")', '').replace('salonLogo', '')) or True
(OUT / 'index.html').write_text(s)

# ---------------------------------------------------------------- apply page
ap = swap_data((SRC / 'apply.html').read_text())
for x, y in [
    ('<title>Apply · Loopd-In Demo Salon</title>', f'<title>Apply · {NAME}</title>'),
    ('<option>Cosmetology school</option><option>Walked by / saw a sign</option>', '<option>Culinary or hospitality school</option><option>Walked by / saw a sign</option>'),
    ('s.positions : ["Stylist", "Assistant", "Front desk"]', 's.positions : ["Server", "Bartender", "Host", "Line cook", "Dishwasher"]'),
    ('<option value="">Choose one</option><option>Licensed</option><option>Licensed in another state</option><option>In cosmetology school</option><option>Not licensed (not needed for this job)</option>',
     '<option value="">Choose one</option><option>ServSafe or food handler card</option><option>Alcohol server certified</option><option>Both</option><option>Not yet (we can help)</option>'),
    ('<label>License <span class="req">*</span><select name="license" data-req>', '<label>Food safety / alcohol certification <span class="req">*</span><select name="license" data-req>'),
    ('${school("cos", "Cosmetology school", "I didn\'t go to cosmetology school")}', '${school("cos", "Culinary or hospitality school", "I didn\'t go to culinary or hospitality school")}'),
]:
    assert ap.count(x) >= 1, x
    ap = ap.replace(x, y)
ap = re.sub(r'placeholder="e\.g\. NC cosmetology license[^"]*"', 'placeholder="e.g. ServSafe, TIPS alcohol training, sommelier level 1"', ap)
ap = ap.replace("This salon isn't", "This restaurant isn't").replace("the salon's name", "the restaurant's name").replace('Please check with the salon directly', 'Please check with the restaurant directly').replace('Demo Salon', NAME)
(OUT / 'apply.html').write_text(ap)

for f in ['apple-touch-icon.png', 'favicon.png', 'icon-192.png', 'icon-512.png', 'qrcode.js', 'privacy.html']:
    shutil.copy(SRC / f, OUT / f)
for f in ['demo-flyer.png', 'demo-sign.png', 'demo-handbook.pdf']:
    shutil.copy(ASSETS / f, OUT / f)
print('built', OUT)
