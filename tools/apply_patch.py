"""Adds the apply-page card and résumé links to an app page (used for Loopd-In's index.html and the demo build)."""
import re, pathlib
HERE = pathlib.Path(__file__).parent
BANNER = '<div class="banner">Managers only. Share your apply page below and applications land here automatically, résumés included. You can also add people by hand.</div>'
APP_SECTION = '  ["Application", [["avail_type","Available for"],["temp_date","If temporary, available"],["license","License"],["experience","Years in the industry"],["availability","Days and hours they can work"],["start","Could start"],["heard","Heard about us from"],["instagram","Instagram"],["address","Home address"],["phone2","Other phone"],["employed_now","Working somewhere now?"],["prev_employed","Worked here before?"],["prev_when","If yes, when"],["languages","Other languages"],["about","About them"]]],\n  ["Getting to work", [["drivers_license","Valid driver\'s license?"],["dl_exp","License expires"],["transportation","Own transportation?"],["reliable","Reliable?"]]],\n  ["Background", [["convicted","Convicted of a crime?"],["offense","Offense"],["offense_date","Date"],["substances","Controlled substance that could affect work?"]]],\n  ["Education and skills", [["cos_na","Cosmetology school"],["cos_name","Cosmetology school"],["cos_years","Years"],["cos_grad","Graduated?"],["hs_name","High school"],["hs_years","Years"],["hs_grad","Graduated?"],["college_na","College or other"],["college_name","College or other"],["college_years","Years"],["college_grad","Graduated?"],["training","Licenses, certificates and classes"],["software","Software"],["skills","Other skills"]]],\n  ["Job 1", [["no_jobs","No job history yet"],["e1_employer","Employer"],["e1_title","Job title"],["e1_dates","Dates"],["e1_phone","Phone"],["e1_address","Address"],["e1_duties","What they did"],["e1_supervisor","Supervisor / manager"],["e1_contact","May we contact them?"],["e1_reason","Reason for leaving"]]],\n  ["Job 2", [["e2_employer","Employer"],["e2_title","Job title"],["e2_dates","Dates"],["e2_phone","Phone"],["e2_address","Address"],["e2_duties","What they did"],["e2_supervisor","Supervisor / manager"],["e2_contact","May we contact them?"],["e2_reason","Reason for leaving"]]],\n  ["Job 3", [["e3_employer","Employer"],["e3_title","Job title"],["e3_dates","Dates"],["e3_phone","Phone"],["e3_address","Address"],["e3_duties","What they did"],["e3_supervisor","Supervisor / manager"],["e3_contact","May we contact them?"],["e3_reason","Reason for leaving"]]],\n  ["Job 4", [["e4_employer","Employer"],["e4_title","Job title"],["e4_dates","Dates"],["e4_phone","Phone"],["e4_address","Address"],["e4_duties","What they did"],["e4_supervisor","Supervisor / manager"],["e4_contact","May we contact them?"],["e4_reason","Reason for leaving"]]],\n  ["References", [["r1_name","Reference 1"],["r1_phone","Phone"],["r1_relation","How they know them"],["r2_name","Reference 2"],["r2_phone","Phone"],["r2_relation","How they know them"],["r3_name","Reference 3"],["r3_phone","Phone"],["r3_relation","How they know them"]]],\n  ["Signature", [["agree","Agreed to the statement"],["signature","Signed"],["signed_on","Date signed"]]],\n'

def patch(s: str, host_js: str, banner: str = BANNER) -> str:
    if 'id="applyBox"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    card = (HERE / 'apply_card.html').read_text()
    js = (HERE / 'apply_card.js').read_text()
    m = re.search(r'(<section id="view-apps"[^>]*>\n)\s*<div class="banner">Managers only\.[^<]*</div>\n', s)
    assert m, 'apps banner'
    s = s[:m.start()] + m.group(1) + '      ' + banner + '\n' + card + s[m.end():]
    rep('</head>', '<script src="qrcode.js" defer></script>\n</head>')
    rep('const AP_SECTIONS = [\n', 'const AP_SECTIONS = [\n' + APP_SECTION)
    rep('const extra = Object.keys(ans).filter(k => k !== "source" && !used.has(k));', 'const extra = Object.keys(ans).filter(k => k !== "source" && !used.has(k) && !/^resume_/.test(k));')
    rep('a.answers && a.answers.q193_instagramHandle ? `<span class="meta">IG ${esc(a.answers.q193_instagramHandle)}</span>` : ""',
        'a.answers && (a.answers.q193_instagramHandle || a.answers.instagram) ? `<span class="meta">IG ${esc(a.answers.q193_instagramHandle || a.answers.instagram)}</span>` : "", aplResumeBtn(a)')
    rep('New Jotform applications will show up here automatically.', 'Share your apply page and new applications show up here automatically.')
    rep('  for (const [tid, v] of Object.entries(keepN)) { const t = $(tid); if (t) t.value = v; }\n}',
        '  for (const [tid, v] of Object.entries(keepN)) { const t = $(tid); if (t) t.value = v; }\n  renderApplyCard(); aplResumeLinks();\n}')
    rep('/* ---------- employee handbook ---------- */', host_js.strip() + '\n' + js + '\n/* ---------- employee handbook ---------- */')
    return s

LOOPD_HOST = '''
const APPLY_HOST = {
  url: () => SALON && SALON.slug ? new URL("apply.html?s=" + encodeURIComponent(SALON.slug), location.href.split(/[?#]/)[0]).href : "",
  name: () => (SALON && SALON.name) || "our salon",
  get: () => { const s = (SALON && SALON.settings) || {}; return { open: s.apply_open !== false, background: !!s.apply_background, positions: s.apply_positions || ["Stylist", "Assistant", "Front desk"], intro: s.apply_intro || "" }; },
  save: async v => {
    const settings = { ...(SALON.settings || {}), apply_open: v.open, apply_background: !!v.background, apply_positions: v.positions, apply_intro: v.intro };
    const { error } = await sbRaw.rpc("lp_update_salon", { p_name: null, p_city: SALON.city, p_settings: settings, p_logo: null });
    if (error) return friendly(error);
    await loadSalon(); return null;
  },
};'''

DEMO_BANNER = BANNER.replace(' You can also add people by hand.', '')
DEMO_HOST = '''
const APPLY_HOST = {
  url: () => new URL("apply.html", location.href.split(/[?#]/)[0]).href,
  name: () => "Demo Salon",
  get: () => window.__demoApplyGet(),
  save: async v => { window.__demoApplySet(v); return null; },
};'''

if __name__ == '__main__':
    p = HERE.parent / 'index.html'
    p.write_text(patch(p.read_text(), LOOPD_HOST))
    print('patched', p)
