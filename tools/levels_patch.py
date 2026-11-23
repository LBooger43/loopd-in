"""Levels preview (coming soon): a managers-only tab showing a sample level scale and how to move stylists between levels.
Sample data only; nothing is saved."""
import pathlib, sys

TAB = '      <button role="tab" id="tab-levels" class="priv" aria-selected="false" hidden>Levels <span class="soon-pill">Soon</span></button>\n'

SECTION = '''    <section id="view-levels" hidden style="display:flex;flex-direction:column;gap:16px">
      <div class="lv-soon"><b>✨ Levels is coming soon.</b> This is a preview with sample stylists, so try anything: nothing here is saved or seen by your team.</div>
      <div class="quick">
        <div class="row"><h2 class="h2">📈 Your level scale</h2><span class="tag">Sample</span></div>
        <p class="meta" style="margin:0">Set your own levels: what each one pays, what it charges, and the numbers a stylist needs to reach it. These are example numbers.</p>
        <div class="lv-scroll"><table class="lv-table" id="lvScale"></table></div>
        <p class="meta" style="margin:0">If a stylist stays under their level's numbers for 60 days in a row, they move back one level. You choose the rule.</p>
      </div>
      <div class="quick">
        <div class="row"><h2 class="h2">👥 Your team's levels</h2><span class="tag">Sample</span></div>
        <p class="meta" style="margin:0">Each stylist's numbers for the last 60 days, compared with the next level up. Tap <b>Move up</b> or <b>Move down</b> to try it.</p>
        <div id="lvTeam" style="display:flex;flex-direction:column;gap:10px"></div>
        <button type="button" class="link" id="lvReset" style="align-self:flex-start">Reset the sample</button>
      </div>
      <div class="quick">
        <h2 class="h2">👀 What a stylist will see</h2>
        <p class="meta" style="margin:0">Each stylist sees only their own level and how close they are to the next one. No one sees anyone else's numbers.</p>
        <div id="lvMine"></div>
      </div>
      <div class="quick">
        <h2 class="h2">How it will work</h2>
        <ol class="lv-steps">
          <li><b>Set your levels.</b> Name each level and set its commission, service prices and target numbers.</li>
          <li><b>Add the numbers.</b> Type in each stylist's monthly numbers, or bring them in from your booking software later.</li>
          <li><b>See who's ready.</b> Loopd-In flags who has hit the next level and who has been under target for 60 days.</li>
          <li><b>Move people up or down.</b> One tap, with the date and who approved it saved to their file. It can also go on their 1:1 agenda.</li>
        </ol>
        <div class="form-actions" style="justify-content:flex-start"><button type="button" class="primary" id="lvWant">I want this for my salon</button></div>
      </div>
    </section>
'''

CSS = ('.soon-pill{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;background:var(--accent);color:#fff;border-radius:99px;padding:1px 6px;margin-left:4px;vertical-align:2px}'
       '.lv-soon{background:var(--accent-soft);border:1.5px dashed var(--accent);color:var(--ink);border-radius:12px;padding:10px 14px;font-size:.9rem}'
       '.lv-scroll{overflow-x:auto;margin:0 -4px}.lv-table{border-collapse:collapse;width:100%;min-width:520px;font-size:.85rem}'
       '.lv-table th,.lv-table td{padding:8px 6px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}.lv-table th{color:var(--muted);font-weight:600;font-size:.75rem}'
       '.lv-badge{display:inline-block;font-weight:700;font-size:.75rem;border-radius:99px;padding:2px 9px;color:#fff}'
       '.lv-card{border:1px solid var(--line);border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:8px;background:var(--surface)}'
       '.lv-bars{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 14px}'
       '.lv-bar{display:flex;flex-direction:column;gap:3px;font-size:.78rem}.lv-bar .track{height:7px;border-radius:99px;background:var(--line);overflow:hidden}.lv-bar .fill{height:100%;border-radius:99px}'
       '.lv-steps{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:6px;font-size:.9rem}'
       '.lv-flag{font-size:.75rem;font-weight:700;border-radius:99px;padding:2px 9px}\n')

