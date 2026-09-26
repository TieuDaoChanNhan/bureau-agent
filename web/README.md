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
| `style.css` | Design tokens (light and dark) and components, taken from the mockup |
| `reference/mockup.html` | Target design: the interactive mockup with hard-coded sample data |

## What the console does
| Area | Behaviour | API |
|---|---|---|
| Event cards | Open blocking / non-blocking counts, proposals ready for review, resolved issues | `GET /api/events/{id}` |
| Issue list | Blocking first, then non-blocking; resolved and dismissed issues move to a collapsed **Done** group | same |
| Status pills | `Running…` (being investigated), `Not analysed` (no proposal), `Action proposed`, `Needs you` (escalation, or identity link below 0.98), `Waiting` (unresolved `depends_on`), `Agent failed`, `Resolved`, `Dismissed` | same |
| Issue detail | Input found by fixed checks, **Agent steps** (the real tool calls of the run, from `ProposedAction.trace`; rejected calls in red), decision trace built from the proposal's evidence (checked / found / applied / proposed), checks ✓ / ✗ / ? (unverified), the agent's note, the proposed action and its draft reply | same |
| Approve / Edit / Dismiss | Edit makes the draft reply editable; approving sends it as `edited_description`. The issue leaves the open list | `POST /api/actions/{id}/approve`, `/dismiss` |
| Run agent | Runs the runnable issues one request at a time (`run?issue_id=`), blocking first: the current row shows **Running…** and the status line `Investigating n/total`. The button becomes **Stop** (takes effect after the current issue). One issue can also be run or retried from its detail pane | `POST /api/events/{id}/run` |
| Outbox | Simulated sent replies, newest first | `GET /api/events/{id}/outbox` |
| Reset demo | Two clicks (no blocking dialog); restores the sample data | `POST /api/events/{id}/reset` |

The decision trace is derived from `ProposedAction.evidence`: every evidence item is listed
under *Checked*, non-rule items under *Found*, rule sections under *Applied*, and the action
title under *Proposed*. Everything user-supplied is HTML-escaped before rendering.

## Extending it
- **Trip view (T15, #14):** the `no_logistics_plan` issue currently shows a placeholder note.
  Add a branch in `renderDetail()` (see `planDetail()` in the mockup) calling `POST /api/events/{id}/plan`.
- **New action type:** add a case to `payloadBlock()` (what will change) and, if it carries a
  reply, to `draftOf()` (what can be edited). Approve labels live in `APPROVE_LABEL`.
- **New issue kind:** add a branch to `inputBlock()`; unknown kinds fall back to a key/value list.
- Keep the layout usable at 400 px wide without horizontal scrolling (checked with a 400 px frame).
