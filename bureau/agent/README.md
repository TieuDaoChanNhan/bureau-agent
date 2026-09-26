# bureau/agent

The single event agent investigates an issue with model-selected tools and returns a proposal for organizer approval.

| File | Role |
|---|---|
| `prompts.py` | Investigation instructions, uncertainty handling, executor payload contracts and AI signature |
| `tool_specs.py` | Tool schemas and read-only handlers, including payment/group records and the complete rule text |
| `loop.py` | `resolve_issue(state, issue)`: bounded tool loop with error feedback; `run_pending(state)`: persist proposals for runnable issues |

## How one issue is resolved

```text
Issue + source messages -> model -> tool call -> result -> ... -> propose_action -> ProposedAction
```

- The model chooses the tools and action. There is no keyword routing or additional agent.
- Source messages include their sender, channel and timestamp as structured data.
- Up to eight model turns are allowed. Independent lookups can share a turn; a final proposal must be called alone after reading their results.
- The last turn is reserved for `propose_action`; the model still chooses the action type and must escalate when evidence is insufficient.
- Malformed JSON, failed tools and incomplete proposal payloads return an error to the model so it can retry.
- Only an accepted proposal changes the issue status and appends to `state.actions`. No payment is linked, group moved or message sent by the agent.
- `run_pending` skips existing proposals and issues blocked by unresolved `depends_on` entries, then saves newly created proposals through the runtime store.
- Payload shape checks prevent missing executor inputs; business invariants are still checked by the deterministic tools and again by the executor after approval.
- `get_payment` and `list_groups` expose actual records rather than requiring guessed ids or memberships.
- Rules are in English. `search_rules` uses English keywords; `list_rules` lets the model read all sections before declaring a policy absent.
- Verbose mode prints the complete tool arguments on `->` lines for review.

The Chat Completions flow follows the [OpenAI function-calling guide](https://developers.openai.com/api/docs/guides/function-calling).

## Configuration

Install the repository dependencies, then set `OPENAI_API_KEY` and `OPENAI_MODEL` in the project `.env` (see `bureau/config.py` and `.env.example`).
Use the model enabled for your hackathon credits, with Chat Completions function-calling support.
The repository default is `gpt-4o-mini`; an environment variable overrides the corresponding `.env` value.

```bash
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -r requirements.txt
```

Keep the key local. `.env` is ignored by Git, and offline tests do not require it.
On Windows PowerShell, set `$env:PYTHONIOENCODING="utf-8"` before capturing accented output.

## Live acceptance checks (T04)

Run these with the configured real OpenAI client, starting each command from the repository root:

```bash
python -m bureau run hackathon --issue message:m01
python -m bureau run hackathon --issue message:m02
python -m bureau run hackathon --issue message:m04
python -m bureau run hackathon
```

The three labeled cases are in `eval/cases/messages.jsonl`:

| Case | Expected evidence in the real trace and proposal |
|---|---|
| `c001` / `m01` | `get_participant`, `check_eligibility`, `match_person`; `LINK_PAYMENT` with `payment_id=f90`, `participant_id=p01`, and an explicit organizer confirmation question because the identity score is 0.91 |
| `c002` / `m02` | `search_rules`; `SEND_MESSAGE` citing §7, with recipient and a complete reply explaining the declaration of existing work |
| `c003` / `m04` | `search_rules`; `ESCALATE` because the supplied rules do not specify a video language |

The full command must finish without errors for every detected issue.
Save the actual `->` lines and JSON proposals in the pull request, together with the model, command, fixture revision and exit status.
Fake-client tests verify the loop mechanics only; they are not evidence that the live acceptance cases passed.

## Offline tests

```bash
python -m unittest tests.test_agent -v
python -m unittest discover -s tests -t .
```
