# bureau (Python package)

| Path | Role |
|---|---|
| [`core/`](core/README.md) | Event state, loading, issue detection, storage, executor |
| [`tools/`](tools/README.md) | Deterministic tools called by the agent |
| [`agent/`](agent/README.md) | The single agent (prompt, tool schemas, loop) |
| [`planner/`](planner/README.md) | Trip planning pipeline |
| `config.py` | Paths and settings from `.env` |
| `cli.py`, `__main__.py` | `python -m bureau detect | run | plan`; `run` batches runnable issues and saves proposals |

Dependency direction: `core` ← `tools` ← `agent` / `planner` ← `cli`, `api`. `core` imports nothing from the other packages except `tools` helpers used by detection.

## Public demo configuration

`config.py` reads `DEMO_MODE`, `DEMO_DAILY_LLM_LIMIT`, `DEMO_SESSION_LLM_LIMIT`
and `DEMO_MAX_OUTPUT_TOKENS` from the environment. Render enables demo mode;
CLI calls retain their usual storage. See [deployment](../docs/DEPLOY.md).
