"""Help button, owner's support-access switch, and the support-view banner (Loopd-In's index.html only)."""
import pathlib, sys

HTML_DLG = '''
  <dialog id="helpDlg" aria-labelledby="helpTitle">
    <form id="helpForm" method="dialog" class="plain" style="display:flex;flex-direction:column;gap:10px">
      <div class="row"><h2 class="h2" id="helpTitle">❓ Help</h2><button type="button" class="link" id="helpClose">Close</button></div>
      <p class="meta" style="margin:0">Tell us what went wrong or what you need. We'll reply right here and on your phone.</p>
      <label>What happened?<textarea id="help-msg" rows="4" maxlength="4000" required placeholder="e.g. I tapped Save on a daily note and nothing happened"></textarea></label>
      <label class="wi-btn" style="align-self:flex-start">📷 Add a screenshot <span class="meta">(optional)</span><input type="file" id="help-shot" accept="image/*"></label>
      <div id="help-picked" class="meta" hidden></div>
      <p class="meta" style="margin:0;font-size:.78rem">We'll include which screen you were on, your phone or computer type, and any error the app saw, so we can find the problem faster.</p>
      <div class="form-actions"><span class="form-err" id="help-err"></span><button type="submit" class="primary" id="help-send">Send</button></div>
      <div id="helpList" class="feed"></div>
    </form>
  </dialog>
'''

HTML_ACCESS = '''        <div id="supAccess" hidden style="display:flex;flex-direction:column;gap:8px;margin-top:6px">
          <h2 class="h2">🛟 Loopd-In support access</h2>
          <p class="meta" style="margin:0" id="sa-state"></p>
          <div class="actions" style="flex-wrap:wrap"><button type="button" class="ghost" data-sa="24">Allow for 24 hours</button><button type="button" class="ghost" data-sa="168">Allow for 7 days</button><button type="button" class="link del" data-sa="0" id="sa-off">Turn off now</button></div>
          <div id="sa-visits" class="meta"></div>
        </div>
'''

CSS = ('#helpDlg{border:0;border-radius:18px;padding:18px;width:min(560px,calc(100vw - 24px));max-height:calc(100vh - 40px);background:var(--surface);color:var(--ink);box-shadow:0 20px 60px rgba(22,33,62,.25)}'
       '#helpDlg::backdrop{background:rgba(22,33,62,.45)}'
       '.support-banner{background:#fff4d6;border:1.5px solid #e8b931;color:#5c4400;border-radius:12px;padding:10px 14px;margin:8px 0;display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;font-weight:600}\n')

