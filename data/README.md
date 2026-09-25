# data

Sample events. **Read-only input**: runtime changes go to `runtime/<event>/` (git-ignored).
All people, emails and payments are fictional. Never commit real personal data.
New hackathon contacts use reserved `.example` domains; the original fictional records are retained unchanged.

| Event | Folder | Planted scenarios |
|---|---|---|
| X-IA hackathon | `hackathon/` | 50 participants, 47 payments, 11 teams, 25 messages (12 French / 13 English); ambiguous and unrelated payments, unpaid members, conflicting teams, team moves, rule questions and organizer escalations |
| Integration weekend | `wei/` | no travel plan yet, transfer with compound surname and nickname (b90 → w01), refund request, recorded travel packages |

## File formats

Datetimes are ISO 8601 **with timezone** (`2026-09-25T09:00:00+02:00`). Money is integer cents.
Payment values use `amount_cents`; `event.json` stores the configured membership fee as `fee_amount_cents`.

| File | Content |
|---|---|
| `event.json` | `name`, `deadlines`, `settings` (e.g. `unpaid_kind`, `group_kind`, `needs_logistics`), `travel` (WEI only: request, participants, origin, destination, depart_after, constraints; loaded into `EventState.travel`) |
| `participants.json` | `id, name, emails[], registered_at, skills[]?, needs[]?, looking_for_group?` |
| `payments.json` | `id, payer_name, amount_cents, currency, paid_at, payer_email?, reference?, participant_id?` |
| `groups.json` | `id, kind (team/room), name, members[], capacity_min, capacity_max, declared_at?` |
| `messages.json` | `id, channel (email/discord/form), sender, text, received_at` |
| `rules.md` | One `## §N Title` section per rule; parsed into `Rule` objects |
| `travel_options.json` | WEI only: recorded packages until the Jinko client (T11/T12) replaces them |

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
