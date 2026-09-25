# web

Static web UI (HTML + vanilla JS, no build step), served by `api/main.py` at `/`.

| File | Role |
|---|---|
| `index.html` | Page skeleton |
| `app.js` | Calls the API; currently lists events and issues |
| `style.css` | Minimal styles |
| `reference/mockup.html` | **Target design**: the interactive mockup. Copy structure and styles from it. |

## Target screens (T06, T15)
1. Event cards with open blocking / non-blocking / resolved counts.
2. Issue list, blocking first, with status pills.
3. Issue detail: input, decision trace (checked / found / applied / proposed), checks ✓/✗, editable proposed action, approve / edit / dismiss.
4. Trip issue: extracted constraints, option comparison table, budget what-if.

Develop against the running API (`uvicorn api.main:app --reload`). While an endpoint returns 501, mock its response in `app.js` with the documented JSON shape.
