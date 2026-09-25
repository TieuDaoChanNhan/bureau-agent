# api

FastAPI app serving the JSON API and the web UI.

```bash
uvicorn api.main:app --reload     # http://127.0.0.1:8000  (docs at /docs)
```

| Method | Path | Status |
|---|---|---|
| GET | `/api/events` | done (runtime state, sample fallback) |
| GET | `/api/events/{event_id}` | done (re-detected issues, stored statuses and actions) |
| POST | `/api/events/{event_id}/run` | done (proposals only) |
| POST | `/api/events/{event_id}/plan` | 501 (T14 / issue #13, outside T05) |
| GET | `/api/actions/{action_id}` | done |
| POST | `/api/actions/{action_id}/approve` | done (executor validation, optional edits/selection) |
| POST | `/api/actions/{action_id}/dismiss` | done (issue status only) |
| GET | `/api/events/{event_id}/outbox` | done (simulated messages with `sent_at`) |
| POST | `/api/events/{event_id}/reset` | done (restore sample data, clear runtime files) |

JSON bodies are the dataclasses of `bureau/core/models.py` (`dataclasses.asdict`). Keep it that way so the web UI has one source of truth.

`run`, `approve`, `dismiss`, and `reset` return the same summary as the event GET:
`{id, name, counts, issues, actions}`. GET routes do not write runtime files.
Issues are re-detected for each summary; repaired issues disappear, and dependent
issues are unlocked immediately after a travel plan is approved. Completed
decisions remain in storage to reject repeat approvals, even after other requests.
Counts describe the issues still detected, so repaired issues that disappear are
not included in `counts.resolved`.

`run` handles `open` and `needs_human` issues without a proposal, skipping issues
with dependencies and `no_logistics_plan`. Existing proposals and terminal issues
are skipped. An OpenAI key is required only when there is work to do. The route
never applies a proposal. Each mutation saves the current state once; it does not
mix `save_action` with a stale `save_state` that could erase other proposals.

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
