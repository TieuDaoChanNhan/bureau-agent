# data

Sample events. **Read-only input**: runtime changes go to `runtime/<event>/` (git-ignored).
All people, emails and payments are fictional. Never commit real personal data.
New hackathon contacts and all WEI contacts use reserved `.example` domains.

| Event | Folder | Planted scenarios |
|---|---|---|
| X-IA hackathon | `hackathon/` | 50 participants, 47 payments, 11 teams, 25 messages (12 French / 13 English); ambiguous and unrelated payments, unpaid members, conflicting teams, team moves, rule questions and organizer escalations |
| kès integration weekend (WEI) | `wei/` | 100 fictional registrations, 97 payments, 7 messages; unconfirmed demo of student registration, payment checks, charter coaches and a group venue with lodging, cooking and activity spaces |

## File formats

Datetimes are ISO 8601 **with timezone** (`2026-09-25T09:00:00+02:00`). Money is integer cents.
Payment values use `amount_cents`; `event.json` stores the configured membership fee as `fee_amount_cents`.

| File | Content |
|---|---|
| `event.json` | `name`, `deadlines`, `settings` (e.g. `unpaid_kind`, `group_kind`, `needs_logistics`), `travel` (WEI only: request, participants, origin, destination, depart_after, return_by, nights, constraints, catering, provenance and organizer_checks; loaded into `EventState.travel`) |
| `participants.json` | `id, name, emails[], registered_at, skills[]?, needs[]?, looking_for_group?` |
| `payments.json` | `id, payer_name, amount_cents, currency, paid_at, payer_email?, reference?, participant_id?` |
| `groups.json` | `id, kind (team/room), name, members[], capacity_min, capacity_max, declared_at?` |
| `messages.json` | `id, channel (email/discord/form), sender, text, received_at` |
| `rules.md` | One `## §N Title` section per rule; parsed into `Rule` objects |
| `travel_options.json` | WEI only: illustrative full packages used as a fallback when Jinko hotel search is unavailable |

## WEI source, assumptions and scenarios (T16 / issue #15)