JS = r'''
/* ---------- Levels preview (coming soon, sample data only) ---------- */
const LV_LEVELS = [
  { n: 1, name: "New Talent", color: "#7a86a6", pay: 38, cut: 45, color$: 85, req: 2, ret: 40, pre: 30, add: 5, retail: 8 },
  { n: 2, name: "Stylist", color: "#2f6be0", pay: 40, cut: 55, color$: 95, req: 4, ret: 50, pre: 40, add: 10, retail: 10 },
  { n: 3, name: "Senior Stylist", color: "#5a56d6", pay: 42, cut: 65, color$: 110, req: 6, ret: 60, pre: 50, add: 15, retail: 12 },
  { n: 4, name: "Master Stylist", color: "#8247b8", pay: 45, cut: 75, color$: 125, req: 8, ret: 70, pre: 60, add: 20, retail: 14 },
  { n: 5, name: "Artistic Director", color: "#b8478a", pay: 48, cut: 90, color$: 140, req: 10, ret: 75, pre: 70, add: 25, retail: 16 },
];
const LV_METRICS = [["req", "New requests / mo", ""], ["ret", "Retention", "%"], ["pre", "Pre-book", "%"], ["add", "Add-ons", "%"], ["retail", "Retail", "%"]];
const LV_SAMPLE = () => [
  { id: "a", name: "Ava M.", level: 2, since: 210, nums: { req: 7, ret: 64, pre: 55, add: 17, retail: 13 } },
  { id: "b", name: "Jordan K.", level: 3, since: 400, nums: { req: 6, ret: 61, pre: 46, add: 15, retail: 12 }, under: 21 },
  { id: "c", name: "Mia R.", level: 1, since: 95, nums: { req: 3, ret: 46, pre: 33, add: 8, retail: 9 } },
  { id: "d", name: "Chris T.", level: 4, since: 520, nums: { req: 6, ret: 62, pre: 52, add: 14, retail: 11 }, under: 48 },
];
let lvTeam = LV_SAMPLE(), lvAsk = null, lvDone = {};
const lvL = n => LV_LEVELS[n - 1];
const lvBadge = n => `<span class="lv-badge" style="background:${lvL(n).color}">Level ${n} · ${esc(lvL(n).name)}</span>`;
const lvHits = (p, n) => LV_METRICS.every(([k]) => p.nums[k] >= lvL(n)[k]);
function lvBars(p, target) {
  return `<div class="lv-bars">${LV_METRICS.map(([k, label, u]) => {
    const goal = lvL(target)[k], v = p.nums[k], pct = Math.min(100, Math.round(v / goal * 100)), ok = v >= goal;
    return `<div class="lv-bar"><span class="row" style="gap:6px"><span>${label}</span><b style="color:${ok ? "var(--ok)" : "var(--ink)"}">${v}${u} <span class="meta">/ ${goal}${u}</span></b></span><div class="track"><div class="fill" style="width:${pct}%;background:${ok ? "var(--ok)" : "var(--accent)"}"></div></div></div>`;
  }).join("")}</div>`;
}
function renderLevels() {
  if (!$("lvScale")) return;
  $("lvScale").innerHTML = `<tr><th>Level</th><th>Commission</th><th>Haircut</th><th>Color</th>${LV_METRICS.map(([, l]) => `<th>${l}</th>`).join("")}</tr>` +
    LV_LEVELS.map(l => `<tr><td>${lvBadge(l.n)}</td><td><b>${l.pay}%</b></td><td>$${l.cut}</td><td>$${l.color$}</td>${LV_METRICS.map(([k, , u]) => `<td>${l[k]}${u}</td>`).join("")}</tr>`).join("");
  $("lvTeam").innerHTML = lvTeam.map(p => {
    const top = p.level === LV_LEVELS.length, next = top ? p.level : p.level + 1;
    const ready = !top && lvHits(p, next), below = !lvHits(p, p.level);
    const flag = ready ? `<span class="lv-flag" style="background:#e3f4ea;color:var(--ok)">✓ Ready to move up</span>`
      : below ? `<span class="lv-flag" style="background:#fdf0dc;color:var(--warn)">Under target ${p.under || 0} of 60 days</span>`
      : `<span class="lv-flag" style="background:var(--accent-soft);color:var(--accent)">On track</span>`;
    const ask = lvAsk && lvAsk.id === p.id ? (() => {
      const to = lvL(lvAsk.to), from = lvL(p.level);
      return `<div class="lv-soon" style="display:flex;flex-direction:column;gap:8px"><span>Move <b>${esc(p.name)}</b> from Level ${from.n} to <b>Level ${to.n} · ${esc(to.name)}</b>?<br><span class="meta">Commission ${from.pay}% → ${to.pay}% · Haircut $${from.cut} → $${to.cut} · Color $${from.color$} → $${to.color$}</span></span>
        <div class="actions"><button type="button" class="primary" data-lv="yes" data-id="${p.id}">Yes, move ${lvAsk.to > p.level ? "up" : "down"}</button><button type="button" class="ghost" data-lv="no">Cancel</button></div></div>`;
    })() : "";
    return `<div class="lv-card"><div class="row" style="flex-wrap:wrap;gap:8px"><b>${esc(p.name)}</b>${lvBadge(p.level)}${flag}</div>
      <span class="meta">${top ? "At the top level. Numbers compared with this level." : `Numbers compared with Level ${next} · ${esc(lvL(next).name)}`} · ${p.since < 30 ? "new to this level" : `on this level ${Math.round(p.since / 30)} months`}</span>
      ${lvBars(p, next)}
      ${lvDone[p.id] ? `<span class="meta" style="color:var(--ok)">✓ ${esc(lvDone[p.id])} <i>(preview, not saved)</i></span>` : ""}
      ${ask || `<div class="actions">${!top ? `<button type="button" class="${ready ? "primary" : "ghost"}" data-lv="ask" data-id="${p.id}" data-to="${p.level + 1}">Move up to Level ${p.level + 1}</button>` : ""}${p.level > 1 ? `<button type="button" class="link" data-lv="ask" data-id="${p.id}" data-to="${p.level - 1}">Move down</button>` : ""}</div>`}</div>`;
  }).join("");
  const me = lvTeam[0], nx = Math.min(me.level + 1, LV_LEVELS.length), have = LV_METRICS.filter(([k]) => me.nums[k] >= lvL(nx)[k]).length;
  $("lvMine").innerHTML = `<div class="lv-card" style="max-width:420px"><div class="row"><b>Hi ${esc(me.name.split(" ")[0])}!</b>${lvBadge(me.level)}</div>
    <span>${have === LV_METRICS.length ? `You've hit every target for <b>Level ${nx}</b>. Talk to your manager about moving up! 🎉` : `You've hit <b>${have} of ${LV_METRICS.length}</b> targets for Level ${nx} · ${esc(lvL(nx).name)}. Keep going!`}</span>${lvBars(me, nx)}</div>`;
}
$("view-levels").addEventListener("click", e => {
  const b = e.target.closest("[data-lv]"); if (!b) return;
  const p = lvTeam.find(x => x.id === b.dataset.id);
  if (b.dataset.lv === "ask") lvAsk = { id: p.id, to: +b.dataset.to };
  if (b.dataset.lv === "no") lvAsk = null;
  if (b.dataset.lv === "yes") {
    const up = lvAsk.to > p.level; p.level = lvAsk.to; p.since = 0; p.under = 0; lvAsk = null;
    lvDone[p.id] = `Moved ${up ? "up" : "down"} to Level ${p.level} today by ${me && me.name ? me.name : "you"}`;
    $("foot").textContent = "Preview only: in the real Levels, this would be saved to their file.";
  }
  renderLevels();
});
$("lvReset").onclick = () => { lvTeam = LV_SAMPLE(); lvAsk = null; lvDone = {}; renderLevels(); };
$("lvWant").onclick = () => { $("help-msg").value = "We'd like Levels for our salon when it's ready! Our level system works like this: "; $("helpBtn").click(); };
'''

