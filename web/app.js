// Organizer console (T06). Talks only to the JSON API in api/main.py; shapes are
// the dataclasses of bureau/core/models.py. Design: web/reference/mockup.html.

const ui = {
  summaries: {},      // event id -> last summary {id, name, counts, issues, actions}
  current: null,      // selected event id
  sel: {},            // event id -> selected key ("issue:<id>" or "action:<id>")
  drafts: {},         // action id -> organizer-edited reply text
  view: "issue",      // "issue" or "outbox"
  outbox: [],
  doneOpen: false,
  busy: false,
  running: null,        // issue id the agent is investigating right now
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

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body && body.detail ? (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)) : res.statusText;
    throw new Error(`${res.status}: ${detail}`);
  }
  return body;
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

function renderEvents() {
  $("#events").innerHTML = Object.values(ui.summaries).map(s => {
    const c = cardCounts(s);
    return `<button class="evcard" type="button" data-ev="${esc(s.id)}" aria-pressed="${ui.current === s.id}">
      <div class="evtop"><h3>${esc(s.name)}</h3>${c.blocking === 0 ? '<span class="ready">No blocking issues</span>' : ""}</div>
      <div class="counts">
        <div class="count block ${c.blocking === 0 ? "zero" : ""}"><span class="v">${c.blocking}</span><span class="k">blocking</span></div>
        <div class="count nonblock ${c.nonBlocking === 0 ? "zero" : ""}"><span class="v">${c.nonBlocking}</span><span class="k">non-blocking</span></div>
        <div class="count you"><span class="v">${c.review}</span><span class="k">ready for review</span></div>
        <div class="count done"><span class="v">${c.resolved}</span><span class="k">resolved</span></div>
      </div></button>`;
  }).join("");
}

function issueMeta(issue) {
  if (issue.details && issue.details.text) {
    const t = issue.details.text;
    return t.length > 70 ? `${t.slice(0, 70)}…` : t;
  }
  return issue.id;
}

function renderIssues() {
  const s = summary();
  const byIssue = actionsByIssue(s);
  const sel = ui.sel[ui.current];
  const row = issue => {
    const st = ui.running === issue.id ? "running" : viewStatus(issue, s, byIssue);
    const [cls, label] = PILL[st];
    return `<button class="issue ${TERMINAL.includes(st) ? "res" : ""}" type="button" data-key="issue:${esc(issue.id)}"
        aria-current="${ui.view === "issue" && sel === `issue:${issue.id}`}">
      <span class="${issue.blocking ? "bar-b" : "bar-n"}"></span>
      <span><span class="t">${esc(issue.title)}</span><span class="m">${esc(issueMeta(issue))}</span></span>
      <span class="pill ${cls}">${label}</span></button>`;
  };
  const doneRow = a => `<button class="issue res" type="button" data-key="action:${esc(a.id)}"
        aria-current="${ui.view === "issue" && sel === `action:${a.id}`}">
      <span class="bar-n"></span>
      <span><span class="t">${esc(a.title)}</span><span class="m">${esc(a.issue_id)}</span></span>
      <span class="pill p-res">Resolved</span></button>`;

  const open = s.issues.filter(i => !TERMINAL.includes(i.status));
  const blocking = open.filter(i => i.blocking), nonBlocking = open.filter(i => !i.blocking);
  const doneIssues = s.issues.filter(i => TERMINAL.includes(i.status));
  const vanished = vanishedActions(s);
  const doneCount = doneIssues.length + vanished.length;
  const group = (label, items) => `<div class="grouphead"><span>${label}</span><span>${items.length}</span></div>
    ${items.length ? items.map(row).join("") : '<p class="note empty">Nothing here.</p>'}`;

  $("#issues").innerHTML = group("Blocking", blocking) + group("Non-blocking", nonBlocking) +
    (doneCount ? `<details class="done" ${ui.doneOpen ? "open" : ""}><summary><div class="grouphead"><span>Done ▾</span><span>${doneCount}</span></div></summary>
      ${vanished.map(doneRow).join("")}${doneIssues.map(row).join("")}</details>` : "");
}

