# API examples

Example JSON bodies for every route in `api/README.md`, generated from the real code.
Use them to build and mock the web UI while a route still returns 501.
The generator uses explicit recorded travel constraints so it works without an
API key. Live constraint extraction is evaluated separately in `eval/`.

WEI examples use the neutral, unconfirmed 100-person student association demo.
An experienced WEI organizer's approval is still pending before merge. Option prices include
coaches, lodging, groceries and food transport; the association buys the groceries and
transports them to the venue. Each `cost_breakdown_per_person_cents` itemizes the
total, including the fictional EUR 20/person for groceries and EUR 2/person for
food transport, with no surcharge. The EUR 150 ceiling applies to the full
package. Search combines cached Jinko hotel rates, scaled from one double room
to 50 rooms, with illustrative two-coach transport and the catering budgets.
Generated options may differ from the A–E fallback packages. The room block,
charter coaches, venue facilities and meal arrangements require organizer
verification; a passing option only satisfies the
currently supported checks. See [data provenance](../../data/README.md#wei-source-assumptions-and-scenarios-t16--issue-15).

At the default EUR 150 budget, cached composed options C/E/F pass at
EUR 135.59/140.59/142.59 per person. The EUR 120 what-if example yields
`ESCALATE`. These generated examples use recorded complete-package constraints;
the initial live request deliberately leaves coach inclusion unclear and should
prompt a clarification before a search. Meals and their transport are explicitly
included in both paths. All 97 fixture payments use the provisional EUR 150 fee.

| File | Route |
|---|---|
| `GET_events.json` | `GET /api/events` |
| `GET_event_hackathon.json` | `GET /api/events/hackathon` (issues, no actions yet) |
| `action_LINK_PAYMENT.json` | an action returned by `GET /api/actions/{id}` (agent output, identity needs confirmation) |
| `action_SELECT_TRAVEL_PLAN.json` | trip plan with every option and its checks in `payload.options` |
| `action_ESCALATE_no_valid_plan.json` | same request with a €120 budget: no valid cached option, `payload.suggestions` |
| `POST_approve_request.json` | body of `POST /api/actions/{id}/approve` |
| `GET_outbox.json` | `GET /api/events/{id}/outbox` |

Regenerate after changing `bureau/core/models.py`:
```bash
python docs/api-examples/generate.py
```
