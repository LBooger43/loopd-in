"""When a manager taps Hired on an applicant, add a 'send a message to the team' reminder to the managers' to-do list."""
import pathlib, sys
OLD = '''  apSched = null; if (act === "note") $("foot").textContent = "Notes saved."; loadAll();
});'''
NEW = '''  if (act === "st" && row.status === "hired" && a.status !== "hired") {
    const who = a.name + (a.position ? ` (${a.position})` : "");
    await sb.from("todos").insert({ task: `Send a message to the team: welcome our new hire, ${who}`, created_by: me.email });
    $("foot").textContent = `Hired ✓ Added "Send a message to the team" to the managers' to-do list.`;
  }
  apSched = null; if (act === "note") $("foot").textContent = "Notes saved."; loadAll();
});'''
def patch(s):
    if 'welcome our new hire' in s: return s
    assert s.count(OLD) == 1, s.count(OLD)
    return s.replace(OLD, NEW)
if __name__ == '__main__':
    for p in map(pathlib.Path, sys.argv[1:]): p.write_text(patch(p.read_text())); print('patched', p)
