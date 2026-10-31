"""One-time fork: turn the Salon Saia app into Loopd-In, the multi-salon app with three plans.
Reads ../salon-saia-front-desk/index.html, writes ./index.html. After this, Loopd-In is edited directly."""
import re, shutil, pathlib
SRC = pathlib.Path('/home/claude/salon-saia-front-desk')
DST = pathlib.Path('/home/claude/loopd-in')
s = (SRC / 'index.html').read_text()

def rep(a, b, count=1):
    global s
    n = s.count(a)
    assert n == count, f'{n}x: {a[:90]!r}'
    s = s.replace(a, b)

# ---------- branding ----------
rep('<title>Loopd-In · Salon Saia</title>', '<title>Loopd-In</title>')
rep('<div class="eyebrow">Salon Saia · Cary</div>', '<div class="eyebrow" id="salonLine">Loopd-In</div>')
rep('<h1 class="brand"', '<img id="salonLogo" alt="" hidden style="height:44px;max-width:120px;object-fit:contain;margin-bottom:4px;display:block">\n      <h1 class="brand"')

# ---------- data layer: every table is the salon's own lp_ table; files live in the salon's folder ----------
rep('const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);', '''const sbRaw = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
let SALON = null;   // { id, name, city, plan, settings, logo }
const salonPath = p => SALON.id + "/" + String(p).replace(/^\\/+/, "");
const salonFiles = () => sbRaw.storage.from("lp-files");
const sb = {
  from: t => sbRaw.from("lp_" + t),
  rpc: (name, args) => sbRaw.rpc("lp_" + name, args),
  auth: sbRaw.auth,
  channel: (...a) => sbRaw.channel(...a),
  storage: { from: () => ({
    upload: (p, f, o) => salonFiles().upload(salonPath(p), f, o),
    createSignedUrl: (p, e) => salonFiles().createSignedUrl(salonPath(p), e),
    createSignedUrls: async (ps, e) => {
      const r = await salonFiles().createSignedUrls(ps.map(salonPath), e);
      if (r.data) r.data = r.data.map((x, i) => ({ ...x, path: ps[i] }));
      return r;
    },
    list: (folder, o) => salonFiles().list(salonPath(folder), o),
    remove: ps => salonFiles().remove(ps.map(salonPath)),
  }) },
};''')

# ---------- sign in / start a salon ----------
rep('''    <p class="meta">Forgot your password? Ask a manager to reset it.</p>
  </section>''', '''    <p class="meta">Forgot your password? Ask a manager to reset it.</p>
    <div style="border-top:1px solid var(--line);margin-top:14px;padding-top:14px;display:flex;flex-direction:column;gap:6px">
      <b>New to Loopd-In?</b>
      <p class="meta" style="margin:0">Salon owners: start your salon with your beta invite code. Team members: ask your manager to add you, then use “Create your password” above.</p>
      <div class="actions"><button type="button" class="primary" id="startOpen">Start a salon</button><a class="link" href="demo/">Try the demo</a></div>
    </div>
  </section>

  <!-- START A SALON -->
  <section id="view-start" class="quick" hidden>
    <h2 class="h2">Start your salon</h2>
    <p class="meta" style="margin:0" id="startHelp">Set up your salon in a minute. You'll be its manager, and you can add your team right after.</p>
    <form id="startForm" class="plain">
      <label>Invite code<input id="st-code" required autocomplete="off" placeholder="e.g. BETA-TEAM" style="text-transform:uppercase"></label>
      <span class="meta" id="st-plan"></span>
      <label>Salon name<input id="st-salon" required maxlength="80" placeholder="e.g. Bella Hair Studio"></label>
      <label>City<input id="st-city" maxlength="60" placeholder="e.g. Raleigh, NC"></label>
      <label>Your name<input id="st-name" required maxlength="80" placeholder="e.g. Jordan Lee"></label>
      <div id="st-acct" style="display:flex;flex-direction:column;gap:8px">
        <label>Your email<input id="st-email" type="email" autocomplete="email" placeholder="you@example.com"></label>
        <label>Create a password<input id="st-pw" type="password" minlength="6" autocomplete="new-password" placeholder="At least 6 characters"></label>
      </div>
      <div class="form-actions"><span class="form-err" id="st-err"></span><button type="button" class="ghost" id="st-cancel">Back</button><button type="submit" class="primary" id="st-btn">Create my salon</button></div>
    </form>
  </section>''')
