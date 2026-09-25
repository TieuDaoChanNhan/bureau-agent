# bureau/agent

The single event agent. One orchestrator, no multi-agent.

| File | Role |
|---|---|
| `prompts.py` | System prompt and the AI signature added to drafted messages |
| `tool_specs.py` | JSON schemas given to the model (`TOOLS`) and their handlers |
| `loop.py` | `resolve_issue(state, issue)` and `run_pending(state)`: propose actions for runnable issues |

## How one issue is resolved
```
issue JSON ─► model ─► tool calls ─► results ─► … ─► propose_action ─► ProposedAction
```
- Max 8 steps. Tool errors are returned to the model, not raised.
- The model chooses which tools to call. **No hard-coded routing** (e.g. "if the message says 'paid', call match_person"): that choice is what makes the agent agentic.
- The agent never executes. `propose_action` only records a proposal.
- `run_pending` skips existing proposals and issues blocked by unresolved `depends_on` entries, then saves newly created proposals through the runtime store.

## Configuration
`OPENAI_API_KEY` and `OPENAI_MODEL` in `.env` (see `bureau/config.py`).

## Try it
```bash
python -m bureau run hackathon --issue message:m01
```
