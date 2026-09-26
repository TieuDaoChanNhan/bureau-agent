// Guided product tour (T34), built on Driver.js (web/vendor/, MIT).
//
// Two kinds of steps:
//   explanation  highlight a region; the viewer reads and clicks Next.
//   action       highlight exactly one control; the viewer clicks it and the tour moves on by
//                itself when `done()` becomes true (proposal created, plan computed...).
// `prepare()` runs before a step is shown and does the navigation (select an event or issue,
// pre-fill a form), so the viewer's clicks are only the product's real actions.
// To add a step: insert an object in STEPS below; `el` is a CSS selector resolved when shown.

const tourState = { driver: null, poll: null, started: 0 };

const hackathon = () => ui.summaries.hackathon;
const wei = () => ui.summaries.wei;
const planAction = () => (wei() ? wei().actions.find(a => a.issue_id === "no_logistics_plan") : null);

async function tourShow(ev, key) {
  if (ui.current !== ev) await selectEvent(ev);
  ui.view = "issue";
  if (key) ui.sel[ev] = key;
  render();
  const row = key && document.querySelector(`[data-key="${CSS.escape(key)}"]`);
  if (row) row.scrollIntoView({ block: "nearest" });
}

async function tourResetAll() {
  for (const ev of Object.keys(ui.summaries)) {
    store(await api(`/api/events/${encodeURIComponent(ev)}/reset`, { method: "POST" }));
    ui.sel[ev] = firstKey(summary(ev));
  }
  ui.drafts = {};
  ui.outbox = [];
  ui.current = null;
  await tourShow("hackathon", "issue:multiple_group_membership:p02");
  setRun("Tour: sample data restored for both events.");
}

const b = text => `<b>${text}</b>`;
const CLICK = label => `<p class="tour-do">👉 Click ${b(label)} (highlighted).</p>`;

