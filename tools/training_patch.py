"""Training preview (coming soon): managers-only tab with a sample associate training path, check-offs, a quiz and progress.
Sample data only; nothing is saved.  Modes: beta (Loopd-In app), demo, saia (button hidden; the demo build un-hides it)."""
import pathlib, sys

TAB = '      <button role="tab" id="tab-training" class="priv" aria-selected="false" hidden>Training <span class="soon-pill">Soon</span></button>\n'

SECTION = '''    <section id="view-training" hidden style="display:flex;flex-direction:column;gap:16px">
      <div class="lv-soon"><b>✨ Training is coming soon.</b> This is a preview with sample associates, so try anything: nothing here is saved or seen by your team.</div>
      <div class="quick">
        <div class="row"><h2 class="h2">✅ Waiting for check-off</h2><span class="tag">Sample</span></div>
        <p class="meta" style="margin:0">Associates upload photos of their model work. An educator or manager checks it out or asks for a redo.</p>
        <div id="trReview" style="display:flex;flex-direction:column;gap:10px"></div>
      </div>
      <div class="quick">
        <div class="row"><h2 class="h2">👩‍🎓 Your associates</h2><span class="tag">Sample</span></div>
        <div id="trPeople" style="display:flex;flex-direction:column;gap:10px"></div>
        <button type="button" class="link" id="trReset" style="align-self:flex-start">Reset the sample</button>
      </div>
      <div class="quick">
        <div class="row"><h2 class="h2">📚 Your training path</h2><span class="tag">Sample</span></div>
        <p class="meta" style="margin:0">Build your own path: the skills in order, your own videos, a short quiz and how many models each skill needs. Finishing the path moves an associate to Level 1.</p>
        <div id="trPath" style="display:flex;flex-direction:column;gap:6px"></div>
      </div>
      <div class="quick">
        <div class="row"><h2 class="h2">📝 Try a sample quiz</h2><span class="tag">Sample</span></div>
        <div id="trQuiz" style="display:flex;flex-direction:column;gap:12px"></div>
      </div>
      <div class="quick">
        <h2 class="h2">👀 What an associate will see</h2>
        <p class="meta" style="margin:0">Each associate sees their own path, their next videos and what's waiting for check-off.</p>
        <div id="trMine"></div>
      </div>
      <div class="quick">
        <h2 class="h2">How it will work</h2>
        <ol class="lv-steps">
          <li><b>Build your path.</b> List your skills in order and link your own training videos (YouTube or Vimeo).</li>
          <li><b>Watch and test.</b> Associates watch the videos and pass a short quiz for each skill.</li>
          <li><b>Model and upload.</b> They do the service on a model and upload before and after photos from their phone.</li>
          <li><b>Check out.</b> An educator or manager taps Checked out or Redo, with notes. Every attempt is saved.</li>
          <li><b>Graduate.</b> When every skill is checked out, they're ready for Level 1, and it can go on their next 1:1.</li>
        </ol>
        <div class="form-actions" style="justify-content:flex-start"><button type="button" class="primary" id="trWant">I want this for my salon</button></div>
      </div>
    </section>
'''

CSS = ('.tr-skill{display:flex;gap:10px;align-items:center;border:1px solid var(--line);border-radius:10px;padding:8px 10px;font-size:.88rem;background:var(--surface)}'
       '.tr-num{flex:none;width:26px;height:26px;border-radius:99px;background:var(--accent-soft);color:var(--accent);font-weight:700;display:grid;place-items:center;font-size:.8rem}'
       '.tr-pics{display:grid;grid-template-columns:1fr 1fr;gap:8px;max-width:300px}.tr-pic{aspect-ratio:4/5;border-radius:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;color:#fff;font-weight:700;font-size:.8rem;text-shadow:0 1px 2px rgba(0,0,0,.3)}'
       '.tr-pic span{font-size:2rem}.tr-vid{display:flex;gap:10px;align-items:center;border:1px solid var(--line);border-radius:10px;padding:8px;font-size:.85rem}'
       '.tr-play{flex:none;width:64px;height:40px;border-radius:8px;background:linear-gradient(135deg,#16213e,#5a56d6);color:#fff;display:grid;place-items:center;font-size:1rem}'
       '.tr-opt{text-align:left;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:10px;padding:9px 12px;font-size:.88rem}'
       '.tr-opt.right{border-color:var(--ok);background:#e3f4ea}.tr-opt.wrong{border-color:var(--crit);background:#fbe9e6}\n')

