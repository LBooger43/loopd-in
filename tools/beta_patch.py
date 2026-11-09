"""60-day beta: warning banners for owners, the locked banner for everyone, and 'Contact Loopd-In team to continue' (Loopd-In's index.html)."""
import pathlib, sys

HTML = '''  <div id="betaBanner" class="beta-banner" hidden></div>
  <dialog id="planDlg" aria-labelledby="planTitle">
    <div style="display:flex;flex-direction:column;gap:10px">
      <div class="row"><h2 class="h2" id="planTitle">Keep using Loopd-In</h2><button type="button" class="link" id="planClose">Close</button></div>
      <p style="margin:0"><b>Contact Loopd-In team to continue.</b></p>
      <p class="meta" style="margin:0">Card payments are coming soon. For now, send us a quick note and we'll keep your salon running. Plans are Front Desk $29, Team $59 and Owner $99 a month per location (<a class="link" href="pricing.html" target="_blank" rel="noopener">see plans</a>).</p>
      <div class="form-actions"><button type="button" class="primary" id="planContact">Send a note to the Loopd-In team</button></div>
    </div>
  </dialog>
'''
CSS = ('.beta-banner{border-radius:12px;padding:10px 14px;margin:8px 0;display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;font-weight:600;background:var(--accent-soft,#ecebfc);border:1.5px solid var(--accent);color:var(--ink)}'
       '.beta-banner.soon{background:#fff4d6;border-color:#e8b931;color:#5c4400}.beta-banner.ended{background:#fdecea;border-color:#c0392b;color:#7a1f16}'
       '#planDlg{border:0;border-radius:18px;padding:18px;width:min(480px,calc(100vw - 24px));background:var(--surface);color:var(--ink);box-shadow:0 20px 60px rgba(22,33,62,.25)}#planDlg::backdrop{background:rgba(22,33,62,.45)}'
       'body.locked section form{opacity:.45;pointer-events:none}\n')
JS = r'''
/* ---------- 60-day beta: warnings, lock, contact ---------- */
function renderBeta() {
  const ban = $("betaBanner"); if (!ban || !SALON) return;
  const paid = SALON.paid_until && new Date(SALON.paid_until) > new Date();
  const ends = SALON.beta_ends_at ? new Date(SALON.beta_ends_at) : null;
  const locked = SALON.active === false && !SALON.support_view;
  document.body.classList.toggle("locked", locked);
  const d = ends ? ends.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : "";
  const left = ends ? Math.ceil((ends - new Date()) / 864e5) : null;
  if ($("betaPlanNote")) $("betaPlanNote").textContent = paid ? "Thanks for being a Loopd-In customer." : ends ? (left > 0 ? `Your free beta ends ${d}. Switch any time to try another plan.` : `Your free beta ended ${d}.`) : "Free during the beta. Switch any time to try another plan.";
  ban.className = "beta-banner"; ban.hidden = true;
  if (paid || !ends || SALON.support_view) return;
  if (locked) {
    ban.hidden = false; ban.classList.add("ended");
    ban.innerHTML = isMgr() ? `<span>Your free beta ended ${esc(d)}. Your salon's information is safe, but new changes can't be saved.</span><button type="button" class="primary" data-beta="plan">Contact Loopd-In team</button>`
      : `<span>Your salon's Loopd-In beta has ended. You can still look things up. Talk to your manager about keeping it.</span>`;
    return;
  }
  if (left <= 14 && isMgr()) {
    ban.hidden = false; if (left <= 3) ban.classList.add("soon");
    ban.innerHTML = `<span>${left <= 1 ? "Your free beta ends tomorrow" : `Your free beta ends ${esc(d)} (${left} days left)`}. Choose a plan to keep going.</span><button type="button" class="ghost" data-beta="plan">Choose a plan</button>`;
  }
}
$("betaBanner").addEventListener("click", e => { if (e.target.closest("[data-beta=plan]")) $("planDlg").showModal(); });
$("planClose").onclick = () => $("planDlg").close();
$("planContact").onclick = () => {
  $("planDlg").close();
  $("help-msg").value = `We'd like to keep using Loopd-In after the free beta. Please contact us about continuing${SALON && SALON.plan ? ` (we're on the ${SALON.plan.replace("_", " ")} plan)` : ""}.`;
  $("helpBtn").click();
};
'''
FRIENDLY = ('  if (err && /SALON_LOCKED/.test(err.message || "")) return "Your salon\'s free beta has ended, so changes can\'t be saved. Contact the Loopd-In team to continue.";\n')

def patch(s: str) -> str:
    if 'id="betaBanner"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    rep('  <div id="supBanner" class="support-banner" hidden></div>\n', '  <div id="supBanner" class="support-banner" hidden></div>\n' + HTML)
    rep('<p class="meta" style="margin:0">Free during the beta. Switch any time to try another plan.</p>',
        '<p class="meta" style="margin:0" id="betaPlanNote">Free during the beta. Switch any time to try another plan.</p>')
    s = s.replace('</style>', CSS + '</style>', 1)
    rep('function friendly(err) {\n', 'function friendly(err) {\n' + FRIENDLY)
    rep('function renderAll() { renderSupport();', 'function renderAll() { renderBeta(); renderSupport();')
    rep('''  } else logo.hidden = true;\n  renderSupport();\n}''', '''  } else logo.hidden = true;\n  renderSupport(); renderBeta();\n}''')
    rep('/* ---------- employee handbook ---------- */', JS + '\n/* ---------- employee handbook ---------- */')
    return s

if __name__ == '__main__':
    for p in sys.argv[1:]:
        p = pathlib.Path(p); p.write_text(patch(p.read_text())); print('patched', p)