const STEPS = [
  {
    title: "Welcome to Bureau Agent",
    text: `<p>Volunteer boards run events on top of their studies: registrations, fees, teams, rooms, trips and dozens of messages.
      Bureau Agent keeps an event consistent. <b>Code</b> detects what needs attention, an <b>AI agent</b> investigates with tools and
      proposes one action with its evidence, and <b>you</b> approve, edit or dismiss it.</p>
      <p>This tour takes about 5 minutes and shows every feature on two sample events. It uses the live agent (a few cents of API
      credit). <b>Clicking Next resets the sample data</b> so the tour starts clean. Press Esc at any time to leave.</p>`,
    next: tourResetAll,
  },
  {
    el: "#eventbar", title: "One console, several events",
    text: `<p>An association runs several events at once. Each tab is one event: here a 50-person hackathon; the second tab is a
      100-student integration weekend (WEI) with a trip to organize.</p>
      <p>The numbers below are live for the selected event: ${b("blocking")} issues stop the event from running (unpaid fees,
      broken teams), ${b("ready for your review")} counts proposals waiting for you, ${b("waiting")} issues depend on another one,
      and ${b("resolved")} is what is done.</p>`,
  },
  {
    el: "#issues", title: "Issues found by code, before any AI",
    text: `<p>Fixed checks read the registrations, payments, teams and inbox and list everything that needs attention,
      ${b("blocking first")}. Each issue has a stable id, so a decision is never lost when the data is checked again.</p>
      <p>The label on the right is the status: ${b("Not analysed")} (the agent has not looked yet), ${b("Action proposed")},
      ${b("Needs you")} (the agent wants your decision), ${b("Waiting")} (depends on another issue) and ${b("Resolved")}.</p>`,
  },
  {
    el: '#detail [data-sec="input"]', title: "What the code detected",
    prepare: () => tourShow("hackathon", "issue:multiple_group_membership:p02"),
    text: `<p>Léa Martin is registered in two teams, but the rules say one team per person. This was found by a deterministic check,
      not guessed by a model: the ${b("Input")} section shows exactly what the check saw.</p>
      <p>Rules that must always hold (team size, one team per person, identity thresholds, budgets) are enforced in code. The AI is used
      only where language and judgment are needed.</p>`,
  },
  {
    el: '[data-act="retry"], #detail .thinking', title: "Let the agent investigate a message", action: true,
    prepare: () => tourShow("hackathon", "issue:message:m01"),
    text: `<p>Antoine writes (in French) that he already paid his membership fee from his personal email, yet keeps getting reminders.
      Answering him means checking registrations and payments, which usually takes a volunteer several minutes.</p>${CLICK("Run agent on this issue")}
      <p class="tour-wait">The agent needs about 10–20 seconds. The tour continues by itself.</p>`,
    done: () => hackathon().actions.some(a => a.issue_id === "message:m01"),
  },
  {
    el: ".steps", title: "Agent steps: the tools it chose",
    text: `<p>Each line is a tool call ${b("chosen by the model")}, in order, with its arguments and a one-line result. Typically it checks
      who has paid, looks up the sender, reads the unmatched payments and scores the identity match between "A. Nguyen" and Antoine.</p>
      <p>No step is hard-coded: another message leads to other tools. A rejected call (for example an invalid proposal blocked by code)
      would appear here in red.</p>`,
  },
  {
    el: '#detail [data-sec="evidence"]', title: "Evidence: the decision trace",
    prepare: () => { ui.open.evidence = true; renderDetail(); },
    text: `<p>The evidence behind the proposal, grouped as ${b("Checked")} (records and rules consulted), ${b("Found")} (facts),
      ${b("Applied")} (rule sections) and ${b("Proposed")}. Hover a name to see the underlying id.</p>
      <p>Below it, ${b("Checks")} lists what was verified: ✓ passed, ✗ failed, ? must be confirmed by a person. This section is
      folded by default so the proposal stays in front; open it whenever you want to audit a decision.</p>`,
  },
  {
    el: "#detail .proposal-card .question", title: "The agent asks instead of guessing",
    text: `<p>The identity score is 0.91: a strong match, but below the 0.98 needed to be sure. So the agent does not decide alone. It
      proposes the link ${b("and asks you to confirm")}, which is why the issue shows ${b("Needs you")}.</p>
      <p>If the score had been below 0.70, code would have refused the link entirely, whatever the model said.</p>`,
  },
  {
    el: '[data-act="edit"]', title: "The proposed action and its draft reply", action: true, side: "left",
    text: `<p>The proposal links the payment ${b("A. Nguyen · 10 EUR")} to ${b("Antoine Nguyen")} and includes a draft reply to Antoine, in
      his language, signed as drafted with AI assistance. Nothing has been changed or sent yet.</p>${CLICK("Edit")}`,
    done: () => !!document.querySelector('#draft[contenteditable="true"]'),
  },
  {
    el: "#draft", title: "Edit the reply", action: true, side: "top",
    text: `<p>The highlighted reply is now editable: click into it and change a word or add a sentence (for example
      "Merci pour votre patience !").</p><p class="tour-do">👉 Then click ${b("Save the reply")} below.</p>`,
    button: { label: "Save the reply", run: () => { const btn = document.querySelector('[data-act="edit"]'); if (btn) btn.click(); } },
    done: () => !document.querySelector('#draft[contenteditable="true"]'),
  },
  {
    el: '[data-act="approve"]', title: "You approve, then it happens", action: true, side: "left",
    text: `<p>Only an organizer's approval changes data. Approving will link the payment to Antoine, mark him as paid, and put
      ${b("your edited reply")} in the outbox. The executor re-checks every rule at this moment.</p>${CLICK("Confirm and link")}`,
    done: () => (hackathon().issues.find(i => i.id === "message:m01") || {}).status === "resolved",
  },
  {
    el: "#issues", title: "The data changed",
    text: `<p>Look at the list: the issue ${b('Payment from "A. Nguyen" may belong to Antoine Nguyen')} is gone, because the payment is
      now linked, and Antoine now counts as paid (he will not get reminders). The message moved to the ${b("Done")} group at the
      bottom, and the card counts updated. Approving the same proposal twice is refused.</p>`,
  },
  {
    el: "#outboxBtn", title: "Outbox", action: true,
    text: `<p>Replies approved by organizers are collected in the outbox. In this demo nothing leaves the machine; in real use this is
      where emails would be sent.</p>${CLICK("Outbox")}`,
    done: () => ui.view === "outbox",
  },
  {
    el: "#detail", title: "Your edited reply",
    text: `<p>The reply to Antoine is here, exactly as you edited it, with the time it was sent and the action it came from.
      Every approval is also written to an audit log.</p>`,
  },
  {
    el: "#composeBtn", title: "Try a message of your own", action: true,
    text: `<p>You can add any incoming message (email, Discord, form) and watch the agent handle it live. The text is treated as data,
      never as instructions to the agent.</p>${CLICK("New message")}`,
    done: () => ui.view === "compose",
  },
  {
    el: "#composeForm, #detail .thinking", title: "A risky request", action: true,
    prepare: () => {
      const ex = EXAMPLES[1], form = $("#composeForm");
      if (form) { form.sender.value = ex.sender; form.channel.value = ex.channel; form.text.value = ex.text; }
    },
    text: `<p>We filled in an example: a sponsor asks for the phone numbers of all participants. You can also type your own message,
      in English or French.</p>${CLICK("Send to the agent")}<p class="tour-wait">The agent runs right away (10–20 seconds).</p>`,
    done: () => hackathon().actions.some(a => a.issue_id.startsWith("message:live")),
  },
  {
    el: "#detail", title: "It refuses to share personal data",
    text: `<p>The agent searched the rules, found the personal-data section (§10), and ${b("escalated")} to the organizers instead of
      sharing anything. Questions the rules do not answer, refunds and exceptions are escalated the same way.</p>
      <p>For an escalation you can ${b("Mark as handled")} once you have decided, or ${b("Dismiss")} it.</p>`,
  },
  {
    el: "#runBtn", title: "Run the agent on everything",
    text: `<p>${b("Run agent")} processes every issue that is ready, one at a time: the row being investigated shows ${b("Running…")},
      the status line shows "Investigating 7/30", and the button becomes ${b("Stop")}. The agent only proposes; you still review each
      proposal. (Not run in this tour, to save time and credit.)</p>`,
  },
  {
    el: '[data-ev="wei"]', title: "Same loop, another kind of event", action: true,
    text: `<p>The integration weekend adds something harder: organizing a trip for 100 students under several constraints.</p>${CLICK("the Student association WEI tab")}`,
    done: () => ui.current === "wei",
  },
  {
    el: "#issues", title: "Issues waiting for a decision",
    text: `<p>Several issues show ${b("Waiting")}: payment reminders need the exact price, rooms need the chosen lodging,
      and four student messages (meeting time, step-free access, the kitchen, the coaches) need the chosen package. They all
      depend on ${b("No validated travel and lodging plan")}, which is selected on the right.</p>`,
  },
  {
    el: '[data-act="plan"]', title: "Plan the trip", action: true,
    prepare: () => tourShow("wei", "issue:no_logistics_plan"),
    text: `<p>The request is the organizers' own words (shown above): 100 students, leave the Palaiseau campus Friday after 17:00,
      €150 per person with meals included, arrive before 21:00, no overnight travel, two step-free rooms, two coaches.</p>
      <p>An AI model turns these words into structured constraints; code will then check every package against them.</p>${CLICK("Plan the trip")}`,
    done: () => !!(document.querySelector("#answerForm") || document.querySelector(".opts")),
  },
  {
    el: "#clarify", title: "The planner asks before searching", action: true, side: "left",
    prepare: () => {
      const form = $("#answerForm");
      if (form) form.answer.value = "Yes, the €150 covers the complete package: coaches, lodging and meals.";
    },
    text: `<p>The organizers say meals are included but are unsure whether the €150 also covers ${b("coach hire")}. The planner
      ${b("asks")} instead of assuming, and nothing is searched yet. We filled in an answer; you can change it.</p>${CLICK("Answer and plan again")}<p class="tour-wait">About 10 seconds.</p>`,
    done: () => !!document.querySelector(".opts"),
  },
  {
    el: ".cons", title: "Constraints extracted from the request",
    text: `<p>${b("Hard")} constraints reject a package if broken: budget, arrival time, no overnight travel, capacity. ${b("Soft")}
      preferences only rank the valid packages.</p>
      <p>Step-free rooms are marked ${b("organizers confirm")}: hotel data cannot prove accessibility, so it is never used to accept
      or reject a package.</p>`,
  },
  {
    el: ".optwrap", title: "Packages built from real hotel offers",
    text: `<p>Each package is one coach departure plus one hotel, priced per person in code with the meal budget added once. Hotels come from ${b("Jinko")} (real offers in
      Deauville, cached); departures are recorded fares. The valid packages are the cards, ranked first highlighted; the table lists
      the rejected ones with the broken constraint in red (arrives after 21:00, overnight travel, over budget). Here 3 of 8 pass.</p>
      <p>Jinko only quotes small bookings, so every hotel says ${b("Group block to confirm with the hotel")}: the agent is explicit about
      what it could not verify.</p>`,
  },
  {
    el: '[data-budget]:not([data-budget=""])', title: "What if the budget were lower?", action: true,
    text: `<p>Organizers often ask "could we charge students less?". Try €120 per person.</p>${CLICK("€120 (what if)")}`,
    done: () => !!document.querySelector(".diag"),
  },
  {
    el: ".diag", title: "No valid option: it says so",
    text: `<p>At €120 no package passes every hard constraint. The planner ${b("does not relax any constraint by itself")}: it explains
      which single change would unlock each option, and leaves that decision to the organizers.</p>`,
  },
  {
    el: '[data-budget=""]', title: "Back to the requested budget", action: true,
    text: `<p>Return to the budget the organizers asked for.</p>${CLICK("€150 (as requested)")}`,
    done: () => !!document.querySelector('[data-act="choose"]'),
  },
  {
    el: '[data-act="choose"]', title: "Choose a package", action: true,
    text: `<p>The first valid package is ranked first under the stated preferences, with the trade-off explained above the buttons.
      Nothing is booked: organizers book the chosen option themselves.</p>${CLICK("Choose option …")}`,
    done: () => !!(wei() && wei().logistics),
  },
  {
    el: "#issues", title: "Dependent issues are unlocked",
    text: `<p>The plan is set, so the reminders, room assignment and the four messages are no longer ${b("Waiting")}: they can now
      be run through the agent with the real price and departure time. Resolving one issue unlocked six others.</p>`,
  },
  {
    title: "That's the whole loop",
    text: `<p>Code detects, the agent investigates and proposes with evidence, rules are enforced in code, and people approve
      everything that has consequences.</p>
      <p>Explore on your own: ${b("Run agent")} on other issues, send your own ${b("New message")}, or click ${b("Reset demo")} twice to
      start again. The ${b("Demo tour")} button replays this tour.</p>`,
  },
];

