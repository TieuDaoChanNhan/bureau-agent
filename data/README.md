# data

Sample events. **Read-only input**: runtime changes go to `runtime/<event>/` (git-ignored).
All people, emails and payments are fictional. Never commit real personal data.

| Event | Folder | Planted inconsistencies |
|---|---|---|
| X-IA hackathon | `hackathon/` | payment with swapped email parts (f90 → p01), unrelated payment (f91), one person in two teams (p02), team of 5 (DataDragons), 5 messages |
| Integration weekend | `wei/` | no travel plan yet, transfer with compound surname and nickname (b90 → w01), refund request, recorded travel packages |

## File formats
Datetimes are ISO 8601 **with timezone** (`2026-09-25T09:00:00+02:00`). Money is integer cents.

| File | Content |
|---|---|
| `event.json` | `name`, `deadlines`, `settings` (e.g. `unpaid_kind`, `group_kind`, `needs_logistics`), `travel` (WEI only: request, origin, destination, constraints) |
| `participants.json` | `id, name, emails[], registered_at, skills[]?, needs[]?, looking_for_group?` |
| `payments.json` | `id, payer_name, amount_cents, currency, paid_at, payer_email?, reference?, participant_id?` |
| `groups.json` | `id, kind (team/room), name, members[], capacity_min, capacity_max, declared_at?` |
| `messages.json` | `id, channel (email/discord/form), sender, text, received_at` |
| `rules.md` | One `## §N Title` section per rule; parsed into `Rule` objects |
| `travel_options.json` | WEI only: recorded packages until the Jinko client (T11/T12) replaces them |

## Adding an event
Create `data/<event_id>/` with at least `event.json` and `participants.json`. It appears automatically in the CLI and the API.