rep('''<div id="view-noaccess" class="empty" hidden style="padding:40px 20px"><b>🔒 Access not granted</b><span id="noaccessMsg"></span><br><br><button type="button" class="ghost" id="logout2">Log out</button></div>''',
    '''<div id="view-noaccess" class="empty" hidden style="padding:40px 20px"><b>You're signed in, but not on a salon team yet</b><span id="noaccessMsg"></span><br><br><div class="actions" style="justify-content:center"><button type="button" class="primary" id="startOpen2">Start a salon</button><button type="button" class="ghost" id="logout2">Log out</button></div></div>''')
rep('''    if (!ok) return err("That email isn't on the Salon Saia team yet. Ask a manager to add you.");''',
    '''    if (!ok) return err("That email isn't on a salon team yet. Ask your manager to add you, or tap “Start a salon” below if you're the owner.");''')
rep('''async function logout() { await sb.auth.signOut(); location.reload(); }''', '''async function logout() { await sb.auth.signOut(); location.reload(); }
const PLAN_NAMES = { front_desk: "Front Desk", team: "Team", owner: "Owner" };
function openStart() {
  const signedIn = !!session;
  $("st-acct").hidden = signedIn;
  $("st-email").required = !signedIn; $("st-pw").required = !signedIn;
  $("startHelp").textContent = signedIn ? `Signed in as ${session.user.email}. Name your salon and you'll be its manager.` : "Set up your salon in a minute. You'll be its manager, and you can add your team right after.";
  show("view-start"); $("st-code").focus();
}
$("startOpen").onclick = openStart; $("startOpen2").onclick = openStart;
$("st-cancel").onclick = () => session ? location.reload() : show("view-login");
$("st-code").addEventListener("change", async () => {
  const code = $("st-code").value.trim(); if (!code) return;
  const { data } = await sbRaw.rpc("lp_check_code", { p_code: code });
  $("st-plan").textContent = data ? `✓ Code works: ${PLAN_NAMES[data]} plan, free during the beta.` : "That code isn't valid or has been used up.";
});
$("startForm").addEventListener("submit", async e => {
  e.preventDefault();
  const err = t => $("st-err").textContent = t; err("");
  const code = $("st-code").value.trim(), salon = $("st-salon").value.trim(), city = $("st-city").value.trim(), name = $("st-name").value.trim();
  $("st-btn").disabled = true;
  try {
    const { data: plan } = await sbRaw.rpc("lp_check_code", { p_code: code });
    if (!plan) return err("That invite code isn't valid or has been used up.");
    if (!session) {
      const email = $("st-email").value.trim().toLowerCase(), password = $("st-pw").value;
      let r = await sbRaw.auth.signUp({ email, password });
      if (r.error && /already/i.test(r.error.message)) r = await sbRaw.auth.signInWithPassword({ email, password });
      if (r.error) return err(/password/i.test(r.error.message) ? "Pick a longer password (at least 6 characters)." : /invalid/i.test(r.error.message) ? "That email already has a Loopd-In account with a different password." : "Couldn't create your account. Try again.");
      if (!r.data.session) return err("Check your email to confirm your account, then sign in and tap “Start a salon” again.");
      session = r.data.session;
    }
    const { error } = await sbRaw.rpc("lp_create_salon", { p_code: code, p_salon: salon, p_city: city, p_name: name });
    if (error) return err(/ALREADY_IN_SALON/.test(error.message) ? "This email already belongs to a salon. Sign in instead." : /BAD_CODE/.test(error.message) ? "That invite code isn't valid or has been used up." : "Couldn't create your salon. Try again.");
    location.reload();
  } finally { $("st-btn").disabled = false; }
});''')