function tourStopPolling() {
  if (tourState.poll) { clearInterval(tourState.poll); tourState.poll = null; }
}

async function tourAdvance() {
  tourStopPolling();
  const d = tourState.driver;
  const i = d.getActiveIndex();
  if (i == null) return;
  const cur = STEPS[i];
  if (cur.next) {
    try { await cur.next(); } catch (err) { setRun(err.message, "error"); }
  }
  if (i + 1 >= STEPS.length) { d.destroy(); return; }
  const nxt = STEPS[i + 1];
  if (nxt.prepare) {
    try { await nxt.prepare(); } catch (err) { setRun(err.message, "error"); }
  }
  d.moveNext();
}

// Poll for the expected result of an action step, and move on when it appears.
function tourWatch(step) {
  tourStopPolling();
  tourState.started = Date.now();
  if (step.done()) { tourAdvance(); return; }
  let rehighlighted = false;
  tourState.poll = setInterval(() => {
    if (step.done()) { tourAdvance(); return; }
    // The console re-renders while the agent works: when the highlighted control is gone, highlight
    // the step again so the selector can match the "thinking" panel (once per step, to avoid flicker).
    if (!rehighlighted && !document.querySelector(".driver-active-element") && document.querySelector("#detail .thinking")) {
      rehighlighted = true;
      tourState.driver.moveTo(tourState.driver.getActiveIndex());
      return;
    }
    const status = document.querySelector(".tour-status");
    if (status && ui.busy && !status.dataset.working) {
      status.dataset.working = "1";
      status.textContent = "The agent is working… the tour continues by itself.";
    }
    const failed = !ui.busy && $("#run").classList.contains("error");
    if (status && failed) status.textContent = `Something went wrong: ${$("#runText").textContent}. Use Skip step, or Close.`;
    else if (status && Date.now() - tourState.started > 120000) status.textContent = "This is taking long. Use Skip step to continue.";
  }, 400);
}