function kv(pairs) {
  const rows = pairs.filter(([, v]) => v !== undefined && v !== null && v !== "" && !(Array.isArray(v) && !v.length));
  return rows.length ? `<dl class="kv">${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(Array.isArray(v) ? v.join(", ") : v)}</dd>`).join("")}</dl>` : "";
}

function checksList(checks) {
  return `<ul class="checks">${checks.map(c => {
    const mark = c.verified === false ? ["u", "?"] : c.passed ? ["y", "✓"] : ["n", "✗"];
    return `<li><span class="${mark[0]}">${mark[1]}</span><span>${esc(c.name)}${c.detail ? ` <span class="d">· ${esc(c.detail)}</span>` : ""}</span></li>`;
  }).join("")}</ul>`;
}

// What the fixed-code detection saw, before any LLM involvement.
function inputBlock(issue) {
  const d = issue.details || {};
  let body;
  if (issue.kind === "unprocessed_message") {
    body = `<div class="mail"><span class="from">${esc(issue.title)}</span>${esc(d.text)}</div>`;
  } else if (issue.kind === "unmatched_payment") {
    const signals = (d.signals || []).map(([name, passed, detail]) => ({ name, passed, detail }));
    body = kv([["Payment", d.payment_id], ["Best candidate", d.candidate], ["Identity score", d.score], ["Band", d.band]]) +
      (signals.length ? checksList(signals) : "");
  } else if (issue.kind === "multiple_group_membership") {
    body = kv([["Participant", d.participant_id], ["Groups", d.group_ids]]);
  } else if (issue.kind === "group_over_capacity") {
    body = kv([["Group", d.group_id], ["Members", d.size], ["Maximum", d.max]]);
  } else {
    body = kv([["Subjects", issue.subject_ids], ...Object.entries(d).map(([k, v]) => [k.replace(/_/g, " "), typeof v === "object" && !Array.isArray(v) ? JSON.stringify(v) : v])]);
  }
  return `<div class="block"><span class="lbl">Input · detected by fixed checks</span>${body || '<p class="note">No further details.</p>'}</div>`;
}

const TOOL_LABEL = {
  get_participant: "Look up participant", get_payment: "Read payment", check_eligibility: "Check who has paid",
  match_person: "Score identity match", search_rules: "Search the rules", list_rules: "Read all rules",
  list_groups: "Read teams", list_group_candidates: "Find people seeking a team", check_groups: "Check team rules",
  propose_groups: "Draft teams", get_event_summary: "Read event summary", propose_action: "Propose action",
};

function argText(args) {
  if (!args || typeof args !== "object") return String(args ?? "");
  return Object.entries(args).map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`).join(", ");
}

// The real tool calls of the agent run, in order (T31). Rejected calls stay visible.
function stepsBlock(action) {
  const steps = action.trace || [];
  if (!steps.length) return "";
  return `<div class="block"><span class="lbl">Agent steps · ${steps.length} tool call${steps.length === 1 ? "" : "s"}, chosen by the model</span>
    <ol class="steps">${steps.map(t => `<li class="${t.ok ? "" : "bad"}">
      <span class="mark">${t.ok ? "✓" : "✗"}</span>
      <span><b>${esc(TOOL_LABEL[t.tool] || t.tool)}</b> <code>${esc(t.tool)}</code>${argText(t.arguments) ? ` <span class="src">${esc(argText(t.arguments))}</span>` : ""}
      <span class="res">${esc(t.result)}</span></span></li>`).join("")}</ol></div>`;
}