# ---------- plans ----------
rep('''/* ---------- tabs & preview ---------- */''', r'''/* ---------- plans ---------- */
const PLAN_ORDER = ["front_desk", "team", "owner"];
const PLAN_INFO = {
  front_desk: { price: "$29", blurb: "The digital logbook for the front desk.", items: ["Daily log with manager follow-ups", "Client incidents", "Supplies shopping list", "Team chat, announcements, issue reports", "Phone notifications"] },
  team: { price: "$59", blurb: "Everything to run your team.", items: ["Everything in Front Desk", "Time off requests with your own limits", "1:1s with goal sheets and goal files", "Employee handbook with sign-off", "Write-ups with signatures"] },
  owner: { price: "$99", blurb: "For owners who are growing and hiring.", items: ["Everything in Team", "Private staff notes and manager log", "Applicant tracking with call checkoffs and interviews", "Your salon's logo in the app", "Personal setup call"] },
};
const planAtLeast = p => !!SALON && PLAN_ORDER.indexOf(SALON.plan) >= PLAN_ORDER.indexOf(p);
const TAB_PLAN = { time: "team", oo: "team", staff: "owner", apps: "owner" };
const tabAllowed = t => !TAB_PLAN[t] || planAtLeast(TAB_PLAN[t]);
async function loadSalon() {
  const { data } = await sbRaw.rpc("lp_my_salon_info");
  SALON = data || null;
  if (!SALON) return;
  SALON.settings = SALON.settings || {};
  $("salonLine").textContent = [SALON.name, SALON.city].filter(Boolean).join(" · ");
  document.title = SALON.name + " · Loopd-In";
  const logo = $("salonLogo");
  if (SALON.logo && planAtLeast("owner")) {
    const { data: u } = await sb.storage.from().createSignedUrl(SALON.logo, 60 * 60 * 12);
    if (u && u.signedUrl) { logo.src = u.signedUrl; logo.hidden = false; }
  } else logo.hidden = true;
}
function renderSalonSettings() {
  if (!SALON || !isMgr()) return;
  const st = SALON.settings || {};
  $("ss-name").value = SALON.name || ""; $("ss-city").value = SALON.city || "";
  $("ss-limit").value = st.timeoff_limit || 2; $("ss-sign").value = st.handbook_sign_url || "";
  $("ss-teamOnly").hidden = !planAtLeast("team"); $("ss-ownerOnly").hidden = !planAtLeast("owner");
  $("planCards").innerHTML = PLAN_ORDER.map(p => {
    const i = PLAN_INFO[p], cur = SALON.plan === p;
    return `<div class="quick" style="${cur ? "border:2px solid var(--accent)" : ""};gap:6px">
      <div class="row"><b>${PLAN_NAMES[p]}</b>${cur ? '<span class="fu ok">Your plan</span>' : ""}</div>
      <div><span style="font-size:1.4rem;font-weight:700">${i.price}</span><span class="meta"> /month per location</span></div>
      <p class="meta" style="margin:0">${i.blurb}</p>
      <ul style="margin:0;padding-left:18px;font-size:.85rem">${i.items.map(x => `<li>${esc(x)}</li>`).join("")}</ul>
      ${cur ? "" : `<button type="button" class="ghost" data-plan="${p}">Switch to ${PLAN_NAMES[p]}</button>`}
    </div>`;
  }).join("");
}
async function saveSalonSettings(e) {
  e.preventDefault();
  const err = t => $("ss-err").textContent = t; err("");
  const limit = Math.max(1, Math.min(10, parseInt($("ss-limit").value, 10) || 2));
  const sign = $("ss-sign").value.trim();
  if (sign && !/^https:\/\//i.test(sign)) return err("The sign-off link should start with https://");
  const settings = { ...(SALON.settings || {}), timeoff_limit: limit, handbook_sign_url: sign || null };
  const { error } = await sbRaw.rpc("lp_update_salon", { p_name: $("ss-name").value, p_city: $("ss-city").value, p_settings: settings, p_logo: null });
  if (error) return err(friendly(error));
  await loadSalon(); applyRole(); $("foot").textContent = "Salon settings saved.";
}
async function uploadLogo(file) {
  if (!file) return;
  if (!/^image\/(png|jpeg|webp)$/.test(file.type)) { $("ss-err").textContent = "Pick a PNG or JPG image."; return; }
  const path = `logo/logo-${Date.now()}.${file.type === "image/png" ? "png" : file.type === "image/webp" ? "webp" : "jpg"}`;
  const up = await sb.storage.from().upload(path, file, { contentType: file.type });
  if (up.error) { $("ss-err").textContent = "Couldn't upload the logo. Try again."; return; }
  const { error } = await sbRaw.rpc("lp_update_salon", { p_name: null, p_city: SALON.city, p_settings: null, p_logo: path });
  if (error) { $("ss-err").textContent = friendly(error); return; }
  await loadSalon(); $("foot").textContent = "Logo updated.";
}

/* ---------- tabs & preview ---------- */''')
rep('''  if ((t === "staff" || t === "team" || t === "apps") && !isMgr()) t = "daily";''',
    '''  if ((t === "staff" || t === "team" || t === "apps") && !isMgr()) t = "daily";
  if (!tabAllowed(t)) t = "daily";''')