JS = r'''
/* ---------- Training preview (coming soon, sample data only) ---------- */
const TR_PATH = [
  { name: "Shampoo, condition and blow-dry", vids: 2, models: 3 },
  { name: "Sectioning and tension", vids: 2, models: 2 },
  { name: "One-length cut (0° elevation)", vids: 3, models: 3 },
  { name: "Long layers (90° and 180°)", vids: 3, models: 3 },
  { name: "Graduated bob (45°)", vids: 2, models: 3 },
  { name: "Men's clipper cut and fade", vids: 3, models: 4 },
  { name: "Single-process color and toning", vids: 3, models: 3 },
  { name: "Foils and partial highlights", vids: 3, models: 3 },
  { name: "Styling: curls, waves and updos", vids: 2, models: 2 },
  { name: "Consultation and retail recommendation", vids: 1, models: 2 },
];
const TR_SAMPLE = () => ({
  people: [
    { id: "p1", name: "Sofia L.", done: 5, started: "Aug 2026", note: "On track to graduate in February." },
    { id: "p2", name: "Marcus D.", done: 3, started: "Sep 2026", note: "Quiz passed for Long layers. Needs models." },
    { id: "p3", name: "Kayla P.", done: 9, started: "Apr 2026", note: "One skill left before Level 1!" },
  ],
  review: [
    { id: "r1", who: "p1", skill: 6, model: 2, when: "Today, 10:40 AM", from: ["#8a6a52", "#c9a27c"], to: ["#2b2b33", "#6b6b78"], tip: "Fade blended to a 1 guard, line-up done with trimmers." },
    { id: "r2", who: "p2", skill: 4, model: 1, when: "Yesterday", from: ["#7a5236", "#b98a5f"], to: ["#b07b45", "#e3bd86"], tip: "Long layers at 90°. Asked the guest about face-framing." },
  ],
});
let tr = TR_SAMPLE(), trAsk = null, trQ = {};
const trName = id => (tr.people.find(p => p.id === id) || {}).name || "";
const trPct = p => Math.round(p.done / TR_PATH.length * 100);
const trPic = (c, label, icon) => `<div class="tr-pic" style="background:linear-gradient(160deg,${c[0]},${c[1]})"><span>${icon}</span>${label}</div>`;
const TR_QUIZ = [
  { q: "In haircutting, what does “elevation” mean?", a: ["How short the hair is cut", "The angle the hair is held away from the head while cutting", "Where the guest's chair is set", "How much the hair is thinned"], right: 1 },
  { q: "Cutting hair held at 0° elevation (straight down) creates…", a: ["A one-length (solid) shape", "Uniform layers", "A shag", "A fade"], right: 0 },
  { q: "Before a color service on a new guest, what should you check first?", a: ["Their favorite color", "Whether they had an allergy or skin test as the color's instructions say", "How long since their last haircut", "Their tip amount"], right: 1 },
];
function renderTraining() {
  if (!$("trPath")) return;
  $("trPath").innerHTML = TR_PATH.map((s, i) => `<div class="tr-skill"><span class="tr-num">${i + 1}</span><span style="flex:1;display:flex;flex-direction:column">${esc(s.name)}<span class="meta">🎬 ${s.vids} video${s.vids > 1 ? "s" : ""} · 📝 quiz · ✂️ ${s.models} models</span></span></div>`).join("");
  $("trReview").innerHTML = tr.review.length ? tr.review.map(r => {
    const s = TR_PATH[r.skill - 1], ask = trAsk && trAsk.id === r.id;
    return `<div class="lv-card"><div class="row" style="flex-wrap:wrap;gap:6px"><b>${esc(trName(r.who))}</b><span class="meta">${esc(r.when)}</span></div>
      <span><b>${esc(s.name)}</b> · model ${r.model} of ${s.models}</span>
      <div class="tr-pics">${trPic(r.from, "Before", "💇")}${trPic(r.to, "After", "✨")}</div>
      <span class="meta">“${esc(r.tip)}”</span>
      ${ask ? `<div class="lv-soon" style="display:flex;flex-direction:column;gap:8px"><label style="margin:0">What should they work on?<textarea id="trNote" rows="2" placeholder="e.g. Check your guide at the crown, it's uneven"></textarea></label><div class="actions"><button type="button" class="primary" data-tr="redo-yes" data-id="${r.id}">Send back for a redo</button><button type="button" class="ghost" data-tr="no">Cancel</button></div></div>`
        : `<div class="actions"><button type="button" class="primary" data-tr="ok" data-id="${r.id}">✓ Checked out</button><button type="button" class="ghost" data-tr="redo" data-id="${r.id}">Redo</button></div>`}</div>`;
  }).join("") : `<div class="meta">All caught up. Nothing waiting for check-off. <i>(preview)</i></div>`;
  $("trPeople").innerHTML = tr.people.map(p => {
    const grad = p.done >= TR_PATH.length, next = TR_PATH[Math.min(p.done, TR_PATH.length - 1)];
    return `<div class="lv-card"><div class="row" style="flex-wrap:wrap;gap:8px"><b>${esc(p.name)}</b>${grad ? `<span class="lv-flag" style="background:#e3f4ea;color:var(--ok)">🎓 Ready for Level 1</span>` : `<span class="lv-badge" style="background:#7a86a6">Associate</span>`}</div>
      <div class="lv-bar"><span class="row"><span>${p.done} of ${TR_PATH.length} skills checked out</span><b>${trPct(p)}%</b></span><div class="track"><div class="fill" style="width:${trPct(p)}%;background:${grad ? "var(--ok)" : "var(--accent)"}"></div></div></div>
      <span class="meta">${grad ? "Every skill checked out. Talk about Level 1 at their next 1:1." : `Working on: <b>${esc(next.name)}</b>`} · started ${esc(p.started)}</span>
      ${p.flash ? `<span class="meta" style="color:var(--ok)">✓ ${esc(p.flash)} <i>(preview, not saved)</i></span>` : `<span class="meta">${esc(p.note)}</span>`}</div>`;
  }).join("");
  $("trQuiz").innerHTML = TR_QUIZ.map((x, i) => `<div style="display:flex;flex-direction:column;gap:6px"><b style="font-size:.92rem">${i + 1}. ${esc(x.q)}</b>${x.a.map((t, j) => {
      const picked = trQ[i] === j, cls = trQ[i] === undefined ? "" : j === x.right ? " right" : picked ? " wrong" : "";
      return `<button type="button" class="tr-opt${cls}" data-tr="q" data-i="${i}" data-j="${j}"${trQ[i] !== undefined ? " disabled" : ""}>${esc(t)}</button>`;
    }).join("")}</div>`).join("") + (Object.keys(trQ).length === TR_QUIZ.length ? (() => {
      const score = TR_QUIZ.filter((x, i) => trQ[i] === x.right).length, pass = score / TR_QUIZ.length >= 0.66;
      return `<div class="lv-soon"><b>${score} of ${TR_QUIZ.length} right. ${pass ? "Passed! 🎉" : "Not yet. Rewatch the videos and try again."}</b> <button type="button" class="link" data-tr="retake">Take it again</button></div>`;
    })() : "");
  const me = tr.people[0], nx = TR_PATH[Math.min(me.done, TR_PATH.length - 1)];
  $("trMine").innerHTML = `<div class="lv-card" style="max-width:440px"><div class="row"><b>Hi ${esc(me.name.split(" ")[0])}!</b><span class="lv-badge" style="background:#7a86a6">Associate</span></div>
    <div class="lv-bar"><span class="row"><span>${me.done} of ${TR_PATH.length} skills done</span><b>${trPct(me)}%</b></span><div class="track"><div class="fill" style="width:${trPct(me)}%;background:var(--accent)"></div></div></div>
    <span>Up next: <b>${esc(nx.name)}</b></span>
    <div class="tr-vid"><span class="tr-play">▶</span><span>${esc(nx.name)}: the basics<br><span class="meta">Video 1 of ${nx.vids} · 8 min</span></span></div>
    <div class="tr-vid"><span class="tr-play">▶</span><span>Step by step on a model<br><span class="meta">Video 2 of ${nx.vids} · 14 min</span></span></div>
    <div class="actions"><span class="meta">📝 Quiz · ✂️ 0 of ${nx.models} models uploaded</span></div></div>`;
}
$("view-training").addEventListener("click", e => {
  const b = e.target.closest("[data-tr]"); if (!b) return;
  const act = b.dataset.tr, r = tr.review.find(x => x.id === b.dataset.id);
  if (act === "q") trQ[+b.dataset.i] = +b.dataset.j;
  if (act === "retake") trQ = {};
  if (act === "redo") trAsk = { id: r.id };
  if (act === "no") trAsk = null;
  if (act === "ok" || act === "redo-yes") {
    const p = tr.people.find(x => x.id === r.who), s = TR_PATH[r.skill - 1];
    if (act === "ok") { if (r.model >= s.models - 1) p.done = Math.max(p.done, r.skill); p.flash = `${s.name}: model ${r.model} checked out today`; }
    else p.flash = `${s.name}: sent back for a redo${($("trNote") || {}).value ? ` (“${$("trNote").value.trim().slice(0, 80)}”)` : ""}`;
    tr.review = tr.review.filter(x => x !== r); trAsk = null;
    $("foot").textContent = "Preview only: in the real Training, this would be saved and the associate would get an alert.";
  }
  renderTraining();
});
$("trReset").onclick = () => { tr = TR_SAMPLE(); trAsk = null; trQ = {}; renderTraining(); };
'''
WANT_BETA = '''$("trWant").onclick = () => { $("help-msg").value = "We'd like Training for our salon when it's ready! How we train associates now: "; $("helpBtn").click(); };\n'''
WANT_DEMO = '''$("trWant").onclick = () => { $("foot").textContent = "Training is coming soon. Ask the Loopd-In team to save you a spot!"; $("foot").scrollIntoView({ behavior: "smooth" }); };\n'''

