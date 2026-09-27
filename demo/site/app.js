// Organizer console (T06, redesigned in T35). Talks only to the JSON API in api/main.py; shapes are
// the dataclasses of bureau/core/models.py.

const ui = {
  summaries: {},      // event id -> last summary {id, name, counts, issues, actions, travel, logistics, records, meta}
  current: null,      // selected event id
  sel: {},            // event id -> selected key ("issue:<id>" or "action:<id>")
  drafts: {},         // action id -> organizer-edited reply text
  view: "issue",      // "issue", "outbox" or "compose"
  outbox: [],
  doneOpen: false,
  open: {},           // collapsible section id -> open (kept across renders)
  busy: false,
  running: null,      // issue id the agent is investigating right now
  runStart: null,     // when the current agent call started (thinking panel)
  reveal: null,       // action id whose agent steps are revealed one by one on next render
  stopRequested: false,
};

const $ = s => document.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const TERMINAL = ["resolved", "dismissed"];
const APPROVE_LABEL = { LINK_PAYMENT: "Confirm and link", SEND_MESSAGE: "Approve and send", ESCALATE: "Mark as handled" };
const PILL = {
  new: ["p-new", "Not analysed"], proposed: ["p-proposed", "Action proposed"], human: ["p-human", "Needs you"],
  waiting: ["p-wait", "Waiting"], running: ["p-run", "Running…"], failed: ["p-fail", "Agent failed"], resolved: ["p-res", "Resolved"], dismissed: ["p-rej", "Dismissed"],
};

const demoStore = createDemoStore(window.DEMO_FIXTURES);
ui.drafts = demoStore.drafts();
async function api(path, options = {}) { const sessionId = demoStore.sessionInfo().id; try { return demoStore.request(path, options); } finally { if (demoStore.sessionInfo().id !== sessionId) restoreSessionUI(); refreshSessionNotice(); } }

function replayLabel(reason) {
  return reason === "live limit reached" ? "Saved example (live limit reached)" : "Saved example (" + (reason || "replay") + ")";
}

function replayBadge(action) {
  return action?.payload?.replay ? `<p class="demo-status">${esc(replayLabel(action.payload.replay_reason))}</p>` : "";
}

function setRun(text, mode = "") {
  $("#runText").textContent = text;
  $("#run").className = `run ${mode}`;
}

// ---------- derived state ----------

function summary(id = ui.current) { return ui.summaries[id]; }

function actionsByIssue(s) {
  const map = {};
  for (const a of s.actions) map[a.issue_id] = a;   // the latest proposal wins
  return map;
}

// A proposal whose issue is no longer detected was applied and fixed the data.
function vanishedActions(s) {
  const ids = new Set(s.issues.map(i => i.id));
  return s.actions.filter(a => !ids.has(a.issue_id));
}

function isWaiting(issue, s) {
  return issue.depends_on.some(dep => {
    const d = s.issues.find(i => i.id === dep);
    return d && !TERMINAL.includes(d.status);
  });
}

// Everything needs approval; "needs you" marks a decision the agent could not make:
// an escalation, or an identity link in the ask-a-human band (score < 0.98).
function needsHuman(action) {
  return action.action_type === "ESCALATE" ||
    (action.action_type === "LINK_PAYMENT" && action.confidence != null && action.confidence < 0.98);
}

function viewStatus(issue, s, byIssue) {
  if (issue.status === "resolved") return "resolved";
  if (issue.status === "dismissed") return "dismissed";
  if (issue.status === "agent_failed") return "failed";
  if (isWaiting(issue, s)) return "waiting";
  const action = byIssue[issue.id];
  if (!action) return "new";
  return needsHuman(action) ? "human" : "proposed";
}

function cardCounts(s) {
  const byIssue = actionsByIssue(s);
  const statuses = s.issues.map(i => viewStatus(i, s, byIssue));
  return {
    blocking: s.counts.blocking,
    nonBlocking: s.counts.non_blocking,
    review: statuses.filter(st => st === "proposed" || st === "human").length,
    resolved: statuses.filter(st => st === "resolved").length + vanishedActions(s).length,
  };
}

// ---------- rendering ----------

