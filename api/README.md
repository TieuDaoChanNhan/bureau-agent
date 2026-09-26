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
| POST | `/api/events/{event_id}/plan` | 501 (T14 / issue #13, outside T05) |
| GET | `/api/actions/{action_id}` | done |
| POST | `/api/actions/{action_id}/approve` | done (executor validation, optional edits/selection) |
| POST | `/api/actions/{action_id}/dismiss` | done (issue status only) |
| GET | `/api/events/{event_id}/outbox` | done (simulated messages with `sent_at`) |
| POST | `/api/events/{event_id}/reset` | done (restore sample data, clear runtime files) |

JSON bodies are the dataclasses of `bureau/core/models.py` (`dataclasses.asdict`). Keep it that way so the web UI has one source of truth.

`approve`, `dismiss`, and `reset` return the same summary as the event GET:
`{id, name, counts, issues, actions}`. `run` adds `remaining` and `errors` to
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