rep('''  $("tab-staff").hidden = !isMgr(); $("tab-team").hidden = !isMgr(); $("tab-apps").hidden = !isMgr();''',
    '''  $("tab-staff").hidden = !isMgr() || !tabAllowed("staff"); $("tab-team").hidden = !isMgr(); $("tab-apps").hidden = !isMgr() || !tabAllowed("apps");
  $("tab-time").hidden = !tabAllowed("time"); $("tab-oo").hidden = !tabAllowed("oo");
  $("hbBox").hidden = !planAtLeast("team"); $("mlBox").hidden = !planAtLeast("owner"); $("wuBox").hidden = !planAtLeast("team");
  const lim = (SALON && SALON.settings && SALON.settings.timeoff_limit) || 2;
  $("toRule").textContent = `No more than ${lim} ${lim === 1 ? "stylist" : "stylists"} (or ${lim} front desk) out at the same time. A request is just a request: it isn't time off until a manager approves it.`;
  const signUrl = SALON && SALON.settings && SALON.settings.handbook_sign_url;
  $("hbSign").hidden = !signUrl; if (signUrl) $("hbSign").href = signUrl;
  renderSalonSettings();''')

# ---------- managers tab: salon settings + plan ----------
rep('''    <section id="view-team" hidden style="display:flex;flex-direction:column;gap:16px">''', '''    <section id="view-team" hidden style="display:flex;flex-direction:column;gap:16px">
      <div class="quick" id="salonBox">
        <h2 class="h2">🏠 Your salon</h2>
        <form id="salonForm" class="plain">
          <label>Salon name<input id="ss-name" maxlength="80" required></label>
          <label>City<input id="ss-city" maxlength="60"></label>
          <div id="ss-teamOnly" style="display:flex;flex-direction:column;gap:8px">
            <label>Most people of one role off on the same day<input id="ss-limit" type="number" min="1" max="10" step="1" inputmode="numeric"></label>
            <label>Handbook sign-off link (optional)<input id="ss-sign" type="url" maxlength="400" placeholder="https://… your own sign-off form"></label>
          </div>
          <div id="ss-ownerOnly" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <button type="button" class="ghost" id="ss-logoBtn">Upload your logo</button><input type="file" id="ss-logo" accept="image/png,image/jpeg,image/webp" hidden>
            <span class="meta">Shows at the top of the app for your whole team.</span>
          </div>
          <div class="form-actions"><span class="form-err" id="ss-err"></span><button type="submit" class="primary">Save</button></div>
        </form>
        <h2 class="h2" style="margin-top:6px">Your plan</h2>
        <p class="meta" style="margin:0">Free during the beta. Switch any time to try another plan.</p>
        <div id="planCards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px"></div>
      </div>''')
rep('''      <div class="quick">
        <h2 class="h2">Manager log 🔒</h2>''', '''      <div class="quick" id="mlBox">
        <h2 class="h2">Manager log 🔒</h2>''')
rep('''      <div class="quick">
        <div class="row"><h2 class="h2">Staff write-ups 🔒</h2>''', '''      <div class="quick" id="wuBox">
        <div class="row"><h2 class="h2">Staff write-ups 🔒</h2>''')
rep('''/* ---------- boot ---------- */''', '''$("salonForm").addEventListener("submit", saveSalonSettings);
$("ss-logoBtn").onclick = () => $("ss-logo").click();
$("ss-logo").addEventListener("change", e => { const f = e.target.files[0]; e.target.value = ""; uploadLogo(f); });
$("planCards").addEventListener("click", async e => {
  const b = e.target.closest("[data-plan]"); if (!b || !isMgr()) return;
  b.disabled = true;
  const { error } = await sbRaw.rpc("lp_set_plan", { p_plan: b.dataset.plan });
  if (error) { b.disabled = false; return alert(friendly(error)); }
  await loadSalon(); applyRole(); renderAll(); $("foot").textContent = `You're now on the ${PLAN_NAMES[SALON.plan]} plan.`;
});

/* ---------- boot ---------- */''')