// Inline icons (Feather-style strokes), one per issue kind.
const ICON_PATHS = {
  payment: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
  unpaid: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
  team: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
  message: '<path d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/><path d="M22 6l-10 7L2 6"/>',
  trip: '<rect x="4" y="3" width="16" height="16" rx="2"/><path d="M4 11h16M12 3v8M8 19l-2 3M16 19l2 3"/><circle cx="8.5" cy="15" r="1"/><circle cx="15.5" cy="15" r="1"/>',
  rooms: '<path d="M2 4v16M2 8h18a2 2 0 0 1 2 2v10M2 17h20"/><path d="M6 8v9"/>',
  other: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>',
};
const KIND_ICON = {
  unmatched_payment: "payment", unpaid_membership: "unpaid", unpaid_participation: "unpaid",
  multiple_group_membership: "team", group_over_capacity: "team", solo_participants: "team",
  unprocessed_message: "message", no_logistics_plan: "trip", rooms_unassigned: "rooms",
};
const KIND_LABEL = {
  unmatched_payment: "Payment", unpaid_membership: "Unpaid fees", unpaid_participation: "Unpaid fees",
  multiple_group_membership: "Team rule", group_over_capacity: "Team size", solo_participants: "Team matching",
  unprocessed_message: "Message", no_logistics_plan: "Trip planning", rooms_unassigned: "Rooms",
};
const ACTION_LABEL = {
  LINK_PAYMENT: "Link a payment", SEND_MESSAGE: "Send a reply", ESCALATE: "Ask the organizers",
  MOVE_MEMBER: "Move a team member", UPDATE_GROUPS: "Update the groups", SELECT_TRAVEL_PLAN: "Choose a travel plan",
};
const icon = kind => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
  stroke-linejoin="round" aria-hidden="true">${ICON_PATHS[KIND_ICON[kind] || "other"]}</svg>`;

function renderEvents() {
  $("#events").innerHTML = Object.values(ui.summaries).map(s =>
    `<button class="evtab" type="button" role="tab" data-ev="${esc(s.id)}" aria-selected="${ui.current === s.id}">
      <b>${esc(s.name)}</b><span>${esc(eventMeta(s))}</span></button>`).join("");
  const s = summary();
  if (!s) return;
  const c = cardCounts(s);
  const waiting = s.issues.filter(i => !TERMINAL.includes(i.status) && isWaiting(i, s)).length;
  const kpi = (cls, v, k) => `<div class="kpi ${cls} ${v === 0 ? "zero" : ""}"><span class="v">${v}</span><span class="k">${k}</span></div>`;
  $("#kpis").innerHTML = kpi("k-block", c.blocking, "blocking") + kpi("k-review", c.review, "ready for your review") +
    kpi("k-wait", waiting, "waiting on another issue") + kpi("k-done", c.resolved, "resolved");
}

function eventMeta(s) {
  const m = s.meta || {};
  const people = s.travel ? `${s.travel.participants} travelling` : `${m.participants ?? "?"} registered`;
  return [m.type, m.dates, m.place, people].filter(Boolean).join(" · ");
}

function issueMeta(issue) {
  if (issue.details && issue.details.text) {
    const t = issue.details.text;
    return t.length > 110 ? `${t.slice(0, 110)}…` : t;
  }
  const r = (summary() && summary().records) || {};
  const names = (issue.subject_ids || []).map(id => (r.payments || {})[id] || (r.participants || {})[id] || (r.groups || {})[id]).filter(Boolean);
  if (names.length) return names.slice(0, 3).join(", ") + (names.length > 3 ? ` +${names.length - 3}` : "");
  return KIND_LABEL[issue.kind] || issue.kind;
}

const LEGEND = ["new", "human", "proposed", "waiting", "resolved"];

function renderIssues() {
  const s = summary();
  const byIssue = actionsByIssue(s);
  const sel = ui.sel[ui.current];
  const row = issue => {
    const st = ui.running === issue.id ? "running" : viewStatus(issue, s, byIssue);
    const [cls, label] = PILL[st];
    return `<button class="issue ${issue.blocking ? "blocking" : ""} ${TERMINAL.includes(st) ? "res" : ""}" type="button"
        data-key="issue:${esc(issue.id)}" aria-current="${ui.view === "issue" && sel === `issue:${issue.id}`}">
      <span class="ico">${icon(issue.kind)}</span>
      <span><span class="t">${esc(issue.title)}</span><span class="m">${esc(issueMeta(issue))}</span></span>
      <span class="chip ${cls}">${label}</span></button>`;
  };
  const doneRow = a => `<button class="issue res" type="button" data-key="action:${esc(a.id)}"
        aria-current="${ui.view === "issue" && sel === `action:${a.id}`}">
      <span class="ico">${icon((s.issues.find(i => i.id === a.issue_id) || {}).kind || "")}</span>
      <span><span class="t">${esc(a.title)}</span><span class="m">${esc(ACTION_LABEL[a.action_type] || a.action_type)}</span></span>
      <span class="chip p-res">Resolved</span></button>`;

  const open = s.issues.filter(i => !TERMINAL.includes(i.status));
  const blocking = open.filter(i => i.blocking), nonBlocking = open.filter(i => !i.blocking);
  const doneIssues = s.issues.filter(i => TERMINAL.includes(i.status));
  const vanished = vanishedActions(s);
  const doneCount = doneIssues.length + vanished.length;
  const group = (label, items) => `<div class="grouphead"><span>${label}</span><span>${items.length}</span></div>
    ${items.length ? items.map(row).join("") : '<p class="note empty">Nothing here.</p>'}`;
  const legend = `<div class="legend" aria-label="Status legend">${LEGEND.map(k =>
    `<span class="chip ${PILL[k][0]}">${PILL[k][1]}</span>`).join("")}</div>`;

  $("#issues").innerHTML = legend + group("Blocking", blocking) + group("Non-blocking", nonBlocking) +
    (doneCount ? `<details class="done" ${ui.doneOpen ? "open" : ""}><summary><div class="grouphead"><span>Done ▾</span><span>${doneCount}</span></div></summary>
      ${vanished.map(doneRow).join("")}${doneIssues.map(row).join("")}</details>` : "");
}
// Display name of a participant, group or payment id (T23, T33); null when unknown.
function recordName(id) {
  if (id == null || id === "") return null;
  const r = (summary() && summary().records) || {};
  return (r.participants || {})[id] || (r.groups || {})[id] || (r.payments || {})[id] || null;
}
// A name for people to read, with the id kept in a tooltip for traceability (T33).
function named(id) {
  const name = recordName(id);
  return name ? { text: name, title: id } : id;
}
const namesOf = ids => (ids || []).map(named);
function nameOf(id) { return recordName(id) || id; }

function cell(v) {
  if (Array.isArray(v)) return v.map(cell).join(", ");
  if (v && typeof v === "object" && "text" in v) return `<span class="named" title="${esc(v.title)}">${esc(v.text)}</span>`;
  return esc(v);
}

function kv(pairs) {
  const rows = pairs.filter(([, v]) => v !== undefined && v !== null && v !== "" && !(Array.isArray(v) && !v.length));
  return rows.length ? `<dl class="kv">${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${cell(v)}</dd>`).join("")}</dl>` : "";
}


function checksList(checks) {
  return `<ul class="checks">${checks.map(c => {
    const mark = c.verified === false ? ["u", "?"] : c.passed ? ["y", "✓"] : ["n", "✗"];
    return `<li><span class="${mark[0]}">${mark[1]}</span><span>${esc(c.name)}${c.detail ? ` <span class="d">· ${esc(c.detail)}</span>` : ""}</span></li>`;
  }).join("")}</ul>`;
}

// What the fixed-code detection saw, before any LLM involvement.
function inputBody(issue) {
  const d = issue.details || {};
  if (issue.kind === "unprocessed_message") {
    return `<div class="mail"><span class="from">${esc(issue.title)}</span>${esc(d.text)}</div>`;
  }
  if (issue.kind === "unmatched_payment") {
    const signals = (d.signals || []).map(([name, passed, detail]) => ({ name, passed, detail }));
    return kv([["Payment", named(d.payment_id)], ["Best candidate", named(d.candidate)], ["Identity score", d.score], ["Band", d.band]]) +
      (signals.length ? checksList(signals) : "");
  }
  if (issue.kind === "multiple_group_membership") return kv([["Participant", named(d.participant_id)], ["Groups", namesOf(d.group_ids)]]);
  if (issue.kind === "group_over_capacity") return kv([["Group", named(d.group_id)], ["Members", d.size], ["Maximum", d.max]]);
  return kv([["Subjects", namesOf(issue.subject_ids)], ...Object.entries(d).map(([k, v]) =>
    [k.replace(/_/g, " "), typeof v === "object" && !Array.isArray(v) ? JSON.stringify(v) : v])]) || '<p class="note">No further details.</p>';
}

function section(id, title, sub, body, open) {
  const isOpen = ui.open[id] ?? open;
  return `<details class="sec" data-sec="${id}" ${isOpen ? "open" : ""}><summary>${esc(title)}${sub ? ` <span class="sub">${esc(sub)}</span>` : ""}</summary>
    <div class="sec-body">${body}</div></details>`;
}

