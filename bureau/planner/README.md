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
| `planner.py` | `plan_trip(req, constraints, client, search) -> ProposedAction`; `search_options` composes Jinko hotels (replay) × recorded transport, falling back to `travel_options.json` | done (T14) |
| `constraints.py` | Hard-constraint checks, ranking by soft priorities, diagnosis | done |
| `extract.py` | Words → `Constraints` with OpenAI strict structured output | done (T10) |
| `jinko.py` | `ground_search`, `hotel_search`, live/replay cache under `data/<event>/jinko_cache/` | done (T11): hotels verified live; ground search returns 404 for our key |
| `compose.py` | Transport × lodging → packages, integer cents; lodging share rounded up; one package per transport first, cheapest always kept | done (T12) |
| `explain.py` | Plain-language trade-offs: LLM prose when a client is given (OpenAI), template otherwise; the list of rejected options and broken constraints is always appended by code; never changes the ranking | done (T13) |

## Hard constraints
| Key | Checked by | Can reject an option |
|---|---|---|
| `max_cost_per_person_cents` (full requested package, including meals when explicit) | code | yes |
| `arrive_before` ("HH:MM") | code | yes |
| `no_overnight` | code | yes |
| `participants` (lodging capacity) | code | yes |
| `step_free_rooms` | organizers (Jinko only has free-text facilities) | no, shown as "confirm with the venue" |

## Try it
```bash
python -m bureau plan wei
python -m bureau plan wei --recorded-constraints
python -m bureau plan wei --recorded-constraints --budget 120
python -m eval.run_eval --suite planning
```

The default extracts the organizer's text using `OPENAI_API_KEY` and
`OPENAI_MODEL` (default `gpt-4.1`). It reads no recorded constraints or options
for extraction. Null hard fields are omitted, cents remain integers, arrival
times use `HH:MM`, and preference order is preserved. Accessibility always
requires organizer verification. Questions stop the planner before searching.
Unsupported hard requirements are retained in the extractor's required
`unsupported_requirements` list. Supplier details (kitchen/activity facilities,
coach count, room types and hotel ratings) become organizer verification notes
and `verified=false` checks on every option, visible in the trip view's shared
confirmation notice. They do not block comparison or claim that a facility is
available. Transport eligibility restrictions require blocking clarification.
Unknown hard keys passed directly
to `plan_trip` also stop search. A separate EN/FR text guard catches explicit
transport-mode restrictions (for example, train only or no coaches) at both
extraction and planning, including when extraction omits the restriction. Mode
preferences alone do not trigger that guard. The planner currently asks for
verification or an explicit revised request; it does not claim to filter by mode.
This lexical guard covers documented direct wording, not every paraphrase or
language; other requirements still depend on extraction. None of
these checks establishes supplier availability or authorizes a booking.

