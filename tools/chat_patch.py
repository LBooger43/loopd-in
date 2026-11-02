"""Team chat replies + reactions, and the no-swearing message, for an app page (Salon Saia's and Loopd-In's index.html).
The demo is built from Salon Saia's page; its in-browser database gets the same rules from mock.js."""
import pathlib, sys

# One list of words, used by the database (Postgres: \\y = word edge) and the demo (JavaScript: \\b).
SWEAR_RE = (r"(f[u*@]+c?k\w*|\ysh[i1!*]t\w*|bullshit\w*|dipshit\w*|horseshit|\ybitch\w*|\yass(hole|holes|hat|es)\y|\yass\y(?!')|jackass\w*|dumbass\w*|smartass\w*"
            r"|\ybastards?\y|\y(god)?damn(ed|it)?\y|\ydickheads?\y|\ycocks?\y|\ypuss(y|ies)\y|\ycunts?\y|\ypiss(ed|ing|es)?\y|\ycrap(py|s)?\y|\ysluts?\y|\ywhores?\y|\ywtf\y|\ystfu\y)")
SWEAR_JS = SWEAR_RE.replace(r"\y", r"\b")
EMOJI = ["👍", "❤️", "😂", "🎉", "🙏", "👀"]

CSS = (".rx{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:4px}"
       ".rx button{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:3px 9px;font-size:.85rem;line-height:1.3;cursor:pointer;color:var(--ink)}"
       ".rx button.mine{border-color:var(--accent);background:var(--accent-soft,#ecebfc)}"
       ".rx .pick{display:inline-flex;gap:2px;border:1px solid var(--line);border-radius:999px;padding:1px 4px;background:var(--surface)}.rx .pick button{border:0;background:transparent;font-size:1.1rem;padding:3px 5px}"
       ".quoteline{border-left:3px solid var(--accent);background:var(--accent-soft,#ecebfc);border-radius:6px;padding:4px 8px;font-size:.85rem;color:var(--muted);margin:2px 0 4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}"
       ".replybar{display:flex;align-items:center;gap:8px;justify-content:space-between}\n")

JS = r'''
/* ---------- team chat: replies and reactions ---------- */
let chatReplyTo = null, chatPick = null;
const CHAT_EMOJI = __EMOJI__;
const snip = (s, n) => { s = String(s || "").replace(/\s+/g, " ").trim(); return s.length > n ? s.slice(0, n - 1) + "…" : s; };
function chatExtras(p, kind) {
  const rx = p.reactions || {}, key = kind + ":" + p.id;
  const chips = Object.keys(rx).filter(e => (rx[e] || []).length).map(e => {
    const who = rx[e], mine = who.includes(me.email);
    return `<button type="button" class="${mine ? "mine" : ""}" data-chat="react" data-kind="${kind}" data-id="${p.id}" data-e="${esc(e)}" title="${esc(who.map(nameOf).join(", "))}">${e} ${who.length}</button>`;
  }).join("");
  const pick = chatPick === key ? `<span class="pick">${CHAT_EMOJI.map(e => `<button type="button" data-chat="react" data-kind="${kind}" data-id="${p.id}" data-e="${e}" aria-label="React ${e}">${e}</button>`).join("")}</span>`
    : `<button type="button" data-chat="pick" data-key="${key}" aria-label="Add a reaction">☺︎ +</button>`;
  const reply = kind === "m" ? `<button type="button" data-chat="reply" data-id="${p.id}">↩ Reply</button>` : "";
  return `<div class="rx">${chips}${pick}${reply}</div>`;
}
function chatQuote(p) {
  if (!p.reply_to) return "";
  const o = msgs.find(x => x.id === p.reply_to);
  return `<div class="quoteline">↩ ${o ? `<b>${esc(nameOf(o.created_by))}</b>: ${esc(snip(o.body, 90))}` : "Replying to an earlier message"}</div>`;
}
function renderReplyBar() {
  const o = chatReplyTo && msgs.find(x => x.id === chatReplyTo);
  if (chatReplyTo && !o) chatReplyTo = null;
  $("replyBar").hidden = !o;
  if (o) $("replyBar").innerHTML = `<div class="quoteline" style="flex:1;margin:0">↩ Replying to <b>${esc(nameOf(o.created_by))}</b>: ${esc(snip(o.body, 70))}</div><button type="button" class="link" data-chat="reply-cancel">Cancel</button>`;
  $("msgText").placeholder = o ? `Reply to ${nameOf(o.created_by)}` : "Message the whole team";
}
'''

