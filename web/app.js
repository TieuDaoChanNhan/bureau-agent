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
};

const $ = s => document.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const TERMINAL = ["resolved", "dismissed"];
const APPROVE_LABEL = { LINK_PAYMENT: "Confirm and link", SEND_MESSAGE: "Approve and send", ESCALATE: "Mark as handled" };
const PILL = {
  new: ["p-new", "Not analysed"], proposed: ["p-proposed", "Action proposed"], human: ["p-human", "Needs you"],
  waiting: ["p-wait", "Waiting"], failed: ["p-fail", "Agent failed"], resolved: ["p-res", "Resolved"], dismissed: ["p-rej", "Dismissed"],
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

function needsHuman(action) {
  return action.action_type === "ESCALATE" || (action.confidence != null && action.confidence < 0.98);
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
    const st = viewStatus(issue, s, byIssue);
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
    default: return kv(Object.entries(p).map(([k, v]) => [k, typeof v === "object" ? JSON.stringify(v) : v]));
  }
}

function actionBlocks(action, editable) {
  const draft = ui.drafts[action.id] ?? draftOf(action);
  const edited = ui.drafts[action.id] != null;
  return `
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
  const editable = st === "proposed" || st === "human";
  let actions;
  if (st === "resolved" || st === "dismissed") {
    actions = `<span class="note">${st === "resolved" ? "Approved. The action ran and the issue is resolved." : "Dismissed. Nothing was sent or changed."}</span>`;
  } else if (st === "waiting") {
    const deps = issue.depends_on.map(dep => (s.issues.find(i => i.id === dep) || { title: dep }).title);
    actions = `<span class="note">Waiting for "${esc(deps.join('", "'))}". Resolve that issue first.</span>`;
  } else if (issue.kind === "no_logistics_plan") {
    actions = `<span class="note">Travel planning (option comparison, budget what-if) is handled by the trip view.</span>`;
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
  ui.summaries[data.id] = { id: data.id, name: data.name, counts: data.counts, issues: data.issues, actions: data.actions };
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

// Calls /run in bounded batches until the backlog is empty or a batch makes no progress.
async function runAgent(issueId = null) {
  await busy(issueId ? `Agent investigating ${issueId}…` : "Agent investigating…", async () => {
    let proposed = 0, failed = 0, remaining = 0;
    for (let round = 0; round < 20; round++) {
      const qs = issueId ? `?limit=1&issue_id=${encodeURIComponent(issueId)}` : "?limit=5";
      const before = summary().actions.length;
      const data = await api(`/api/events/${encodeURIComponent(ui.current)}/run${qs}`, { method: "POST" });
      store(data);
      const added = data.actions.length - before;
      proposed += added; failed += data.errors.length; remaining = data.remaining;
      renderEvents(); renderIssues();
      setRun(`Agent: ${proposed} proposals, ${failed} failed, ${remaining} issues left…`, "busy");
      if (issueId || remaining === 0 || (added === 0 && data.errors.length === 0)) break;
    }
    keepSelection();
    setRun(proposed || failed
      ? `Agent finished: ${proposed} proposals ready for review${failed ? `, ${failed} failed (see the audit log)` : ""}${remaining ? `, ${remaining} left` : ""}.`
      : "Nothing for the agent to do: every runnable issue already has a proposal.", failed && !proposed ? "error" : "");
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
  const btn = e.target.closest("[data-act]");
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
  } else if (act === "retry") {
    runAgent(currentAction().issueId);
  } else if (act === "back") {
    ui.view = "issue"; renderIssues(); renderDetail();
  }
});

$("#runBtn").addEventListener("click", () => runAgent());
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
