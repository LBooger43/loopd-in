"""1) Applicants: an 'Interviewing' button (next to Hired / Not a fit) and an 'Interviewing' filter.
2) Supplies: add a new item under a category (e.g. Cleaning → Dryer sheets) straight onto the shopping list,
   and keep it on the 'Running low' list for next time.
For Salon Saia's and Loopd-In's index.html; the demo is built from Salon Saia's."""
import pathlib, sys

SUP_FORM = '''        <form id="supOtherForm" class="plain" style="display:flex;flex-direction:column;gap:8px">
          <label for="supOther">Need something that's not listed?</label>
          <div style="display:grid;grid-template-columns:minmax(0,2fr) minmax(0,3fr);gap:8px"><select id="supOtherCat" aria-label="Category"></select><input id="supOther" maxlength="200" required autocomplete="off" placeholder="e.g. Dryer sheets, balloons for Friday"></div>
          <p class="meta" style="margin:0">One-time things like balloons for a party: <b>Just this once</b>. Things you'll buy again: <b>Add + save</b> so it's a button next time.</p>
          <div class="form-actions"><span class="form-err" id="supErr"></span><button type="submit" class="ghost" data-keep="0">Just this once</button><button type="submit" class="primary" data-keep="1">Add + save for next time</button></div>
        </form>'''

SUP_SUBMIT = '''$("supOtherForm").addEventListener("submit", async e => {
  e.preventDefault(); $("supErr").textContent = "";
  const v = $("supOther").value.trim(); if (!v) return;
  const category = $("supOtherCat").value || "Other";
  const same = supItems.find(i => i.category === category && i.name.toLowerCase() === v.toLowerCase());
  let item = same || null;
  const keep = !(e.submitter && e.submitter.dataset.keep === "0");
  if (!item && keep) {
    const sort = supItems.filter(i => i.category === category).reduce((m, i) => Math.max(m, i.sort || 0), supItems.reduce((m, i) => Math.max(m, i.sort || 0), 0)) + 1;
    const r = await sb.from("supply_items").insert({ category, name: v, sort }).select("id,name,category").single();
    if (!r.error) item = r.data;   // if saving it for next time isn't allowed, it still goes on today's list
  }
  if (item && supNeeds.some(n => !n.bought && n.item_id === item.id)) { $("supErr").textContent = `${item.name} is already on the list.`; return; }
  if (await addNeed(item ? { item_id: item.id, item_name: item.name, category: item.category } : { item_name: v, category })) { $("supOther").value = ""; loadAll(); }
});'''

def patch(s: str) -> str:
    if 'id="supOtherCat"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    # ---- applicants
    rep('''<div class="tabs" id="apFilter" role="tablist" style="grid-template-columns:repeat(4,1fr)">
        <button type="button" data-apf="active" aria-selected="true">Active</button>''',
        '''<div class="tabs" id="apFilter" role="tablist" style="grid-template-columns:repeat(5,1fr)">
        <button type="button" data-apf="active" aria-selected="true">Active</button>
        <button type="button" data-apf="interview" aria-selected="false">Interviewing</button>''')
    rep('interview: ["Interview scheduled", "var(--ok)"]', 'interview: ["Interviewing", "var(--ok)"]')
    rep('''<div class="actions"><button class="link done" data-ap="st" data-st="hired" data-id="${a.id}">✓ Hired</button>''',
        '''<div class="actions">${a.status !== "interview" ? `<button class="link" data-ap="st" data-st="interview" data-id="${a.id}">🗣 Interviewing</button>` : ""}<button class="link done" data-ap="st" data-st="hired" data-id="${a.id}">✓ Hired</button>''')
    # ---- supplies
    old_start = s.index('        <form id="supOtherForm" class="plain">')
    old_end = s.index('</form>', old_start) + len('</form>')
    s = s[:old_start] + SUP_FORM + s[old_end:]
    a0 = s.index('$("supOtherForm").addEventListener("submit", async e => {')
    a1 = s.index('\n});', a0) + len('\n});')
    s = s[:a0] + SUP_SUBMIT + s[a1:]
    rep('''  $("supCats").innerHTML = catOrder.map(c => `<option value="${esc(c)}">`).join("");''',
        '''  $("supCats").innerHTML = catOrder.map(c => `<option value="${esc(c)}">`).join("");
  { const sel = $("supOtherCat"), keep = sel.value, cats = [...catOrder.filter(c => c !== "Other"), "Other"];
    sel.innerHTML = cats.map(c => `<option${c === keep ? " selected" : ""}>${esc(c)}</option>`).join(""); }''')
    return s

if __name__ == '__main__':
    for p in sys.argv[1:]:
        p = pathlib.Path(p); p.write_text(patch(p.read_text())); print('patched', p)