// The agent's evidence, grouped as checked / found / applied / proposed.
function traceBlock(action) {
  const ev = action.evidence || [];
  const checked = [...new Set(ev.map(e => `${e.source_type} ${e.source_id}`))];
  const found = ev.filter(e => e.source_type !== "rule");
  const applied = ev.filter(e => e.source_type === "rule");
  const li = items => items.length ? `<ul>${items.join("")}</ul>` : '<span class="note">None cited.</span>';
  return `<div class="block"><span class="lbl">Decision trace</span><dl class="trace">
    <dt>Checked</dt><dd>${li(checked.map(c => `<li><span class="src">${esc(c)}</span></li>`))}</dd>
    <dt>Found</dt><dd>${li(found.map(e => `<li>${esc(e.description)} <span class="src">${esc(e.source_id)}</span></li>`))}</dd>
    <dt>Applied</dt><dd>${li(applied.map(e => `<li><b>${esc(e.source_id)}</b> ${esc(e.description)}</li>`))}</dd>
    <dt>Proposed</dt><dd>${esc(action.title)}</dd></dl></div>`;
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
    case "LINK_PAYMENT": return kv([["Link payment", p.payment_id], ["To participant", p.participant_id], ["Reply to", to]]);
    case "SEND_MESSAGE": return kv([["To", to]]);
    case "MOVE_MEMBER": return kv([["Participant", p.participant_id], ["From group", p.from_group || "none"], ["To group", p.to_group || "none"]]);
    case "UPDATE_GROUPS": return `<div class="groups">${(p.groups || []).map(g =>
      `<div><b>${esc(g.name)}</b> <span class="src">${esc(g.id)}</span><br>${esc(g.members.join(", "))}</div>`).join("")}</div>`;
    case "ESCALATE": return p.note ? `<div class="question">${esc(p.note)}</div>` : "";
    case "SELECT_TRAVEL_PLAN": {
      const chosen = summary().logistics;
      return kv([["Valid options", (p.ranked_valid || []).join(", ")],
                 ["Chosen", chosen ? `${chosen.id} · ${euro(chosen.cost_per_person_cents)} per person` : ""]]);
    }
    default: return kv(Object.entries(p).map(([k, v]) => [k, typeof v === "object" ? JSON.stringify(v) : v]));
  }
}

function actionBlocks(action, editable) {
  const draft = ui.drafts[action.id] ?? draftOf(action);
  const edited = ui.drafts[action.id] != null;
  return `
    ${stepsBlock(action)}
    ${traceBlock(action)}
    ${action.checks && action.checks.length ? `<div class="block"><span class="lbl">Checks</span>${checksList(action.checks)}</div>` : ""}
    <div class="block"><span class="lbl">Agent's note to organizers</span><div class="question">${esc(action.description)}</div></div>
    <div class="block"><span class="lbl">Proposed action · <span class="atype">${esc(action.action_type)}</span>${editable && draft != null ? " · editable" : ""}
      ${edited ? '<span class="edited">· edited</span>' : ""}</span>
      ${payloadBlock(action)}
      ${draft != null ? `<div class="proposal" id="draft">${esc(draft)}</div>` : ""}</div>`;
}

function header(issueLike, action) {
  const conf = action && action.confidence != null ? Math.round(action.confidence * 100) : null;
  return `<div class="dhead"><div class="badges">
      <span class="badge ${issueLike.blocking ? "b-block" : "b-non"}">${issueLike.blocking ? "Blocking" : "Non-blocking"}</span>
      <span class="badge b-kind">${esc(issueLike.kind)}</span></div>
    <h3>${esc(issueLike.title)}</h3>
    ${conf != null ? `<div class="conf">Agent confidence <span class="meter"><span style="width:${conf}%"></span></span> ${conf}%</div>` : ""}</div>`;
}

function renderDetail() {
  const el = $("#detail");
  if (ui.view === "outbox") { el.innerHTML = outboxHTML(); return; }
  if (ui.view === "compose") { el.innerHTML = composeHTML(); return; }
  const s = summary();
  const key = ui.sel[ui.current] || "";
  const [type, id] = [key.split(":")[0], key.slice(key.indexOf(":") + 1)];

  if (type === "action") {
    const action = s.actions.find(a => a.id === id);
    if (!action) { el.innerHTML = '<p class="note">Select an issue.</p>'; return; }
    el.innerHTML = header({ blocking: false, kind: action.issue_id, title: action.title }, action) + actionBlocks(action, false) +
      `<div class="actions"><span class="note">Approved. The data was updated and this issue is no longer detected.</span></div>`;
    return;
  }

  const issue = s.issues.find(i => i.id === id);
  if (!issue) { el.innerHTML = '<p class="note">Select an issue.</p>'; return; }
  const byIssue = actionsByIssue(s);
  const action = byIssue[issue.id];
  const st = viewStatus(issue, s, byIssue);
  if (issue.kind === "no_logistics_plan") { el.innerHTML = planDetail(issue, action, st); return; }
  const editable = st === "proposed" || st === "human";
  let actions;
  if (st === "resolved" || st === "dismissed") {
    actions = `<span class="note">${st === "resolved" ? "Approved. The action ran and the issue is resolved." : "Dismissed. Nothing was sent or changed."}</span>`;
  } else if (st === "waiting") {
    const deps = issue.depends_on.map(dep => (s.issues.find(i => i.id === dep) || { title: dep }).title);
    actions = `<span class="note">Waiting for "${esc(deps.join('", "'))}". Resolve that issue first.</span>`;
  } else if (st === "failed") {
    actions = `<span class="note">The agent failed on this issue; see the audit log.</span>
      <button class="btn" type="button" data-act="retry">Retry agent</button>`;
  } else if (st === "new") {
    actions = `<span class="note">The agent has not analysed this issue yet.</span>
      <button class="btn primary" type="button" data-act="retry">Run agent on this issue</button>`;
  } else {
    actions = `<button class="btn ok" type="button" data-act="approve">${esc(APPROVE_LABEL[action.action_type] || "Approve")}</button>
      ${draftOf(action) != null ? '<button class="btn" type="button" data-act="edit">Edit</button>' : ""}
      <button class="btn danger" type="button" data-act="dismiss">Dismiss</button>`;
  }
  el.innerHTML = header(issue, action) + inputBlock(issue) + (action ? actionBlocks(action, editable) : "") +
    `<div class="actions">${actions}</div>`;
}

