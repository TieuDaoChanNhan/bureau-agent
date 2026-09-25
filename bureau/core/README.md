# bureau/core

The event state and everything that reads or changes it.

| File | Role | Status |
|---|---|---|
| `models.py` | Dataclasses: `EventState`, `Participant`, `Payment`, `Group`, `Message`, `Rule`, `Issue`, `Check`, `Evidence`, `ProposedAction` | done |
| `loader.py` | Loads `data/<event>/` into an `EventState`; rejects datetimes without timezone | done |
| `detect.py` | Finds issues with fixed code; issue ids are deterministic fingerprints | done |
| `store.py` | Runtime persistence under `runtime/<event>/`, status merge after re-detection | skeleton (T02) |
| `executor.py` | Applies an **approved** action; re-checks invariants | skeleton (T03) |

## Rules of this layer
- Only `executor.apply` changes state. Nothing else writes.
- Money is integer cents. Datetimes are timezone-aware.
- Changing `models.py` changes the contract for everyone: announce it before merging.

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