// The real tool calls of the agent run, in order (T31). After a run they are revealed one by one.
function stepsList(action) {
  const steps = action.trace || [];
  const reveal = ui.reveal === action.id;
  return `<ol class="steps">${steps.map((t, i) => `<li class="${t.ok ? "" : "bad"} ${reveal ? "reveal" : ""}"
      ${reveal ? `style="animation-delay:${i * 280}ms"` : ""}>
      <span class="mark">${t.ok ? "✓" : "✗"}</span>
      <span><b>${esc(TOOL_LABEL[t.tool] || t.tool)}</b> <code>${esc(t.tool)}</code>${argText(t.arguments) ? ` <span class="src">${esc(argText(t.arguments))}</span>` : ""}
      <span class="res">${esc(t.result)}</span></span></li>`).join("")}</ol>`;
}

// The agent's evidence, grouped as checked / found / applied / proposed.
function traceBlock(action) {
  const ev = action.evidence || [];
  const seen = new Set();
  const checked = ev.filter(e => !seen.has(e.source_type + e.source_id) && seen.add(e.source_type + e.source_id))
    .map(e => e.source_type === "rule" ? `${e.source_type} ${e.source_id}` : { text: `${e.source_type} ${nameOf(e.source_id)}`, title: e.source_id });
  const found = ev.filter(e => e.source_type !== "rule");
  const applied = ev.filter(e => e.source_type === "rule");
  const li = items => items.length ? `<ul>${items.join("")}</ul>` : '<span class="note">None cited.</span>';
  return `<dl class="trace">
    <dt>Checked</dt><dd>${li(checked.map(c => `<li><span class="src">${cell(c)}</span></li>`))}</dd>
    <dt>Found</dt><dd>${li(found.map(e => `<li title="${esc(e.source_id)}">${esc(e.description)}</li>`))}</dd>
    <dt>Applied</dt><dd>${li(applied.map(e => `<li><b>${esc(e.source_id)}</b> ${esc(e.description)}</li>`))}</dd>
    <dt>Proposed</dt><dd>${esc(action.title)}</dd></dl>`;
}

// The proposal comes first: what will happen, the agent's question, the draft and the decision.
function proposalCard(action, editable, buttons) {
  const draft = ui.drafts[action.id] ?? draftOf(action);
  const edited = ui.drafts[action.id] != null;
  const asks = needsHuman(action);
  return `<div class="card proposal-card">
      <div class="card-head"><span class="card-kicker">Proposed action · ${esc(ACTION_LABEL[action.action_type] || action.action_type)}</span>
        <span>${editable && draft != null ? '<span class="tag">editable</span>' : ""} ${edited ? '<span class="tag edited">edited</span>' : ""}</span></div>
      <div class="card-title">${esc(action.title)}</div>
      ${asks ? `<div class="question"><span class="qlabel">The agent asks you</span>${esc(action.description)}</div>`
             : `<div class="question"><span class="qlabel">Why</span>${esc(action.description)}</div>`}
      ${payloadBlock(action)}
      ${draft != null ? `<span class="draft-label">Draft reply, sent only after approval</span><div class="proposal" id="draft">${esc(draft)}</div>` : ""}
      ${buttons ? `<div class="actions">${buttons}</div>` : ""}
    </div>`;
}

function evidenceBody(action) {
  return traceBlock(action) + (action.checks && action.checks.length ? `<span class="lbl">Checks</span>${checksList(action.checks)}` : "");
}

function header(issueLike, action) {
  const conf = action && action.confidence != null ? Math.round(action.confidence * 100) : null;
  return `<div class="dhead"><div class="badges">
      <span class="badge ${issueLike.blocking ? "b-block" : "b-non"}">${issueLike.blocking ? "Blocking" : "Non-blocking"}</span>
      <span class="badge b-kind">${esc(KIND_LABEL[issueLike.kind] || issueLike.kind)}</span></div>
    <h3>${esc(issueLike.title)}</h3>
    ${conf != null ? `<div class="conf">Identity confidence <span class="meter"><span style="width:${conf}%"></span></span> ${conf}%</div>` : ""}</div>`;
}

// While the agent runs on the selected issue.
const THINKING = ["Reading the issue and the message", "Choosing which tools to use", "Looking up records and rules",
                  "Checking the facts it found", "Drafting one proposal with evidence"];
function thinkingCard() {
  const secs = Math.max(0, Math.round((Date.now() - (ui.runStart || Date.now())) / 1000));
  return `<div class="card"><div class="thinking"><span class="spinner" aria-hidden="true"></span>
    <div><b>Loading the saved example… <span id="thinkSecs">${secs}s</span></b>
    <span id="thinkPhase">${THINKING[Math.min(THINKING.length - 1, Math.floor(secs / 3))]}</span></div></div>
    <p class="note">This replays a curated example. No model or external service is called.</p></div>`;
}

function renderDetail() {
  const el = $("#detail");
  if (ui.view === "audit") { el.innerHTML = auditHTML(); return; }
  if (ui.view === "outbox") { el.innerHTML = outboxHTML(); return; }
  if (ui.view === "compose") { el.innerHTML = composeHTML(); return; }
  const s = summary();
  const key = ui.sel[ui.current] || "";
  const [type, id] = [key.split(":")[0], key.slice(key.indexOf(":") + 1)];

  if (type === "action") {
    const action = s.actions.find(a => a.id === id);
    if (!action) { el.innerHTML = '<p class="note">Select an issue.</p>'; return; }
    el.innerHTML = replayBadge(action) + header({ blocking: false, kind: (s.issues.find(i => i.id === action.issue_id) || {}).kind || "", title: action.title }, action)
      + proposalCard(action, false, '<span class="note">Approved. The data was updated and this issue is no longer detected.</span>')
      + ((action.trace || []).length ? section("steps", "Agent steps", `${action.trace.length} tool calls`, stepsList(action), true) : "")
      + section("evidence", "Evidence", "decision trace and checks", evidenceBody(action), false);
    return;
  }

  const issue = s.issues.find(i => i.id === id);
  if (!issue) { el.innerHTML = '<p class="note">Select an issue.</p>'; return; }
  const byIssue = actionsByIssue(s);
  const action = byIssue[issue.id];
  const st = viewStatus(issue, s, byIssue);
  if (issue.kind === "no_logistics_plan") { el.innerHTML = replayBadge(action) + planDetail(issue, action, st); return; }
  const editable = st === "proposed" || st === "human";
  let top;
  if (ui.running === issue.id) {
    top = thinkingCard();
  } else if (action) {
    let buttons;
    if (st === "resolved" || st === "dismissed") {
      buttons = `<span class="note">${st === "resolved" ? "Approved. The action ran and the issue is resolved." : "Dismissed. Nothing was sent or changed."}</span>`;
    } else if (st === "waiting") {
      buttons = `<span class="note">Waiting for another issue to be resolved first.</span>`;
    } else {
      buttons = `<button class="btn ok" type="button" data-act="approve">${esc(APPROVE_LABEL[action.action_type] || "Approve")}</button>
        ${draftOf(action) != null ? '<button class="btn" type="button" data-act="edit">Edit</button>' : ""}
        <button class="btn danger" type="button" data-act="dismiss">Dismiss</button>`;
    }
    top = proposalCard(action, editable, buttons);
  } else if (st === "waiting") {
    const deps = issue.depends_on.map(dep => (s.issues.find(i => i.id === dep) || { title: dep }).title);
    top = `<div class="card cta-card"><b>Waiting for another issue</b><p>This issue depends on "${esc(deps.join('", "'))}". Resolve that one first; this one will unlock automatically.</p></div>`;
  } else if (st === "failed") {
    top = `<div class="card cta-card"><b>The agent could not finish this issue</b><p>The error is in the audit log. You can try again.</p>
      <div class="actions"><button class="btn primary" type="button" data-act="retry">Retry agent</button></div></div>`;
  } else if (TERMINAL.includes(st)) {
    top = `<div class="card"><p class="note">${st === "resolved" ? "Resolved." : "Dismissed. Nothing was sent or changed."}</p></div>`;
  } else {
    top = `<div class="card cta-card"><b>Let the agent investigate</b>
      <p>Load a saved sample proposal and inspect its evidence. Cases without a specific example are handed to the organizers; no live AI runs here.</p>
      <div class="actions"><button class="btn primary" type="button" data-act="retry">Run agent on this issue</button></div></div>`;
  }
  const hasSteps = action && (action.trace || []).length;
  el.innerHTML = replayBadge(action) + header(issue, action) + top
    + (hasSteps && ui.running !== issue.id ? section("steps", "Agent steps", `${action.trace.length} illustrative tool calls from the saved example`, stepsList(action), true) : "")
    + (action && ui.running !== issue.id ? section("evidence", "Evidence", "decision trace and checks", evidenceBody(action), false) : "")
    + section("input", "Input", "what the fixed checks detected", inputBody(issue), !action);
  if (ui.reveal && action && ui.reveal === action.id) ui.reveal = null;   // animate only once
}

