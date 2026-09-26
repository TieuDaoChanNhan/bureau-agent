# eval

Evaluation against labeled synthetic fixtures (T08). Here **offline** means a fixed
corpus with expected answers, independent of an organizer session. Message runs
still call OpenAI and incur API usage; unit tests use scripted clients without a key.

| File | Content |
|---|---|
| `cases/messages.jsonl` | 50 labeled cases: all 25 fixture messages plus 25 independently written paraphrases |
| `cases/planning.jsonl` | One labelled trip request per line: expected hard constraints, clarifications, feasibility |
| `run_eval.py` | Runs the real agent and recorded planner baseline, prints metrics, writes timestamped JSON to ignored `eval/results/` |

## Run

Install the repository requirements and configure `OPENAI_API_KEY` and
`OPENAI_MODEL` in your local `.env`. `gpt-4.1` is the model used for T04 acceptance.

```bash
python -m eval.run_eval                         # all 50 messages plus planner baseline
python -m eval.run_eval --suite messages --limit 3
python -m eval.run_eval --suite planning         # recorded inputs, no API calls
python -m unittest tests.test_eval -v            # scripted clients, no API calls
```

`--limit` bounds message cases, each using the agent's existing eight-turn limit.
`--output-dir PATH` changes where reports are saved. Windows users can set
`$env:PYTHONIOENCODING="utf-8"` before capturing output.

The evaluator loads fresh **sample** state for every case and calls `resolve_issue`
directly. It does not read or change runtime proposals, approve actions, or send
messages. The original fixtures remain unchanged. Expected labels never enter the
model context, and the client wrapper records actual model tool requests.

One failed case is recorded and later cases continue. Model/execution errors produce
exit code 1 after the report is saved; a completed evaluation exits 0 even if some
predictions disagree with the labels. There is no invented minimum accuracy gate.

## Corpus and labels

Every row has the original eight keys: `id`, `event`, `message_id`, `expected_kind`,
`expected_tools`, `expected_action`, `must_ask_human`, and `expected_rule`.
The first three cases remain unchanged. An optional `text` field replaces only the
message text in that case's in-memory state, preserving sender, channel and date.
This adds distinct questions without duplicating or expanding operational fixtures.
Paraphrases share their source scenario, so these are 50 prompts covering 25
scenarios, not 50 independent situations.

Labels come from `data/hackathon/rules.md`, the synthetic records and the expected
outcomes in `data/README.md`. Examples of distinctions requiring judgment:

- An explicit rule can be answered with `SEND_MESSAGE`, including a rule-based refusal.
- A waiver, unknown policy, privacy request or refund needs `ESCALATE`.
- The consensual, capacity-safe transfer in m10 is `MOVE_MEMBER`.
- m12 asks for a grouping suggestion, so `SEND_MESSAGE` drafts it for participants;
  a complete group replacement would also touch existing unresolved team conflicts.
- m14 has no payment evidence: request the receipt in a reply, without marking the
  participant paid. Normal approval of a reply is not an exceptional organizer question.

Schema, IDs, tool names, actions and rule references are checked before API calls.
`expected_kind` is retained for analysis, but intent accuracy is not fabricated:
the current agent contract returns an action rather than a predicted intent label.

## Metrics

| Metric | Definition and denominator |
|---|---|
| Action accuracy | Exact action type; all attempted cases, including errors |
| Tool selection | All required tool names requested by the model; additional tools allowed; errors fail |
| Rule citation | Expected ID in evidence with `source_type=rule`; only cases with a rule label |
| Human handling | `ESCALATE` or a question mark in the organizer-facing description, compared with `must_ask_human`; all cases |
| Invariant violations | Final proposals rejected by an isolated executor simulation, approval bypasses, or event-record mutations during investigation; target 0 |

Human handling is a **text heuristic**, not a semantic judge. Questions only in a
participant reply do not count; `requires_approval` does not count because all
proposals require approval. Missed and unnecessary interventions are reported
separately. Rule citation checks a reference, not whether the entire reply faithfully
interprets the rule. Tool selection measures requested tools, not successful execution.

The invariant simulation uses copied state and replaces executor outbox/audit writes
with in-memory no-ops. Existing fixture conflicts do not count against unrelated
actions; the executor applies its normal scoped checks. The metric covers those
implemented checks, not every possible semantic error. Rejected intermediate tool
arguments are retained in the trace but are not final-proposal violations. Reports
show both checked and unchecked cases; an API failure is never counted as a safe proposal.

The planning section compares the existing recorded baseline with the one supplied
planning label: exact hard constraints (plus per-key results), clarification strings,
and feasibility against recorded travel options. `extract_constraints` still ignores
the request text until T10, so these numbers are **not LLM extraction accuracy**.

## Report

`eval/results/<UTC timestamp>.json` includes the configured model, Git revision,
dataset and fixture hashes, metric definitions and denominators, input messages,
labels, tool calls, proposals, errors and invariant findings. Empty denominators are
reported as `N/A` rather than 100%. Inspect the per-case evidence when a metric fails.

These are offline metrics. "Approved unchanged", time saved and feedback come only from a real organizer session (T18) and are reported separately.
