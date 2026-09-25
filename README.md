# Bureau Agent

**An event operations agent for volunteer-run associations.**
It keeps an event operationally consistent: detects what needs attention, investigates across internal and external data, proposes valid actions, and lets organizers approve the consequences.

> LLM for ambiguity · Code for invariants · Humans for accountability

Built during the X-IA Hackathon #1 "Rise of Agents X" (25–27 Sep 2026). All code in this repository was written during the hackathon.

---

## Start here

| I want to… | Go to |
|---|---|
| Understand the product | [docs/product-proposal.md](docs/product-proposal.md) (Vietnamese) · [interactive mockup](https://claude.ai/artifact/JCKLf1tuJLtPUPsfXK1ox4) |
| Understand the architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (Vietnamese) |
| Pick a task | [TASKS.md](TASKS.md) |
| Know how we work (branches, PRs, tests) | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Run it | [Quick start](#quick-start) below |

## How it works

```
 Event state ──► detect issues ──► agent investigates with tools ──► proposed action
     ▲                                                                     │
     └──────────── executor applies it ◄──── organizer approves ◄──────────┘
```

Answering a question, reconciling a payment, fixing a team or planning a trip are all ways of resolving an **issue** in this one loop. The agent never executes anything: it only produces `ProposedAction`s that an organizer approves.

## Repository map

| Folder | What is inside | README |
|---|---|---|
| `bureau/core/` | Data model, loading, issue detection, storage, executor | [→](bureau/core/README.md) |
| `bureau/tools/` | Deterministic tools the agent calls (rules, eligibility, identity, groups) | [→](bureau/tools/README.md) |
| `bureau/agent/` | The single agent: prompt, tool schemas, tool-calling loop | [→](bureau/agent/README.md) |
| `bureau/planner/` | Trip planning: constraints, Jinko search, packages, checks, ranking | [→](bureau/planner/README.md) |
| `api/` | FastAPI HTTP API used by the web UI | [→](api/README.md) |
| `web/` | Web UI (static HTML/JS) and the reference mockup | [→](web/README.md) |
| `data/` | Sample events (read-only input) and their file formats | [→](data/README.md) |
| `eval/` | Offline evaluation cases and runner | [→](eval/README.md) |
| `tests/` | Unit tests for every invariant | [→](tests/README.md) |
| `docs/` | Product proposal and architecture | [→](docs/README.md) |

## Quick start

Requires Python 3.11+.

```bash
pip install -r requirements.txt
cp .env.example .env                      # add OPENAI_API_KEY and OPENAI_MODEL

python -m bureau detect hackathon         # issues found by fixed code (no LLM)
python -m bureau plan wei                 # trip planner on recorded options (no LLM)
python -m bureau plan wei --budget 90     # no valid option: diagnosis, no relaxation
python -m bureau run hackathon --issue message:m01   # the agent (needs a key)

uvicorn api.main:app --reload             # API + web UI on http://127.0.0.1:8000
python -m unittest discover -s tests -t . # tests
```
On Windows, set `PYTHONIOENCODING=utf-8` if accented names print incorrectly.

## Status

| Part | Status |
|---|---|
| Data model, sample data (2 events), issue detection | ✅ done, tested |
| Deterministic tools (rules, eligibility, identity, groups) | ✅ done, tested |
| Planner: hard-constraint gate, ranking, diagnosis | ✅ done, tested |
| Agent loop (OpenAI tool calling) | 🟡 written, not yet run against the API |
| Store, executor, API routes, web UI, evaluation | ⬜ skeletons, see [TASKS.md](TASKS.md) |
| Constraint extraction (LLM), Jinko client, package composition | ⬜ skeletons, see [TASKS.md](TASKS.md) |

## What is real and what is simulated

| Component | In this build |
|---|---|
| Event state, detection, rule checks, identity scoring, constraint gate | Real (Python) |
| Agent investigation and proposals | Real (OpenAI) |
| Registrations, payments, messages | Simulated sample data with planted inconsistencies; no real personal data |
| Travel options | Recorded illustrative data until the Jinko client lands |
| Sending messages, booking, payments | Not performed; actions are proposals for organizers |

Messages drafted by the agent end with "Drafted with AI assistance, approved by the organizers." (EU AI Act, Art. 50).