def patch(s: str, mode: str) -> str:
    if 'id="view-training"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    rep('      <button role="tab" id="tab-staff" class="priv"', TAB + '      <button role="tab" id="tab-staff" class="priv"')
    sec = SECTION if mode != 'saia' else SECTION.replace('id="trWant">', 'id="trWant" hidden>')
    rep('    <section id="view-apps" hidden', sec + '    <section id="view-apps" hidden')
    rep('"apps", "levels", "staff", "team"];', '"apps", "levels", "training", "staff", "team"];')
    rep('t === "apps" || t === "levels") && !isMgr()) t = "daily";', 't === "apps" || t === "levels" || t === "training") && !isMgr()) t = "daily";')
    rep('$("tab-levels").hidden = !isMgr(); renderLevels();', '$("tab-levels").hidden = !isMgr(); renderLevels(); $("tab-training").hidden = !isMgr(); renderTraining();')
    s = s.replace('</style>', CSS + '</style>', 1)
    rep('/* ---------- employee handbook ---------- */', JS + (WANT_BETA if mode == 'beta' else WANT_DEMO) + '\n/* ---------- employee handbook ---------- */')
    return s

if __name__ == '__main__':
    mode = sys.argv[1]
    for p in map(pathlib.Path, sys.argv[2:]):
        p.write_text(patch(p.read_text(), mode)); print('patched', mode, p)
