"""Walk-in / phone-call applicants on the Applicants tab (Salon Saia's and Loopd-In's index.html; the demo is built from Salon Saia's).
Replaces Loopd-In's older plain 'Add an applicant' box."""
import pathlib, re, sys

CARD = '''      <div class="quick" id="wiBox">
        <div class="row"><h2 class="h2">🚶 Walk-ins and calls</h2><button type="button" class="primary" id="wiToggle">+ Add someone</button></div>
        <p class="meta" style="margin:0">Someone stopped by or called about a job? Jot down their info so they land here with everyone else.</p>
        <form id="wiForm" hidden style="display:flex;flex-direction:column;gap:10px">
          <label>Name<input id="wi-name" required maxlength="100" autocomplete="off"></label>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
            <label>Phone<input id="wi-phone" type="tel" maxlength="40" autocomplete="off"></label>
            <label>Email <span class="meta">(optional)</span><input id="wi-email" type="email" maxlength="120" autocomplete="off"></label>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
            <label>Interested in<select id="wi-pos"><option>Stylist</option><option>Assistant</option><option>Front desk</option><option value="">Not sure yet</option></select></label>
            <label>How they reached us<select id="wi-src"><option value="walk-in">Walked in</option><option value="phone">Called</option><option value="referral">Referred by someone</option><option value="other">Other</option></select></label>
          </div>
          <label>Notes<textarea id="wi-notes" rows="3" maxlength="2000" placeholder="e.g. Licensed 4 years, free Tue–Sat, wants to bring clients, great energy"></textarea></label>
          <label>Paper application or résumé <span class="meta">(optional: snap a photo or attach a file)</span><input type="file" id="wi-file" accept="image/*,application/pdf,.doc,.docx"></label>
          <div class="form-actions"><span class="form-err" id="wi-err"></span><button type="button" class="ghost" id="wi-cancel">Cancel</button><button type="submit" class="primary" id="wi-save">Save applicant</button></div>
        </form>
      </div>
'''

