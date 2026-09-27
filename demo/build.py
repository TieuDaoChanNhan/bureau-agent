"""Build the self-contained public demo. No dependencies, credentials or network calls.

Run from the repository root: python demo/build.py
Only demo/site/ is published. The live console remains the source for its UI.
"""
from __future__ import annotations

import json
import base64
import hashlib
import re
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bureau.core.detect import detect_issues
from bureau.core.loader import load_event
from demo.replay import payment_example, scenarios_and_rules, planner_example, BUDGET_ANSWER, BUDGET_QUESTION

DEMO = ROOT / "demo"
SITE = DEMO / "site"


def replace(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError(f"Console changed; review the static adaptation: {old[:80]}")
    return text.replace(old, new)


def write(name: str, text: str) -> None:
    (SITE / name).write_text(text, encoding="utf-8", newline="\n")


def build() -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    fixtures = {"events": {}}
    for event_id in ("hackathon", "wei"):
        state = load_event(event_id)
        fixtures["events"][event_id] = {
            "id": state.id, "name": state.name,
            "issues": [asdict(i) for i in detect_issues(state)], "actions": [],
            "travel": state.travel, "logistics": None,
            "records": {
                "participants": {p.id: p.name for p in state.participants},
                "payments": {p.id: f"{p.payer_name} · €{p.amount_cents / 100:g}" for p in state.payments},
                "groups": {g.id: g.name for g in state.groups},
            },
            "meta": {**state.settings.get("display", {}), "participants": len(state.participants)},
            "outbox": [], "audit": [],
        }
    examples = ROOT / "docs" / "api-examples"
    fixtures["payment"] = payment_example()
    fixtures["plan"] = asdict(planner_example(load_event("wei"), recorded=True, saved_hotels=False))
    fixtures["budget_answer"], fixtures["budget_question"] = BUDGET_ANSWER, BUDGET_QUESTION
    fixtures["scenarios"], fixtures["rules"] = scenarios_and_rules()
    if any(s["rule"] not in fixtures["rules"] for s in fixtures["scenarios"].values()):
        raise ValueError("A curated scenario references an unknown rule.")
    fixtures["revision"] = hashlib.sha256(json.dumps(fixtures, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]
    write("fixtures.js", "// Generated from fictional repository samples; no live calls.\nwindow.DEMO_FIXTURES = " +
          json.dumps(fixtures, ensure_ascii=False, default=str, indent=2) + ";\n")
    shutil.copyfile(DEMO / "offline.js", SITE / "offline.js")
    shutil.copyfile(DEMO / "session.js", SITE / "session.js")
    shutil.copyfile(DEMO / "customer-ui.js", SITE / "customer-ui.js")
    shutil.copytree(ROOT / "web" / "vendor", SITE / "vendor", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("*.ttf"))
    # Spaces redirects binary font assets to its CDN. Embed them in the static
    # CSS to preserve the self-contained site and its no-network policy.
    fonts = (ROOT / "web/vendor/fonts.css").read_text(encoding="utf-8")
    for name in ("geist.ttf", "geist-mono.ttf"):
        encoded = base64.b64encode((ROOT / "web/vendor" / name).read_bytes()).decode("ascii")
        fonts = fonts.replace(f'url("./{name}")', f'url("data:font/ttf;base64,{encoded}")')
        (SITE / "vendor" / name).unlink(missing_ok=True)
    write("vendor/fonts.css", fonts)
    shutil.copyfile(ROOT / "web" / "style.css", SITE / "style.css")

    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    html = "\n".join(line for line in html.splitlines() if "fonts.googleapis.com" not in line and "fonts.gstatic.com" not in line)
    html = replace(html, "/web/", "./")
    html = replace(html, "<title>Bureau Agent</title>", "<title>Bureau Agent · Interactive customer demo</title>")
    html = replace(html, '<meta charset="utf-8">', '<meta charset="utf-8">\n  <meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'self\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; font-src \'self\' data:; connect-src \'none\'; base-uri \'none\'; form-action \'none\'">')
    html = replace(html, '<main id="top">', '<main id="top">\n    <p class="demo-banner" role="note"><b>Interactive sample demo</b> · Saved proposals, zero model calls. Nothing is sent or booked.<br><span id="sessionNotice">Changes stay in this tab.</span></p>\n    <noscript>This demo needs JavaScript enabled. It runs entirely in your browser.</noscript>')
    html = replace(html, "Nothing is sent, changed or booked until an organizer approves it.", "Review the evidence, edit the reply, and approve the next step. This demo applies your decisions only to fictional data in your browser.")
    html = replace(html, "The guided demo shows the highlights; the full tour covers every feature. Both use the live agent on fictional sample data.", "About 5 minutes · 30 guided steps · No signup, installation or API credit needed.")
    # The static site has one 30-step tour: keep a single hero button and a single top-bar button.
    html = replace(html, "Start the guided demo · 3 min", "Start the guided demo")
    html = replace(html, '\n        <button class="btn big" id="fullTourBtn" type="button">Full tour · 6 min</button>', "")
    html = replace(html, '\n        <button class="btn" id="fullTourTopBtn" type="button" title="Every feature, about 6 minutes">Full tour</button>', "")
    html = replace(html, 'title="The highlights, about 3 minutes">Quick tour</button>', '>Demo tour</button>')
    html = replace(html, '<button class="btn" id="outboxBtn"', '<button class="btn" id="auditBtn" type="button">Activity</button>\n            <button class="btn" id="outboxBtn"')
    html = replace(html, '<script src="./app.js"></script>', '<script src="./fixtures.js"></script>\n  <script src="./session.js"></script>\n  <script src="./offline.js"></script>\n  <script src="./customer-ui.js"></script>\n  <script src="./app.js"></script>')
    write("index.html", html + "\n")
    with (SITE / "style.css").open("a", encoding="utf-8") as f:
        f.write("\n/* Static customer demo notice. */\n.demo-banner{max-width:1200px;margin:20px auto 0;padding:12px 20px;border:1px solid var(--line);border-radius:12px;background:var(--accent-soft);color:var(--ink-2);font-size:13px}\n@media(max-width:600px){.demo-banner{margin:12px 14px 0}.toolbar{flex-wrap:wrap}.console-title{flex-wrap:wrap}}\n")

    app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    start, end = app.index("async function api("), app.index("function replayLabel(")
    app = app[:start] + "const demoStore = createDemoStore(window.DEMO_FIXTURES);\nui.drafts = demoStore.drafts();\nasync function api(path, options = {}) { const sessionId = demoStore.sessionInfo().id; try { return demoStore.request(path, options); } finally { if (demoStore.sessionInfo().id !== sessionId) restoreSessionUI(); refreshSessionNotice(); } }\n\n" + app[end:]
    changes = {
        "The agent is investigating…": "Loading the saved example…",
        "Extracting constraints and searching…": "Loading the saved planning example…",
        "It chooses its own tools; each step it took will appear below when it has finished.": "This replays a curated example. No model or external service is called.",
        "It will read this issue, choose tools (records, payments, rules, teams) and propose one action with its evidence. Nothing changes until you approve.": "Load a saved sample proposal and inspect its evidence. Cases without a specific example are handed to the organizers; no live AI runs here.",
        "tool calls, chosen by the model": "illustrative tool calls from the saved example",
        "Paste an email or a Discord message. It is added to the event, detected as an issue, and the agent investigates it right away. The text is treated as data, never as instructions.": "Try one of the three saved examples below. Other messages are saved locally for organizer review; this demo does not analyze new text with AI.",
        "An AI model turns the request into structured constraints; code then builds travel + lodging packages from real hotel\n      offers and checks every one of them. Nothing is booked.": "Replay the saved planning example, clarify coach inclusion, and compare five illustrative complete packages. Prices include groceries and food transport; no current quote or booking is made.",
        "Nothing is searched until the request is clear. Your answer is added to the request and the constraints are extracted again.": "Confirm that the complete budget includes coach hire, lodging, groceries and food transport. No live search or text extraction occurs.",
        '<textarea name="answer" required maxlength="1000" rows="3"\n        placeholder="Confirm what the budget includes."></textarea>': f'<textarea name="answer" required readonly rows="3">{BUDGET_ANSWER}</textarea>',
        'if (ui.view === "outbox")': 'if (ui.view === "audit") { el.innerHTML = auditHTML(); return; }\n  if (ui.view === "outbox")',
        '${seg}\n      <span class="lbl">Options compared</span>': '${seg}\n      ${plannerControls(action, decided)}\n      <span class="lbl">Options compared</span>',
        'if (text !== draftOf(action)) ui.drafts[action.id] = text; else delete ui.drafts[action.id];': 'if (text !== draftOf(action)) ui.drafts[action.id] = text; else delete ui.drafts[action.id];\n  demoStore.saveDrafts(ui.drafts);\n  refreshSessionNotice();',
        'ui.drafts = {}; ui.outbox = []; ui.view = "issue";': 'ui.drafts = demoStore.drafts(); ui.outbox = []; ui.view = "issue";',
        "const whatIf = requested ? Math.round(requested * 0.8 / 1000) * 1000 : null;": "const whatIf = requested && requested > 9000 ? 9000 : null;",
        'if (overrideBudget) body.overrides = { max_cost_per_person_cents: overrideBudget };': 'body.overrides = { max_cost_per_person_cents: overrideBudget ?? requestedBudget(summary()) };',
    }
    for old, new in changes.items():
        app = replace(app, old, new)
    app += '''\nfunction auditHTML() {
  const rows = demoStore.request(`/api/events/${encodeURIComponent(ui.current)}/audit`);
  return `<div class="dhead"><h3>Activity in this tab</h3><p class="note">Local decisions on fictional data. Reset clears this event's activity.</p></div>`
    + rows.slice().reverse().map(row => `<div class="mail"><span class="from">${esc(row.at)}</span>${esc(row.message)}</div>`).join("")
    + (!rows.length ? '<p class="note">No decisions yet. Review and approve a sample proposal.</p>' : "")
    + '<button class="btn" data-act="back" type="button">Back to issues</button>';
}
$("#auditBtn").addEventListener("click", () => { if (!ui.busy) { ui.view = "audit"; renderDetail(); } });
'''
    write("app.js", app)
    tour = (ROOT / "web" / "tour.js").read_text(encoding="utf-8")
    tour = tour[:tour.index("const b =")] + (DEMO / "tour-steps.js").read_text(encoding="utf-8") + "\n" + tour[tour.index("function tourStopPolling()") :]
    tour = replace(tour, "The agent is working… the tour continues by itself.", "Loading the saved example… the tour continues by itself.")
    # The static site keeps one 30-step tour (demo/tour-steps.js); the console's quick tour
    # needs live results, so both entry points open the same steps here.
    tour = replace(tour, "function startTour(", "const QUICK = STEPS;\n\nfunction startTour(")
    # Saved actions complete immediately. Disable animated transitions so an action
    # cannot advance the driver while its previous highlight is still animating.
    write("tour.js", tour)
    write("README.md", """---
title: Bureau Agent
emoji: 🗂️
colorFrom: blue
colorTo: purple
sdk: static
app_file: index.html
pinned: false
---

# Bureau Agent · Customer demo

Explore two fictional events in a guided 30-step console tour. Saved sample
proposals demonstrate investigation, evidence, human approval and trip planning.
No live model calls, external bookings or messages. Changes stay in your browser
tab and survive refreshes for up to 24 hours after the last interaction when
browser session storage is available. Reset restores the selected event.
Try editable replies and your own budget, group size and arrival deadline.
No secrets or configuration are needed.

Built from the repository's `demo/` directory with `python demo/build.py`.
""")
    print("Built demo/site (upload its contents to the Static Space).")


if __name__ == "__main__":
    build()
