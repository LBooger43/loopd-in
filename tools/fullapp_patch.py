"""Manager view for the full apply-page application (sections like a paper application) + a Print button on every full application.
Print goes into Salon Saia, Loopd-In and the demo; the apply-page sections go where the apply page lives (Loopd-In, demo)."""
import pathlib, sys
YN = []
def emp(i): return f'  ["Job {i}", [["e{i}_employer","Employer"],["e{i}_title","Job title"],["e{i}_dates","Dates"],["e{i}_phone","Phone"],["e{i}_address","Address"],["e{i}_duties","What they did"],["e{i}_supervisor","Supervisor / manager"],["e{i}_contact","May we contact them?"],["e{i}_reason","Reason for leaving"]]],\n'
SECTIONS = ('  ["Application", [["avail_type","Available for"],["temp_date","If temporary, available"],["license","License"],["experience","Years in the industry"],["availability","Days and hours they can work"],["start","Could start"],["heard","Heard about us from"],["instagram","Instagram"],["address","Home address"],["phone2","Other phone"],["employed_now","Working somewhere now?"],["prev_employed","Worked here before?"],["prev_when","If yes, when"],["languages","Other languages"],["about","About them"]]],\n'
            '  ["Getting to work", [["drivers_license","Valid driver\'s license?"],["dl_exp","License expires"],["transportation","Own transportation?"],["reliable","Reliable?"]]],\n'
            '  ["Background", [["convicted","Convicted of a crime?"],["offense","Offense"],["offense_date","Date"],["substances","Controlled substance that could affect work?"]]],\n'
            '  ["Education and skills", [["cos_name","Cosmetology school"],["cos_years","Years"],["cos_grad","Graduated?"],["hs_name","High school"],["hs_years","Years"],["hs_grad","Graduated?"],["college_name","College or other"],["college_years","Years"],["college_grad","Graduated?"],["training","Licenses, certificates and classes"],["software","Software"],["skills","Other skills"]]],\n'
            + ''.join(emp(i) for i in range(1, 5)) +
            '  ["References", [["r1_name","Reference 1"],["r1_phone","Phone"],["r1_relation","How they know them"],["r2_name","Reference 2"],["r2_phone","Phone"],["r2_relation","How they know them"],["r3_name","Reference 3"],["r3_phone","Phone"],["r3_relation","How they know them"]]],\n'
            '  ["Signature", [["agree","Agreed to the statement"],["signature","Signed"],["signed_on","Date signed"]]],\n')

PRINT_JS = r'''
/* print a full application (like Jotform's PDF) */
function apPrint(a) {
  const w = window.open("", "_blank"); if (!w) return;
  const body = apAnswers(a).replace(/<button[^>]*data-ap="print"[^>]*>.*?<\/button>/, "");
  w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>Application · ${esc(a.name)}</title>
  <style>body{font:14px/1.45 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;color:#16213e;margin:32px auto;max-width:720px;padding:0 20px}
  h1{font-size:22px;margin:0 0 4px}.meta{color:#5f6b85;font-size:12px}.note{margin:1px 0 6px}b{display:block;font-size:15px;margin-top:14px;border-bottom:1px solid #dfe3ef;padding-bottom:3px}
  .mgr{display:block!important}.mgr>div{break-inside:avoid}@media print{.bar{display:none}body{margin:0 auto}}<\/style><\/head><body><div class="bar" style="text-align:right"><button onclick="print()" style="font:600 14px sans-serif;padding:8px 14px;border-radius:8px;border:0;background:#5a56d6;color:#fff">Print</button></div>
  <h1>${esc(a.name)}</h1><div class="meta">${esc([a.position, a.phone, a.email].filter(Boolean).join(" · "))}</div>
  <div class="meta">Applied ${esc(whenFull(a.submitted_at))}${a.status ? ` · Status: ${esc((AP_STATUS[a.status] || [a.status])[0])}` : ""}</div>
  ${body}${a.notes ? `<b>Manager notes</b><div class="note" style="white-space:pre-wrap">${esc(a.notes)}</div>` : ""}
  <script>window.onload=function(){setTimeout(function(){print()},300)}<\/script><\/body><\/html>`);
  w.document.close();
}
'''

def patch(s: str, sections: bool) -> str:
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    if sections and '["Job 1", [["e1_employer"' not in s:
        i = s.index('  ["Application", [["license","License"]'); j = s.index('\n', i) + 1
        s = s[:i] + SECTIONS + s[j:]
    if 'data-ap="print"' not in s:
        rep('''  return `<div class="mgr" style="display:flex;flex-direction:column;gap:14px">${secs.join("") || `<span class="meta">No answers saved.</span>`}</div>`;''',
            '''  return `<div class="mgr" style="display:flex;flex-direction:column;gap:14px"><button class="link" data-ap="print" data-id="${a.id}" style="align-self:flex-start">🖨 Print application</button>${secs.join("") || `<span class="meta">No answers saved.</span>`}</div>`;''')
        rep('''  if (act === "close") { apSched = null; apDel = null; return renderApps(); }''',
            '''  if (act === "print") { if (a) apPrint(a); return; }
  if (act === "close") { apSched = null; apDel = null; return renderApps(); }''')
        rep('/* ---------- employee handbook ---------- */', PRINT_JS + '\n/* ---------- employee handbook ---------- */')
    return s

if __name__ == '__main__':
    for p in sys.argv[1:]:
        p = pathlib.Path(p); p.write_text(patch(p.read_text(), sections='loopd-in' in str(p))); print('patched', p)