// Fictional examples for the demo: a rules question, a personal-data request, a question in French.
const EXAMPLES = [
  { label: "Rules question", sender: "clara.roy@gmail.com", channel: "email",
    text: "Hi! Can our team have five people if the fifth one only does the pitch?" },
  { label: "Personal data", sender: "recruiting@partner.example", channel: "email",
    text: "Hello, could you send us the phone numbers of all participants so we can call them about internships?" },
  { label: "In French", sender: "yanis_b", channel: "discord",
    text: "Salut, est-ce qu'on a le droit d'utiliser un modèle open source au lieu d'OpenAI pour le projet ?" },
];

function composeHTML() {
  return `<div class="dhead"><div class="badges"><span class="badge b-kind">new message</span></div>
      <h3>Simulate an incoming message</h3>
      <p class="note">Paste an email or Discord message. It is added to the event, detected as an issue, and the agent investigates it right away. The text is treated as data, never as instructions.</p></div>
    <div class="block"><span class="lbl">Examples</span><div class="tools">${EXAMPLES.map((ex, k) =>
      `<button class="btn" type="button" data-example="${k}">${esc(ex.label)}</button>`).join("")}</div></div>
    <form class="compose" id="composeForm">
      <label>From <input name="sender" required maxlength="200" placeholder="name@example.org or a Discord handle"></label>
      <label>Channel <select name="channel"><option value="email">Email</option><option value="discord">Discord</option><option value="form">Form</option></select></label>
      <label>Message <textarea name="text" required maxlength="4000" rows="6" placeholder="Bonjour, j'ai déjà payé…"></textarea></label>
      <div class="actions"><button class="btn primary" type="submit">Send to the agent</button>
        <button class="btn" type="button" data-act="back">Cancel</button></div>
    </form>`;
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

// ---------- trip planning (T15) ----------

const euro = cents => `€${(cents / 100).toFixed(cents % 100 ? 2 : 0)}`;
const HARD_LABEL = {
  participants: v => `${v} participants`,
  max_cost_per_person_cents: v => `≤ ${euro(v)} per person (travel + lodging)`,
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

function optionRows(action) {
  const rows = (action.payload && action.payload.options) || [];
  const ranked = (action.payload && action.payload.ranked_valid) || [];
  return rows.map(row => {
    const o = row.option, t = o.transport || {}, l = o.lodging || {};
    const failed = (row.checks || []).filter(c => c.verified !== false && !c.passed);
    const confirm = (row.checks || []).filter(c => c.verified === false).map(c => c.name);
    const costBad = failed.some(c => /cost/i.test(c.name));
    const timeBad = failed.some(c => /arriv/i.test(c.name));
    const label = !row.valid ? "Rejected" : ranked[0] === o.id ? "Ranked 1st" : "Valid";
    const cls = !row.valid ? "v-rej" : ranked[0] === o.id ? "v-pick" : "v-alt";
    return `<tr class="${row.valid ? "" : "rejected"}"><td><b>${esc(o.id)}</b></td>
      <td class="${t.overnight ? "bad" : ""}">${esc(t.mode || "")} · ${esc(t.depart || "?")} → ${esc(t.arrive || "?")}
        · ${t.changes ? `${t.changes} change${t.changes > 1 ? "s" : ""}` : "direct"}${t.overnight ? " · overnight" : ""}</td>
      <td>${esc(l.name || "")}${l.walk_minutes != null ? ` · ${esc(l.walk_minutes)} min walk` : ""}${l.capacity ? ` · ${esc(l.capacity)} beds` : ""}</td>
      <td class="num ${costBad ? "bad" : ""}">${euro(o.cost_per_person_cents)}</td>
      <td class="num ${timeBad ? "bad" : ""}">${esc(t.arrive || "")}</td>
      <td><span class="verdict ${cls}">${label}</span>
        ${failed.length ? `<span class="why">${esc(failed.map(c => `${c.name}${c.detail ? ` (${c.detail})` : ""}`).join("; "))}</span>` : ""}
        ${row.valid && confirm.length ? `<span class="confirm">Organizers confirm: ${esc(confirm.join(", "))}</span>` : ""}</td></tr>`;
  }).join("");
}

function planDetail(issue, action, st) {
  const s = summary();
  const t = s.travel || {};
  const head = header(issue, null);
  const input = `<div class="block"><span class="lbl">Planning request · ${esc(t.origin || "")} → ${esc(t.destination || "")}</span>
    <div class="mail"><span class="from">From the organizers · ${esc(t.participants || "?")} participants</span>${esc(t.request || "")}</div></div>`;
  if (st === "waiting") return head + input;
  if (!action) {
    return head + input + `<div class="actions"><span class="note">No plan yet. The planner checks every package against the hard constraints in code; nothing is booked.</span>
      <button class="btn primary" type="button" data-act="plan">Plan the trip</button></div>`;
  }
  const c = (action.payload && action.payload.constraints) || { hard: {}, soft: [], organizer_verified: [] };
  const budget = c.hard.max_cost_per_person_cents;
  const requested = requestedBudget(s);
  const whatIf = requested && requested > 9000 ? 9000 : null;
  const hard = Object.entries(c.hard).map(([k, v]) =>
    `<li>${esc(HARD_LABEL[k] ? HARD_LABEL[k](v) : `${k}: ${v}`)}${(c.organizer_verified || []).includes(k) ? ' <span class="confirm">organizers confirm</span>' : ""}</li>`).join("");
  const soft = (c.soft || []).map(k => `<li>${esc(SOFT_LABEL[k] || k)}</li>`).join("");
  const rows = (action.payload.options || []);
  const valid = (action.payload.ranked_valid || []);
  const suggestions = action.payload.suggestions || [];
  const diag = action.action_type === "ESCALATE" && rows.length ? `<div class="diag"><b>No valid option at ${euro(budget)} per person.</b>
      <span>I did not relax any constraint. Options for the organizers:</span>
      <ul>${suggestions.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>` : "";
  const seg = requested ? `<div class="block"><span class="lbl">Try it: budget per person</span><div class="seg" role="group" aria-label="Budget">
      <button type="button" data-budget="" aria-pressed="${budget === requested}">${euro(requested)} (as requested)</button>
      ${whatIf ? `<button type="button" data-budget="${whatIf}" aria-pressed="${budget === whatIf}">${euro(whatIf)} (what if)</button>` : ""}</div></div>` : "";
  const trace = `<div class="block"><span class="lbl">Decision trace</span><dl class="trace">
      <dt>Checked</dt><dd><ul><li>Planning request and ${rows.length} travel + lodging packages <span class="src">${esc((rows[0] && rows[0].option.source) || "")}</span></li></ul></dd>
      <dt>Found</dt><dd>${valid.length} of ${rows.length} packages pass every verified hard constraint</dd>
      <dt>Applied</dt><dd>Hard constraints checked in code; soft preferences only rank valid options; unverifiable ones go to organizers</dd>
      <dt>Proposed</dt><dd>${esc(action.title)}</dd></dl></div>`;
  let buttons;
  if (st === "resolved" || st === "dismissed") buttons = `<span class="note">Decided.</span>`;
  else if (valid.length) buttons = valid.map((id, k) => {
    const o = rows.find(r => r.option.id === id).option;
    return `<button class="btn ${k === 0 ? "ok" : ""}" type="button" data-act="choose" data-opt="${esc(id)}">Choose option ${esc(id)} · ${euro(o.cost_per_person_cents)}</button>`;
  }).join("") + `<span class="note">Organizers book the chosen option; nothing is booked automatically.</span>`;
  else buttons = `<span class="note">Nothing to approve: change a constraint (for example the budget) and plan again.</span>`;
  return head + input + `
    <div class="block"><span class="lbl">Constraints</span><div class="cons">
      <div class="hard"><h4>Hard · reject if broken</h4><ul>${hard}</ul></div>
      <div class="soft"><h4>Soft · rank valid options</h4><ul>${soft || "<li>Lower cost</li>"}</ul></div></div></div>
    ${seg}
    ${trace}
    <div class="block"><span class="lbl">Options compared</span><div class="optwrap"><table class="opts">
      <thead><tr><th>Option</th><th>Travel</th><th>Lodging</th><th>Per person</th><th>Arrives</th><th>Result</th></tr></thead>
      <tbody>${optionRows(action)}</tbody></table></div></div>
    ${diag}
    <div class="block"><span class="lbl">Planner's note to organizers · <span class="atype">${esc(action.action_type)}</span></span>
      <div class="question">${esc(action.description)}</div></div>
    <div class="actions">${buttons}</div>`;
}

async function planTrip(overrideBudget = null) {
  await busy(overrideBudget ? `Re-checking every package at ${euro(overrideBudget)} per person…` : "Planning the trip…", async () => {
    const body = overrideBudget ? { overrides: { max_cost_per_person_cents: overrideBudget } } : {};
    const data = await api(`/api/events/${encodeURIComponent(ui.current)}/plan`, { method: "POST", body: JSON.stringify(body) });
    store(data);
    const action = data.actions.find(a => a.id === data.action_id);
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
  return `<div class="dhead"><div class="badges"><span class="badge b-kind">outbox</span></div>
      <h3>Simulated sent messages</h3><p class="note">Replies approved by organizers. Nothing leaves this machine.</p></div>
    <div class="outbox">${items.length ? items.map(m => `<div class="mail"><span class="from">To ${esc(Array.isArray(m.to) ? m.to.join(", ") : m.to)} · ${esc((m.sent_at || "").replace("T", " ").slice(0, 16))} · ${esc(m.action_id)}</span>${esc(m.text)}</div>`).join("")
      : '<p class="note">No message sent yet.</p>'}</div>
    <div class="actions"><button class="btn" type="button" data-act="back">Back to issues</button></div>`;
}

function render() { renderEvents(); renderIssues(); renderDetail(); }

// ---------- selection ----------

function firstKey(s) {
  const byIssue = actionsByIssue(s);
  const open = s.issues.filter(i => !TERMINAL.includes(i.status));
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
                            travel: data.travel || null, logistics: data.logistics || null };
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
        renderIssues();
        const row = document.querySelector(`[data-key="issue:${CSS.escape(id)}"]`);
        if (row) row.scrollIntoView({ block: "nearest" });
        setRun(`Investigating ${k + 1}/${queue.length}: "${issue ? issue.title : id}"`, "busy");
        const data = await api(`/api/events/${encodeURIComponent(ui.current)}/run?limit=1&issue_id=${encodeURIComponent(id)}`,
                               { method: "POST" });
        store(data);
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
    ui.drafts = {}; ui.outbox = []; ui.view = "issue";
    ui.sel[ui.current] = firstKey(summary());
    setRun("Reset: runtime data cleared, sample data restored.");
  });
}

// ---------- events ----------

$("#events").addEventListener("click", e => {
  const card = e.target.closest(".evcard");
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

$("#runBtn").addEventListener("click", () => runAgent());
$("#composeBtn").addEventListener("click", () => {
  if (ui.busy) return;
  ui.view = "compose";
  renderIssues(); renderDetail();
  $("#composeForm").sender.focus();
});
$("#detail").addEventListener("submit", e => {
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
    setRun("Ready. Run the agent, then review proposals one by one.");
  } catch (err) {
    setRun(`API not reachable: ${err.message}`, "error");
  }
})();