// Fictional examples for the demo: a rules question, a personal-data request, a question in French.
const EXAMPLES = [
  { label: "Rules question", sender: "clara.roy@gmail.example", channel: "email",
    text: "Hi! Can our team have five people if the fifth one only does the pitch?" },
  { label: "Personal data", sender: "recruiting@partner.example", channel: "email",
    text: "Hello, could you send us the phone numbers of all participants so we can call them about internships?" },
  { label: "In French", sender: "yanis_b", channel: "discord",
    text: "Salut, est-ce qu'on a le droit d'utiliser un modèle open source au lieu d'OpenAI pour le projet ?" },
];

function composeHTML() {
  return `<div class="dhead"><div class="badges"><span class="badge b-kind">New message</span></div>
      <h3>Simulate an incoming message</h3>
      <p class="note">Try one of the three saved examples below. Other messages are saved locally for organizer review; this demo does not analyze new text with AI.</p></div>
    <div class="block"><span class="lbl">Try an example</span><div class="examples">${EXAMPLES.map((ex, k) =>
      `<button class="btn" type="button" data-example="${k}">${esc(ex.label)}</button>`).join("")}</div></div>
    <form class="compose card" id="composeForm">
      <label>From <input name="sender" required maxlength="200" placeholder="name@example.org or a Discord handle"></label>
      <label>Channel <select name="channel"><option value="email">Email</option><option value="discord">Discord</option><option value="form">Form</option></select></label>
      <label>Message <textarea name="text" required maxlength="4000" rows="6" placeholder="Bonjour, j'ai déjà payé…"></textarea></label>
      <div class="actions"><button class="btn primary" type="submit">Send to the agent</button>
        <button class="btn" type="button" data-act="back">Cancel</button></div>
    </form>`;
}
const TOOL_LABEL = {
  get_participant: "Look up participant", get_payment: "Read payment", check_eligibility: "Check who has paid",
  match_person: "Score identity match", search_rules: "Search the rules", list_rules: "Read all rules",
  list_groups: "Read teams", list_group_candidates: "Find people seeking a team", check_groups: "Check team rules",
  propose_groups: "Draft teams", get_event_summary: "Read event summary", propose_action: "Propose action",
};

function argText(args) {
  if (!args || typeof args !== "object") return String(args ?? "");
  return Object.entries(args).map(([k, v]) => {
    const text = typeof v === "object" ? JSON.stringify(v) : String(v);
    const name = typeof v === "string" && recordName(v);
    return `${k}: ${text}${name ? ` (${name})` : ""}`;
  }).join(", ");
}

function draftOf(action) {
  const p = action.payload || {};
  if (action.action_type === "SEND_MESSAGE") return p.text;
  if (action.action_type === "LINK_PAYMENT") return p.message;
  return null;
}

function payloadBlock(action) {
  const p = action.payload || {};
  const to = Array.isArray(p.to) ? p.to.join(", ") : p.to;
  switch (action.action_type) {
    case "LINK_PAYMENT": return kv([["Link payment", named(p.payment_id)], ["To participant", named(p.participant_id)], ["Reply to", to]]);
    case "SEND_MESSAGE": return kv([["To", to]]);
    case "MOVE_MEMBER": return kv([["Participant", named(p.participant_id)], ["From group", p.from_group ? named(p.from_group) : "none"],
                                   ["To group", p.to_group ? named(p.to_group) : "none"]]);
    case "UPDATE_GROUPS": return `<div class="groups">${(p.groups || []).map(g =>
      `<div><b>${esc(g.name)}</b> <span class="src">${esc(g.id)}</span><br>${esc(g.members.map(id => (summary().records.participants || {})[id] || id).join(", "))}</div>`).join("")}</div>`;
    case "ESCALATE": {
      // The model sometimes repeats its question as the note: show the note only when it adds something.
      const same = t => String(t || "").replace(/\s+/g, " ").trim().toLowerCase();
      return p.note && same(p.note) !== same(action.description)
        ? `<div class="question"><span class="qlabel">Note for the organizers</span>${esc(p.note)}</div>` : "";
    }
    case "SELECT_TRAVEL_PLAN": {
      const chosen = summary().logistics;
      return kv([["Valid options", (p.ranked_valid || []).join(", ")],
                 ["Chosen", chosen ? `${chosen.id} · ${euro(chosen.cost_per_person_cents)} per person` : ""]]);
    }
    default: return kv(Object.entries(p).map(([k, v]) => [k, typeof v === "object" ? JSON.stringify(v) : v]));
  }
}

async function submitMessage(form) {
  const body = Object.fromEntries(new FormData(form).entries());
  let issueId = null;
  await busy("Adding the message…", async () => {
    const data = await api(`/api/events/${encodeURIComponent(ui.current)}/messages`,
                           { method: "POST", body: JSON.stringify(body) });
    store(data);
    issueId = data.issue_id;
    ui.view = "issue";
    ui.sel[ui.current] = `issue:${issueId}`;
  });
  if (issueId) await runAgent(issueId);
}

