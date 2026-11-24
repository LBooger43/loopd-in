/* Sample data for the Loopd-In restaurant demo. Dates are relative to today so the demo always looks current. */
window.__demoSeed = function (ME) {
  const pad = n => String(n).padStart(2, "0");
  const iso = d => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  const day = n => { const d = new Date(); d.setDate(d.getDate() - n); return iso(d); };      // n days ago (negative = future)
  const ts = (n, h, m) => { const d = new Date(); d.setDate(d.getDate() - n); d.setHours(h, m || 0, 0, 0); return d.toISOString(); };
  const ym = n => { const d = new Date(); d.setDate(1); d.setMonth(d.getMonth() - n); return d.getFullYear() + "-" + pad(d.getMonth() + 1); };
  const yr = String(new Date().getFullYear());
  const E = n => n + "@demokitchen.example";
  const SAM = E("sam"), RILEY = E("riley"), CASEY = E("casey"), MAYA = E("maya"), AVA = E("ava"), LILY = E("lily"), NOAH = E("noah"), EMMA = E("emma");
  let i = 0; const id = p => p + "-" + (++i);

  // role keys stay the app's own: front_desk = shift lead, stylist = team member
  const staff = [
    { email: ME, name: "Jordan Lee", role: "manager" },
    { email: SAM, name: "Sam Patel", role: "manager" },
    { email: RILEY, name: "Riley Brooks", role: "front_desk" },
    { email: CASEY, name: "Casey Nguyen", role: "front_desk" },
    { email: MAYA, name: "Maya Torres", role: "stylist" },
    { email: AVA, name: "Ava Johnson", role: "stylist", also_desk: true },
    { email: LILY, name: "Lily Chen", role: "stylist" },
    { email: NOAH, name: "Noah Kim", role: "stylist" },
    { email: EMMA, name: "Emma Davis", role: "stylist" },
  ];

  const dl = (n, time, category, note, by, extra) => ({ id: id("dl"), entry_date: day(n), entry_time: time, category, note, created_by: by, created_at: ts(n, +time.slice(0, 2), +time.slice(3)), needs_followup: false, deleted_at: null, ...(extra || {}) });
  const cooler = dl(0, "15:05", "Maintenance", "Walk-in cooler read 43°F at 3pm. Moved the fish to the reach-in and called the repair company. Checking it again at 4.", RILEY, { needs_followup: true });
  const rep = dl(0, "14:10", "Visitor", "Beer rep dropped off samples of two new seasonal drafts. They're in the office for Jordan to try.", CASEY);
  const inspect = dl(1, "16:45", "Reminder", "Health inspection window opens next week. Temp logs and the sanitizer log need to be up to date.", RILEY, { needs_followup: true });
  const pie = dl(1, "20:10", "86'd", "86 key lime pie. Sold the last slice at 8.", RILEY);
  const allergy = dl(0, "11:40", "Phone call", "Mr. Alvarez called: shellfish allergy, reservation tonight at 7:30, table 9. Maya has that section.", RILEY);
  const daily_log = [
    dl(0, "09:10", "Delivery", "Sysco order in. Short 1 case of romaine; credit memo signed and on the office desk.", RILEY),
    allergy, rep, cooler,
    dl(0, "17:45", "86'd", "86 short rib. Kitchen is out until tomorrow's prep.", CASEY),
    dl(0, "18:20", "86'd", "86 Sauvignon Blanc by the glass until Thursday's delivery. Pinot Grigio is the swap.", CASEY),
    dl(0, "19:15", "Guest", "Guest at table 12 left a credit card. Locked in the office safe with a note.", RILEY),
    pie, inspect,
    dl(1, "22:40", "General", "Big night: 212 covers. Kitchen closed clean, drawer balanced. Thanks all!", RILEY),
    dl(2, "12:30", "Phone call", "Party of 14 Saturday at 7 for a birthday. Put them in the back room; they want the prix fixe.", CASEY),
    dl(3, "10:20", "Supplies", "Low on fryer oil and large to-go containers. Added both to Supplies.", RILEY),
  ];
  const followups = [
    { log_id: cooler.id, flagged: true, done: false, note: "", updated_by: RILEY, updated_at: ts(0, 15, 6) },
    { log_id: inspect.id, flagged: true, done: true, note: "Sam went through the logs. All caught up.", updated_by: SAM, updated_at: ts(1, 17, 30) },
    { log_id: pie.id, flagged: false, done: true, note: "Back on: fresh pies made this morning.", updated_by: SAM, updated_at: ts(0, 10, 0) },
  ];
  const staff_alerts = [{ id: id("sa"), to_email: MAYA, note: allergy.note, log_id: allergy.id, created_by: RILEY, created_at: ts(0, 11, 41), done_at: ts(0, 16, 5) }];
  const cash_outs = [
    { id: id("co"), close_date: day(0), note: "Bar drawer over $12. Recounted twice. Probably a cash tip that went in the drawer.", created_by: CASEY, created_at: ts(0, 23, 5) },
    { id: id("co"), close_date: day(1), note: "Both drawers balanced. Deposit bag is in the safe.", created_by: RILEY, created_at: ts(1, 23, 2), reviewed_by: SAM, reviewed_at: ts(0, 9, 0), mgr_note: "Thanks Riley!" },
  ];
  const log_replies = [{ id: id("rp"), log_id: rep.id, note: "Thanks! I'll try them before pre-shift.", created_by: ME, created_at: ts(0, 14, 40) }];

  const inc = (n, client, stylist, issue_type, severity, note, by) => ({ id: id("in"), client, stylist, issue_type, incident_date: day(n), severity, note, created_by: by, created_at: ts(n, 21, 0), deleted_at: null });
  const i1 = inc(1, "Karen M.", "Maya Torres", "Food complaint", "med", "Ordered her steak medium-rare; it came out medium. Refired right away and Jordan stopped by the table. Comped dessert.", RILEY);
  const i2 = inc(5, "Tom R.", "Lily Chen", "No-show / late cancel", "low", "No-show for a party of 8 on Friday. Third time this year. Hosts will hold large parties with a card next time.", CASEY);
  const i3 = inc(9, "Denise P.", "Noah Kim", "Allergy concern", "high", "Guest with a sesame allergy found sesame seeds on her bowl. No reaction. Sam pulled the garnish from that dish and went over allergy tickets with the line.", SAM);
  const incidents = [i1, i2, i3];
  const resolutions = [
    { incident_id: i2.id, done: true, note: "Card-hold note added to his reservation profile.", updated_by: CASEY, updated_at: ts(4, 10, 0) },
    { incident_id: i3.id, done: true, note: "Called her the next day; she thanked us and came back Sunday.", updated_by: SAM, updated_at: ts(7, 13, 0) },
  ];

  const staff_notes = [
    { id: id("sn"), staff_member: "Noah Kim", note_type: "Late arrival", note_date: day(2), note_time: "16:20", note: "Arrived 20 minutes late for a 4:00 line shift, right before the rush. Said traffic. Second time this month.", created_by: SAM, created_at: ts(2, 16, 25) },
    { id: id("sn"), staff_member: "Ava Johnson", note_type: "Praise", note_date: day(4), note_time: null, note: "A guest left a 5-star review naming Ava for her cocktails and recommendations.", created_by: ME, created_at: ts(4, 12, 0) },
    { id: id("sn"), staff_member: "Lily Chen", note_type: "Called out / sick", note_date: day(6), note_time: "14:45", note: "Called Jordan before her shift. Emma covered the host stand.", created_by: ME, created_at: ts(6, 14, 50) },
  ];

  const items = [["Bar", "Limes"], ["Bar", "Lemons"], ["Bar", "Simple syrup"], ["Bar", "Cocktail napkins"], ["Bar", "Straws"],
    ["Kitchen", "Fryer oil"], ["Kitchen", "To-go containers (large)"], ["Kitchen", "Foil"], ["Kitchen", "Gloves (L)"],
    ["Front of house", "Receipt paper"], ["Front of house", "Kids' crayons"], ["Front of house", "Check presenters"],
    ["Cleaning", "Sanitizer test strips"], ["Cleaning", "Paper towels"], ["Cleaning", "Trash bags"]];
  const supply_items = items.map(([category, name], k) => ({ id: id("si"), category, name, sort: k + 1, active: true }));
  const item = n => supply_items.find(s => s.name === n);
  const need = (n, by, d, bought) => { const it = item(n); return { id: id("sn"), item_id: it.id, item_name: it.name, category: it.category, requested_by: by, requested_at: ts(d, 10, 0), bought: !!bought, bought_by: bought ? SAM : null, bought_at: bought ? ts(d - 1, 15, 0) : null }; };
  const supply_needs = [need("Fryer oil", RILEY, 3), need("To-go containers (large)", RILEY, 3), need("Limes", CASEY, 0), need("Paper towels", MAYA, 4, true)];

  const todos = [
    { id: id("td"), task: "Follow up with the repair company about the walk-in cooler", done: false, created_by: ME, created_at: ts(0, 15, 30) },
    { id: id("td"), task: "Dish machine is leaking under the door", reported: true, done: false, created_by: NOAH, created_at: ts(1, 21, 0) },
    { id: id("td"), task: "Order new host stand menus", done: true, done_by: SAM, done_at: ts(3, 12, 0), created_by: SAM, created_at: ts(5, 9, 0) },
  ];
  const manager_log = [
    { id: id("ml"), note: "Talked to the landlord about the parking lot lights. They're fixing them next week.", created_by: ME, created_at: ts(1, 15, 0) },
    { id: id("ml"), note: "Holiday menu approved. Starts the 1st; staff tasting Thursday at 3.", created_by: SAM, created_at: ts(3, 11, 0) },
  ];
  const announcements = [
    { id: id("an"), body: "Pre-shift at 4:30 tonight: features are seared scallops and pumpkin cheesecake. Push the new fall cocktail!", created_by: ME, created_at: ts(0, 13, 0), reactions: { "👍": [MAYA, AVA, LILY], "🔥": [NOAH] } },
    { id: id("an"), body: "Great weekend, everyone: 1,040 covers and a 4.8 review average. Thank you!", created_by: SAM, created_at: ts(3, 23, 0), reactions: { "🎉": [MAYA, EMMA, AVA], "❤️": [RILEY] } },
  ];
  const m1 = id("ms"), m2 = id("ms"), m3 = id("ms"), m4 = id("ms"), m5 = id("ms");
  const messages = [
    { id: m1, body: "Can anyone pick up my Thursday double? Family thing.", created_by: MAYA, created_at: ts(0, 10, 2), reactions: { "🙏": [RILEY] } },
    { id: m2, body: "I can take the night half!", created_by: LILY, created_at: ts(0, 10, 4), reply_to: m1 },
    { id: m3, body: "I'll take lunch", created_by: EMMA, created_at: ts(0, 10, 6), reply_to: m2, reactions: { "👍": [MAYA, RILEY] } },
    { id: m4, body: "Who moved the fish spatulas? 😅", created_by: NOAH, created_at: ts(0, 12, 30) },
    { id: m5, body: "Guilty. They're drying in the dish pit!", created_by: AVA, created_at: ts(0, 12, 33), reply_to: m4, reactions: { "😂": [NOAH, MAYA] } },
  ];

  const time_off = [
    { id: id("to"), off_from: day(-10), back_on: day(-14), note: "Family wedding in Charleston", created_by: AVA, role: "stylist", status: "pending", created_at: ts(2, 9, 0) },
    { id: id("to"), off_from: day(-11), back_on: day(-13), note: "Long weekend", created_by: EMMA, role: "stylist", status: "pending", created_at: ts(1, 9, 0) },
    { id: id("to"), off_from: day(-3), back_on: day(-6), note: "", created_by: NOAH, role: "stylist", status: "approved", decided_by: SAM, decided_at: ts(8, 10, 0), created_at: ts(10, 9, 0) },
  ];

  const oMaya = { id: id("oo"), created_by: MAYA, with_manager: ME, req_date: day(-2), req_time: "14:00:00", meet_date: day(-2), meet_time: "14:00:00", topic: "Becoming a server trainer", status: "confirmed", decided_by: ME, decided_at: ts(1, 9, 0), created_at: ts(2, 8, 0) };
  const oNoah = { id: id("oo"), created_by: NOAH, with_manager: SAM, req_date: day(25), req_time: "15:00:00", meet_date: day(25), meet_time: "15:00:00", topic: "Moving up to grill station", status: "done", decided_by: SAM, decided_at: ts(27, 9, 0), created_at: ts(28, 9, 0) };
  const one_on_ones = [
    oMaya,
    { id: id("oo"), created_by: LILY, with_manager: null, req_date: day(-4), req_time: "14:00:00", topic: "Moving from host to server", status: "pending", created_at: ts(0, 8, 30) },
    { id: id("oo"), created_by: EMMA, with_manager: ME, req_date: day(-1), req_time: "15:00:00", meet_date: day(-3), meet_time: "15:30:00", topic: "Schedule change", manager_note: "Tomorrow is slammed. Does this time work?", status: "proposed", decided_by: ME, decided_at: ts(0, 13, 0), created_at: ts(1, 11, 0) },
    oNoah,
  ];
  const goal_sheets = [
    { id: id("gs"), created_by: MAYA, kind: "monthly", period: ym(0), one_on_one_id: oMaya.id, updated_at: ts(0, 21, 0), data: { professional: "Sell a dessert or after-dinner drink at 2 of every 5 tables\nPass the wine level 1 test", personal: "Run 3 times a week", days: "5", service_month: "32000", service_week: "8000", service_day: "1600", retail_month: "4000", retail_week: "1000", retail_day: "200", notes: "Want to talk about training new servers." } },
    { id: id("gs"), created_by: MAYA, kind: "smart", period: yr, one_on_one_id: oMaya.id, updated_at: ts(0, 21, 5), data: { m3: "Become a server trainer", m6: "Train 3 new servers", m12: "Move up to shift lead" } },
    { id: id("gs"), created_by: MAYA, kind: "monthly", period: ym(1), one_on_one_id: null, updated_at: ts(32, 20, 0), data: { professional: "Learn every wine on the list", service_month: "30000", service_week: "7500", retail_month: "3500", notes: "Hit 108% of goal!" } },
    { id: id("gs"), created_by: NOAH, kind: "monthly", period: ym(1), one_on_one_id: oNoah.id, updated_at: ts(26, 20, 0), data: { professional: "Clock in by 3:50 every shift\nLearn the grill station", personal: "Start a savings plan", days: "5" } },
  ];

  const ans = o => o;
  const applicants = [
    { id: id("ap"), submission_id: "demo-1", name: "Jasmine Ortiz", position: "Server", phone: "(919) 555-0142", email: "jasmine@example.com", status: "new", submitted_at: ts(0, 8, 50), log: [], answers: ans({ q3_positionsApplied: "Server", q5_name: "Jasmine Ortiz", q191_email: "jasmine@example.com", q9_cell: "(919) 555-0142", q10_areYou10: "Full Time", q55_employer: "Main Street Bistro", q159_jobTitle159: "Server", q136_reasonFor136: "Looking for more hours" }) },
    { id: id("ap"), submission_id: "demo-2", name: "Brooke Lane", position: "Host", phone: "(919) 555-0177", email: "brooke@example.com", status: "no_answer", submitted_at: ts(3, 13, 0), answers: ans({ q3_positionsApplied: "Host", q5_name: "Brooke Lane", q10_areYou10: "Part Time", q17_whatLanguages: "Spanish" }),
      log: [{ what: "Called – no answer", by: RILEY, at: ts(2, 14, 15) }, { what: "Called – no answer", by: ME, at: ts(1, 10, 5) }] },
    { id: id("ap"), submission_id: "demo-3", name: "Mia Chen", position: "Line cook, Prep cook", phone: "(984) 555-0110", email: "mia@example.com", status: "interview", interview_at: ts(-2, 14, 0), submitted_at: ts(5, 18, 0), notes: "Culinary school grad. Worked sauté at a busy brunch spot.",
      answers: ans({ q3_positionsApplied: "Line cook, Prep cook", q5_name: "Mia Chen", q10_areYou10: "Full Time", q55_employer: "Sunny Side Brunch", q159_jobTitle159: "Line cook", q136_reasonFor136: "Want to work dinner service" }),
      log: [{ what: "Spoke to", by: SAM, at: ts(4, 16, 0) }, { what: "Interview scheduled", by: SAM, at: ts(4, 16, 2) }] },
    { id: id("ap"), submission_id: "demo-4", name: "Daniel Reyes", position: "Dishwasher", phone: "(919) 555-0188", email: "daniel@example.com", status: "hired", submitted_at: ts(20, 12, 0), answers: ans({ q3_positionsApplied: "Dishwasher", q5_name: "Daniel Reyes" }), log: [{ what: "Spoke to", by: SAM, at: ts(19, 10, 0) }, { what: "Hired", by: SAM, at: ts(12, 16, 0) }] },
  ];

  const staff_writeups = [
    { id: id("wu"), staff_member: "Noah Kim", incident_date: day(2), category: "Attendance", level: "Documented verbal warning", policy: "Punctuality",
      description: "Arrived at 4:20 for a 4:00 line shift, right before the dinner rush. Second late arrival this month (also on the 3rd).",
      notes: "Noah said traffic on I-40. We talked about leaving earlier.", action_plan: "Clock in by 3:50 for every shift for the next 30 days. Another late arrival in that time moves to a written warning.",
      actions: [{ task: "Clock in by 3:50 every shift for 30 days", due: day(-28), done: false }, { task: "Check in with Sam at 2 weeks", due: day(-12), done: false }],
      review_date: day(-28), witnesses: null, created_by: SAM, created_at: ts(2, 22, 0) },
  ];

  const print_jobs = [
    { id: id("pr"), title: "Holiday menu insert", file_path: "print/demo-flyer.png", file_name: "Holiday menu.png", file_type: "image/png", copies: 60, paper: "Cardstock",
      due_kind: "open", due_date: day(0), note: "One in every menu before lunch. Extras at the host stand.", status: "pending", created_by: ME, created_at: ts(1, 20, 15) },
    { id: id("pr"), title: "Trivia night table tents", file_path: "print/demo-sign.png", file_name: "Trivia night.png", file_type: "image/png", copies: 25, paper: "Cardstock",
      due_kind: "day", due_date: day(-2), note: "Fold in half, one on every table and the bar.", status: "pending", created_by: ME, created_at: ts(0, 7, 40) },
    { id: id("pr"), title: "Kids' coloring menus", file_path: "print/demo-flyer.png", file_name: "Kids menu.png", file_type: "image/png", copies: 50, paper: "Regular paper",
      due_kind: "open", due_date: day(2), note: null, status: "printed", printed_by: RILEY, printed_at: ts(2, 10, 10), created_by: ME, created_at: ts(3, 21, 0) },
  ];

  return {
    print_jobs, staff, daily_log, followups, staff_alerts, cash_outs, log_replies, incidents, resolutions, staff_notes, supply_items, supply_needs, todos, manager_log,
    announcements, messages, time_off, one_on_ones, goal_sheets, applicants, staff_writeups, handbook_versions: [], push_subs: [],
    _handbooks: [{ name: "Demo_Kitchen_and_Bar_Handbook.pdf", created_at: ts(14, 12, 0), seed: true }],
    _fileMap: { "print/demo-flyer.png": "demo-flyer.png", "print/demo-sign.png": "demo-sign.png" },
  };
};
