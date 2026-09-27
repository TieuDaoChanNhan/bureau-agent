# Architecture

Bureau Agent helps volunteer-run associations keep event operations consistent. It detects concrete problems in an event, investigates ambiguous cases with an AI agent, and asks an organizer to approve every consequential change.

> LLMs investigate ambiguity. Code enforces invariants. Organizers decide.

## System overview

```text
sample data -> EventState -> deterministic detection -> Issue
                    ^                                |
                    |                                v
runtime store <- executor <- organizer approval <- ProposedAction <- agent / planner
```

The FastAPI application serves the JSON API and the organizer console. The static public demo is a separate replayable build with per-browser state.

| Layer | Responsibility |
|---|---|
| `bureau/core` | Dataclasses, data loading, deterministic detection, runtime persistence, approved-action execution |
| `bureau/tools` | Pure rule, eligibility, identity, and group helpers used by the agent |
| `bureau/agent` | OpenAI tool-calling loop; it creates proposals but never changes event data |
| `bureau/planner` | Constraint extraction, recorded/live search, package composition, validation, ranking, and explanation |
| `api` | FastAPI routes for events, runs, planning, approval, reset, sessions, and the web console |
| `web` | Plain HTML, JavaScript, and CSS organizer console with guided tours |
| `demo` | Public, static replay build with no live model or provider calls |
| `eval` | Labeled, offline evaluation harness and reports |

## Event state and records

`EventState` holds an event's immutable context and mutable operating state:

- participants, payments, groups, messages, rules, deadlines, settings, travel, and logistics;
- detected `Issue` records with deterministic ids and dependencies;
- `ProposedAction` records, evidence, checks, tool trace, and approval metadata.

Money is stored as integer cents and every datetime is timezone-aware. `data/<event>/` is committed sample input. `runtime/<event>/` is ignored local state containing approved changes, issue state, actions, audit log, and simulated outbox messages.

## Issue lifecycle

1. `detect_issues(state)` derives issues from the current records: payment mismatches, unpaid registrations, group violations, logistics gaps, room allocation, and unprocessed messages.
2. Stored issue state is merged by deterministic id. Resolved and dismissed decisions remain in history even after their issue disappears from new detection.
3. The agent or planner creates a proposal for one runnable issue. Dependencies prevent premature work.
4. An organizer approves, edits, or dismisses the proposal.
5. `executor.apply()` uses a deep copy, checks scoped invariants, writes an audit event and optional simulated message, then returns the new state.
6. Detection runs again, so repaired issues disappear and dependent work becomes runnable.

The agent cannot execute actions. The executor is the only state-changing boundary.

## Agent execution

The agent uses OpenAI Chat Completions with tools such as rule search, participant lookup, eligibility checks, identity matching, group validation, and group proposals. It ends only by calling `propose_action`.

`run_pending()` is shared by CLI and API. It selects open or human-review issues without an existing proposal, skips blocked dependencies, persists each successful proposal immediately, records individual agent failures in the audit log, and returns the remaining backlog. The console runs issues one at a time to show progress and permit cancellation between issues.

Tool calls and outcomes are recorded in proposal traces. The console displays the trace after a run; it is not a live token stream.

## Planner pipeline

The trip planner keeps interpretation and enforcement separate:

```text
organizer text -> structured constraints -> search/replay -> package composition
              -> deterministic checks -> ranking -> explanation -> travel proposal
```

- Constraint extraction uses structured LLM output and asks clarifying questions instead of guessing.
- Hotel search supports Jinko live mode and recorded replay. Public demo transport choices are illustrative because the available ground-search endpoint was unavailable.
- Composition and checks are deterministic Python code. Prices are integer cents and every hard constraint produces a visible check.
- Unsupported verification, such as venue accessibility described only in free text, remains an organizer confirmation rather than a fabricated fact.
- The planner either returns a `SELECT_TRAVEL_PLAN` proposal with ranked packages or an `ESCALATE` diagnosis. Approval stores logistics and unlocks dependent work.

## API and console

The API returns dataclass-shaped JSON. The key route groups are:

- events, issue summaries, actions, and outbox;
- bounded agent runs and individual retry;
- incoming messages, which are saved as data and then investigated;
- approval, dismissal, and reset;
- trip planning, clarification answers, and what-if budgets;
- public-demo sessions and limits.

The organizer console shows detected issues, evidence, checks, proposals, tool traces, approvals, simulated outbox messages, and the trip planner. It uses no frontend build step. The public static demo replays curated fixtures and clearly marks replay behavior.

## Key decisions

| Decision | Rationale |
|---|---|
| One orchestrating agent | The agent chooses tools; fixed Python code enforces rules and execution boundaries. |
| JSON runtime state | Small, inspectable demo data is easy to reset; deployed demo sessions are isolated per browser. |
| Approval before execution | The agent drafts; organizers retain responsibility for money, identity, messages, groups, and travel. |
| Invariants in code, at two layers | Identity threshold (T29) and requester identity (T50) are checked when the model proposes, so it can revise, and again when an organizer approves. Safety findings are fixed in code, not in the prompt. |
| Replayable external data | The demonstration remains reliable without network availability or provider credits. |
| Plain web console | No build pipeline is needed for the demo, and the API remains the single data contract. |
| Labeled evaluation | Quality is measured against fixtures, while organizer feedback is reported separately when available. |

## Quality and delivery

Unit tests cover deterministic rules, agent loop recovery with fake clients, API behavior, planner replay, data consistency, evaluation, and public-demo isolation. Browser tests cover the console tours. CI runs the test suite on pushes and pull requests; dependency consistency is checked from `uv.lock`.

See the root [README](../README.md) for setup, live/demo links, results, and limitations. See [DEPLOY.md](DEPLOY.md) for the public demo deployment and [demo-script.md](demo-script.md) for the submission video flow.
