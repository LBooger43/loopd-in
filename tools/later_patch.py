"""Applicants: 'Save for later' keeps someone on file with a check-back date (1, 3 or 6 months) and flags them when it's time.
The check-back date is kept in interview_at (only used for interviews while status is 'interview')."""
import pathlib, sys

def patch(s: str) -> str:
    if 'later: ["Saved for later"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    rep('hired: ["Hired", "var(--ok)"], not_a_fit: ["Not a fit", "var(--muted)"],',
        'hired: ["Hired", "var(--ok)"], later: ["Saved for later", "#2f6be0"], not_a_fit: ["Not a fit", "var(--muted)"],')
    rep('<button type="button" data-apf="not_a_fit" aria-selected="false">Not a fit</button>',
        '<button type="button" data-apf="later" aria-selected="false">Saved for later</button><button type="button" data-apf="not_a_fit" aria-selected="false">Not a fit</button>')
    rep('let applicants = [], apFilter = "active", apOpen = null, apFull = null, apSched = null, apDel = null;',
        'let applicants = [], apFilter = "active", apOpen = null, apFull = null, apSched = null, apDel = null, apLater = null;\n'
        'const apDue = a => a.status === "later" && a.interview_at && new Date(a.interview_at) <= new Date();\n'
        'const apDay = iso => new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });')
    # the picker that opens when you tap Save for later
    rep('if (apSched === a.id) {',
        'if (apLater === a.id) {\n'
        '    actions = `<div class="fu-box"><b>Save ${esc(a.name || "them")} for later</b><span class="meta">They stay on file, and we\'ll remind you to check back.</span><div class="actions"><span class="meta">Check back in</span>${[1, 3, 6].map(m => `<button class="${m === 3 ? "primary" : "ghost"}" data-ap="later-save" data-m="${m}" data-id="${a.id}">${m} month${m > 1 ? "s" : ""}</button>`).join("")}<button class="link" data-ap="close">Cancel</button></div></div>`;\n'
        '  } else if (apSched === a.id) {')
    rep('data-st="not_a_fit" data-id="${a.id}">Not a fit</button>',
        'data-st="not_a_fit" data-id="${a.id}">Not a fit</button>${a.status !== "later" ? `<button class="link" data-ap="later" data-id="${a.id}">⏳ Save for later</button>` : ""}')
    rep('${a.status === "interview" && a.interview_at ? `<div><b>Interview ${esc(apWhen(a.interview_at))}</b></div>` : ""}',
        '${a.status === "interview" && a.interview_at ? `<div><b>Interview ${esc(apWhen(a.interview_at))}</b></div>` : ""}'
        '${a.status === "later" && a.interview_at ? (apDue(a) ? `<div class="fu-box" style="border-color:#2f6be0"><b>⏰ Time to check back with ${esc(a.name || "them")}</b><span class="meta">Saved for later until ${esc(apDay(a.interview_at))}. Give them a call, then move them back to Active or save them for later again.</span><div class="actions"><button class="link" data-ap="st" data-st="new" data-id="${a.id}">Move back to Active</button><button class="link" data-ap="later" data-id="${a.id}">⏳ Save for later again</button></div></div>` : `<div class="meta"><b>⏳ Check back ${esc(apDay(a.interview_at))}</b></div>`) : ""}')
    rep('const n = applicants.filter(a => a.status === "new").length;',
        'const n = applicants.filter(a => a.status === "new" || apDue(a)).length;\n'
        '  const dueN = applicants.filter(apDue).length, lb = $("apFilter").querySelector("[data-apf=later]"); if (lb) lb.textContent = dueN ? `Saved for later (${dueN} to check)` : "Saved for later";')
    rep('if (act === "close") { apSched = null; apDel = null; return renderApps(); }',
        'if (act === "close") { apSched = null; apDel = null; apLater = null; return renderApps(); }\n'
        '  if (act === "later") { apLater = id; apSched = null; apDel = null; return renderApps(); }')
    rep('if (act === "sched") { apSched = id; apDel = null; return renderApps(); }',
        'if (act === "sched") { apSched = id; apDel = null; apLater = null; return renderApps(); }')
    # saving: status 'later', check-back date in interview_at, and a history line
    rep('if (act === "st") { const st = b.dataset.st;',
        'if (act === "later-save") {\n'
        '    const m = +b.dataset.m, when = new Date(); when.setMonth(when.getMonth() + m); when.setHours(9, 0, 0, 0);\n'
        '    row = { status: "later", interview_at: when.toISOString(), log: entry("Saved for later", `Check back ${apDay(when.toISOString())}`) }; apLater = null;\n'
        '  }\n'
        '  if (act === "st") { const st = b.dataset.st;')
    # moving out of 'later' clears the check-back date
    rep('if (st === "new" || st === "not_a_fit" || st === "hired") row.interview_at = st === "hired" ? a.interview_at : null; }',
        'if (st === "new" || st === "not_a_fit" || st === "hired") row.interview_at = st === "hired" ? a.interview_at : null; if (a.status === "later") row.interview_at = null; }')
    rep('${a.interview_at ? "Reschedule interview" : "Schedule interview"}', '${a.interview_at && a.status !== "later" ? "Reschedule interview" : "Schedule interview"}')
    return s

if __name__ == '__main__':
    for p in map(pathlib.Path, sys.argv[1:]):
        p.write_text(patch(p.read_text())); print('patched', p)