The WEI briefing describes a neutral student association's 100-person demo, charter coaches and a group
venue with cooking and activity spaces. Meals and grocery transport are included
in the EUR 150 provisional student fee: the association buys groceries and transports
them to the venue. Two separate step-free rooms are requested. The short request
deliberately leaves coach inclusion in the EUR 150 budget unclear. The live demo
should first ask about this scope; after an all-inclusive answer it can search
and propose options. Charter hire, kitchens and activity
permissions are outside the current schema. The model may ask clarifications or
proceed with only the supported checks. See [fixture provenance and limits](../../data/README.md#wei-source-assumptions-and-scenarios-t16--issue-15).

The budget is the ceiling for the full requested package. Explicit meal inclusion
is supported; ambiguity about inclusion still requires clarification. The optional
`TravelRequest.catering` dictionary is empty by default and carries the organizer's
per-person allocations. For the WEI demo, composition adds EUR 20 for groceries
and EUR 2 for food transport per person once, alongside transport and lodging
(EUR 2000 + EUR 200 for 100 people). The fallback
packages already include these allocations in their unchanged totals; option A
costs EUR 112, independently of the EUR 150 provisional participation fee.
Composed prices may also differ from that fee. These fictional budgets await
organizer confirmation; the scenario was reviewed by a team member who has taken
part in a WEI (see `data/README.md`). An optional
`cost_breakdown_per_person_cents` dictionary (empty by default) itemizes a `TravelOption`; code requires
nonnegative integer values whose sum equals `cost_per_person_cents` and never
adds the breakdown a second time. Menus, quantities, dietary needs, purchasing
and food transport arrangements remain organizer checks.

`--recorded-constraints` explicitly replays the supported sample constraints,
including the EUR 150 full-package ceiling, for an offline demo without extraction.
Search normally combines cached Jinko hotel rates with illustrative charter
transport. A cached quote for one double room is scaled to 50 rooms for 100 people;
group availability remains unconfirmed. Ground search returned 404 for the current
key, so transport is recorded. If hotel search is unavailable, the planner uses
`travel_options.json`: A/B/D pass at EUR 150, A/B pass at EUR 120, and none passes at EUR 90 in that
fallback fixture. Composed options have their own IDs and prices. Neither path
confirms coach hire, group availability or venue facilities; those requirements
remain in `travel.organizer_checks`. This mode does not evaluate extraction.
The current composed options C/E/F pass at the configured EUR 150 ceiling,
at EUR 135.59/140.59/142.59 per person including meals. Lower-budget what-if
scenarios at EUR 120 or EUR 90 return `ESCALATE`; an override does not change
the stored ceiling or provisional participation fee.
Unit tests and API example generation also
use explicit fixtures. Missing credentials, API errors, refusals, truncated output,
and invalid values raise errors; they never fall back to the sample's answers.
The optional `client=` argument supports scripted tests without network access.

## Provider choice

Constraint extraction uses [OpenAI structured output](https://developers.openai.com/api/docs/guides/structured-outputs/)
with the same SDK and model configuration as the agent. A Pipelex prototype of this single call
also worked during the hackathon; we kept one provider to avoid a second runtime and dependency
tree. No Pipelex code or dependency is shipped.

## Validation and limits

The PR #62 live API check exercised the current WEI sequence: the initial request
returned `ESCALATE` with a question about coach inclusion; an appended all-inclusive
budget answer returned `SELECT_TRAVEL_PLAN`, ranked F/C/E. The recorded EUR 120
what-if returned `ESCALATE`. Restoring EUR 150 and approving F removed
`no_logistics_plan` and unlocked dependent issues. This verifies the API flow;
the browser tour copy is updated separately.

`tests/test_extract.py` covers the provider boundary using scripted completions.
The eight synthetic planning cases cover English/French, decimal budgets, time
normalization, ambiguity, preferences, and accessibility. The live evaluation
with `gpt-4.1`, rerun for PR #62, matched hard constraints on 8/8 cases, clarification presence on
8/8, optional preference/verification labels on 7/7, and recorded feasibility on
5/5; the three clarification cases were not searched. Reports are saved under
ignored `eval/results/`; see [evaluation definitions](../../eval/README.md).

These small corpus results are not a general accuracy guarantee. The schema
validates shape and types, not the truth of an interpretation. The original p001
gold maps two people needing accessible rooms to two provisional rooms; the
organizer must confirm allocation and accessibility before proceeding. Currency
conversion and arbitrary new hard fields are unsupported and need clarification.
Hotel search supports live and replay modes. The demo, the tests and the public
site replay the responses saved on 26 September 2026 (`JINKO_MODE=replay`), so the
WEI story is reproducible: 3 of 8 packages valid at EUR 150, none at EUR 120. Live
prices change daily; a live run on 27 September returned 0 of 8 at EUR 150. Set
`JINKO_MODE=live` with `JINKO_API_KEY` to search live. Cached individual-room quotes,
scaled group prices and illustrative transport do not establish current group
availability, private coach hire or venue permissions.

## Public demo allowance and replay

Extraction and explanation each reserve a model call through `core.llm_usage`.
An exhausted quota propagates to the API, including between those two steps.
Only public demo mode selects a clearly labeled saved scenario; unknown custom
text returns 429. `demo/replay.py` reuses the recorded packages and deterministic
planner checks without Jinko or model calls. Live validation errors remain errors.
