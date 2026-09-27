# web

Organizer console: static HTML + vanilla JS (no build step), served by `api/main.py` at `/`.
It talks only to the JSON API; response shapes are the dataclasses of `bureau/core/models.py`.

```bash
uvicorn api.main:app --reload     # then open http://127.0.0.1:8000
```

| File | Role |
|---|---|
| `index.html` | Page shell: top bar, event cards, status line, issue list, detail pane |
| `app.js` | State, API calls, rendering and event handlers |
| `tour.js` | The guided product tours (T34, T38): the full `STEPS` list, the `QUICK` tour built from it, and the logic that waits for each action |
| `vendor/` | Driver.js 1.3.1 (MIT, licence in `DRIVER_LICENSE`), vendored so the tour works offline and when deployed |
| `style.css` | Design tokens (light and dark) and console components |

## Layout (T35)
- **Hero** (first screen): value proposition, three numbers (issues detected in the sample, the 90% evaluation
  result, zero actions without approval) and **Start the guided demo**. "How it works" in three steps.
- **Console**: title and actions (New message, Outbox, Reset demo, Run agent); event **tabs** with context
  (type, dates, headcount); a KPI row (blocking, ready for review, waiting, resolved).
- **Issue list**: an icon per kind, title and names on two lines, colour-coded status chips with a legend.
- **Issue detail, proposal first**: a card with the action type, a one-line summary, the agent's question (or
  "why"), what will change, the draft reply and the decision buttons. Below it, collapsible **Agent steps**
  (open), **Evidence** (decision trace and checks) and **Input** (what the fixed checks detected). Open/closed
  state is remembered while you browse.
- **While the agent runs** on the selected issue, a "thinking" card shows elapsed seconds and a generic phase;
  when the result arrives, the **recorded** tool calls are revealed one by one. This is a replay of the real
  steps of that run, not a live stream.
- **Trip view**: the planner's proposal card (trade-offs or diagnosis, what-if budget) with the valid packages
  as cards (ranked first highlighted, Choose buttons) and the rejected ones in a compact table with the broken
  constraint; constraints below; evidence and input collapsible.
- **Theme**: light by default, **Dark** toggle in the top bar (remembered per browser when storage is
  available). Works at 400 px wide without horizontal scrolling.

## What the console does
| Area | Behaviour | API |
|---|---|---|
| Intro (T33) | One sentence on what the product does and the loop in three steps | — |
| Demo tour (T34, T38) | Two guided tours (Driver.js). **Quick** (default, 15 steps, about 3 minutes): the highlights with short copy and the key numbers at the end. **Full** ("see every feature", 30 steps). Each step shows its chapter (Intro, Agent, Safety or Messages, Trip, Wrap-up) and "Step n of N", the page dimmed and one element highlighted, a detailed explanation next to it. Action steps name the button to click and move on by themselves when the result appears; Skip step, Close and Esc always work; clicks on the dimmed page do not end the tour. It resets both sample events first and uses the live agent (a few cents) | the routes the steps trigger |
| Event cards | Open blocking / non-blocking counts, proposals ready for review, resolved issues | `GET /api/events/{id}` |
| Issue list | Blocking first, then non-blocking; resolved and dismissed issues move to a collapsed **Done** group | same |
| Status pills | `Running…` (being investigated), `Not analysed` (no proposal), `Action proposed`, `Needs you` (escalation, or identity link below 0.98), `Waiting` (unresolved `depends_on`), `Agent failed`, `Resolved`, `Dismissed` | same |
| Issue detail | Input found by fixed checks, **Agent steps** (the real tool calls of the run, from `ProposedAction.trace`; rejected calls in red), decision trace built from the proposal's evidence (checked / found / applied / proposed), checks ✓ / ✗ / ? (unverified), the agent's note, the proposed action and its draft reply | same |
| Approve / Edit / Dismiss | Edit makes the draft reply editable; approving sends it as `edited_description`. The issue leaves the open list | `POST /api/actions/{id}/approve`, `/dismiss` |
| Run agent | Runs the runnable issues one request at a time (`run?issue_id=`), blocking first: the current row shows **Running…** and the status line `Investigating n/total`. The button becomes **Stop** (takes effect after the current issue). One issue can also be run or retried from its detail pane | `POST /api/events/{id}/run` |
| New message | A form (with three fictional examples) that adds an incoming message and immediately runs the agent on it, with the run progress display | `POST /api/events/{id}/messages`, then `run?issue_id=` |
| Trip view (`no_logistics_plan`) | The planning request, hard / soft constraints (with the ones organizers must confirm), the planner's clarification questions with an answer box (nothing is searched until they are answered), a budget what-if (requested vs 20% less, rounded to €10, keeping the answers), the decision trace, option cards with the return time and per-person cost split (coach, lodging, meals), the option table with rejection reasons in red, the diagnosis when nothing is valid, and one **Choose option** button per valid option. Choosing sets the plan and unlocks the waiting issues | `POST /api/events/{id}/plan`, `/approve` with `option_id` |
| Outbox | Simulated sent replies, newest first | `GET /api/events/{id}/outbox` |
| Reset demo | Two clicks (no blocking dialog); restores the sample data | `POST /api/events/{id}/reset` |

