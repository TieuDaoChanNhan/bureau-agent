# api

FastAPI app serving the JSON API and the web UI.

```bash
uvicorn api.main:app --reload     # http://127.0.0.1:8000  (docs at /docs)
```

| Method | Path | Status |
|---|---|---|
| GET | `/api/events` | done (runtime state, sample fallback) |
| GET | `/api/events/{event_id}` | done (re-detected issues, stored statuses and actions) |
| POST | `/api/events/{event_id}/run?limit=5` | done (bounded proposals only) |
| POST | `/api/events/{event_id}/messages` | done (T32: add an incoming message; returns the summary and the new `issue_id`) |
| POST | `/api/events/{event_id}/plan` | done (T14: planner proposal for `no_logistics_plan`; optional `overrides` for what-if) |
| GET | `/api/actions/{action_id}` | done |
| POST | `/api/actions/{action_id}/approve` | done (executor validation, optional edits/selection) |
| POST | `/api/actions/{action_id}/dismiss` | done (issue status only) |
| GET | `/api/events/{event_id}/outbox` | done (simulated messages with `sent_at`) |
| POST | `/api/events/{event_id}/reset` | done (restore sample data, clear runtime files) |

JSON bodies are the dataclasses of `bureau/core/models.py` (`dataclasses.asdict`). Keep it that way so the web UI has one source of truth.

`approve`, `dismiss`, and `reset` return the same summary as the event GET:
`{id, name, counts, issues, actions, travel, logistics, records}`. `records` maps ids to display
names (`participants`, `groups`, `payments`) so the UI can show names instead of ids (T23). `run` adds `remaining` and `errors` to
that summary. GET routes do not write runtime files.
Issues are re-detected for each summary; repaired issues disappear, and dependent
issues are unlocked immediately after a travel plan is approved. Completed
decisions remain in storage to reject repeat approvals, even after other requests.
Counts describe the issues still detected, so repaired issues that disappear are
not included in `counts.resolved`.

`run` delegates to the agent's shared `run_pending` selector. It handles `open`
and `needs_human` issues without a proposal, skips `no_logistics_plan` and issues
blocked by an unresolved dependency, and defaults to five attempted issues per
request. Existing proposals and terminal issues are skipped. Each successful
proposal is saved before the next issue; an agent error is appended to the audit
log, the issue is marked `agent_failed`, and the rest of the bounded batch goes on.
`agent_failed` issues are not counted in `remaining` or retried by later calls, so a
client can call `run` until `remaining` is 0; `run?issue_id=<id>` retries one issue.
An OpenAI key is required only when there is work to do. The route never applies
a proposal.

Approve accepts an optional JSON body with string fields `edited_description`
and `option_id`. Errors use FastAPI's `detail` field:

| Status | Meaning |
|---|---|
| 404 | Unknown event or action |
| 409 | Executor invariant violation, already decided issue, or stale proposal |
| 422 | Invalid approval body or action payload (e.g. unknown participant/option) |
| 503 | Agent work requires an OpenAI key that is not configured |

The JSON store is intended for a local demo with one writer at a time; it does
not provide transactions or coordinate concurrent requests/processes.

Tests use a temporary runtime directory and a fake agent, without external calls:

```bash
python -m unittest tests.test_api -v
```

## Adding a message (T32)
`POST /api/events/{event_id}/messages` with `{"sender": str, "channel": "email" | "discord" | "form", "text": str}`
(sender 1–200 characters, text 1–4000, not blank; otherwise 422). The message gets the next free id
`liveNN`, a timezone-aware `received_at`, and is saved in runtime `state.json`; detection turns it into
`message:liveNN`, returned as `issue_id`. Run the agent on it with `run?issue_id=`. Reset removes it.
The text is data for the agent, never instructions.

## Planning a trip (T14)
`POST /api/events/{event_id}/plan` with an optional body `{"text"?: str, "overrides"?: {key: value}, "recorded"?: bool}`.
Constraints are extracted from the request text by the LLM (T10); `recorded: true` uses the constraints
recorded with the event instead (offline demo). Without an OpenAI key and without `recorded`, the route
returns 503; unusable model output returns 422 and a provider failure 502, and nothing is stored.
When the planner has questions it returns `ESCALATE` with `payload.clarifications` and does not search;
send the request again with the organizer's answer appended to `text` (`payload.request_text` holds
the text last used). Packages are Jinko hotels (replay cache) composed with recorded transport,
and the LLM phrases the explanation.
The request is built from the runtime `state.travel`. `overrides` may only set the hard constraints
checked in code (`participants`, `max_cost_per_person_cents`, `arrive_before`, `no_overnight`,
`step_free_rooms`) with the right JSON type, otherwise 422; this powers the budget what-if.
The planner proposal (`SELECT_TRAVEL_PLAN`, or `ESCALATE` with `suggestions` when nothing is valid)
replaces any earlier planner proposal and carries the constraints used in `payload.constraints`.
The response is the event summary plus `action_id`. Approving `SELECT_TRAVEL_PLAN` needs
`{"option_id": ...}` and only accepts a valid option; it sets `logistics` and unlocks dependent
issues. 409 when the event has no open travel issue. Nothing is booked.
