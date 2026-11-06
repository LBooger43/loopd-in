"""Adds the apply-page card and résumé links to an app page (used for Loopd-In's index.html and the demo build)."""
import re, pathlib
HERE = pathlib.Path(__file__).parent
BANNER = '<div class="banner">Managers only. Share your apply page below and applications land here automatically, résumés included. You can also add people by hand.</div>'
APP_SECTION = '  ["Application", [["license","License"],["experience","Years in the industry"],["availability","Days and hours they can work"],["start","Could start"],["instagram","Instagram"],["heard","Heard about us from"],["about","About them"]]],\n'

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
  get: () => { const s = (SALON && SALON.settings) || {}; return { open: s.apply_open !== false, positions: s.apply_positions || ["Stylist", "Assistant", "Front desk"], intro: s.apply_intro || "" }; },
  save: async v => {
    const settings = { ...(SALON.settings || {}), apply_open: v.open, apply_positions: v.positions, apply_intro: v.intro };
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