The decision trace is derived from `ProposedAction.evidence`: every evidence item is listed
under *Checked*, non-rule items under *Found*, rule sections under *Applied*, and the action
title under *Proposed*. Everything user-supplied is HTML-escaped before rendering. Ids are shown as names, with the id in a tooltip (T33;
`named()` / `cell()`), rather than in brackets (`nameOf()`, from the summary's `records`): "Antoine Nguyen (p01)"; the issue list
shows the subjects' names under each non-message issue.

## Extending it
- **Trip view:** `planDetail()` renders the `no_logistics_plan` issue; the planner response shape is documented in `api/README.md` (Planning a trip).
- **New action type:** add a case to `payloadBlock()` (what will change) and, if it carries a
  reply, to `draftOf()` (what can be edited). Approve labels live in `APPROVE_LABEL`.
- **New issue kind:** add a branch to `inputBlock()`; unknown kinds fall back to a key/value list.
- Keep the layout usable at 400 px wide without horizontal scrolling (checked with a 400 px frame).

## Adding a tour step
Add an object to `STEPS` in `tour.js`:
- `el`: a CSS selector, resolved when the step is shown. Omit it for a centred step.
- `title` and `text`: HTML, in English; start action steps with the button to click.
- `prepare()`: optional; navigate before the step is shown (`tourShow(event, issueKey)`, fill a form).
- `action: true` with `done()`: the step waits for the viewer's click and moves on when `done()` becomes true.
- `button`: optional; an extra button in the popover (used to save the edited reply).
- `side`: optional; where the popover goes (`top`, `left`…).
- `id`: needed only if the quick tour reuses the step. `QUICK` entries spread a step (`{ ...step("id"), ch, text }`) and override its copy; the full tour's chapters are set by index after `STEPS`.

Keep steps short enough to be read in about ten seconds; quick-tour steps stay under about 45 words plus the click instruction.

## Public demo and bundled fonts

Saved server proposals carry a replay marker. `app.js` displays a persistent
source badge, including `Saved example (live limit reached)`, which survives
reloading the action. The 30-step tour also works when the API uses replay.

`vendor/fonts.css`, `geist.ttf` and `geist-mono.ttf` bundle the variable fonts
from the official Google Fonts repository (`ofl/geist` and `ofl/geistmono`).
The accompanying `GEIST_OFL.txt` and `GEIST_MONO_OFL.txt` are their SIL licenses.
Both live and static builds load these fonts locally and retain the real 90%
evaluation metric. No Google Fonts network request is needed.