// ---------- trip planning (T15, redesigned in T35) ----------

const euro = cents => `€${(cents / 100).toFixed(cents % 100 ? 2 : 0)}`;
const HARD_LABEL = {
  participants: v => `${v} participants`,
  max_cost_per_person_cents: v => `≤ ${euro(v)} per person (whole package)`,
  arrive_before: v => `Arrive before ${v}`,
  no_overnight: v => (v ? "No overnight travel" : "Overnight travel allowed"),
  step_free_rooms: v => `≥ ${v} step-free rooms`,
};
const SOFT_LABEL = { fewer_changes: "Fewer changes", near_station: "Lodging near the station",
                     early_return: "Early return on Sunday", lower_cost: "Lower cost" };

function requestedBudget(s) {
  const c = s.travel && s.travel.constraints;
  return c && c.hard ? c.hard.max_cost_per_person_cents : null;
}

const legKind = t => `${t.changes ? `${t.changes} change${t.changes > 1 ? "s" : ""}` : "direct"}${t.mode ? ` ${t.mode}` : ""}`;
// Per-person cost split (T16 data), meal items grouped: "Coach €42 · Lodging €78.59 · Meals €22".
const COST_LABEL = { coach: "Coach", transport: "Travel", lodging: "Lodging" };
function costParts(o) {
  const parts = o.cost_breakdown_per_person_cents || {};
  let meals = 0;
  const shown = [];
  for (const [k, v] of Object.entries(parts)) {
    if (COST_LABEL[k]) shown.push(`${COST_LABEL[k]} ${euro(v)}`); else meals += v;
  }
  if (meals) shown.push(`Meals ${euro(meals)}`);
  return shown.join(" · ");
}
// What organizers must still confirm for a package (checks code cannot verify, and the group block).
function toConfirm(row) {
  const items = (row.checks || []).filter(c => c.verified === false).map(c => c.name);
  if ((row.option.lodging || {}).group_block_confirmed === false) items.push("group block with the hotel");
  return items;
}

// Valid packages as cards with labelled rows (ranked first highlighted); what every package still needs
// confirmed is said once above them; rejected packages in a table with separate time columns (T48).
function optionsBlock(action, decided) {
  const rows = (action.payload && action.payload.options) || [];
  const ranked = (action.payload && action.payload.ranked_valid) || [];
  const byId = Object.fromEntries(rows.map(r => [r.option.id, r]));
  const validRows = ranked.map(id => byId[id]).filter(Boolean);
  const shared = validRows.length ? toConfirm(validRows[0]).filter(x => validRows.every(r => toConfirm(r).includes(x))) : [];
  const cards = validRows.map((row, k) => {
    const o = row.option, t = o.transport || {}, l = o.lodging || {};
    const own = toConfirm(row).filter(x => !shared.includes(x));
    const facts = [
      ["Outbound", `${esc(t.depart || "?")} → ${esc(t.arrive || "?")} · ${esc(legKind(t))}${t.overnight ? ' · <span class="bad">overnight</span>' : ""}`],
      t.return_arrive ? ["Return", `back ${esc(t.return_arrive)} on Sunday`] : null,
      ["Lodging", `${esc(l.name || "")}<small>${[l.walk_minutes != null ? `${esc(l.walk_minutes)} min walk to the station` : "",
                                                 l.capacity ? `${esc(l.capacity)} beds` : ""].filter(Boolean).join(" · ")}</small>`],
      costParts(o) ? ["Per person", esc(costParts(o))] : null,
    ].filter(Boolean);
    return `<div class="optcard ${k === 0 ? "first" : ""}">
      <div class="top"><b>Option ${esc(o.id)}</b><span class="verdict ${k === 0 ? "v-pick" : "v-alt"}">${k === 0 ? "Ranked 1st" : "Valid"}</span></div>
      <div class="price">${euro(o.cost_per_person_cents)} <small>per person</small></div>
      <dl class="facts">${facts.map(([k2, v]) => `<dt>${k2}</dt><dd>${v}</dd>`).join("")}</dl>
      ${own.length ? `<span class="confirm">Organizers also confirm: ${esc(own.join(", "))}</span>` : ""}
      ${decided ? "" : `<button class="btn ${k === 0 ? "ok" : ""}" type="button" data-act="choose" data-opt="${esc(o.id)}">Choose option ${esc(o.id)} · ${euro(o.cost_per_person_cents)}</button>`}
    </div>`;
  }).join("");
  const rejected = rows.filter(r => !r.valid).map(row => {
    const o = row.option, t = o.transport || {}, l = o.lodging || {};
    const failed = (row.checks || []).filter(c => c.verified !== false && !c.passed);
    const costBad = failed.some(c => /cost/i.test(c.name)), timeBad = failed.some(c => /arriv/i.test(c.name));
    return `<tr><td><b>${esc(o.id)}</b></td>
      <td class="num ${t.overnight ? "bad" : ""}">${esc(t.depart || "")}${t.overnight ? " · overnight" : ""}</td>
      <td class="num ${timeBad ? "bad" : ""}">${esc(t.arrive || "")}</td>
      <td class="num">${esc(t.return_arrive || "")}</td>
      <td>${esc(l.name || "")}</td>
      <td class="num ${costBad ? "bad" : ""}">${euro(o.cost_per_person_cents)}</td>
      <td><span class="whyred">${esc(failed.map(c => `${c.name}${c.detail ? ` (${c.detail})` : ""}`).join("; "))}</span></td></tr>`;
  }).join("");
  return `<div class="optwrap">
    ${cards && shared.length ? `<p class="shared-confirm">For every package, organizers still confirm: ${esc(shared.join(", "))}.</p>` : ""}
    ${cards ? `<div class="optcards">${cards}</div>` : '<p class="note">No package passes every hard constraint.</p>'}
    ${rejected ? `<span class="lbl">Rejected packages and why</span><div class="rejwrap"><table class="opts">
      <thead><tr><th>Option</th><th>Departs</th><th>Arrives</th><th>Back</th><th>Lodging</th><th>Per person</th><th>Broken constraint</th></tr></thead>
      <tbody>${rejected}</tbody></table></div>` : ""}
  </div>`;
}

