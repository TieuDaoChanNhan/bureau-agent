/* Static demo adapter. State belongs to one tab; sessionStorage survives reload.
 * No fetch, shared storage, model client, cookies, or credentials are used.
 * These are curated examples, not a substitute for the live Python executor.
 */
function createDemoStore(fixtures, options = {}) {
  const copy = value => JSON.parse(JSON.stringify(value));
  const session = createDemoSession(fixtures, options);
  const events = session.state.events;
  const terminal = issue => ["resolved", "dismissed"].includes(issue.status);
  const signature = "\n— Drafted with AI assistance, approved by the organizers.";
  const fail = (status, message) => { throw new Error(`${status}: ${message}`); };
  const audit = (s, message) => {
    s.audit.push({at: new Date().toISOString(), session: session.state.id, message});
    if (s.audit.length > 300) s.audit.splice(0, s.audit.length - 300);
  };
  const waiting = (s, issue) => issue.depends_on.some(id => s.issues.some(i => i.id === id && !terminal(i)));
  const summary = s => {
    const result = copy(s);
    result.counts = {
      blocking: s.issues.filter(i => !terminal(i) && i.blocking).length,
      non_blocking: s.issues.filter(i => !terminal(i) && !i.blocking).length,
      resolved: s.issues.filter(i => i.status === "resolved").length,
    };
    return result;
  };
  const proposal = (s, issue, type, title, description, payload = {}, evidence = []) => ({
    id: `${s.id}:${issue.id}`, event_id: s.id, issue_id: issue.id,
    action_type: type, title, description, payload, evidence, checks: [],
    confidence: null, requires_approval: true,
    trace: [{step: 1, tool: "get_event_summary", arguments: {}, result: "Saved fictional event snapshot", ok: true},
      {step: 2, tool: "propose_action", arguments: {action_type: type}, result: "Curated sample; organizer approval required", ok: true}],
  });
  const saveProposal = (s, action) => {
    s.actions = s.actions.filter(a => a.issue_id !== action.issue_id);
    s.actions.push(action);
    return action;
  };
  function investigate(s, issue) {
    if (issue.id === "message:m01" || issue.id === "unmatched_payment:f90") {
      const a = copy(fixtures.payment);
      a.id = `${s.id}:${issue.id}`; a.issue_id = issue.id;
      return saveProposal(s, a);
    }
    const text = issue.details.text || "";
    const sample = s.id === "hackathon" && fixtures.scenarios[issue.id.replace(/^message:/, "")];
    const personal = text === "Hello, could you send us the phone numbers of all participants so we can call them about internships?" || (s.id === "hackathon" && issue.id === "message:m05");
    const team = text === "Hi! Can our team have five people if the fifth one only does the pitch?";
    const french = text === "Salut, est-ce qu'on a le droit d'utiliser un modèle open source au lieu d'OpenAI pour le projet ?";
    let a;
    if (sample) {
      a = proposal(s, issue, "SEND_MESSAGE", sample.title,
        "A curated reply to this sample message, based on the displayed rule. Review it before adding it to the simulated outbox.",
        {to: issue.details.sender, text: sample.text + signature},
        [{source_type: "rule", source_id: sample.rule, description: fixtures.rules[sample.rule]},
          {source_type: "message", source_id: issue.id, description: text}]);
      a.trace.unshift({step: 1, tool: "search_rules", arguments: {section: sample.rule}, result: fixtures.rules[sample.rule], ok: true});
    } else if (personal) {
      a = proposal(s, issue, "ESCALATE", "A sponsor requests participants' personal data",
        "The saved example hands this request to the organizers. No participant list or contact details are shared.",
        {note: "Please decide how to respond to the sponsor under the association's personal-data rules."},
        [{source_type: "rule", source_id: "§10", description: "Personal-data requests require organizer review."}]);
      a.trace.unshift({step: 1, tool: "search_rules", arguments: {query: "personal data"}, result: "Saved example: consult §10 and escalate", ok: true});
    } else if (team) {
      const reply = "Hi! Teams may have at most four members, including anyone preparing the pitch. Please form a team within that limit.";
      a = proposal(s, issue, "SEND_MESSAGE", "Review a reply to the rules question", "This is a saved reply to the exact example you selected.",
        {to: issue.details.sender, text: reply + signature},
        [{source_type: "rule", source_id: "§3", description: "Maximum four people per team."}]);
    } else if (french) {
      a = proposal(s, issue, "ESCALATE", "Confirm which models are permitted",
        "The sample rules require an agentic project using LLMs, but do not explicitly specify permitted model providers.",
        {note: "Merci de confirmer avec les organisateurs si le modèle open source envisagé est autorisé."},
        [{source_type: "rule", source_id: "§2", description: "Projects must use LLMs and implement real agent logic; provider choice is not specified."}]);
    } else {
      a = proposal(s, issue, "ESCALATE", "Organizer review needed",
        "No tailored response is saved for this issue. The public demo does not analyze arbitrary messages. In the live application, the agent investigates with tools.",
        {note: "Review this issue manually. Mark as handled only after you have made the decision; dismissing leaves the sample records unchanged."},
        [{source_type: "issue", source_id: issue.id, description: "Original issue retained for organizer review; no new facts inferred."}]);
      a.trace = [];
    }
    return saveProposal(s, a);
  }
  function plan(s, body) {
    const issue = s.issues.find(i => i.id === "no_logistics_plan");
    if (!issue || terminal(issue)) fail(409, "Reset the event before planning again.");
    const prior = s.actions.find(a => a.issue_id === issue.id);
    if (!body.text && !prior?.payload?.answered) {
      return saveProposal(s, proposal(s, issue, "ESCALATE", "Does the budget include coach hire?",
        "Clarify coach inclusion before comparing the saved complete packages.",
        {clarifications: [fixtures.budget_question], request_text: s.travel.request}));
    }
    // The UI supplies a fixed answer: this static demo performs no text extraction.
    if (body.text && ![fixtures.budget_answer, s.travel.request + "\n\nOrganizer answers: " + fixtures.budget_answer].includes(body.text)) {
      fail(422, "This saved scenario supports the provided answer only; no live text analysis is available.");
    }
    const hard = {...s.travel.constraints.hard, ...prior?.payload?.constraints?.hard, ...body.overrides};
    const budget = hard.max_cost_per_person_cents;
    if (!Number.isSafeInteger(budget) || budget < 100 || budget > 100000) fail(422, "Enter a budget from €1 to €1,000 per person.");
    if (!Number.isInteger(hard.participants) || hard.participants < 1 || hard.participants > 200) fail(422, "Enter a group size from 1 to 200.");
    if (!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(hard.arrive_before)) fail(422, "Enter a valid arrival deadline.");
    if (Object.keys(body.overrides || {}).some(k => !["max_cost_per_person_cents", "participants", "arrive_before"].includes(k))) fail(422, "This demo supports budget, group size and arrival deadline changes.");
    const a = copy(fixtures.plan);
    a.payload.constraints = copy(s.travel.constraints);
    a.payload.constraints.hard = hard;
    a.payload.answered = true;
    a.payload.request_text = body.text || prior.payload.request_text;
    a.payload.options.forEach(row => {
      const o = row.option;
      row.checks = [
        {name: "itemized cost matches total", passed: Object.values(o.cost_breakdown_per_person_cents).every(n => Number.isInteger(n) && n >= 0) && Object.values(o.cost_breakdown_per_person_cents).reduce((a,b) => a+b, 0) === o.cost_per_person_cents, verified: true, detail: "Coach + lodging + groceries + food transport"},
        {name: `cost ≤ €${budget / 100}/person`, passed: o.cost_per_person_cents <= budget, verified: true, detail: `€${o.cost_per_person_cents / 100}`},
        {name: `arrive before ${hard.arrive_before}`, passed: !o.transport.arrives_next_day && o.transport.arrive <= hard.arrive_before, verified: true, detail: o.transport.arrive},
        {name: "no overnight travel", passed: !o.transport.overnight, verified: true, detail: ""},
        {name: `lodging for ${hard.participants}`, passed: o.lodging.capacity >= hard.participants, verified: true, detail: String(o.lodging.capacity)},
        {name: "2 step-free rooms and group availability", passed: null, verified: false, detail: "Organizers must confirm with the venue"},
      ];
      row.valid = row.checks.filter(c => c.verified).every(c => c.passed);
      o.source = "Illustrative repository fixture — not a live quote";
    });
    const priorities = {fewer_changes: o => o.transport.changes || 0, near_station: o => o.lodging.walk_minutes ?? 99,
      early_return: o => o.transport.return_arrive || "23:59", lower_cost: o => o.cost_per_person_cents};
    a.payload.ranked_valid = a.payload.options.filter(r => r.valid).sort((x, y) => {
      for (const key of [...a.payload.constraints.soft, "lower_cost"]) {
        const value = priorities[key]; if (!value) continue;
        const left = value(x.option), right = value(y.option);
        if (left !== right) return left < right ? -1 : 1;
      }
      return 0;
    }).map(r => r.option.id);
    a.action_type = a.payload.ranked_valid.length ? "SELECT_TRAVEL_PLAN" : "ESCALATE";
    a.title = `${a.payload.ranked_valid.length} of ${a.payload.options.length} sample options pass verified constraints`;
    a.description = a.payload.ranked_valid.length ? `Option ${a.payload.ranked_valid[0]} ranks first under the stated preferences. ${a.payload.ranked_valid.length} package(s) pass the verified constraints. Accessibility and group availability still need confirmation. Sample prices stay fixed when group size changes; these are not live quotes.`
      : `No sample option meets the €${budget / 100} budget, ${hard.participants}-person capacity and arrival deadline of ${hard.arrive_before} together. No requirement was relaxed.`;
    a.payload.suggestions = ["Adjust the budget, group size or arrival deadline explicitly, or ask organizers to source other offers."];
    audit(s, `Compared sample packages: €${budget / 100}/person, ${hard.participants} participants, before ${hard.arrive_before}; ${a.payload.ranked_valid.length} valid.`);
    return saveProposal(s, a);
  }
  function decide(s, action, operation, body) {
    const issue = s.issues.find(i => i.id === action.issue_id);
    if (!issue || terminal(issue)) fail(409, "This proposal has already been decided.");
    if (waiting(s, issue)) fail(409, "Resolve the prerequisite first.");
    if (operation === "dismiss") {
      issue.status = "dismissed";
      audit(s, `Dismissed: ${action.title}. No sample records changed.`);
      return;
    }
    let selected;
    if (action.action_type === "SELECT_TRAVEL_PLAN") {
      selected = action.payload.options.find(r => r.option.id === body.option_id);
      if (!selected || !selected.valid || !action.payload.ranked_valid.includes(body.option_id)) fail(409, "Choose a valid sample package.");
    } else if (action.action_type === "LINK_PAYMENT") {
      if (action.confidence < 0.7) fail(409, "Identity evidence is insufficient.");
      if (s.linkedPayment) fail(409, "The sample payment is already linked.");
    } else if (!["ESCALATE", "SEND_MESSAGE"].includes(action.action_type)) fail(422, "Unsupported sample action.");
    const draft = action.action_type === "SEND_MESSAGE" ? action.payload.text : action.payload.message;
    const edited = body.edited_description ?? draft;
    if (draft != null && (typeof edited !== "string" || !edited.trim() || edited.length > 10000)) fail(422, "Reply must contain 1–10,000 characters.");
    if (selected) s.logistics = copy(selected.option);
    if (action.action_type === "LINK_PAYMENT") {
      s.linkedPayment = action.payload.participant_id;
      // Reconciliation resolves related detections as well as the incoming message.
      for (const other of s.issues) {
        if (["unmatched_payment:f90", "message:m01"].includes(other.id)) other.status = "resolved";
        if (other.kind === "unpaid_membership" && other.subject_ids.includes("p01")) {
          other.subject_ids = other.subject_ids.filter(id => id !== "p01");
          if (Array.isArray(other.details.participant_ids)) other.details.participant_ids = other.details.participant_ids.filter(id => id !== "p01");
          if (!other.subject_ids.length) other.status = "resolved";
        }
      }
    }
    if (draft != null) {
      s.outbox.push({action_id: action.id, to: action.payload.to, text: edited, sent_at: new Date().toISOString()});
      if (action.action_type === "SEND_MESSAGE") action.payload.text = edited;
      else action.payload.message = edited;
    }
    issue.status = "resolved";
    issue.resolved_by_action_id = action.id;
    audit(s, `Approved: ${action.title}. ${selected ? "Sample travel plan selected; nothing booked." : draft != null ? "Reply added to simulated outbox; nothing sent." : "Marked as handled by an organizer."}`);
  }
  function request(path, options = {}) {
    const url = new URL(path, "https://demo.invalid");
    const parts = url.pathname.split("/").filter(Boolean).map(decodeURIComponent);
    const method = options.method || "GET";
    const body = options.body ? JSON.parse(options.body) : {};
    if (parts[0] !== "api") fail(404, "Unknown demo route.");
    if (parts[1] === "events" && parts.length === 2 && method === "GET") return Object.values(events).map(summary);
    if (parts[1] === "events") {
      const s = events[parts[2]];
      if (!s) fail(404, "Unknown sample event.");
      const route = parts[3];
      if (!route && method === "GET") return summary(s);
      if (["outbox", "audit"].includes(route) && method === "GET") return copy(s[route]);
      if (method !== "POST") fail(405, "Unsupported demo operation.");
      if (route === "reset") {
        events[s.id] = copy(fixtures.events[s.id]);
        for (const key of Object.keys(session.state.drafts)) if (key.startsWith(s.id + ":")) delete session.state.drafts[key];
        return summary(events[s.id]);
      }
      if (route === "run") {
        const id = url.searchParams.get("issue_id");
        const issues = s.issues.filter(i => (!id || i.id === id) && !terminal(i) && !waiting(s, i) && i.kind !== "no_logistics_plan" && !s.actions.some(a => a.issue_id === i.id));
        issues.forEach(i => { const a = investigate(s, i); audit(s, `Loaded saved proposal: ${a.title}. Model calls: 0.`); });
        return {...summary(s), remaining: 0, errors: []};
      }
      if (route === "plan") { const a = plan(s, body); return {...summary(s), action_id: a.id}; }
      if (route === "messages") {
        if (typeof body.text !== "string" || !body.text.trim() || body.text.length > 4000 || typeof body.sender !== "string" || !body.sender.trim() || body.sender.length > 200) fail(422, "Enter a sender and a message (maximum 4,000 characters).");
        if (s.issues.filter(i => i.id.startsWith("message:live")).length >= 50) fail(429, "This tab has 50 sample messages. Reset the event to start again.");
        const id = `message:live${++session.state.sequence}`;
        s.issues.push({id, kind: "unprocessed_message", blocking: false, title: `Message from ${body.sender}`, subject_ids: [],
          status: "open", depends_on: [], details: {sender: body.sender, text: body.text, channel: body.channel || "email"}});
        return {...summary(s), issue_id: id};
      }
    }
    if (parts[1] === "actions" && method === "POST" && ["approve", "dismiss"].includes(parts[3])) {
      const s = Object.values(events).find(e => e.actions.some(a => a.id === parts[2]));
      if (!s) fail(404, "Unknown sample proposal.");
      decide(s, s.actions.find(a => a.id === parts[2]), parts[3], body);
      delete session.state.drafts[parts[2]];
      return summary(s);
    }
    fail(404, "Unknown demo route.");
  }
  return {
    request(path, options = {}) {
      if (session.expireIfNeeded() && options.method === "POST" && !path.endsWith("/reset")) {
        fail(409, "Your demo session expired after 24 hours. Sample data was restored; please run this step again.");
      }
      const result = request(path, options); session.save(); return result;
    },
    sessionInfo: session.info,
    drafts: () => copy(session.state.drafts),
    saveDrafts(drafts) { session.state.drafts = copy(drafts); session.save(); },
  };
}