**Source:** the project owner's description during implementation of
[issue #15](https://github.com/TieuDaoChanNhan/bureau-agent/issues/15), on
26 September 2026. WEI means *weekend d'intégration*, organized by **kès**, the
École polytechnique student association. The supplied workflow is to collect
student registrations, check payments, hire buses, and find a resort-like venue
with accommodation, cooking facilities and space for group activities. Meals are
included in the student participation fee: kès buys the groceries and transports
them to the venue. Jinko is the intended service for transport and lodging searches.

The owner explicitly approved retaining demo dates and prices and then requested
about 100 registrations. This dataset uses **100**. It represents that real event
workflow, but **is not a confirmed itinerary or an official kès dataset**. No
organizer roster, supplier quote or confirmed destination was supplied. The
source and unconfirmed assumptions are also stored in `travel.provenance` so
they survive loading and runtime persistence.

| Field | Demo assumption, requiring kès confirmation |
|---|---|
| Dates | Friday 9 to Sunday 11 October 2026, two nights |
| Pickup / search area | École polytechnique campus in Palaiseau / Trouville-Deauville; the exact pickup and venue are undecided |
| Headcount | 100 synthetic registrations (`w01`–`w100`), including two separate step-free room requests |
| Transport | Two privately hired 53-seat coaches, 106 passenger seats total, round trip |
| Venue | Space for 100 overnight guests, shared kitchen with permission to cook, indoor and outdoor activity spaces |
| Budget ceiling | EUR 120/person (12000 cents), EUR 12000/group for round-trip coaches, two nights, groceries and their transport |
| Provisional participation fee | EUR 112/person (11200 cents), used by the sample payments; includes meals and grocery transport, remains distinct from the ceiling and subject to reconciliation once a plan is approved |
| Meals | kès buys groceries and transports them to the venue; demo allocation EUR 20/person for groceries and EUR 2/person for food transport, already included in the package total (EUR 2000 + EUR 200 for 100 people) |
| Policies | Payment by 1 October and the sample refund rules are demo policies, not confirmed kès rules |

All student names, registration details, payments, accessibility requests and
messages are fictional. All WEI email addresses use the reserved `wei.example`
domain. No room allocation, venue reservation or transport booking has been made.

### Registration and payment scenarios

| Records | Expected behavior |
|---|---|
| `w02`–`w05`, `w09`–`w100` | 96 students have exact-email payment matches. Added payments use `b009`–`b100`; `b090` is distinct from the original ambiguous `b90`. |
| `w01`, `b90`, `wm04` | Camille's compound-surname/nickname transfer needs organizer review. Do not auto-link it or send a duplicate payment reminder while the match is pending. |
| `w06`, `w07`, `w08`, `wm03` | Three students have no matched payment; registration alone does not establish payment. |
| `wm02` | Tom requests a refund; organizers handle the financial decision under the explicitly provisional policy. |
| `w03`, `w05`, `wm05` | Two accessibility requests require venue and transport verification; a facility hint is not confirmation. |
| `wm01`, `wm06`, `wm07` | Pickup, group-cooking/activity permissions and return details depend on an approved logistics plan. Do not invent supplier confirmations. |
| `no_logistics_plan`, `rooms_unassigned` | No plan or room assignments yet. Payment reminders, room assignments and messages `wm01`, `wm05`, `wm06`, `wm07` wait on `no_logistics_plan`. |

### Illustrative fallback packages and current limits

Every package in `travel_options.json` models two charter coaches and two nights at an **illustrative**
group venue, with groceries and their transport included. Venue names are
invented, and all costs, schedules, capacities and facility hints are demo inputs.
The original per-person totals are retained with a reassigned fictional cost
breakdown to include meals; they are not recalculated supplier quotes.
`charter_verified` and `facilities_verified` remain false.

| Option | EUR/person | Numeric constraint result at EUR 120/person |
|---|---:|---|
| A | 112 | Pass; first among the recorded options |
| B | 118 | Pass; later return than A |
| C | 96 | Rejected: arrives at 22:10, after 21:00 |
| D | 141 | Rejected: exceeds the budget ceiling |
| E | 78 | Rejected: overnight travel and arrival the following day |

The per-person breakdown in EUR is A: 35 coaches + 55 lodging + 20 groceries +
2 food transport; B: 40 + 56 + 20 + 2; C: 30 + 44 + 20 + 2;
D: 42 + 77 + 20 + 2; E: 22 + 34 + 20 + 2. These are allocations within each
total, not surcharges. `cost_breakdown_per_person_cents`, when supplied, contains
nonnegative integer cents and must sum to `cost_per_person_cents`; code checks
this consistency. `max_cost_per_person_cents` applies to the full requested
package, including meals when explicitly requested. Ambiguous meal inclusion
still requires clarification.

The default `python -m bureau plan wei` sends the full briefing to the LLM.
The request explicitly includes meals and food transport and requests two
separate accessible rooms. Private coach hire, kitchen access and activity
permissions are not supported hard fields in the current extraction schema.
The model may ask clarifications, but a successful extraction can also omit
these unsupported checks and proceed to search. Search normally composes cached
Jinko hotel rates with recorded charter transport, including the catering budgets
once. Composed options have different IDs and may have different prices from the
fallback packages or the provisional participation fee.

With the current cache, the cheapest package meeting the travel-time checks is
EUR 135.59/person (EUR 35 charter transport + EUR 78.59 lodging + EUR 20 groceries
+ EUR 2 food transport). Both the unchanged EUR 120 ceiling and EUR 90 return
`ESCALATE`. An explicit EUR 140 override can demonstrate selection, but is only a
what-if scenario, not an approved budget or participation fee.

`--recorded-constraints` skips extraction and exercises the supported numeric/time
checks and ranking on the search results. When using the fallback package fixture,
A/B pass at EUR 120; no option passes at EUR 90. A `VALID` result in this
offline demonstration does **not** certify charter service, bus capacity, venue
facilities, return deadline or availability. The current gate checks cost-breakdown
consistency, lodging capacity, price, outbound arrival and overnight travel; accessibility is marked
for organizer verification. Extra transport/lodging fields are descriptive
metadata, not additional enforced constraints. `travel.catering` records kès's
purchasing and food-transport responsibilities and the unconfirmed demo budgets.
It is passed to `TravelRequest.catering` so composition includes groceries and
their transport in the per-person price; fallback package totals already include them.
`travel.organizer_checks` and `rules.md` retain the outstanding requirements for
human review: menu, quantities, dietary needs, food transport capacity, storage
and handling, as well as venue and coach checks. No particular food-transport
method is confirmed.

Jinko hotel search supports live and replay modes. Its cached quote prices one
double room; the demo scales it to 50 rooms for 100 people, without confirming
a group block. Ground search returned 404 for the current key, so charter
transport remains illustrative. **Private coach hire**, group kitchens and
activity permissions still require verification. Preserve raw cached responses
as provider evidence; the illustrative fallback packages are not Jinko results.
The current planner takes a supplied destination, so
Trouville-Deauville is an unconfirmed search area, not a destination it discovered.

```bash
python -m bureau detect wei
python -m bureau plan wei                         # configured OpenAI key; supported checks only
python -m bureau plan wei --recorded-constraints   # offline, cached hotels + recorded transport
python -m bureau plan wei --recorded-constraints --budget 90  # offline, ESCALATE
python -m unittest tests.test_wei_data tests.test_planner
```

Detection prints **100 participants, 97 payments, 0 groups, 7 messages**, with
**4 blocking** and **7 non-blocking** issues. These are fixture checks, not
evidence of real registrations or payments. The historical planning evaluation
cases keep their own explicit 40-person request context and transport/lodging-only
options in `eval/cases/planning_options.json`, independent of this 100-person demo;
their gold labels are not rewritten to fit event data.

## Hackathon scenarios and expected outcomes

The original `p01`–`p18`, payments, three teams and `m01`–`m05` are preserved.
All 32 added participants have an exact-email payment, so the original unpaid and unmatched-payment expectations remain valid.
The eight added teams have 2–4 members each, with no overlapping membership.

### State detected by fixed code

| Records | Scenario | Expected outcome |
|---|---|---|
| `f90` → `p01` (Antoine), `m01` | Initial in payer name and swapped email parts | `unmatched_payment:f90` is blocking and `needs_human`; identity score 0.91, band `ask_human`. Propose linking only with organizer confirmation. Exclude `p01` from payment reminders while the match is pending. |
| `f91` | Jean Dupuis payment with no registered participant | Non-blocking `unmatched_payment:f91`, `needs_human`; all candidates remain `different`. Do not link it to a registrant. |
| `p07, p12, p15, p18` | No recorded payment | Blocking `unpaid_membership`; investigate or draft reminders. Raw eligibility also lists `p01` as unpaid, before detection excludes the pending match. |
| `p02`, `t-orbit`, `t-nomads` | Léa belongs to two teams | Blocking `multiple_group_membership:p02`; ask which team she will keep before proposing a move. |
| `t-dragons` | DataDragons has five members | Blocking `group_over_capacity:t-dragons`; propose a compliant reorganization after confirming members' choices. |
| `p13`–`p18`, `p48`, `p49` | Eight ungrouped participants want a team | Non-blocking `solo_participants`. Propose groups of 2–4 with each person once; address outstanding fees and existing team violations before approving a complete replacement of team assignments. |
| `p19`–`p50`, `f19`–`f50` | Added registrations and matching payments | All 32 are paid; no new unmatched-payment or unpaid issues. In particular, `f30` matches the second registered email of `p30`. |
| `t-lantern, t-mosaic, t-cobalt, t-harbor, t-cedar, t-pixel, t-aurora, t-river` | Eight valid added teams | No additional team violations. Mosaic, Harbor and Aurora have three members; the other five have four. |
| `p50` | Salomé intentionally competes alone | No team-search issue for her: individual participation is permitted and `looking_for_group` is false. |

### Messages for agent investigation

Every message initially becomes one non-blocking `unprocessed_message` issue (`message:mNN`).
The outcomes below are review/evaluation expectations, **not recorded live-model results**.
Rule answers must cite the relevant section. Unsupported questions, refunds, personal-data requests and rule exceptions go to organizers.
Draft replies use the sender's language and the AI-assistance signature; every proposed action requires approval.

| Message | Language / channel | Scenario | Expected proposal or response |
|---|---|---|---|
| `m01` | FR / email | Antoine says he paid from his personal address | Check eligibility and `match_person(f90)`; propose `LINK_PAYMENT` to `p01` with a question for organizers, never an automatic match. |
| `m02` | EN / email | Continue a project started before the hackathon | `SEND_MESSAGE`, citing §7: declare the existing project; only work created during the hackathon is evaluated. |
| `m03` | FR / Discord | Conflicting October and November final dates | `SEND_MESSAGE`, citing §4: the final moved to November; do not invent an exact day. |
| `m04` | EN / email | Can the demo video be in English? | `ESCALATE`: §6 limits duration but does not specify a language. |
| `m05` | EN / email | Sponsor requests participant contacts for later marketing | `ESCALATE`, citing §5 and §10. Do not disclose the list; activating partner access does not authorize post-event marketing. |
| `m06` | FR / email | Membership fee and Luma registration | `SEND_MESSAGE`, citing §3: the 2026 fee is EUR 10 (1000 cents), and Luma registration is also required. |
| `m07` | EN / email | Submission checklist | `SEND_MESSAGE`, citing §6: video up to two minutes, description, repository with README test instructions, and member names. |
| `m08` | FR / Discord | Does a pitch-only fifth member count in DataDragons? | Cite §3: teams have at most four people; a pitch role does not remove membership. Do not approve the five-person team. |
| `m09` | EN / email | Léa asks to remain in Orbit and NeuralNomads | Cite §3, explain one team per person and ask which team she chooses. Any requested exception needs `ESCALATE`; do not choose for her. |
| `m10` | FR / email | Elias (`p22`) requests a move from Lantern to Mosaic with both teams' agreement | Check eligibility and team sizes; propose `MOVE_MEMBER` from `t-lantern` to `t-mosaic`. Result after approval: three and four members, respectively, and one membership for `p22`. |
| `m11` | EN / email | Elena (`p25`) requests a fifth slot in full Cobalt | Capacity check fails under §3; `ESCALATE` the exception request. No `MOVE_MEMBER` that would leave Cobalt with five members. |
| `m12` | FR / form | Daria (`p48`) and Kenji (`p49`) want help finding a team | Check eligibility and existing memberships, then use `propose_groups` for the available participants. Respect 2–4 members per team and keep existing teams when preparing any complete `UPDATE_GROUPS` proposal. |
| `m13` | EN / email | Malik asks about payment made with his second registered email | Check `p30` / `f30`: exact email match, already paid. Draft confirmation without creating or linking another payment. |
| `m14` | FR / email | Victor claims payment but has no receipt | Check `p18`: no matching payment. Ask for payment details/evidence; do not mark him paid or reuse `f91`. |
| `m15` | EN / email | Resell unused partner credits | `SEND_MESSAGE`, citing §5: resale and transfer are prohibited. |
| `m16` | FR / email | Use partner credits for personal consulting | `SEND_MESSAGE`, citing §5: personal and commercial use outside the hackathon is prohibited. |
| `m17` | EN / email | Is paying alone enough without Luma registration? | `SEND_MESSAGE`, citing §3: both membership payment and registration are required; do not invent a registration for the friend. |
| `m18` | FR / email | Exact submission time and timezone | `SEND_MESSAGE`, citing §4 / §6 and the event deadline: `2026-09-27T23:59:00+02:00`. |
| `m19` | EN / email | Would a submission just after the deadline be accepted? | `SEND_MESSAGE`, citing §6: late submissions are not accepted. Any request to waive that rule must go to organizers. |
| `m20` | FR / email | Prize amount and travel reimbursement | `ESCALATE`: neither is specified in the supplied rules. Do not invent an amount or reimbursement policy. |
| `m21` | EN / email | Wheelchair access at the final venue | `ESCALATE`: `p37.needs` records the request, but the fixtures do not confirm venue accessibility. |
| `m22` | FR / form | Vegetarian meals at the final | `ESCALATE`: `p38.needs` records the request, but meal provision is not documented. |
| `m23` | EN / email | Cancellation and membership-fee refund | `ESCALATE`: a refund is a financial decision and there is no refund policy in the supplied rules. No automatic refund. |
| `m24` | FR / email | Salomé wants to compete individually | `SEND_MESSAGE`, citing §3: individual participation is allowed. Do not add `p50` to the team-search pool. |
| `m25` | EN / email | Dashboard with fixed scripts and no LLM | `SEND_MESSAGE`, citing §2: the project must use an LLM and implement real agent logic. |

### Verify the fixtures

```bash
python -m bureau detect hackathon
python -m unittest discover -s tests -t .
```

Detection should print **50 participants, 47 payments, 11 groups, 25 messages**, then **4 blocking** and **27 non-blocking** issues.
The 31 issues consist of the six state issues above and 25 message issues.
Existing test expectations need no changes. These checks run offline; they do not validate live-model responses.
On Windows, use `$env:PYTHONIOENCODING="utf-8"` in PowerShell if accented names do not print correctly.

## Adding an event

Create `data/<event_id>/` with at least `event.json` and `participants.json`. It appears automatically in the CLI and the API.

## `wei/transport_options.json` (T14)
Illustrative round-trip charter options from the École polytechnique campus in Palaiseau
to the Trouville-Deauville search area, using two 53-seat coaches for 100 students
(price per person in cents). They remain unverified because Jinko ground search
returned 404 for our key. Composition combines them with Jinko hotel rates and the
demo catering budgets. `wei/event.json` → `travel.search` holds the hotel search
parameters (city, dates, 50 double rooms, station).

## `wei/jinko_cache/` (T11)
Raw Jinko responses saved by `JINKO_MODE=live` and read in `replay` mode (tests, demo), keyed by a
hash of the request body. `hotel_search_*.json` is a real response from 2026-09-26: one double room
in Deauville, 9–11 October 2026. The raw response is preserved; scaling its room
price to 50 rooms for 100 people does not establish group availability, kitchen
access or activity permissions. `group_block_confirmed` remains false. Hotel names
and prices are public offers, not personal data. No API key is stored. Ground search
is not cached because the endpoint returned 404 for our key.
