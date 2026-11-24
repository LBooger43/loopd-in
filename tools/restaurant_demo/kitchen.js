
/* ---------- Kitchen (restaurant): chef notes to the line, 86 list, temps, line check, chef log, Spanish ---------- */
const isBoh = () => effRole() === "boh";
const isChef = () => effRole() === "chef";
const isKitchen = () => isBoh() || isChef() || isMgr();
const isKLead = () => isChef() || isMgr();
let kLangPick = null, kLastRole = null, kShift = new Date().getHours() < 15 ? "AM" : "PM", kOrig = {};
const kLang = () => kLangPick || (isBoh() ? "es" : "en");
const KT = {
  en: { title: "🔪 Kitchen", t86: "🚫 86'd right now", none86: "Nothing is 86'd. 👍", ph86: "What's out? e.g. salmon", b86: "86 it", back: "Back on",
    temps: "🌡️ Temps", rule: "Cold 41°F or below · Frozen 0°F or below · Hot 135°F or above", save: "Save", last: "Last", noRead: "No reading yet today",
    over: "Out of range: tell the chef", lc: "✅ Line check", lcHelp: "Check every item before service. Out-of-range temps turn red and go to the chef.",
    submit: "Submit line check", done: "Done", waiting: "Waiting for chef sign-off", signed: "Signed off by", sign: "Sign off", flagged: "flagged",
    notice: "From the chef", got: "Got it", gotDone: "Got it ✓", seen: "got it", orig: "Original", trans: "Translated from English", showOrig: "See original", hideOrig: "Hide original",
    today: "Today", foot: "Kitchen view. Everything you log goes to the chef and managers.", recent: "Today's readings", by: "by", tempErr: "Type the temperature first.", lcErr: "Add a temp for every item, or check it off." },
  es: { title: "🔪 Cocina", t86: "🚫 86 ahora", none86: "No hay nada en 86. 👍", ph86: "¿Qué se acabó? ej. salmón", b86: "Marcar 86", back: "Ya hay",
    temps: "🌡️ Temperaturas", rule: "Frío 41°F o menos · Congelado 0°F o menos · Caliente 135°F o más", save: "Guardar", last: "Última", noRead: "Sin lectura hoy",
    over: "Fuera de rango: avisa al chef", lc: "✅ Revisión de línea", lcHelp: "Revisa cada producto antes del servicio. Las temperaturas fuera de rango salen en rojo y le llegan al chef.",
    submit: "Enviar revisión de línea", done: "Listo", waiting: "Esperando firma del chef", signed: "Firmado por", sign: "Firmar", flagged: "marcados",
    notice: "Aviso del chef", got: "Enterado", gotDone: "Enterado ✓", seen: "enterados", orig: "Original", trans: "Traducido del inglés", showOrig: "Ver original", hideOrig: "Ocultar original",
    today: "Hoy", foot: "Vista de cocina. Todo lo que anotas le llega al chef y a los gerentes.", recent: "Lecturas de hoy", by: "por", tempErr: "Primero escribe la temperatura.", lcErr: "Pon la temperatura de cada producto o márcalo como listo." },
};
const kt = k => (KT[kLang()] || KT.en)[k];
const K_LIMIT = { cold: [null, 41], frozen: [null, 0], hot: [135, null] };
const kOk = (kind, t) => { const [lo, hi] = K_LIMIT[kind] || []; return (lo == null || t >= lo) && (hi == null || t <= hi); };
const K_UNITS = [["walkin", "Walk-in cooler", "Cámara fría", "cold"], ["reachin", "Reach-in (line)", "Refrigerador de la línea", "cold"], ["freezer", "Walk-in freezer", "Congelador", "frozen"], ["hotbox", "Hot holding cabinet", "Gabinete caliente", "hot"]];
const K_LINE = [
  ["Grill", "Parrilla", [["Burger patties", "Hamburguesas", "cold"], ["Steaks", "Filetes", "cold"], ["Chicken breast", "Pechuga de pollo", "cold"]]],
  ["Sauté", "Salteado", [["Salmon", "Salmón", "cold"], ["Scallops", "Vieiras", "cold"], ["Béarnaise (holding)", "Bearnesa (en caliente)", "hot"]]],
  ["Fry", "Freidora", [["Fryer oil filtered", "Aceite de freidora filtrado", "check"], ["Fries", "Papas fritas", "frozen"]]],
  ["Cold side", "Lado frío", [["Salad greens", "Lechuga", "cold"], ["Dressings", "Aderezos", "cold"], ["Cut fruit", "Fruta picada", "cold"]]],
  ["Hot holding", "Mantener caliente", [["Soup of the day", "Sopa del día", "hot"], ["Rice", "Arroz", "hot"]]],
];
const kName = (en, es) => kLang() === "es" ? es : en;
const kItemName = n => { for (const [, , list] of K_LINE) { const f = list.find(x => x[0] === n); if (f) return kName(f[0], f[1]); } return n; };
const kUnitName = id => { const u = K_UNITS.find(x => x[0] === id); return u ? kName(u[1], u[2]) : id; };
const kTime = iso => new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" }).replace(" ", "").toLowerCase();
const kToday = () => daysAgo(0);
let kTemps = [], kChecks = [], kChef = [];
async function kLoad() {
  if (!me) return;
  const [a, b, c] = await Promise.all([
    sb.from("temp_logs").select("*").order("created_at", { ascending: false }).limit(200),
    sb.from("line_checks").select("*").order("created_at", { ascending: false }).limit(60),
    sb.from("chef_log").select("*").order("created_at", { ascending: false }).limit(200),
  ]);
  kTemps = a.data || []; kChecks = b.data || []; kChef = c.data || [];
}
function renderKitchen() { kLoad().then(() => { renderKitchenView(); renderChefLog(); kTrans(); }); }
function renderKitchenView() {
  if (!$("view-kitchen")) return;
  if (kLastRole !== effRole()) { kLastRole = effRole(); kLangPick = null; }
  $("kLang").hidden = !isKitchen();
  $("kLang").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.klang === kLang()));
  $("kTitle").textContent = kt("title"); $("k86Title").textContent = kt("t86"); $("kTempTitle").textContent = kt("temps"); $("kTempRule").textContent = kt("rule");
  $("kLcTitle").textContent = kt("lc"); $("kLcHelp").textContent = kt("lcHelp"); $("kLcBtn").textContent = kt("submit");
  $("k86Item").placeholder = kt("ph86"); $("k86Btn").textContent = kt("b86");
  // chef notes to the line (last 3 days)
  const since = Date.now() - 3 * 864e5;
  const notes = kChef.filter(n => n.to_line && new Date(n.created_at) > since);
  $("kNotices").innerHTML = notes.map(n => {
    const es = kLang() === "es", txt = es && n.note_es ? n.note_es : n.note, acks = n.acks || [], mine = acks.includes(me.email), showO = kOrig[n.id];
    return `<div class="quick k-notice"><div class="row"><span class="tag" style="background:var(--accent-soft);color:var(--accent)">${esc(kt("notice"))}</span><span class="meta">${esc(kTime(n.created_at))} · ${esc(nameOf(n.created_by))}</span></div>
      <b style="font-size:1.02rem">${esc(txt)}</b>
      ${es && n.note_es ? `<span class="meta">🌐 ${esc(kt("trans"))} · <button type="button" class="link" data-korig="${n.id}">${esc(showO ? kt("hideOrig") : kt("showOrig"))}</button></span>${showO ? `<span class="meta">${esc(kt("orig"))}: “${esc(n.note)}”</span>` : ""}` : ""}
      <div class="actions">${isBoh() ? `<button type="button" class="${mine ? "ghost" : "primary"}" data-kack="${n.id}"${mine ? " disabled" : ""}>${esc(mine ? kt("gotDone") : kt("got"))}</button>` : ""}<span class="meta">${acks.length} ${esc(kt("seen"))}</span></div></div>`;
  }).join("");
  // 86 list, same data as the shift log's board
  const out = daily.filter(d => d.category === "86'd" && d.entry_date >= daysAgo(1) && !(fups[d.id] && fups[d.id].done));
  $("k86List").innerHTML = out.length ? out.map(d => `<div class="row k-item"><span style="flex:1"><b>${esc(d.note.replace(/^86\s*/i, "").replace(/^./, c => c.toUpperCase()))}</b><br><span class="meta">${esc(t12(d.entry_time))} · ${esc(nameOf(d.created_by))}</span></span>${isKLead() || effRole() === "expo" ? `<button type="button" class="ghost" data-back86="${d.id}">${esc(kt("back"))}</button>` : ""}</div>`).join("") : `<span class="meta">${esc(kt("none86"))}</span>`;
  // temps: one row per unit with today's last reading
  const today = kTemps.filter(t => t.created_at.slice(0, 10) === new Date().toISOString().slice(0, 10) || new Date(t.created_at).toDateString() === new Date().toDateString());
  $("kUnits").innerHTML = K_UNITS.map(([id, , , kind]) => {
    const last = today.find(t => t.unit === id), bad = last && !kOk(kind, last.temp);
    return `<form class="k-unit${bad ? " bad" : ""}" data-kunit="${id}"><span style="flex:1"><b>${esc(kUnitName(id))}</b><br><span class="meta">${last ? `${esc(kt("last"))}: <b style="color:${bad ? "var(--crit)" : "var(--ok)"}">${last.temp}°F</b> · ${esc(kTime(last.created_at))}${bad ? ` · ⚠ ${esc(kt("over"))}` : ""}` : esc(kt("noRead"))}</span></span>
      <input type="number" step="1" inputmode="numeric" aria-label="°F" placeholder="°F" style="width:74px"><button type="submit" class="ghost">${esc(kt("save"))}</button></form>`;
  }).join("");
  $("kTempLog").innerHTML = today.length ? `<div class="lbl" style="margin-top:6px">${esc(kt("recent"))}</div>` + today.slice(0, 8).map(t => { const u = K_UNITS.find(x => x[0] === t.unit) || [, , , "cold"], bad = !kOk(u[3], t.temp); return `<div class="meta">${esc(kTime(t.created_at))} · ${esc(kUnitName(t.unit))} <b style="color:${bad ? "var(--crit)" : "inherit"}">${t.temp}°F${bad ? " ⚠" : ""}</b> · ${esc(nameOf(t.created_by))}</div>`; }).join("") : "";
  // line check
  $("kShift").querySelectorAll("button").forEach(b => b.setAttribute("aria-selected", b.dataset.kshift === kShift));
  const doneNow = kChecks.find(c => c.check_date === kToday() && c.shift === kShift);
  $("kLcForm").hidden = !!doneNow;
  if (!doneNow && !$("kLcItems").dataset.built) {
    $("kLcItems").innerHTML = K_LINE.map(([st, stEs, items], si) => `<div class="k-station"><b>${esc(kName(st, stEs))}</b>${items.map(([it, itEs, kind], ii) => `<div class="row k-item" data-kli="${si}-${ii}" data-kind="${kind}"><span style="flex:1">${esc(kName(it, itEs))}<br><span class="meta">${kind === "check" ? "" : kind === "hot" ? "≥ 135°F" : kind === "frozen" ? "≤ 0°F" : "≤ 41°F"}</span></span>${kind === "check" ? `<label class="fu-check" style="margin:0"><input type="checkbox"> ${esc(kt("done"))}</label>` : `<input type="number" step="1" inputmode="numeric" placeholder="°F" style="width:74px">`}</div>`).join("")}</div>`).join("");
    $("kLcItems").dataset.built = kLang();
  }
  if ($("kLcItems").dataset.built && $("kLcItems").dataset.built !== kLang()) { $("kLcItems").dataset.built = ""; renderKitchenView(); return; }
  const recent = kChecks.filter(c => c.check_date >= daysAgo(1));
  $("kLcDone").innerHTML = recent.map(c => {
    const flags = (c.items || []).filter(i => i.kind !== "check" && !kOk(i.kind, i.temp));
    return `<div class="k-done${c.signed_by ? " ok" : ""}"><div class="row"><b>${esc(c.check_date === kToday() ? kt("today") : fmt(c.check_date))} · ${esc(c.shift)}</b><span class="meta">${esc(nameOf(c.created_by))} · ${esc(kTime(c.created_at))}</span></div>
      ${flags.length ? `<span style="color:var(--crit);font-weight:600">⚠ ${flags.length} ${esc(kt("flagged"))}: ${flags.map(i => esc(kItemName(i.name)) + " " + i.temp + "°F").join(", ")}</span>` : ""}
      <div class="row"><span class="meta">${c.signed_by ? `✓ ${esc(kt("signed"))} ${esc(nameOf(c.signed_by))} · ${esc(kTime(c.signed_at))}` : esc(kt("waiting"))}</span>${!c.signed_by && isKLead() ? `<button type="button" class="primary" data-ksign="${c.id}">${esc(kt("sign"))}</button>` : ""}</div></div>`;
  }).join("");
}
function renderChefLog() {
  if (!$("chefFeed")) return;
  $("chefFeed").innerHTML = kChef.length ? kChef.map(n => `<div class="entry"><div class="row"><span class="tag">${esc(n.cat || "Note")}</span><span class="meta">${esc(new Date(n.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }))} · ${esc(kTime(n.created_at))} · ${esc(nameOf(n.created_by))}</span></div>
    <p class="note" style="margin:6px 0 0">${esc(n.note)}</p>${n.to_line ? `<span class="meta">📣 Posted to the line · ${(n.acks || []).length} got it${n.note_es ? ` · 🇪🇸 “${esc(n.note_es)}”` : ""}</span>` : ""}</div>`).join("") : `<div class="empty"><b>No chef notes yet</b>Prep, waste, orders and equipment notes for the kitchen go here.</div>`;
}
// Spanish for the cook's screens: swaps fixed labels in the app (chat, time off, 1:1s, tabs) while Spanish is on.
const K_ES = {
  "Shift log": "Bitácora", "Team 💬": "Equipo 💬", "Time off": "Días libres", "1:1s": "1:1", "Kitchen": "Cocina", "Cook": "Cocinero", "Sous chef": "Sous chef",
  "💬 Team chat": "💬 Chat del equipo", "📣 Announcements": "📣 Avisos", "📌 For you": "📌 Para ti", "📘 Employee handbook": "📘 Manual del empleado", "🔔 Notifications": "🔔 Notificaciones",
  "🛠 Report an issue": "🛠 Reportar un problema", "Send": "Enviar", "Read handbook": "Leer manual", "Read it, then sign that you received it.": "Léelo y firma que lo recibiste.", "Sign receipt ↗": "Firmar recibo ↗",
  "Goes straight to the managers' to-do list.": "Va directo a la lista de tareas de los gerentes.", "Message the whole team": "Mensaje para todo el equipo", "e.g. Out of limes, fryer 2 won't heat": "ej. No hay limones, la freidora 2 no calienta",
  "Request time off": "Pedir días libres", "First day off": "Primer día libre", "Back to work": "Regreso al trabajo", "Note (optional)": "Nota (opcional)", "Send to managers": "Enviar a los gerentes",
  "My requests": "Mis solicitudes", "Upcoming approved": "Próximos aprobados", "e.g. Family wedding": "ej. Boda familiar",
  "No more than two people from the same station off at the same time. A request is just a request: it isn't time off until a manager approves it.": "No más de dos personas de la misma estación libres al mismo tiempo. Una solicitud no es día libre hasta que un gerente la aprueba.",
  "Request a 1:1": "Pedir una reunión 1:1", "Pick a time that works for you. A manager will confirm it or suggest another time.": "Elige una hora que te funcione. Un gerente la confirma o sugiere otra.",
  "With": "Con", "Any manager": "Cualquier gerente", "Day": "Día", "Time": "Hora", "What do you want to talk about? (optional)": "¿De qué quieres hablar? (opcional)", "Send request": "Enviar solicitud",
  "My 1:1s": "Mis reuniones 1:1", "Upcoming 1:1s": "Próximas reuniones 1:1", "📁 My goal sheets": "📁 Mis hojas de metas", "e.g. Training to bartend, picking up more shifts": "ej. Aprender la parrilla, más turnos",
  "↩ Reply": "↩ Responder", "Reply": "Responder", "Back to manager view": "Volver a la vista de gerente", "Pending": "Pendiente", "Approved": "Aprobado", "Declined": "No aprobado", "Cancel": "Cancelar", "Delete": "Borrar", "Exit preview": "Salir de la vista previa",
};
const K_EN = {}; Object.entries(K_ES).forEach(([a, b]) => K_EN[b] = a);
function kTrans() {
  if (kLastRole !== effRole()) { kLastRole = effRole(); kLangPick = null; }
  const es = kLang() === "es", dict = es ? K_ES : K_EN, root = document.querySelector(".wrap");
  if (!root) return;
  const swap = v => { const t = v.trim(); if (dict[t]) return v.replace(t, dict[t]); const m = t.match(/^(.+?)( \(\d+\))$/); return m && dict[m[1]] ? v.replace(m[1], dict[m[1]]) : null; };
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n; (n = w.nextNode());) { if (n.parentElement && n.parentElement.closest("#view-kitchen, script, style")) continue; const r = swap(n.nodeValue); if (r !== null && r !== n.nodeValue) n.nodeValue = r; }
  root.querySelectorAll("[placeholder]").forEach(el => { const r = swap(el.placeholder); if (r !== null) el.placeholder = r; });
  if (isBoh()) $("foot").textContent = kt("foot");
}
document.addEventListener("click", async e => {
  const lang = e.target.closest("[data-klang]"); if (lang) { kLangPick = lang.dataset.klang; renderKitchenView(); kTrans(); return; }
  const sh = e.target.closest("[data-kshift]"); if (sh) { kShift = sh.dataset.kshift; renderKitchenView(); return; }
  const o = e.target.closest("[data-korig]"); if (o) { kOrig[o.dataset.korig] = !kOrig[o.dataset.korig]; renderKitchenView(); return; }
  const a = e.target.closest("[data-kack]"); if (a) {
    const n = kChef.find(x => x.id === a.dataset.kack); a.disabled = true;
    await sb.from("chef_log").update({ acks: [...new Set([...(n.acks || []), me.email])] }).eq("id", n.id); loadAll(); return;
  }
  const s = e.target.closest("[data-ksign]"); if (s) {
    s.disabled = true; await sb.from("line_checks").update({ signed_by: me.email, signed_at: new Date().toISOString() }).eq("id", s.dataset.ksign);
    $("foot").textContent = "Line check signed off."; loadAll(); return;
  }
});
document.addEventListener("submit", async e => {
  const f = e.target;
  if (f.id === "k86Form") {
    e.preventDefault(); const v = $("k86Item").value.trim(); if (!v) return;
    await sb.from("daily_log").insert({ entry_date: daysAgo(0), entry_time: nowTime(), category: "86'd", note: "86 " + v, needs_followup: false, created_by: me.email });
    $("k86Item").value = ""; loadAll(); return;
  }
  if (f.dataset && f.dataset.kunit) {
    e.preventDefault(); const inp = f.querySelector("input"), t = parseFloat(inp.value);
    if (isNaN(t)) { inp.focus(); $("foot").textContent = kt("tempErr"); return; }
    const u = K_UNITS.find(x => x[0] === f.dataset.kunit);
    await sb.from("temp_logs").insert({ unit: u[0], temp: t, created_by: me.email });
    if (!kOk(u[3], t)) await sb.from("daily_log").insert({ entry_date: daysAgo(0), entry_time: nowTime(), category: "Maintenance", note: `${u[1]} read ${t}°F (${u[3] === "hot" ? "should be 135°F or above" : u[3] === "frozen" ? "should be 0°F or below" : "should be 41°F or below"}). Logged from the Kitchen tab.`, needs_followup: true, created_by: me.email });
    inp.value = ""; loadAll(); return;
  }
  if (f.id === "kLcForm") {
    e.preventDefault(); const items = []; let missing = false;
    f.querySelectorAll("[data-kli]").forEach(row => {
      const [si, ii] = row.dataset.kli.split("-").map(Number), [st, , list] = K_LINE[si], [name, , kind] = list[ii];
      if (kind === "check") { const c = row.querySelector("input").checked; if (!c) missing = true; items.push({ station: st, name, kind, ok: c }); }
      else { const v = parseFloat(row.querySelector("input").value); if (isNaN(v)) missing = true; items.push({ station: st, name, kind, temp: v }); }
    });
    if (missing) { $("kLcErr").textContent = kt("lcErr"); return; }
    $("kLcErr").textContent = "";
    await sb.from("line_checks").insert({ check_date: kToday(), shift: kShift, items, created_by: me.email, signed_by: null, signed_at: null });
    const bad = items.filter(i => i.kind !== "check" && !kOk(i.kind, i.temp));
    if (bad.length) await sb.from("daily_log").insert({ entry_date: daysAgo(0), entry_time: nowTime(), category: "Maintenance", note: `Line check (${kShift}): ${bad.map(i => i.name + " " + i.temp + "°F").join(", ")} out of range.`, needs_followup: true, created_by: me.email });
    $("kLcItems").dataset.built = ""; loadAll(); return;
  }
  if (f.id === "chefForm") {
    e.preventDefault(); const note = $("chefNote").value.trim(); if (!note) return;
    const cat = ($("chefCats").querySelector("[aria-pressed=true]") || {}).textContent || "Note";
    const { error } = await sb.from("chef_log").insert({ cat, note, note_es: $("chefEs").value.trim() || null, to_line: $("chefLine").checked, acks: [], created_by: me.email });
    if (error) { $("chefErr").textContent = friendly(error); return; }
    $("chefNote").value = ""; $("chefEs").value = ""; $("chefLine").checked = false; $("chefEsWrap").hidden = true;
    $("foot").textContent = "Saved to the chef log."; loadAll(); return;
  }
});
$("chefCats").addEventListener("click", e => { const b = e.target.closest(".cat"); if (!b) return; $("chefCats").querySelectorAll(".cat").forEach(x => x.setAttribute("aria-pressed", x === b)); });
$("chefLine").addEventListener("change", () => { $("chefEsWrap").hidden = !$("chefLine").checked; });