function planDetail(issue, action, st) {
  const s = summary();
  const t = s.travel || {};
  const head = header(issue, null);
  const input = `<div class="block"><span class="lbl">Planning request · ${esc(t.origin || "")} → ${esc(t.destination || "")}</span>
    <div class="mail"><span class="from">From the organizers · ${esc(t.participants || "?")} participants</span>${esc(t.request || "")}</div></div>`;
  if (st === "waiting") return head + input;
  if (!action) {
    return head + input + `<div class="card cta-card"><b>Plan the trip</b>
      <p>Replay the saved planning example, clarify coach inclusion, and compare five illustrative complete packages. Prices include groceries and food transport; no current quote or booking is made.</p>
      <div class="actions"><button class="btn primary" type="button" data-act="plan">Plan the trip</button></div></div>`;
  }
  const questions = (action.payload && action.payload.clarifications) || [];
  if (action.action_type === "ESCALATE" && questions.length && !(action.payload.options || []).length) {
    return head + input + `<div id="clarify" class="card proposal-card"><span class="card-kicker">The planner asks before searching</span>
      <div class="question"><span class="qlabel">Question for the organizers</span>${questions.map(q => esc(q)).join("<br>")}</div>
      <p class="note">Confirm that the complete budget includes coach hire, lodging, groceries and food transport. No live search or text extraction occurs.</p>
      <form class="compose" id="answerForm"><label>Your answer <textarea name="answer" required readonly rows="3">Yes, the €150 per person includes round-trip coach hire, lodging, groceries and food transport.</textarea></label>
        <div class="actions"><button class="btn primary" type="submit">Answer and plan again</button></div></form></div>`;
  }
  const c = (action.payload && action.payload.constraints) || { hard: {}, soft: [], organizer_verified: [] };
  const budget = c.hard.max_cost_per_person_cents;
  const requested = requestedBudget(s);
  // What-if: 20% below the requested budget, rounded to €10 (€150 -> €120).
  const whatIf = requested && requested > 9000 ? 9000 : null;
  const hard = Object.entries(c.hard).map(([k, v]) =>
    `<li>${esc(HARD_LABEL[k] ? HARD_LABEL[k](v) : `${k}: ${v}`)}${(c.organizer_verified || []).includes(k) ? ' <span class="confirm">organizers confirm</span>' : ""}</li>`).join("");
  const soft = (c.soft || []).map(k => `<li>${esc(SOFT_LABEL[k] || k)}</li>`).join("");
  const rows = (action.payload.options || []);
  const valid = (action.payload.ranked_valid || []);
  const suggestions = action.payload.suggestions || [];
  const decided = st === "resolved" || st === "dismissed";
  const diag = action.action_type === "ESCALATE" && rows.length ? `<div class="diag"><b>No valid option at ${euro(budget)} per person.</b>
      <span>I did not relax any constraint. Options for the organizers:</span>
      <ul>${suggestions.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>` : "";
  const seg = requested ? `<div class="block"><span class="lbl">Try it: budget per person</span><div class="seg" role="group" aria-label="Budget">
      <button type="button" data-budget="" aria-pressed="${budget === requested}">${euro(requested)} (as requested)</button>
      ${whatIf ? `<button type="button" data-budget="${whatIf}" aria-pressed="${budget === whatIf}">${euro(whatIf)} (what if)</button>` : ""}</div></div>` : "";
  const trace = `<dl class="trace">
      <dt>Checked</dt><dd><ul><li>Planning request and ${rows.length} travel + lodging packages <span class="src">${esc((rows[0] && rows[0].option.source) || "")}</span></li></ul></dd>
      <dt>Found</dt><dd>${valid.length} of ${rows.length} packages pass every verified hard constraint</dd>
      <dt>Applied</dt><dd>Hard constraints checked in code; soft preferences only rank valid options; unverifiable ones go to organizers</dd>
      <dt>Proposed</dt><dd>${esc(action.title)}</dd></dl>`;
  return head + `
    <div class="card proposal-card"><span class="card-kicker">Planner's proposal · ${valid.length} of ${rows.length} packages valid</span>
      <div class="question"><span class="qlabel">${valid.length ? "Trade-offs" : "Diagnosis"}</span>${esc(action.description)}</div>
      ${diag}
      ${seg}
      ${plannerControls(action, decided)}
      <span class="lbl">Options compared</span>
      ${optionsBlock(action, decided)}
      <p class="note">${decided ? "Decided." : "Organizers book the chosen option; nothing is booked automatically."}</p>
    </div>
    <div class="block"><span class="lbl">Constraints extracted from the request</span><div class="cons">
      <div class="hard"><h4>Hard · reject if broken</h4><ul>${hard}</ul></div>
      <div class="soft"><h4>Soft · rank valid options</h4><ul>${soft || "<li>Lower cost</li>"}</ul></div></div></div>
    ${section("plantrace", "Evidence", "how the planner decided", trace, false)}
    ${section("planinput", "Input", "the organizers' request", input, false)}`;
}

// The request text the planner last used (it includes answers to its questions).
function planRequestText() {
  const plan = summary().actions.find(a => a.issue_id === "no_logistics_plan");
  return plan && plan.payload && plan.payload.request_text;
}

async function planTrip(overrideBudget = null, text = null) {
  await busy(overrideBudget ? `Re-checking every package at ${euro(overrideBudget)} per person…`
                            : "Loading the saved planning example…", async () => {
    const body = {};
    const requestText = text || planRequestText();
    if (requestText) body.text = requestText;
    body.overrides = { max_cost_per_person_cents: overrideBudget ?? requestedBudget(summary()) };
    const data = await api(`/api/events/${encodeURIComponent(ui.current)}/plan`, { method: "POST", body: JSON.stringify(body) });
    store(data);
    const action = data.actions.find(a => a.id === data.action_id);
    if ((action.payload.clarifications || []).length && !(action.payload.options || []).length) {
      setRun(`Planner: ${action.payload.clarifications.length} question(s) for the organizers before searching.`);
      return;
    }
    const valid = (action.payload.ranked_valid || []).length;
    setRun(`Planner: ${valid} of ${(action.payload.options || []).length} packages pass every hard constraint`
      + `${overrideBudget ? ` at ${euro(overrideBudget)}` : ""}.`, valid ? "" : "error");
  });
}

async function chooseOption(optionId) {
  const { action } = currentAction();
  // Count before approving: once the plan exists, detection drops the dependency.
  const unlocked = summary().issues.filter(i => i.depends_on.includes("no_logistics_plan")).length;
  await busy(`Selecting option ${optionId}…`, async () => {
    const data = await api(`/api/actions/${encodeURIComponent(action.id)}/approve`,
                           { method: "POST", body: JSON.stringify({ option_id: optionId }) });
    store(data);
    keepSelection();
    setRun(`Travel plan chosen: option ${optionId}. ${unlocked} dependent issue${unlocked === 1 ? "" : "s"} unlocked.`);
  });
}

function outboxHTML() {
  const items = ui.outbox.slice().reverse();
  return `<div class="dhead"><div class="badges"><span class="badge b-kind">Outbox</span></div>
      <h3>Simulated sent messages</h3><p class="note">Replies approved by organizers. In this demo nothing leaves the machine.</p></div>
    <div class="outbox">${items.length ? items.map(m => `<div class="mail"><span class="from">To ${esc(Array.isArray(m.to) ? m.to.join(", ") : m.to)} · ${esc((m.sent_at || "").replace("T", " ").slice(0, 16))}</span>${esc(m.text)}</div>`).join("")
      : '<p class="note">No message sent yet.</p>'}</div>
    <div class="actions"><button class="btn" type="button" data-act="back">Back to issues</button></div>`;
}