# ---------- boot: load the salon before showing the app ----------
rep('''  if (!role) { show("view-noaccess"); $("noaccessMsg").textContent = `${email} isn't on the Salon Saia team yet. Ask a manager to add you, then sign in again.`; $("roleBadge").textContent = ""; $("foot").textContent = ""; return; }''',
    '''  if (!role) { show("view-noaccess"); $("noaccessMsg").textContent = ` ${email} isn't on a salon team yet. If you work at a salon, ask your manager to add this email. If you own one, start it here.`; $("roleBadge").textContent = ""; $("foot").textContent = ""; return; }
  await loadSalon();''')

# ---------- time off rule, handbook link, applicants ----------
rep('''      <div class="banner">No more than two stylists (or two front desk) out of the salon at the same time.''', '''      <div class="banner" id="toRule">No more than two stylists (or two front desk) out of the salon at the same time.''')
rep('href="https://form.jotform.com/220726080750046"', 'href="#"')
rep('''      <div class="banner">Managers only. New applications from the Jotform job application show up here automatically.</div>''',
    '''      <div class="banner">Managers only. Add people as they apply and track every call and interview. Want applications from your website to land here automatically? We'll connect your form on your setup call.</div>
      <div class="quick">
        <div class="row"><h2 class="h2">Add an applicant</h2><button type="button" class="link" id="apAddToggle">+ Add</button></div>
        <form id="apAddForm" hidden>
          <label>Name<input id="apa-name" required maxlength="100"></label>
          <label>Position<input id="apa-pos" maxlength="100" placeholder="e.g. Stylist"></label>
          <label>Phone<input id="apa-phone" type="tel" maxlength="40"></label>
          <label>Email<input id="apa-email" type="email" maxlength="120"></label>
          <label class="full">Notes<input id="apa-notes" maxlength="1000" placeholder="Where they heard about us, experience…"></label>
          <div class="full form-actions"><span class="form-err" id="apa-err"></span><button type="submit" class="primary">Add applicant</button></div>
        </form>
      </div>''')
rep('''$("apFilter").addEventListener("click",''', '''$("apAddToggle").onclick = () => { $("apAddForm").hidden = !$("apAddForm").hidden; if (!$("apAddForm").hidden) $("apa-name").focus(); };
$("apAddForm").addEventListener("submit", async e => {
  e.preventDefault(); $("apa-err").textContent = "";
  const row = { name: $("apa-name").value.trim(), position: $("apa-pos").value.trim() || null, phone: $("apa-phone").value.trim() || null, email: $("apa-email").value.trim() || null, notes: $("apa-notes").value.trim() || null, submission_id: "manual-" + crypto.randomUUID(), answers: {} };
  if (!row.name) return;
  const { error } = await sb.from("applicants").insert(row);
  if (error) { $("apa-err").textContent = friendly(error); return; }
  $("apAddForm").reset(); $("apAddForm").hidden = true; loadAll();
});
$("apFilter").addEventListener("click",''')

# ---------- remove Salon Saia specifics ----------
s = s.replace('Salon Saia · Employee write-up', '${(SALON && SALON.name) || "Loopd-In"} · Employee write-up')
rep('text("${(SALON && SALON.name) || "Loopd-In"} · Employee write-up", 18, true)', 'text(`${(SALON && SALON.name) || "Loopd-In"} · Employee write-up`, 18, true)')
rep('const text = "Salon Saia shopping list\\n"', 'const text = `${SALON.name} shopping list\\n`')
rep('<img src="salon-saia-logo.png" alt="Salon Saia">', '<img src="${esc($("salonLogo").hidden ? "icon-192.png" : $("salonLogo").src)}" alt="">')
s = s.replace('When someone applies on Jotform', 'When someone applies')
s = re.sub(r' \(pp?\. [0-9–-]+\)', '', s)   # handbook page numbers were Salon Saia's
rep('fetch(SUPABASE_URL + "/functions/v1/notify?test=1"', 'fetch(SUPABASE_URL + "/functions/v1/notify?test=1&prefix=lp_"')
assert 'Salon Saia' not in s, [s[m.start()-60:m.start()+40] for m in re.finditer('Salon Saia', s)]
assert 'jotform.com' not in s

(DST / 'index.html').write_text(s)
for f in ['icon-192.png', 'icon-512.png', 'icon-maskable-512.png', 'apple-touch-icon.png', 'favicon.png', 'sw.js']:
    shutil.copy(SRC / f, DST / f)
print('wrote', len(s), 'bytes')