def patch(s: str) -> str:
    if 'id="view-levels"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    rep('      <button role="tab" id="tab-staff" class="priv"', TAB + '      <button role="tab" id="tab-staff" class="priv"')
    rep('    <section id="view-apps" hidden', SECTION + '    <section id="view-apps" hidden')
    rep('const TABS = ["daily", "log", "supplies", "cash", "chat", "time", "oo", "apps", "staff", "team"];',
        'const TABS = ["daily", "log", "supplies", "cash", "chat", "time", "oo", "apps", "levels", "staff", "team"];')
    rep('if ((t === "staff" || t === "team" || t === "apps") && !isMgr()) t = "daily";',
        'if ((t === "staff" || t === "team" || t === "apps" || t === "levels") && !isMgr()) t = "daily";')
    rep('$("tab-time").hidden = !tabAllowed("time"); $("tab-oo").hidden = !tabAllowed("oo");\n',
        '$("tab-time").hidden = !tabAllowed("time"); $("tab-oo").hidden = !tabAllowed("oo"); $("tab-levels").hidden = !isMgr(); renderLevels();\n')
    s = s.replace('</style>', CSS + '</style>', 1)
    rep('/* ---------- employee handbook ---------- */', JS + '\n/* ---------- employee handbook ---------- */')
    return s

if __name__ == '__main__':
    for p in map(pathlib.Path, sys.argv[1:]):
        p.write_text(patch(p.read_text())); print('patched', p)
