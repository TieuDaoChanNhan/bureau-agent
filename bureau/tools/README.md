# bureau/tools

Deterministic functions the agent calls through `bureau/agent/tool_specs.py`. No LLM here.

| File | Function | Returns |
|---|---|---|
| `rules.py` | `search_rules(state, query)` | matching rule sections with their id (e.g. `§3`) |
| `eligibility.py` | `check_eligibility(state)` | `paid`, `unpaid` participant ids and `unmatched_payments` (exact matches only) |
| `identity.py` | `match_person(state, payment_id)` | candidates with score, band and signals |
| `groups.py` | `check_groups(state, kind)` / `propose_groups(state, ids, size)` | violations / a greedy grouping |

## Identity bands (`identity.py`)
| Score | Band | What the agent may do |
|---|---|---|
| ≥ 0.98 | `propose_link` | propose `LINK_PAYMENT` (still approved by a human) |
| 0.70–0.98 | `ask_human` | propose `LINK_PAYMENT` with a question for organizers |
| < 0.70 | `different` | treat as different people |

## Adding a tool
1. Write a pure function here, taking `EventState` and returning JSON-serialisable data.
2. Add a unit test in `tests/test_tools.py`.
3. Register it in `bureau/agent/tool_specs.py` (schema + handler).