JS = r'''
/* ---------- walk-ins and calls ---------- */
const WI_SRC = { "walk-in": ["🚶 Walk-in", "Walked in"], phone: ["📞 Called in", "Called us"], referral: ["🤝 Referral", "Referred to us"], other: ["✍️ Added by hand", "Added"] };
const wiSrc = a => (a.answers && a.answers.source) || (/^manual-/.test(a.submission_id || "") ? "other" : "");
const wiTag = a => { const s = WI_SRC[wiSrc(a)]; return s ? ` <span class="tag">${s[0]}</span>` : ""; };
const wiWhen = a => { const s = WI_SRC[wiSrc(a)]; return s ? s[1] : "Applied"; };
/* résumé photo link, for pages that don't already show one */
const wiUrls = {}, wiAsked = {};
function wiFileBtn(a) {
  const p = a.answers && a.answers.resume_file; if (!p || typeof aplResumeBtn === "function") return "";
  return wiUrls[p] ? `<a class="link" href="${esc(wiUrls[p])}" target="_blank" rel="noopener">📄 Application / résumé</a>` : `<span class="meta">📄 Loading file…</span>`;
}
async function wiSign() {
  if (typeof aplResumeBtn === "function") return;
  const need = (applicants || []).map(a => a.answers && a.answers.resume_file).filter(p => p && !wiUrls[p] && !wiAsked[p]);
  if (!need.length) return;
  need.forEach(p => wiAsked[p] = 1);
  const { data } = await sb.storage.from("photos").createSignedUrls(need, 60 * 60 * 6);
  (data || []).forEach(x => { if (x.signedUrl) wiUrls[x.path] = x.signedUrl; });
  renderApps();
}
$("wiToggle").onclick = () => { $("wiForm").hidden = false; $("wiToggle").hidden = true; $("wi-name").focus(); };
$("wi-cancel").onclick = () => { $("wiForm").reset(); $("wiForm").hidden = true; $("wiToggle").hidden = false; $("wi-err").textContent = ""; };
$("wiForm").addEventListener("submit", async e => {
  e.preventDefault();
  const err = t => $("wi-err").textContent = t; err("");
  const name = $("wi-name").value.trim(), phone = $("wi-phone").value.trim(), email = $("wi-email").value.trim().toLowerCase();
  if (!name) return err("Add their name.");
  if (!phone && !email) return err("Add a phone number or email so you can reach them.");
  const src = $("wi-src").value, btn = $("wi-save"); btn.disabled = true; btn.textContent = "Saving…";
  const answers = { source: src };
  const f = $("wi-file").files[0];
  if (f) {
    if (f.size > 10 * 1024 * 1024) { btn.disabled = false; btn.textContent = "Save applicant"; return err("That file is over 10 MB. A phone photo works fine."); }
    const ext = ((f.name.split(".").pop() || "jpg").toLowerCase().replace(/[^a-z0-9]/g, "") || "jpg").slice(0, 5);
    const path = `resumes/${Date.now()}-${(crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)).slice(0, 8)}.${ext}`;
    const up = await sb.storage.from("photos").upload(path, f, { contentType: f.type || undefined });
    if (up.error) { btn.disabled = false; btn.textContent = "Save applicant"; return err("The file didn't upload. Try a photo instead."); }
    answers.resume_file = path; answers.resume_name = f.name;
  }
  const now = new Date().toISOString();
  const row = { name, phone: phone || null, email: email || null, position: $("wi-pos").value || null, notes: $("wi-notes").value.trim() || null,
    status: "new", answers, submission_id: src + "-" + (crypto.randomUUID ? crypto.randomUUID() : Date.now()), submitted_at: now,
    log: [{ what: WI_SRC[src][1], note: "", by: me.email, at: now }] };
  const { error } = await sb.from("applicants").insert(row);
  btn.disabled = false; btn.textContent = "Save applicant";
  if (error) return err(friendly(error));
  $("wiForm").reset(); $("wiForm").hidden = true; $("wiToggle").hidden = false;
  $("foot").textContent = `${name} added to applicants.`; loadAll();
});
'''

def patch(s: str) -> str:
    if 'id="wiBox"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    # Loopd-In's older plain form goes away (the walk-in form covers it)
    m = re.search(r'      <div class="quick">\n        <div class="row"><h2 class="h2">Add an applicant</h2>.*?</form>\n      </div>\n', s, re.S)
    if m:
        s = s[:m.start()] + s[m.end():]
        m2 = re.search(r'\$\("apAddToggle"\)\.onclick = .*?\n\$\("apAddForm"\)\.addEventListener\("submit", async e => \{.*?\n\}\);\n', s, re.S)
        assert m2, 'old add handler'
        s = s[:m2.start()] + s[m2.end():]
    rep('      <div class="tabs" id="apFilter"', CARD + '      <div class="tabs" id="apFilter"')
    rep('${a.position ? ` <span class="tag">${esc(a.position)}</span>` : ""}</span>${apTag(a.status)}</div>',
        '${a.position ? ` <span class="tag">${esc(a.position)}</span>` : ""}${wiTag(a)}</span>${apTag(a.status)}</div>')
    rep('<div style="display:flex;gap:12px;flex-wrap:wrap">${contact}</div>\n    <div class="meta">Applied ${esc(whenFull(a.submitted_at))}</div>',
        '<div style="display:flex;gap:12px;flex-wrap:wrap">${contact}${wiFileBtn(a)}</div>\n    <div class="meta">${wiWhen(a)} ${esc(whenFull(a.submitted_at))}</div>')
    rep('function renderApps() {', 'function renderApps() {\n  setTimeout(wiSign, 0);')
    rep('/* ---------- employee handbook ---------- */', JS + '\n/* ---------- employee handbook ---------- */')
    return s

if __name__ == '__main__':
    for p in sys.argv[1:]:
        p = pathlib.Path(p); p.write_text(patch(p.read_text())); print('patched', p)