function render() { renderEvents(); renderIssues(); renderDetail(); }

// ---------- selection ----------

function firstKey(s) {
  const byIssue = actionsByIssue(s);
  const open = s.issues.filter(i => !TERMINAL.includes(i.status));
  const planning = open.find(i => i.kind === "no_logistics_plan");
  if (planning) return `issue:${planning.id}`;
  const sorted = [...open.filter(i => i.blocking), ...open.filter(i => !i.blocking)];
  const ready = sorted.find(i => ["proposed", "human"].includes(viewStatus(i, s, byIssue)));
  const pick = ready || sorted[0];
  return pick ? `issue:${pick.id}` : null;
}

function keepSelection() {
  const s = summary();
  const key = ui.sel[ui.current];
  const id = key ? key.slice(key.indexOf(":") + 1) : null;
  const stillOpen = key && key.startsWith("issue:") && s.issues.some(i => i.id === id && !TERMINAL.includes(i.status));
  if (!stillOpen) ui.sel[ui.current] = firstKey(s);
}

function store(data) {
  ui.summaries[data.id] = { id: data.id, name: data.name, counts: data.counts, issues: data.issues, actions: data.actions,
                            travel: data.travel || null, logistics: data.logistics || null,
                            records: data.records || { participants: {}, groups: {}, payments: {} },
                            meta: data.meta || {} };
}

async function selectEvent(id) {
  ui.current = id;
  ui.view = "issue";
  store(await api(`/api/events/${encodeURIComponent(id)}`));
  ui.outbox = await api(`/api/events/${encodeURIComponent(id)}/outbox`);
  if (!ui.sel[id]) ui.sel[id] = firstKey(summary());
  render();
}

// ---------- actions ----------

function currentAction() {
  const s = summary();
  const key = ui.sel[ui.current] || "";
  const issueId = key.slice(key.indexOf(":") + 1);
  return { issueId, action: actionsByIssue(s)[issueId] };
}

function captureDraft(action) {
  const box = $("#draft");
  if (!box || box.getAttribute("contenteditable") !== "true") return;
  const text = box.innerText.replace(/\n$/, "");
  if (text !== draftOf(action)) ui.drafts[action.id] = text; else delete ui.drafts[action.id];
  demoStore.saveDrafts(ui.drafts);
  refreshSessionNotice();
}

async function busy(label, fn) {
  if (ui.busy) return;
  ui.busy = true;
  document.querySelectorAll(".btn").forEach(b => { b.disabled = true; });
  $("#run").classList.add("busy");
  setRun(label, "busy");
  try { await fn(); } catch (err) { setRun(err.message, "error"); }
  finally {
    ui.busy = false;
    render();
    document.querySelectorAll(".btn").forEach(b => { b.disabled = false; });
    $("#run").classList.remove("busy");
  }
}

async function decide(kind) {
  const { action } = currentAction();
  if (!action) return;
  captureDraft(action);
  await busy(kind === "approve" ? `Applying ${action.action_type}…` : "Dismissing…", async () => {
    const edited = ui.drafts[action.id];
    const body = kind === "approve" && edited != null ? JSON.stringify({ edited_description: edited }) : undefined;
    const before = ui.outbox.length;
    store(await api(`/api/actions/${encodeURIComponent(action.id)}/${kind}`, { method: "POST", body }));
    delete ui.drafts[action.id];
    keepSelection();
    if (kind === "approve") {
      ui.outbox = await api(`/api/events/${encodeURIComponent(ui.current)}/outbox`);
      const sent = ui.outbox.length - before;
      setRun(`Approved: ${action.title}${sent > 0 ? ` · ${sent} message added to the outbox` : ""}`);
    } else {
      setRun(`Dismissed: ${action.title}. Nothing was sent.`);
    }
  });
}

// The runnable rule mirrors bureau/agent/loop.py:runnable_issues; the server
// re-checks it, so a stale client list only costs a no-op request.
function runnableIds(s) {
  const byIssue = actionsByIssue(s);
  return s.issues
    .filter(i => ["open", "needs_human"].includes(i.status) && !byIssue[i.id]
      && i.kind !== "no_logistics_plan" && !isWaiting(i, s))
    .sort((a, b) => b.blocking - a.blocking)
    .map(i => i.id);
}

// One request per issue, so the list shows which issue is being investigated and
// each result appears as soon as it is ready. Stop takes effect after the current issue.
async function runAgent(issueId = null) {
  if (ui.busy) {
    if (ui.running) { ui.stopRequested = true; setRun("Stopping after the current issue…", "busy"); }
    return;
  }
  const queue = issueId ? [issueId] : runnableIds(summary());
  if (!queue.length) {
    setRun("Nothing for the agent to do: every runnable issue already has a proposal.");
    return;
  }
  await busy("Agent investigating…", async () => {
    ui.stopRequested = false;
    const runBtn = $("#runBtn");
    runBtn.disabled = false;
    runBtn.textContent = "Stop";
    let proposed = 0, failed = 0, remaining = null;
    const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
    try {
      for (const [k, id] of queue.entries()) {
        if (ui.stopRequested) break;
        const issue = summary().issues.find(i => i.id === id);
        ui.running = id;
        ui.runStart = Date.now();
        renderIssues();
        if (ui.sel[ui.current] === `issue:${id}`) renderDetail();
        const row = document.querySelector(`[data-key="issue:${CSS.escape(id)}"]`);
        if (row) row.scrollIntoView({ block: "nearest" });
        setRun(`Investigating ${k + 1}/${queue.length}: "${issue ? issue.title : id}"`, "busy");
        const data = await api(`/api/events/${encodeURIComponent(ui.current)}/run?limit=1&issue_id=${encodeURIComponent(id)}`,
                               { method: "POST" });
        store(data);
        const made = data.actions.find(a => a.issue_id === id);
        if (made) ui.reveal = made.id;
        proposed += data.errors.length ? 0 : 1;
        failed += data.errors.length;
        remaining = issueId ? null : data.remaining;
        ui.running = null;
        renderEvents(); renderIssues();
        if (ui.sel[ui.current] === `issue:${id}`) renderDetail();
      }
    } finally {
      ui.running = null;
      runBtn.textContent = "Run agent";
    }
    const stopped = ui.stopRequested;
    ui.stopRequested = false;
    keepSelection();
    setRun(`${stopped ? "Stopped" : "Agent finished"}: ${plural(proposed, "proposal")} ready for review`
      + `${failed ? `, ${failed} failed (see the audit log)` : ""}`
      + `${remaining ? `, ${plural(remaining, "issue")} left` : ""}.`, failed && !proposed ? "error" : "");
  });
}

