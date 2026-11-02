/* ---------- print queue: managers send flyers and ads; front desk prints and checks them off ---------- */
let prJobs = [], prReady = false, prDoneOpen = false, prDel = null, prFile = null, prCleaned = false;
const PR_MAX = 10 * 1024 * 1024;
const prCanSee = () => isDesk();
const prToday = () => daysAgo(0), prTomorrow = () => daysAgo(-1);
function prDueText(j) {
  if (j.due_kind === "any" || !j.due_date) return "Whenever";
  const d = j.due_date === prToday() ? "today" : j.due_date === prTomorrow() ? "tomorrow" : new Date(j.due_date + "T12:00").toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  return j.due_kind === "open" ? `Before we open ${d}` : `By ${d}`;
}
function prLate(j) {
  if (j.status !== "pending" || j.due_kind === "any" || !j.due_date) return false;
  return j.due_date < prToday() || (j.due_kind === "open" && j.due_date === prToday() && new Date().getHours() >= 11);
}
const prRank = j => j.due_kind === "any" || !j.due_date ? "9999-12-31" : j.due_date + (j.due_kind === "open" ? "a" : "b");
function prCard(j) {
  const url = photoUrls[j.file_path], isImg = /^image\//.test(j.file_type || "");
  const late = prLate(j), done = j.status === "printed";
  const head = `<div class="row"><span><span class="name">${esc(j.title)}</span> <span class="tag">${esc(j.copies)} ${j.copies === 1 ? "copy" : "copies"}</span>${j.paper && j.paper !== "Regular paper" ? ` <span class="tag">${esc(j.paper)}</span>` : ""}</span>${done ? `<span class="fu ok">✓ Printed</span>` : late ? `<span class="fu wait">Late</span>` : `<span class="fu">${esc(prDueText(j))}</span>`}</div>`;
  const thumb = isImg && url ? `<a href="${esc(url)}" target="_blank" rel="noopener"><img class="photo" src="${esc(url)}" alt="${esc(j.title)}" loading="lazy" style="max-height:140px;object-fit:contain;background:#fff"></a>` : "";
  const meta = done ? `<div class="meta">Printed by ${esc(nameOf(j.printed_by))} · ${esc(stamp(j.printed_at))} · sent by ${esc(nameOf(j.created_by))}</div>`
    : `<div class="meta">${late ? esc(prDueText(j)) + " · " : ""}Sent by ${esc(nameOf(j.created_by))} · ${esc(stamp(j.created_at))}${j.file_name ? ` · ${esc(j.file_name)}` : ""}</div>`;
  let acts = "";
  if (prDel === j.id) acts = `<div class="actions"><span class="meta">Remove this for good?</span><button class="link del" data-pr="del-yes" data-id="${j.id}">Yes, remove</button><button class="link" data-pr="close">No</button></div>`;
  else if (!done) acts = `<div class="actions">${url ? `<a class="primary" style="text-decoration:none;padding:10px 14px;border-radius:10px" href="${esc(url)}" target="_blank" rel="noopener">🖨 Open to print</a>` : `<span class="meta">Getting the file…</span>`}<button class="link done" data-pr="printed" data-id="${j.id}">✓ Printed</button>${isMgr() ? `<button class="link del" data-pr="del" data-id="${j.id}">Cancel</button>` : ""}</div>`;
  else acts = `<div class="actions">${url ? `<a class="link" href="${esc(url)}" target="_blank" rel="noopener">Open file</a>` : ""}${isMgr() ? `<button class="link" data-pr="again" data-id="${j.id}">Print again</button><button class="link del" data-pr="del" data-id="${j.id}">Remove</button>` : ""}</div>`;
  return `<article class="entry" style="--stripe:${done ? "var(--ok)" : late ? "var(--crit)" : "var(--accent)"}">${head}${j.note ? `<div class="note">${esc(j.note)}</div>` : ""}${thumb}${meta}${acts}</article>`;
}
function renderPrint() {
  const box = $("prBox"); if (!box) return;
  box.hidden = !me || !prCanSee() || !prReady;
  if (box.hidden) return;
  $("prNew").hidden = !isMgr() || !$("prForm").hidden;
  const open = prJobs.filter(j => j.status === "pending").sort((a, b) => prRank(a).localeCompare(prRank(b)) || a.created_at.localeCompare(b.created_at));
  const done = prJobs.filter(j => j.status === "printed").sort((a, b) => (b.printed_at || "").localeCompare(a.printed_at || ""));
  const late = open.filter(prLate).length;
  $("prHead").textContent = open.length ? `🖨 To print (${open.length})${late ? ` · ${late} late` : ""}` : "🖨 To print";
  $("prList").innerHTML = open.length ? open.map(prCard).join("") : `<div class="meta">Nothing to print right now.${isMgr() ? " Tap “+ Send to print” to send a flyer or ad to the front desk." : ""}</div>`;
  $("prDoneToggle").hidden = !done.length;
  $("prDoneToggle").textContent = prDoneOpen ? "Hide printed" : `Printed recently (${done.length})`;
  $("prDone").hidden = !prDoneOpen;
  $("prDone").innerHTML = prDoneOpen ? done.slice(0, 30).map(prCard).join("") : "";
  if (realMgr() && !prCleaned) { prCleaned = true; prCleanup(); }
}
/* printed or cancelled more than 30 days ago: remove the job, and its file once nothing else uses it */
async function prCleanup() {
  const cut = new Date(Date.now() - 30 * 864e5).toISOString();
  const old = prJobs.filter(j => j.status !== "pending" && (j.printed_at || j.created_at) < cut);
  if (!old.length) return;
  const keep = new Set(prJobs.filter(j => !old.includes(j)).map(j => j.file_path));
  const files = [...new Set(old.map(j => j.file_path))].filter(p => !keep.has(p));
  await sb.from("print_jobs").delete().in("id", old.map(j => j.id));
  if (files.length) await sb.storage.from("photos").remove(files);
}
function prSetWhen() {
  $("pr-dateWrap").hidden = $("pr-when").value !== "day";
  if ($("pr-when").value === "day" && !$("pr-date").value) $("pr-date").value = prTomorrow();
}
function prPick(f) {
  $("pr-err").textContent = "";
  if (!f) return;
  if (!/^(application\/pdf|image\/)/.test(f.type || "")) { $("pr-err").textContent = "Pick a PDF or a picture."; return; }
  if (f.size > PR_MAX) { $("pr-err").textContent = "That file is over 10 MB. In Canva, try PDF Standard instead of PDF Print."; return; }
  prFile = f;
  $("pr-fileTxt").innerHTML = `<b>📄 ${esc(f.name)}</b><br><span class="meta">${(f.size / 1024 / 1024).toFixed(1)} MB · tap to choose a different file</span>`;
  if (!$("pr-title").value.trim()) $("pr-title").value = f.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ").slice(0, 120);
}
$("prNew").onclick = () => {
  $("prForm").hidden = false; $("prNew").hidden = true; prFile = null; $("prForm").reset();
  $("pr-fileTxt").innerHTML = `<b>Choose the file to print</b><br><span class="meta">or drag it here · PDF or image · up to 10 MB</span>`;
  $("pr-when").value = new Date().getHours() >= 12 ? "open_tomorrow" : "open_today"; prSetWhen();
};
$("pr-cancel").onclick = () => { $("prForm").hidden = true; prFile = null; renderPrint(); };
$("pr-when").onchange = prSetWhen;
$("pr-file").onchange = e => prPick(e.target.files[0]);
["dragenter", "dragover"].forEach(ev => $("pr-drop").addEventListener(ev, e => { e.preventDefault(); $("pr-drop").classList.add("over"); }));
["dragleave", "drop"].forEach(ev => $("pr-drop").addEventListener(ev, e => { e.preventDefault(); $("pr-drop").classList.remove("over"); }));
$("pr-drop").addEventListener("drop", e => prPick(e.dataTransfer.files && e.dataTransfer.files[0]));
$("prForm").addEventListener("submit", async e => {
  e.preventDefault();
  const err = t => $("pr-err").textContent = t; err("");
  if (!prFile) return err("Choose the file to print first.");
  const copies = Math.max(1, Math.min(1000, parseInt($("pr-copies").value, 10) || 1));
  const w = $("pr-when").value;
  if (w === "day" && !$("pr-date").value) return err("Pick the day it's needed.");
  const btn = $("pr-send"); btn.disabled = true; btn.textContent = "Sending…";
  const ext = ((prFile.name.split(".").pop() || "pdf").toLowerCase().replace(/[^a-z0-9]/g, "") || "pdf").slice(0, 5);
  const path = `print/${Date.now()}-${(crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)).slice(0, 8)}.${ext}`;
  const up = await sb.storage.from("photos").upload(path, prFile, { contentType: prFile.type });
  if (up.error) { btn.disabled = false; btn.textContent = "Send to front desk"; return err("The file didn't upload. Check your connection and try again."); }
  const row = { title: $("pr-title").value.trim() || prFile.name, file_path: path, file_name: prFile.name.slice(0, 150), file_type: prFile.type, copies, paper: $("pr-paper").value,
    due_kind: w === "any" ? "any" : w === "day" ? "day" : "open", due_date: w === "any" ? null : w === "day" ? $("pr-date").value : w === "open_today" ? prToday() : prTomorrow(), note: $("pr-note").value.trim() || null, status: "pending" };
  const { error } = await sb.from("print_jobs").insert(row);
  btn.disabled = false; btn.textContent = "Send to front desk";
  if (error) return err(friendly(error));
  $("prForm").hidden = true; prFile = null; $("foot").textContent = "Sent to the front desk to print."; loadAll();
});
$("prDoneToggle").onclick = () => { prDoneOpen = !prDoneOpen; renderPrint(); };
$("prBox").addEventListener("click", async e => {
  const b = e.target.closest("[data-pr]"); if (!b) return;
  const act = b.dataset.pr, id = b.dataset.id, j = prJobs.find(x => x.id === id);
  if (act === "close") { prDel = null; return renderPrint(); }
  if (act === "del") { prDel = id; return renderPrint(); }
  b.disabled = true;
  let error = null;
  if (act === "printed") ({ error } = await sb.from("print_jobs").update({ status: "printed", printed_by: me.email, printed_at: new Date().toISOString() }).eq("id", id));
  if (act === "again" && j) ({ error } = await sb.from("print_jobs").insert({ title: j.title, file_path: j.file_path, file_name: j.file_name, file_type: j.file_type, copies: j.copies, paper: j.paper,
    due_kind: "open", due_date: new Date().getHours() >= 12 ? prTomorrow() : prToday(), note: j.note, status: "pending" }));
  if (act === "del-yes" && j) {
    ({ error } = await sb.from("print_jobs").delete().eq("id", id));
    if (!error && !prJobs.some(x => x.id !== id && x.file_path === j.file_path)) await sb.storage.from("photos").remove([j.file_path]);
    prDel = null;
  }
  if (error) { b.disabled = false; return alert(friendly(error)); }
  if (act === "printed") $("foot").textContent = "Marked printed.";
  if (act === "again") $("foot").textContent = "Sent to print again.";
  loadAll();
});