function startTour() {
  if (!window.driver || !window.driver.js) { setRun("The tour library did not load.", "error"); return; }
  if (tourState.driver) tourState.driver.destroy();
  const d = window.driver.js.driver({
    showProgress: true,
    progressText: "Step {{current}} of {{total}}",
    allowClose: true,
    overlayOpacity: 0.62,
    stagePadding: 6,
    popoverClass: "tour-popover",
    nextBtnText: "Next →",
    doneBtnText: "Finish",
    steps: STEPS.map(s => ({
      element: s.el,
      popover: {
        title: s.title,
        description: s.text,
        showButtons: s.action ? ["close"] : ["next", "close"],
        side: s.side || "bottom", align: "start",
      },
      onHighlighted: () => { if (s.action) tourWatch(s); },
    })),
    onNextClick: () => { tourAdvance(); },
    onPopoverRender: (popover, { state }) => {
      const s = STEPS[state.activeIndex];
      if (!s || !s.action) return;
      const extra = document.createElement("div");
      extra.className = "tour-extra";
      extra.innerHTML = `<span class="tour-status" aria-live="polite">Waiting for you…</span>
        ${s.button ? `<button type="button" class="tour-act">${s.button.label}</button>` : ""}
        <button type="button" class="tour-skip">Skip step</button>`;
      if (s.button) extra.querySelector(".tour-act").addEventListener("click", s.button.run);
      extra.querySelector(".tour-skip").addEventListener("click", () => tourAdvance());
      popover.description.appendChild(extra);
    },
    // A click on the dimmed page must not end the tour (easy to do by accident); the close button
    // and Esc still do. Driver calls onDestroyStarted for overlay clicks and Esc, not for destroy().
    onDestroyStarted: () => {},
    onCloseClick: () => d.destroy(),
    onDestroyed: () => { tourStopPolling(); tourState.driver = null; },
  });
  tourState.driver = d;
  d.drive(0);
}

$("#tourBtn").addEventListener("click", () => { if (!ui.busy) startTour(); });
$("#heroTourBtn").addEventListener("click", () => { if (!ui.busy) startTour(); });
document.addEventListener("keydown", e => { if (e.key === "Escape" && tourState.driver) tourState.driver.destroy(); });