let resetArmed = null;
async function resetDemo() {
  const btn = $("#resetBtn");
  if (!resetArmed) {   // two clicks instead of a blocking confirm() dialog
    btn.textContent = "Click again to reset";
    resetArmed = setTimeout(() => { resetArmed = null; btn.textContent = "Reset demo"; }, 3000);
    return;
  }
  clearTimeout(resetArmed); resetArmed = null; btn.textContent = "Reset demo";
  await busy("Resetting to the sample data…", async () => {
    store(await api(`/api/events/${encodeURIComponent(ui.current)}/reset`, { method: "POST" }));
    ui.drafts = demoStore.drafts(); ui.outbox = []; ui.view = "issue";
    ui.sel[ui.current] = firstKey(summary());
    setRun("Reset: runtime data cleared, sample data restored.");
  });
}

// ---------- events ----------

$("#events").addEventListener("click", e => {
  const card = e.target.closest(".evtab");
  if (card && !ui.busy) selectEvent(card.dataset.ev).catch(err => setRun(err.message, "error"));
});

$("#issues").addEventListener("click", e => {
  const row = e.target.closest(".issue");
  if (!row) return;
  ui.sel[ui.current] = row.dataset.key;
  ui.view = "issue";
  renderIssues(); renderDetail();
});
$("#issues").addEventListener("toggle", e => { if (e.target.matches("details.done")) ui.doneOpen = e.target.open; }, true);
$("#detail").addEventListener("toggle", e => {
  if (e.target.matches("details.sec")) ui.open[e.target.dataset.sec] = e.target.open;
}, true);

// Thinking panel: elapsed seconds and phase, while the agent works on the selected issue.
setInterval(() => {
  const secs = $("#thinkSecs");
  if (!secs || !ui.runStart) return;
  const n = Math.round((Date.now() - ui.runStart) / 1000);
  secs.textContent = `${n}s`;
  $("#thinkPhase").textContent = THINKING[Math.min(THINKING.length - 1, Math.floor(n / 3))];
}, 500);

// Demo video (T17): the hero button and footer link stay hidden until a URL is set here.
const DEMO_VIDEO_URL = "";
for (const id of ["#videoBtn", "#videoLink"]) {
  const a = $(id);
  if (DEMO_VIDEO_URL) { a.href = DEMO_VIDEO_URL; a.hidden = false; }
}

// Theme: light by default; the choice is remembered per browser when storage is available.
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const b = $("#themeBtn");
  b.textContent = theme === "dark" ? "Light" : "Dark";
  b.setAttribute("aria-label", `Switch to ${theme === "dark" ? "light" : "dark"} theme`);
}
try { applyTheme(localStorage.getItem("bureau-theme") === "dark" ? "dark" : "light"); } catch { applyTheme("light"); }
$("#themeBtn").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(next);
  try { localStorage.setItem("bureau-theme", next); } catch { /* storage unavailable: keep for this page only */ }
});

$("#detail").addEventListener("click", e => {
  const bud = e.target.closest("[data-budget]");
  if (bud && !ui.busy) { planTrip(bud.dataset.budget ? +bud.dataset.budget : null); return; }
  const btn = e.target.closest("[data-act], [data-example]");
  if (!btn || ui.busy) return;
  const act = btn.dataset.act;
  if (act === "edit") {
    const box = $("#draft");
    const { action } = currentAction();
    if (box.getAttribute("contenteditable") === "true") {
      captureDraft(action);
      renderDetail();
    } else {
      box.setAttribute("contenteditable", "true");
      box.focus();
      btn.textContent = "Save";
    }
  } else if (act === "approve" || act === "dismiss") {
    decide(act);
  } else if (act === "plan") {
    planTrip();
  } else if (act === "choose") {
    chooseOption(btn.dataset.opt);
  } else if (act === "retry") {
    runAgent(currentAction().issueId);
  } else if (btn.dataset.example !== undefined) {
    const ex = EXAMPLES[+btn.dataset.example];
    const form = $("#composeForm");
    form.sender.value = ex.sender; form.channel.value = ex.channel; form.text.value = ex.text;
  } else if (act === "back") {
    ui.view = "issue"; renderIssues(); renderDetail();
  }
});

$("#runBtn").addEventListener("click", () => runAgent());   // doubles as Stop during a run
$("#composeBtn").addEventListener("click", () => {
  if (ui.busy) return;
  ui.view = "compose";
  renderIssues(); renderDetail();
  $("#composeForm").sender.focus();
});
$("#detail").addEventListener("submit", e => {
  if (e.target.id === "answerForm") {
    e.preventDefault();
    const answer = e.target.answer.value.trim();
    if (answer && !ui.busy) planTrip(null, `${planRequestText()}\n\nOrganizer answers: ${answer}`);
    return;
  }
  if (e.target.id !== "composeForm") return;
  e.preventDefault();
  if (!ui.busy) submitMessage(e.target);
});   // doubles as Stop during a run
$("#resetBtn").addEventListener("click", () => resetDemo());
$("#outboxBtn").addEventListener("click", async () => {
  if (ui.busy) return;
  try {
    ui.outbox = await api(`/api/events/${encodeURIComponent(ui.current)}/outbox`);
    ui.view = "outbox";
    renderIssues(); renderDetail();
  } catch (err) { setRun(err.message, "error"); }
});

(async () => {
  try {
    const events = await api("/api/events");
    for (const ev of events) store(await api(`/api/events/${encodeURIComponent(ev.id)}`));
    ui.current = events.length ? events[0].id : null;
    if (ui.current) ui.sel[ui.current] = firstKey(summary());
    ui.outbox = ui.current ? await api(`/api/events/${encodeURIComponent(ui.current)}/outbox`) : [];
    render();
    const hack = ui.summaries.hackathon;
    // Everything detected in the sample, including issues already resolved in this session.
    if (hack) $("#mIssues").textContent = hack.issues.length + vanishedActions(hack).length;
    setRun("Ready. Pick an issue, or start the guided demo.");
  } catch (err) {
    setRun(`API not reachable: ${err.message}`, "error");
  }
})();

function auditHTML() {
  const rows = demoStore.request(`/api/events/${encodeURIComponent(ui.current)}/audit`);
  return `<div class="dhead"><h3>Activity in this tab</h3><p class="note">Local decisions on fictional data. Reset clears this event's activity.</p></div>`
    + rows.slice().reverse().map(row => `<div class="mail"><span class="from">${esc(row.at)}</span>${esc(row.message)}</div>`).join("")
    + (!rows.length ? '<p class="note">No decisions yet. Review and approve a sample proposal.</p>' : "")
    + '<button class="btn" data-act="back" type="button">Back to issues</button>';
}
$("#auditBtn").addEventListener("click", () => { if (!ui.busy) { ui.view = "audit"; renderDetail(); } });