HANDLERS = r'''  if (a === "pick") { chatPick = chatPick === b.dataset.key ? null : b.dataset.key; return renderChat(); }
  if (a === "reply") { chatReplyTo = b.dataset.id; chatPick = null; renderChat(); $("msgText").focus(); return; }
  if (a === "reply-cancel") { chatReplyTo = null; return renderChat(); }
  if (a === "react") {
    chatPick = null; b.disabled = true;
    const { error } = await sb.rpc("chat_react", { p_kind: b.dataset.kind === "a" ? "a" : "m", p_id: b.dataset.id, p_emoji: b.dataset.e });
    if (error) { b.disabled = false; return alert(friendly(error)); }
    return loadAll();
  }
'''

FRIENDLY = ('  const sw = err && /NO_SWEARING:?\\s*(.*)/.exec(err.message || "");\n'
            '  if (sw) return `Let\'s keep it professional: please reword${sw[1] ? " “" + sw[1].trim() + "”" : " that"}. No swearing in team chat or notes.`;\n')

def patch(s: str) -> str:
    if 'id="replyBar"' in s:
        return s
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, f'{s.count(a)}x: {a[:80]!r}'
        s = s.replace(a, b)
    s = s.replace('</style>', CSS + '</style>', 1)
    rep('        <form id="msgForm" class="todo-add plain" style="flex-direction:row">',
        '        <div class="replybar" id="replyBar" hidden></div>\n        <form id="msgForm" class="todo-add plain" style="flex-direction:row">')
    # message rows: quoted reply above the text, reactions + reply under it
    rep('''    : `<p class="note">${esc(p.body)}</p>${photoHtml(p.photo)}${(edit || del) ? `<div class="actions">${edit}${del}</div>` : ""}`;''',
        '''    : `${kind === "m" ? chatQuote(p) : ""}<p class="note">${esc(p.body)}</p>${photoHtml(p.photo)}${chatExtras(p, kind)}${(edit || del) ? `<div class="actions">${edit}${del}</div>` : ""}`;''')
    rep('''  $("msgFeed").innerHTML = msgs.length ? msgs.map(m => postRow(m, "m")).join("") : `<div class="meta">No messages yet. Say hi to the team.</div>`;''',
        '''  $("msgFeed").innerHTML = msgs.length ? msgs.map(m => postRow(m, "m")).join("") : `<div class="meta">No messages yet. Say hi to the team.</div>`;
  renderReplyBar();''')
    rep('''$("msgForm").addEventListener("submit", e => { e.preventDefault(); quickPost("msgText", "msgErr", "messages", body => ({ body, created_by: me.email }), "msg", "chat"); });''',
        '''$("msgForm").addEventListener("submit", async e => {
  e.preventDefault();
  const rt = chatReplyTo;
  await quickPost("msgText", "msgErr", "messages", body => ({ body, created_by: me.email, ...(rt ? { reply_to: rt } : {}) }), "msg", "chat");
  if (!$("msgText").value) { chatReplyTo = null; renderReplyBar(); }
});''')
    rep('''  const b = e.target.closest("[data-chat]"); if (!b) return;
  const a = b.dataset.chat;
''', '''  const b = e.target.closest("[data-chat]"); if (!b) return;
  const a = b.dataset.chat;
''' + HANDLERS)
    rep('function friendly(err) {', 'function friendly(err) {\n' + FRIENDLY)
    rep('/* ---------- employee handbook ---------- */', JS.replace('__EMOJI__', str(EMOJI).replace("'", '"')) + '\n/* ---------- employee handbook ---------- */')
    return s

if __name__ == '__main__':
    for p in sys.argv[1:]:
        p = pathlib.Path(p); p.write_text(patch(p.read_text())); print('patched', p)