JS = r'''
/* ---------- Help requests and Loopd-In support ---------- */
const recentErrs = [];
const pushErr = m => { if (!m) return; recentErrs.push(`${new Date().toLocaleTimeString()} ${String(m).slice(0, 200)}`); if (recentErrs.length > 8) recentErrs.shift(); };
addEventListener("error", e => pushErr(e.message));
addEventListener("unhandledrejection", e => pushErr(e.reason && (e.reason.message || e.reason)));
{ const f0 = friendly; friendly = err => { const m = f0(err); pushErr(err && (err.message || err)); return m; }; }
let helpShot = null, helpRows = [];
function helpContext() {
  return { screen: current, role: me && me.role, also_front_desk: !!(me && me.also_desk), plan: SALON && SALON.plan, salon: SALON && SALON.name,
    page: location.pathname + location.search, device: navigator.userAgent, size: innerWidth + "×" + innerHeight,
    home_screen_app: matchMedia("(display-mode: standalone)").matches || !!navigator.standalone, app_version: document.lastModified, errors: recentErrs.slice(-5) };
}
async function loadHelp() {
  const { data } = await sb.from("support_tickets").select("*").order("created_at", { ascending: false }).limit(20);
  helpRows = data || []; renderHelp();
}
function renderHelp() {
  const mine = helpRows;
  $("helpList").innerHTML = mine.length ? `<b style="margin-top:6px">${isMgr() ? "Help requests from your salon" : "Your requests"}</b>` + mine.map(t => `<div class="todo"><div class="body">
      <div class="row"><span class="meta">${esc(nameOf(t.created_by))} · ${esc(whenFull(t.created_at))}</span><span class="fu${t.status === "closed" ? " ok" : ""}">${t.status === "closed" ? "Solved" : t.reply ? "Answered" : "Sent"}</span></div>
      <p class="note">${esc(t.message)}</p>${t.reply ? `<div class="quoteline" style="white-space:normal">💬 <b>Loopd-In:</b> ${esc(t.reply)}</div>` : ""}</div></div>`).join("") : "";
}
$("helpBtn").onclick = () => { $("help-err").textContent = ""; $("helpDlg").showModal(); loadHelp(); };
$("helpClose").onclick = () => $("helpDlg").close();
$("help-shot").addEventListener("change", e => {
  const f = e.target.files[0]; e.target.value = ""; if (!f) return;
  if (f.size > 10 * 1024 * 1024) { $("help-err").textContent = "That picture is over 10 MB."; return; }
  helpShot = f; $("help-picked").hidden = false;
  $("help-picked").innerHTML = `📎 ${esc(f.name || "Screenshot")} <button type="button" class="link" id="help-unpick">Remove</button>`;
  $("help-unpick").onclick = () => { helpShot = null; $("help-picked").hidden = true; };
});
$("helpForm").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = $("help-msg").value.trim(); if (!msg) return;
  const btn = $("help-send"); btn.disabled = true; btn.textContent = "Sending…"; $("help-err").textContent = "";
  let screenshot = null;
  if (helpShot) {
    const ext = ((helpShot.type.split("/")[1] || "png").replace(/[^a-z0-9]/g, "") || "png").slice(0, 5);
    const path = `support/${Date.now()}-${(crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)).slice(0, 8)}.${ext}`;
    const up = await sb.storage.from().upload(path, helpShot, { contentType: helpShot.type || undefined });
    if (!up.error) screenshot = path;
  }
  const { error } = await sb.from("support_tickets").insert({ message: msg, context: helpContext(), screenshot });
  btn.disabled = false; btn.textContent = "Send";
  if (error) { $("help-err").textContent = friendly(error); return; }
  $("help-msg").value = ""; helpShot = null; $("help-picked").hidden = true;
  $("help-err").textContent = ""; $("foot").textContent = "Sent. We'll reply here and on your phone.";
  loadHelp();
});

/* the owner's switch, and the banner Loopd-In support sees inside a salon */
async function renderSupport() {
  const view = !!(SALON && SALON.support_view);
  $("supBanner").hidden = !view;
  if (view) $("supBanner").innerHTML = `<span>🛟 Support view: you're inside <b>${esc(SALON.name)}</b> as Loopd-In support · access ends ${esc(whenFull(SALON.support_until))}</span><button type="button" class="ghost" id="supLeave">Leave salon</button>`;
  if (view) $("supLeave").onclick = async () => { await sb.rpc("admin_exit"); location.href = "admin.html"; };
  $("helpBtn").hidden = view;
  const box = $("supAccess"); if (!box) return;
  box.hidden = !SALON || view || !isMgr();
  if (box.hidden) return;
  const until = SALON.support_until && new Date(SALON.support_until) > new Date() ? SALON.support_until : null;
  $("sa-state").innerHTML = until ? `<b style="color:var(--ok)">On</b> until ${esc(whenFull(until))}. Loopd-In support can open your salon as a manager to help you. Every visit is listed below.`
    : `<b>Off.</b> Turn it on when you've asked us for help and want us to look at your salon. It turns itself off when time's up.`;
  $("sa-off").hidden = !until;
  if (Date.now() - (renderSupport.at || 0) < 60e3 && renderSupport.rows) return;
  renderSupport.at = Date.now();
  const { data } = await sb.from("support_visits").select("*").order("started_at", { ascending: false }).limit(5);
  renderSupport.rows = data || [];
  $("sa-visits").innerHTML = (data || []).length ? "<b>Recent support visits</b><br>" + data.map(v => `${esc(whenFull(v.started_at))}${v.ended_at ? ` – ${esc(new Date(v.ended_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }))}` : " (in progress)"}`).join("<br>") : "";
}
$("supAccess").addEventListener("click", async e => {
  const b = e.target.closest("[data-sa]"); if (!b) return;
  b.disabled = true;
  const { error } = await sb.rpc("grant_support", { p_hours: Number(b.dataset.sa) });
  b.disabled = false;
  if (error) return alert(friendly(error));
  $("foot").textContent = Number(b.dataset.sa) ? "Support access is on." : "Support access is off.";
  renderSupport.at = 0; await loadSalon();
});
'''

def patch(s: str) -> str:
    if 'id="helpBtn"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    rep('      <button type="button" class="link" id="logout">Log out</button>',
        '      <button type="button" class="link" id="helpBtn">Help</button>\n      <button type="button" class="link" id="logout">Log out</button>')
    rep('  </header>\n', '  </header>\n  <div id="supBanner" class="support-banner" hidden></div>\n' + HTML_DLG)
    rep('''        <div id="planCards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px"></div>\n''',
        '''        <div id="planCards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px"></div>\n''' + HTML_ACCESS)
    s = s.replace('</style>', CSS + '</style>', 1)
    rep('''  } else logo.hidden = true;\n}''', '''  } else logo.hidden = true;\n  renderSupport();\n}''')
    rep('function renderAll() { renderPrint();', 'function renderAll() { renderSupport(); renderPrint();')
    rep('/* ---------- employee handbook ---------- */', JS + '\n/* ---------- employee handbook ---------- */')
    return s

if __name__ == '__main__':
    for p in sys.argv[1:]:
        p = pathlib.Path(p); p.write_text(patch(p.read_text())); print('patched', p)
