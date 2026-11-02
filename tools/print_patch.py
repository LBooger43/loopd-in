"""Adds the print queue (top of the Daily log) to an app page: Salon Saia's index.html and Loopd-In's index.html.
The demo is built from Salon Saia's page, so it gets it from there."""
import pathlib, sys
HERE = pathlib.Path(__file__).parent
CSS = '.pr-drop{position:relative;display:block;border:2px dashed var(--line);border-radius:12px;padding:14px;text-align:center;cursor:pointer;background:var(--accent-soft, #f4f3fe)}.pr-drop.over{border-color:var(--accent)}\n'

def patch(s: str) -> str:
    if 'id="prBox"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    rep('      <form class="quick" id="dailyForm" style="display:flex">', (HERE / 'print_card.html').read_text() + '      <form class="quick" id="dailyForm" style="display:flex">')
    s = s.replace('</style>', CSS + '</style>', 1)
    rep('  await Promise.all([fetchRange("d"), fetchRange("l")]);\n',
        '  await Promise.all([fetchRange("d"), fetchRange("l")]);\n'
        '  const rpj = me && (me.role === "manager" || me.role === "front_desk") ? await sb.from("print_jobs").select("*").order("created_at", {ascending: false}).limit(300) : { data: [] };\n'
        '  prJobs = rpj.data || []; prReady = !rpj.error;\n')
    rep('.map(x => x.photo).concat(', '.map(x => x.photo).concat(prJobs.map(j => j.file_path), ')
    rep('function renderAll() { renderDaily();', 'function renderAll() { renderPrint(); renderDaily();')
    rep('/* ---------- employee handbook ---------- */', (HERE / 'print_card.js').read_text() + '\n/* ---------- employee handbook ---------- */')
    return s

if __name__ == '__main__':
    for p in sys.argv[1:]:
        p = pathlib.Path(p); p.write_text(patch(p.read_text())); print('patched', p)
