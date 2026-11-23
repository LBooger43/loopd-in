"""Levels preview for the demo build (no plans or Help button in the demo)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import levels_patch as L

def patch(s: str) -> str:
    if 'id="view-levels"' in s: return s
    hide_old = '$("tab-time").hidden = !tabAllowed("time"); $("tab-oo").hidden = !tabAllowed("oo");\n'
    s = s.replace('$("tab-apps").hidden = !isMgr();', '$("tab-apps").hidden = !isMgr(); $("tab-levels").hidden = !isMgr(); renderLevels();', 1)
    js = L.JS.replace('''$("lvWant").onclick = () => { $("help-msg").value = "We'd like Levels for our salon when it's ready! Our level system works like this: "; $("helpBtn").click(); };''',
        '''$("lvWant").onclick = () => { $("foot").textContent = "Levels is coming soon. Ask the Loopd-In team to save you a spot!"; $("foot").scrollIntoView({ behavior: "smooth" }); };''')
    assert js != L.JS
    orig_js, L.JS = L.JS, js
    try:
        s = L.patch(s.replace('</style>', '</style>', 1)) if hide_old in s else _patch_no_hide(s, L)
    finally:
        L.JS = orig_js
    return s

def _patch_no_hide(s, L):
    # same as levels_patch.patch, minus the plan-gating line the demo doesn't have
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    rep('      <button role="tab" id="tab-staff" class="priv"', L.TAB + '      <button role="tab" id="tab-staff" class="priv"')
    rep('    <section id="view-apps" hidden', L.SECTION + '    <section id="view-apps" hidden')
    rep('const TABS = ["daily", "log", "supplies", "cash", "chat", "time", "oo", "apps", "staff", "team"];',
        'const TABS = ["daily", "log", "supplies", "cash", "chat", "time", "oo", "apps", "levels", "staff", "team"];')
    rep('if ((t === "staff" || t === "team" || t === "apps") && !isMgr()) t = "daily";',
        'if ((t === "staff" || t === "team" || t === "apps" || t === "levels") && !isMgr()) t = "daily";')
    s = s.replace('</style>', L.CSS + '</style>', 1)
    rep('/* ---------- employee handbook ---------- */', L.JS + '\n/* ---------- employee handbook ---------- */')
    return s

if __name__ == '__main__':
    for p in map(pathlib.Path, sys.argv[1:]): p.write_text(patch(p.read_text())); print('patched', p)
