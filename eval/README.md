# eval

Offline evaluation with labels written by the team (T08).

| File | Content |
|---|---|
| `cases/messages.jsonl` | One labelled message per line: expected kind, tools, action, rule, whether a human must be asked |
| `cases/planning.jsonl` | One labelled trip request per line: expected hard constraints, clarifications, feasibility |
| `run_eval.py` | Runs agent and planner on the cases, prints metrics, writes `eval/results/` |

## Metrics
Intent accuracy · tool selection · rule citation · escalation (needed vs unnecessary) · **invariant violations (target 0)** · constraint extraction accuracy · infeasibility detection.

These are offline metrics. "Approved unchanged", time saved and feedback come only from a real organizer session (T18) and are reported separately.
