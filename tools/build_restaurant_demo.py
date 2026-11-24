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
    ('I want this for my salon', 'I want this for my restaurant', 2),
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
    ('this would be saved and the associate would get an alert.', 'this would be saved and the trainee would get an alert.'),
]
for r in R:
    rep(*r)
s = s.replace('Demo Salon', NAME)   # write-up and goal-sheet headings, apply host name, logo alt text

# ---- Levels: server levels instead of stylist levels
LV_OLD = s[s.index('const LV_LEVELS = ['):s.index('let lvTeam = LV_SAMPLE()')]
LV_NEW = '''const LV_LEVELS = [
  { n: 1, name: "Trainee", color: "#7a86a6", pay: "Base", cut: 3, color$: "Last pick", req: 0, ret: 85, pre: 15, add: 20, retail: 90 },
  { n: 2, name: "Server", color: "#2f6be0", pay: "+$0.50/hr", cut: 4, color$: "4th pick", req: 1, ret: 88, pre: 20, add: 25, retail: 93 },
  { n: 3, name: "Lead Server", color: "#5a56d6", pay: "+$1.00/hr", cut: 5, color$: "3rd pick", req: 2, ret: 90, pre: 25, add: 30, retail: 95 },
  { n: 4, name: "Trainer", color: "#8247b8", pay: "+$1.50/hr", cut: 5, color$: "2nd pick", req: 3, ret: 92, pre: 30, add: 35, retail: 97 },
  { n: 5, name: "Captain", color: "#b8478a", pay: "+$2.00/hr", cut: 6, color$: "First pick", req: 4, ret: 94, pre: 35, add: 40, retail: 98 },
];
const LV_METRICS = [["req", "5-star mentions / mo", ""], ["ret", "Guest score", "%"], ["pre", "Apps & desserts", "%"], ["add", "Drinks & wine", "%"], ["retail", "On time", "%"]];
const LV_SAMPLE = () => [
  { id: "a", name: "Maya T.", level: 2, since: 210, nums: { req: 3, ret: 91, pre: 27, add: 31, retail: 96 } },
  { id: "b", name: "Emma D.", level: 3, since: 400, nums: { req: 2, ret: 90, pre: 22, add: 30, retail: 95 }, under: 21 },
  { id: "c", name: "Lily C.", level: 1, since: 95, nums: { req: 0, ret: 87, pre: 17, add: 21, retail: 92 } },
  { id: "d", name: "Ava J.", level: 4, since: 520, nums: { req: 3, ret: 90, pre: 27, add: 33, retail: 94 }, under: 48 },
];
'''
s = s.replace(LV_OLD, LV_NEW)
for r in [
    ('<th>Commission</th><th>Haircut</th><th>Color</th>', '<th>Pay</th><th>Section</th><th>Shift pick</th>'),
    ('<td><b>${l.pay}%</b></td><td>$${l.cut}</td><td>$${l.color$}</td>', '<td><b>${l.pay}</b></td><td>${l.cut} tables</td><td>${l.color$}</td>'),
    ('Commission ${from.pay}% → ${to.pay}% · Haircut $${from.cut} → $${to.cut} · Color $${from.color$} → $${to.color$}', 'Pay ${from.pay} → ${to.pay} · Section ${from.cut} → ${to.cut} tables · Shift pick ${from.color$} → ${to.color$}'),
    ('This is a preview with sample stylists, so try anything', 'This is a preview with sample servers, so try anything'),
    ('Set your own levels: what each one pays, what it charges, and the numbers a stylist needs to reach it.', 'Set your own levels: the pay bump, section size and shift pick for each one, and the numbers a server needs to reach it.'),
    ('If a stylist stays under', 'If a server stays under'),
    ("Each stylist's numbers for the last 60 days", "Each server's numbers for the last 60 days"),
    ('👀 What a stylist will see', '👀 What a server will see'),
    ('Each stylist sees only their own level', 'Each server sees only their own level'),
    ("Type in each stylist's monthly numbers, or bring them in from your booking software later.", "Type in each server's monthly numbers, or bring them in from your POS later."),
    ('<li><b>Set your levels.</b> Name each level and set its commission, service prices and target numbers.</li>', '<li><b>Set your levels.</b> Name each level and set its pay bump, section size, shift pick and target numbers.</li>'),
]:
    rep(*r)

