/* ---------- apply page (shared by Loopd-In and the demo; APPLY_HOST says where settings live) ---------- */
let aplPanel = null, aplQrUrl = null;
const resumeUrls = {}, resumeAsked = {};
function aplLink(embed) { return APPLY_HOST.url() + (embed ? (APPLY_HOST.url().includes("?") ? "&" : "?") + "embed=1" : ""); }
function aplEmbedCode() {
  return `<iframe id="loopdin-apply" src="${aplLink(true)}" title="Apply to ${esc(APPLY_HOST.name())}" style="width:100%;min-height:1500px;border:0" loading="lazy"></iframe>\n<script>addEventListener("message",function(e){if(e.data&&e.data.loopdinHeight){document.getElementById("loopdin-apply").style.minHeight=e.data.loopdinHeight+"px"}})<\/script>`;
}
function aplQrSvg(cell) {
  if (!window.qrcode) return "";
  const q = qrcode(0, "M"); q.addData(aplLink(false)); q.make();
  return q.createSvgTag({ cellSize: cell || 6, margin: 0, scalable: true });
}
function renderApplyCard() {
  if (!$("applyBox")) return;
  const ready = !!APPLY_HOST.url();
  $("applyBox").classList.toggle("apl-wait", !ready);
  if (!ready) { $("apl-state").textContent = "Setting up"; $("apl-state").className = "fu"; return; }
  const st = APPLY_HOST.get();
  $("apl-state").textContent = st.open ? "Taking applications" : "Not taking applications";
  $("apl-state").className = "fu" + (st.open ? " ok" : "");
  $("apl-url").value = aplLink(false); $("apl-open").href = aplLink(false);
  ["embed", "qr", "set"].forEach(k => $("apl-" + k).hidden = aplPanel !== k);
  $("applyBox").querySelectorAll("[data-apl]").forEach(b => b.setAttribute("aria-expanded", aplPanel === b.dataset.apl));
  if (aplPanel === "embed") $("apl-code").value = aplEmbedCode();
  if (aplPanel === "qr") {
    $("apl-qrImg").innerHTML = aplQrSvg(6);
    const svg = $("apl-qrImg").querySelector("svg"); if (svg) { svg.style.width = "100%"; svg.style.height = "100%"; }
    if (window.qrcode) { const q = qrcode(0, "M"); q.addData(aplLink(false)); q.make(); $("apl-qrDl").href = q.createDataURL(12, 16); }
  }
  if (aplPanel === "set" && !$("apl-set").dataset.filled) {
    $("apl-openChk").checked = st.open; $("apl-bg").checked = !!st.background; $("apl-pos").value = st.positions.join(", "); $("apl-intro").value = st.intro || "";
    $("apl-set").dataset.filled = "1";
  }
}
async function aplCopy(text, btn, label) {
  try { await navigator.clipboard.writeText(text); } catch { const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); }
  btn.textContent = "Copied ✓"; setTimeout(() => btn.textContent = label, 1600);
}
$("apl-copy").onclick = e => aplCopy(aplLink(false), e.currentTarget, "Copy link");
$("apl-copyCode").onclick = e => aplCopy(aplEmbedCode(), e.currentTarget, "Copy code");
$("applyBox").addEventListener("click", e => {
  const b = e.target.closest("[data-apl]"); if (!b) return;
  aplPanel = aplPanel === b.dataset.apl ? null : b.dataset.apl;
  if (aplPanel === "set") delete $("apl-set").dataset.filled;
  renderApplyCard();
});
$("apl-set").addEventListener("submit", async e => {
  e.preventDefault(); $("apl-err").textContent = "";
  const positions = $("apl-pos").value.split(",").map(x => x.trim()).filter(Boolean).slice(0, 12);
  if (!positions.length) { $("apl-err").textContent = "Add at least one job."; return; }
  const err = await APPLY_HOST.save({ open: $("apl-openChk").checked, background: $("apl-bg").checked, positions, intro: $("apl-intro").value.trim() || null });
  if (err) { $("apl-err").textContent = err; return; }
  aplPanel = null; renderApplyCard(); $("foot").textContent = "Apply page saved.";
});
$("apl-sign").onclick = () => {
  const st = APPLY_HOST.get(), logo = $("salonLogo") && !$("salonLogo").hidden ? $("salonLogo").src : "";
  const w = window.open("", "_blank"); if (!w) return;
  w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>Now hiring · ${esc(APPLY_HOST.name())}</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Figtree:wght@500;600&display=swap">
  <style>@page{size:letter;margin:0.5in}body{margin:0;font-family:Figtree,system-ui,sans-serif;color:#16213e;text-align:center;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .s{border:3px solid #5a56d6;border-radius:28px;padding:44px 40px;max-width:7in;margin:0 auto}
  .k{display:inline-block;background:#ecebfc;color:#5a56d6;font-weight:700;letter-spacing:.12em;text-transform:uppercase;border-radius:999px;padding:6px 18px;font-size:14px}
  h1{font:700 64px/1.05 Poppins,sans-serif;margin:18px 0 6px;background:linear-gradient(135deg,#2f6be0,#5a56d6);-webkit-background-clip:text;background-clip:text;color:transparent}
  h2{font:600 26px Poppins,sans-serif;margin:0 0 6px}.p{font-size:20px;color:#5f6b85;margin:0 0 26px}
  .q{width:3.3in;height:3.3in;margin:0 auto 18px}.q svg{width:100%;height:100%}.u{font-size:13px;color:#5f6b85;word-break:break-all}
  img{max-height:90px;max-width:2.6in;object-fit:contain;margin-bottom:6px}.b{margin-top:22px;font-size:12px;color:#8a93ab}
  .bar{position:fixed;top:10px;right:10px}@media print{.bar{display:none}}</style></head><body>
  <div class="bar"><button onclick="print()" style="font:600 15px Figtree;padding:10px 16px;border-radius:10px;border:0;background:#5a56d6;color:#fff">Print</button></div>
  <div class="s">${logo ? `<img src="${esc(logo)}" alt="">` : ""}<div class="k">${esc(APPLY_HOST.name())}</div><h1>We're hiring!</h1>
  <h2>${esc(st.positions.join(" · "))}</h2><p class="p">Scan with your phone camera to apply in 2 minutes.</p>
  <div class="q">${aplQrSvg(10)}</div><div class="u">${esc(aplLink(false))}</div><div class="b">Ask the front desk for details</div></div>
  <script>window.onload=function(){setTimeout(function(){print()},400)}<\/script></body></html>`);
  w.document.close();
};

/* résumés: signed links made ahead of time so they open on iPhone */
async function aplResumeLinks() {
  const need = (applicants || []).map(a => a.answers && a.answers.resume_file).filter(p => p && !resumeUrls[p] && !resumeAsked[p]);
  if (!need.length) return;
  need.forEach(p => resumeAsked[p] = 1);
  const { data } = await sb.storage.from("photos").createSignedUrls(need, 60 * 60 * 6);
  (data || []).forEach(x => { if (x.signedUrl) resumeUrls[x.path] = x.signedUrl; });
  need.forEach(p => resumeAsked[p] = 2);
  renderApps();
}
function aplResumeBtn(a) {
  const p = a.answers && a.answers.resume_file; if (!p) return "";
  const u = resumeUrls[p], nm = a.answers.resume_name || "Résumé";
  if (u) return `<a class="link" href="${esc(u)}" target="_blank" rel="noopener" title="${esc(nm)}">📄 View résumé</a>`;
  return resumeAsked[p] === 2 ? `<span class="meta">📄 Résumé: ${esc(nm)}</span>` : `<span class="meta">📄 Loading résumé…</span>`;
}
