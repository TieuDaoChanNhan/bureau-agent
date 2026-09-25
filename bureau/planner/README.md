# bureau/planner

Trip planning for events that involve travel (e.g. an integration weekend).
The destination is given by organizers; the planner does not choose where to go.

## Pipeline
```
request text ─► extract (LLM) ─► search (Jinko) ─► compose (code) ─► check + rank (code) ─► explain (LLM)
                   │                                                      │
                   └─ clarifications? → ESCALATE                          └─ nothing valid? → ESCALATE + diagnosis
```
LLM interprets and explains. Code composes, prices and validates. The planner never relaxes a constraint.

| File | Role | Status |
|---|---|---|
| `interface.py` | Contract with the core: `TravelRequest`, `Constraints`, `TravelOption` | done |
| `planner.py` | `plan_trip(req, constraints) -> ProposedAction` | done (uses recorded packages) |
| `constraints.py` | Hard-constraint checks, ranking by soft priorities, diagnosis | done |
| `extract.py` | Words → `Constraints` (Pipelex or OpenAI structured output) | skeleton (T10) |
| `jinko.py` | `ground_search`, `hotel_search`, live/replay cache | skeleton (T11) |
| `compose.py` | Transport × lodging → packages, integer cents | skeleton (T12) |
| `explain.py` | Plain-language trade-offs, never changes the ranking | template (T13) |

## Hard constraints
| Key | Checked by | Can reject an option |
|---|---|---|
| `max_cost_per_person_cents` | code | yes |
| `arrive_before` ("HH:MM") | code | yes |
| `no_overnight` | code | yes |
| `participants` (lodging capacity) | code | yes |
| `step_free_rooms` | organizers (Jinko only has free-text facilities) | no, shown as "confirm with the venue" |

## Try it
```bash
python -m bureau plan wei
python -m bureau plan wei --budget 90
```
