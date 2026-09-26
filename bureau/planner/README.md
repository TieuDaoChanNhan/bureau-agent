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
| `extract.py` | Words → `Constraints` with OpenAI strict structured output | done (T10) |
| `jinko.py` | `ground_search`, `hotel_search`, live/replay cache under `data/<event>/jinko_cache/` | done (T11): hotels verified live; ground search returns 404 for our key |
| `compose.py` | Transport × lodging → packages, integer cents; lodging share rounded up; one package per transport first, cheapest always kept | done (T12) |
| `explain.py` | Plain-language trade-offs: LLM prose when a client is given (OpenAI), template otherwise; the list of rejected options and broken constraints is always appended by code; never changes the ranking | done (T13) |

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
python -m bureau plan wei --recorded-constraints
python -m bureau plan wei --recorded-constraints --budget 90
python -m eval.run_eval --suite planning
```

The default extracts the organizer's text using `OPENAI_API_KEY` and
`OPENAI_MODEL` (default `gpt-4.1`). It reads no recorded constraints or options
for extraction. Null hard fields are omitted, cents remain integers, arrival
times use `HH:MM`, and preference order is preserved. Accessibility always
requires organizer verification. Questions stop the planner before searching.
The original WEI text leaves meals unclear, so a clarification is expected.

`--recorded-constraints` explicitly replays the sample constraints for an offline
demo. It does not evaluate extraction. Unit tests and API example generation also
use explicit fixtures. Missing credentials, API errors, refusals, truncated output,
and invalid values raise errors; they never fall back to the sample's answers.
The optional `client=` argument supports scripted tests without network access.

## Provider choice and Pipelex trial (T10)

We tried Pipelex **0.66.0** in a separate Python 3.11 environment before choosing
the implementation. Its installation resolved 94 packages. Following the
[self-hosted guide](https://docs.pipelex.com/latest/get-started/run-it-yourself/)
and [typed concept guide](https://docs.pipelex.com/latest/building-methods/concepts/inline-structures/),
we ran a typed `PipeLLM` via `PipelexMTHDSProtocol.execute` against the synthetic
`p001` request, with direct OpenAI routing, Gateway disabled and `DO_NOT_TRACK=1`.

The shipped model catalogue lacked `gpt-4.1` (`ModelChoiceNotFoundError`), so the
trial added that handle to the local OpenAI backend. Windows also required UTF-8
output (`python -X utf8`) after a console encoding failure. After those fixes the
typed result was correct: 40 participants, 12000 cents, 21:00, no overnight travel,
and 2 step-free rooms. This was a compatibility trial, not full corpus validation.

We selected [OpenAI structured output](https://developers.openai.com/api/docs/guides/structured-outputs/)
for the shipped path: it uses the existing SDK/model configuration and avoids a
second runtime, provider catalogue, and dependency tree for a single extraction
call. Pipelex can perform the task; the fallback is a maintenance/scope decision.
No Pipelex dependency, credentials, or machine-specific configuration is shipped.

## Validation and limits

`tests/test_extract.py` covers the provider boundary using scripted completions.
The eight synthetic planning cases cover English/French, decimal budgets, time
normalization, ambiguity, preferences, and accessibility. The live T10 evaluation
with `gpt-4.1` matched hard constraints on 8/8 cases, clarification presence on
8/8, optional preference/verification labels on 7/7, and recorded feasibility on
5/5; the three clarification cases were not searched. Reports are saved under
ignored `eval/results/`; see [evaluation definitions](../../eval/README.md).

These small corpus results are not a general accuracy guarantee. The schema
validates shape and types, not the truth of an interpretation. The original p001
gold maps two people needing accessible rooms to two provisional rooms; the
organizer must confirm allocation and accessibility before proceeding. Currency
conversion and arbitrary new hard fields are unsupported and need clarification.
Option availability is still recorded until T11/T12.