# ---- Training: restaurant onboarding, kitchen plate check-offs with photos
TR_OLD = s[s.index('const TR_PATH = ['):s.index('let tr = TR_SAMPLE()')]
TR_NEW = '''const TR_PATH = [
  { name: "Host stand and greeting guests", vids: 2, models: 2 },
  { name: "Menu knowledge and tasting", vids: 3, models: 2 },
  { name: "Allergies and special requests", vids: 2, models: 2 },
  { name: "Steps of service", vids: 3, models: 3 },
  { name: "POS: orders, splits and comps", vids: 2, models: 2 },
  { name: "Wine and cocktail basics", vids: 3, models: 2 },
  { name: "Food safety and sanitation", vids: 2, models: 1 },
  { name: "Line: prep and station setup", vids: 3, models: 3 },
  { name: "Line: plating to spec", vids: 3, models: 4 },
  { name: "Certification shift", vids: 1, models: 1 },
];
const TR_SAMPLE = () => ({
  people: [
    { id: "p1", name: "Daniel R.", done: 8, started: "Oct 2026", note: "Moving from dish to the line. Plating check-offs next." },
    { id: "p2", name: "Lily C.", done: 3, started: "Sep 2026", note: "Host moving to server. Trailing Maya this week." },
    { id: "p3", name: "Jasmine O.", done: 9, started: "Aug 2026", note: "One step left: her certification shift!" },
  ],
  review: [
    { id: "r1", who: "p1", skill: 9, model: 2, when: "Today, 4:40 PM", from: ["#4a5a3c", "#8aa06a"], to: ["#6b4a2f", "#c48a52"], tip: "Salmon entrée: sauce under the fish, greens on the left, like the spec photo.", pics: ["Spec photo", "Their plate"] },
    { id: "r2", who: "p2", skill: 4, model: 1, when: "Yesterday", tip: "Trailed Maya on section 3: greeted every table in under a minute, rang in apps and drinks correctly." },
  ],
});
'''
s = s.replace(TR_OLD, TR_NEW)
QUIZ_OLD = s[s.index('const TR_QUIZ = ['):s.index('function renderTraining()')]
QUIZ_NEW = '''const TR_QUIZ = [
  { q: "What is the temperature danger zone for food?", a: ["32°F to 100°F", "41°F to 135°F", "50°F to 150°F", "70°F to 165°F"], right: 1 },
  { q: "A guest tells you they have a peanut allergy. What do you do first?", a: ["Suggest a dish that looks safe", "Tell the kitchen and a manager, and mark the allergy on the ticket", "Ask them to order something else", "Nothing, the menu lists allergens"], right: 1 },
  { q: "How long should you scrub when you wash your hands?", a: ["5 seconds", "At least 20 seconds", "Only if they look dirty", "Hand sanitizer is enough"], right: 1 },
];
'''
s = s.replace(QUIZ_OLD, QUIZ_NEW)
for r in [
    ('<div class="tr-pics">${trPic(r.from, "Before", "💇")}${trPic(r.to, "After", "✨")}</div>', '${r.from ? `<div class="tr-pics">${trPic(r.from, r.pics[0], "📋")}${trPic(r.to, r.pics[1], "🍽️")}</div>` : ""}'),
    ('✂️ ${s.models} models', '✅ ${s.models} check-off${s.models > 1 ? "s" : ""}'),
    ('model ${r.model} of ${s.models}', 'check-off ${r.model} of ${s.models}'),
    ('✂️ 0 of ${nx.models} models uploaded', '✅ 0 of ${nx.models} check-offs done'),
    ('<span class="lv-badge" style="background:#7a86a6">Associate</span>', '<span class="lv-badge" style="background:#7a86a6">Trainee</span>', 2),
    ('This is a preview with sample associates, so try anything', 'This is a preview with sample trainees, so try anything'),
    ('Associates upload photos of their model work. An educator or manager checks it out or asks for a redo.', 'A trainer or manager signs off each step on the floor or the line, with photos for kitchen plates. Or asks for a redo.'),
    ('👩‍🎓 Your associates', '👩‍🍳 Your trainees'),
    ('Build your own path: the skills in order, your own videos, a short quiz and how many models each skill needs. Finishing the path moves an associate to Level 1.', 'Build your own path: the skills in order, your own videos, a short quiz and how many check-offs each one needs. Front of house and kitchen can each have their own path.'),
    ('👀 What an associate will see', '👀 What a trainee will see'),
    ('Each associate sees their own path, their next videos and what\'s waiting for check-off.', 'Each trainee sees their own path, their next videos and what\'s waiting for sign-off.'),
    ('<li><b>Watch and test.</b> Associates watch the videos and pass a short quiz for each skill.</li>', '<li><b>Watch and test.</b> Trainees watch the videos and pass a short quiz for each step: menu, allergies, food safety.</li>'),
    ('<li><b>Model and upload.</b> They do the service on a model and upload before and after photos from their phone.</li>', '<li><b>Trail and practice.</b> They trail a trainer on real shifts. Cooks upload photos of their plates next to the spec.</li>'),
    ('<li><b>Check out.</b> An educator or manager taps Checked out or Redo, with notes. Every attempt is saved.</li>', '<li><b>Sign off.</b> A trainer or manager taps Checked out or Redo, with notes. Every attempt is saved.</li>'),
    ('<li><b>Graduate.</b> When every skill is checked out, they\'re ready for Level 1, and it can go on their next 1:1.</li>', '<li><b>Certify.</b> After the certification shift they\'re on the schedule on their own, and it can go on their next 1:1.</li>'),
    ('Every skill checked out. Talk about Level 1 at their next 1:1.', 'Every step signed off. Put them on the schedule and talk about it at their next 1:1.'),
    ('🎓 Ready for Level 1', '🎓 Certified'),
    ('Step by step on a model', 'Step by step on a real shift'),
]:
    rep(*r)

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
