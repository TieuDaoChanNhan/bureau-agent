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
| Pick a task | Claim an unassigned [GitHub issue](https://github.com/TieuDaoChanNhan/bureau-agent/issues) (rules in [CONTRIBUTING.md](CONTRIBUTING.md)) · specs in [TASKS.md](TASKS.md) |
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
| `docs/` | Product proposal, architecture, example API payloads | [→](docs/README.md) |

## Quick start

Requires Python 3.11+. Full setup (venv, pre-commit hook, Windows notes) in [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
pip install -r requirements.txt
cp .env.example .env                      # add OPENAI_API_KEY (default model: gpt-4.1)

python -m bureau detect hackathon         # issues found by fixed code (no LLM)
python -m bureau plan wei                 # LLM extraction, cached hotels + recorded transport (needs an OpenAI key)
python -m bureau plan wei --recorded-constraints  # offline demo, recorded constraints + Jinko replay
python -m bureau plan wei --recorded-constraints --budget 120  # diagnosis, no relaxation
python -m bureau run hackathon --issue message:m01   # the agent (needs a key)
python -m eval.run_eval                  # labeled corpus evaluation (needs a key)

uvicorn api.main:app --reload             # API + web UI on http://127.0.0.1:8000
python -m unittest discover -s tests -t . # tests
```
On Windows, set `PYTHONIOENCODING=utf-8` if accented names print incorrectly.

The planner reads the organizer's request with the configured LLM. Ambiguous
requests produce clarification questions before any travel-option search. Use
`--recorded-constraints` explicitly to demonstrate the deterministic planner
without an API key. `--budget` overrides the per-person budget; other unresolved
questions still require an organizer's answer.

The neutral **Student association WEI (demo)** has 100 fictional registrations
and a provisional EUR 150 student fee, including groceries and their transport
by the association. Dates, prices and logistics remain unconfirmed; an experienced
WEI organizer's review is still pending before merge. The short organizer request
deliberately leaves coach inclusion in the EUR 150 ceiling unclear, so live
extraction should ask for clarification before searching. Once the organizer
answers that the ceiling covers the full package, current cached options C/E/F
pass the supported checks at EUR 135.59/140.59/142.59. The offline
`--recorded-constraints` mode supplies that complete-package interpretation
explicitly; `--budget 120` demonstrates `ESCALATE` with the same cache.

## Status

| Part | Status |
|---|---|
| Data model, sample data (2 events), issue detection | ✅ done, tested |
| Deterministic tools (rules, eligibility, identity, groups) | ✅ done, tested |
| Planner: hard-constraint gate, ranking, diagnosis | ✅ done, tested |
| Agent loop (OpenAI tool calling) | ✅ live acceptance verified with `gpt-4.1`; 3 labeled cases and full hackathon batch (see [agent checks](bureau/agent/README.md#live-acceptance-checks-t04)) |
| Store, executor, API routes except `/plan` | ✅ done, tested; messages use a simulated outbox |
| Evaluation | ✅ 50 labeled message cases and 8 planning requests, live LLM metrics and saved reports; [definitions and limits](eval/README.md) |
| Web UI | ✅ organizer console wired to the runtime API; [usage](web/README.md) |
| Constraint extraction (LLM) | ✅ structured constraints from organizer text, with clarification and accessibility verification flags; [planner details](bureau/planner/README.md) |
| Jinko client, package composition | ✅ hotels verified live with replay cache; recorded transport because ground search returns 404; group availability requires confirmation |

## What is real and what is simulated

| Component | In this build |
|---|---|
| Event state, detection, rule checks, identity scoring, constraint gate | Real (Python) |
| Agent investigation and proposals | Real (OpenAI) |
| Travel constraint extraction | Real (configured LLM); `--recorded-constraints` selects the offline fixture explicitly |
| Registrations, payments, messages | Simulated sample data with planted inconsistencies; no real personal data |
| Travel options | Cached Jinko hotel rates scaled to the group + illustrative charter transport + demo catering budgets; illustrative full-package fallback if hotel search is unavailable |
| Sending messages, booking, payments | Not performed; actions are proposals for organizers |

Messages drafted by the agent end with "Drafted with AI assistance, approved by the organizers." (EU AI Act, Art. 50).
