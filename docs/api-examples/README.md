# API examples

Example JSON bodies for every route in `api/README.md`, generated from the real code.
Use them to build and mock the web UI while a route still returns 501.

| File | Route |
|---|---|
| `GET_events.json` | `GET /api/events` |
| `GET_event_hackathon.json` | `GET /api/events/hackathon` (issues, no actions yet) |
| `action_LINK_PAYMENT.json` | an action returned by `GET /api/actions/{id}` (agent output, identity needs confirmation) |
| `action_SELECT_TRAVEL_PLAN.json` | trip plan with every option and its checks in `payload.options` |
| `action_ESCALATE_no_valid_plan.json` | same request with a €90 budget: no valid option, `payload.suggestions` |
| `POST_approve_request.json` | body of `POST /api/actions/{id}/approve` |
| `GET_outbox.json` | `GET /api/events/{id}/outbox` |

Regenerate after changing `bureau/core/models.py`:
```bash
python docs/api-examples/generate.py
```
