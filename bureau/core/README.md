# bureau/core

The event state and everything that reads or changes it.

| File | Role | Status |
|---|---|---|
| `models.py` | Dataclasses: `EventState` (incl. optional `travel` request and chosen `logistics`), `Participant`, `Payment`, `Group`, `Message`, `Rule`, `Issue`, `Check`, `Evidence`, `ProposedAction` | done |
| `loader.py` | Loads `data/<event>/` into an `EventState`; rejects datetimes without timezone | done |
| `detect.py` | Finds issues with fixed code; issue ids are deterministic fingerprints | done |
| `store.py` | Runtime persistence under `runtime/<event>/`, status merge after re-detection | done |
| `executor.py` | Applies an **approved** action; re-checks invariants | done |

## Rules of this layer
- Only `executor.apply` changes state. Nothing else writes.
- Money is integer cents. Datetimes are timezone-aware.
- Changing `models.py` changes the contract for everyone: announce it before merging.

`executor.apply` rejects invalid travel options and payment links to unknown
participants, to a participant whose identity score is below 0.70 (unless the
payer email is one they registered), or to another owner (explicit ID, otherwise a case-insensitive email
match). Rejected actions leave the input state, outbox and audit log unchanged.
`LINK_PAYMENT` can include `to` and `message` to append one simulated reply after
validation; `edited_description` overrides that reply, as for `SEND_MESSAGE`.
Group validation remains scoped to the groups and members affected by the action.
For messages explicitly requesting a verbatim copy of a purportedly approved
answer, the executor accepts only escalation (#103). It rechecks the source
message before any outbox or audit write, including for stale or edited drafts;
approval does not bypass this guard. Ordinary quoted code is not itself a trigger.

`save_state` also stores messages, so messages added at runtime (T32) survive reloads; an older
`state.json` without them keeps the sample messages.

`store.load_outbox(event_id)` returns simulated messages, or an empty list before
any are sent. `append_outbox` stamps each entry with a timezone-aware ISO `sent_at`.
`save_state` replaces the complete actions list: callers must mutate one loaded
state and save it once, rather than saving a new action then writing an old state.

## Issue kinds produced by `detect.py`
| Kind | Blocking | Id pattern |
|---|---|---|
| `unmatched_payment` | yes if a candidate exists, else no | `unmatched_payment:<payment_id>` |
| `unpaid_membership` / `unpaid_participation` | yes | `<kind>` (one aggregated issue) |
| `multiple_group_membership` | yes | `multiple_group_membership:<participant_id>` |
| `group_over_capacity` | yes | `group_over_capacity:<group_id>` |
| `no_logistics_plan`, `rooms_unassigned` | yes | `<kind>` |
| `solo_participants` | no | `solo_participants` |
| `unprocessed_message` | no | `message:<message_id>` |

## Browser sandboxes and model budgets

`session.py` carries a request-local context variable. In public demo mode,
`store._event_dir` uses `runtime/<session>/<event>/`; other callers retain
`runtime/<event>/`. Never mutate the global runtime root for individual requests.

`llm_usage.py` reserves model attempts atomically in SQLite before every provider
call. Agent turns and both planner steps share global UTC-day and 24-hour-session
caps. Failed attempts count, output tokens are bounded, and session-tagged logs
contain no prompts or keys. Accounting failures refuse live calls. SQLite is
outside session directories and Reset never clears it, but a Render disk reset
does. The independent provider project hard limit is required; see deployment docs.
