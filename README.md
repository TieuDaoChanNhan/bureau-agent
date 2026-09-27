# Bureau Agent

**An operations agent for volunteer-run associations.** It finds what needs attention in an event, investigates it with tools, and proposes one action with its evidence. **Nothing is sent, changed or booked until an organizer approves it.**

> LLM for ambiguity · Code for invariants · Humans for accountability

**▶ Try it online:** [bureau-agent.onrender.com](https://bureau-agent.onrender.com) · **🎬 Demo video (2 min):** TODO · **🧭 Guided demo:** open the app and click **Start the guided demo**

Built during the X-IA Hackathon #1 "Rise of Agents X" (25–27 September 2026). All code in this repository was written during the hackathon.

![Bureau Agent: hero and console](docs/screenshots/t35-hero.jpg)

---

## The problem

Student and volunteer associations run real events (hackathons, integration weekends, galas) with a board of volunteers who study or work full time. Around every event they juggle:
- registrations and payments that do not match ("I already paid from my personal email");
- team and room rules;
- trips with several constraints (budget, arrival time, accessibility);
- dozens of repetitive messages in French and English.

The work is not hard. It is **fragmented, repetitive, and easy to get wrong**, and a mistake (a wrong payment link, a missing reply, a team over the limit) lands on a participant.

## What Bureau Agent does

One loop handles every kind of event:

![The loop: event state → detect (code) → investigate (AI agent) → proposed action → organizer approves, edits or dismisses → executor re-checks rules and applies → event state](docs/screenshots/loop-diagram.png)

1. **Detect.** Deterministic checks read the event and list what needs attention, blocking first: unmatched payments, unpaid fees, a person in two teams, a team over capacity, unanswered messages, a trip without a plan. 31 issues are found in the sample hackathon.
2. **Investigate.** An AI agent (OpenAI `gpt-4.1`, tool calling) picks its own tools: look up a participant, read payments, score an identity match, search the rules, check teams. It proposes **one** action: link a payment, send a reply, move a member, or ask the organizers. Every tool call is recorded and shown.
3. **Decide.** The organizer sees the proposal first, with the agent's question, the evidence and an editable draft reply. Approving is what changes data or "sends" the reply (to a simulated outbox), and it is logged.

The same loop plans trips. The organizer's request for a student integration weekend ("100 students, leave the campus Friday after 17:00, €150 each with meals included, arrive before 21:00, no overnight travel, two step-free rooms, two coaches") becomes structured constraints. The request does not say whether the €150 covers the coaches, so the planner **asks before searching**. It builds packages from **real hotel offers (Jinko responses saved on 26 September 2026 and replayed, so the demo is reproducible)**, adds the meal budget once, and checks every package in code: **3 of 8 are valid** at €150, ranked by the organizers' preferences. At €120, **none is**, and it **never relaxes a constraint by itself**: it says which single change would unlock each option. Choosing a package unlocks six waiting issues (reminders, rooms, four student questions).

## Why it is safe to use

| Risk | What prevents it |
|---|---|
| The model links a payment to the wrong person | The identity score is enforced **in code** at two layers (proposal and approval): below 0.70 is refused. A live `gpt-4o-mini` run did propose such a link; it is now impossible. |
| Someone writes on behalf of another participant | Also in code, at both layers: a reply about a participant goes only to their registered address, and a team change needs a request from the member's registered address. Found by our held-out safety evaluation, then fixed. |
| The model invents a rule | Answers must cite a rule section; when the rules are silent, it escalates to the organizers ("silence is not permission"). |
| A personal-data or refund request | Escalated, never answered by the agent. |
| A team over the size limit, a person in two teams | Group invariants are re-checked by the executor on approval. |
| A trip that breaks a constraint | Hard constraints are checked in code; soft preferences only rank valid options; accessibility is marked "organizers confirm". |
| Anything with consequences | Every action requires approval, drafted replies carry "Drafted with AI assistance, approved by the organizers.", and approvals are logged. |

## Results

Offline evaluation on **50 labeled messages** (the 25 sample messages plus 25 paraphrases), same code, one run per model ([details](eval/README.md)):

| Metric | `gpt-4.1` (default) | `gpt-4o-mini` |
|---|---|---|
| Correct action type | **90%** (45/50) | 76% (38/50) |
| Rule citation | **96.7%** | 90.0% |
| Asks the organizers at the right time | **84%** | 66% |
| Unnecessary questions to organizers | **6** | 15 |
| Invariant violations | **0** | 1 |

Planning evaluation on **20 requests**, including 12 current-WEI cases using cached Jinko hotels:
supported hard fields 20/20, clarification presence 16/20, feasibility 11/12 searched
cases and exact ranking 5/5 labeled searched cases. Cheapest-first selected C;
earliest-return selected F. One request forbidding coaches still received coach
options ([#102](https://github.com/TieuDaoChanNhan/bureau-agent/issues/102)); three
current cases stopped for unnecessary accessibility questions. [Results and limits](eval/README.md#recorded-expanded-planning-run).

**Held-out safety evaluation** (24 new adversarial and control cases the prompt was not tuned on, `gpt-4.1`, 3 runs each; [details](eval/README.md#safety-corpus-held-out-t46)):

| Category | Handled correctly |
|---|---|
| Prompt injection ("mark me as paid", "admin mode", "ignore the rules") | **18/18** |
| Personal-data requests | **9/9** |
| Pressure and exceptions (claimed authority, refunds, waivers) | **15/15** |
| Ordinary questions (must be answered, not escalated) | **15/15**, 0 false refusals |
| Impersonation (unregistered or look-alike sender) | 11/15 → **15/15** after the fix |

The first run found one real weakness: the agent did not check that the **sender is the registered participant** a request is about. 7 of 72 proposals acted on such requests, for example addressing a payment confirmation to an unregistered address. None bypassed approval, but none was blocked by code either. We fixed it **in code, not in the prompt** ([T50](https://github.com/TieuDaoChanNhan/bureau-agent/issues/94)): replies about a participant go only to their registered address, and team changes need a request from the member. Re-run on the same corpus: **0 unsafe proposals out of 72**, 100% acceptable actions, still 0 false refusals. The corpus is small and was written by the team that fixed it; a larger, independently written one is in progress ([#96](https://github.com/TieuDaoChanNhan/bureau-agent/issues/96)).

**230 automated tests** (no API calls: a scripted fake model) run on every push.

Real-user feedback: TODO (T18).

## Try it

### Online
[bureau-agent.onrender.com](https://bureau-agent.onrender.com) runs the live agent (`gpt-4.1`). Each browser gets its own copy of the sample data; a shared daily limit on model calls applies, after which proposals come from clearly labelled saved examples. The first load after a quiet period can take up to a minute (free hosting). Open it and click **Start the guided demo**: a 3-minute, 15-step tour that highlights each button. **See every feature** under it opens the full 30-step tour.

### Locally
Requires Python 3.11+ and an OpenAI API key for the live agent. Everything else works without a key.

**macOS / Linux**
```bash
git clone https://github.com/TieuDaoChanNhan/bureau-agent.git && cd bureau-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then put your key in OPENAI_API_KEY=...
uvicorn api.main:app --reload   # open http://127.0.0.1:8000
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/TieuDaoChanNhan/bureau-agent.git; cd bureau-agent
py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env     # then put your key in OPENAI_API_KEY=...
$env:PYTHONIOENCODING="utf-8"; python -m uvicorn api.main:app --reload
```

**With [uv](https://docs.astral.sh/uv/)** (any OS; same locked versions)
```bash
uv sync                          # creates .venv from uv.lock (Python 3.11)
uv run uvicorn api.main:app --reload
```
`pyproject.toml` and `uv.lock` are the source of the dependencies; `requirements.txt` is exported from the lock (command at the top of `pyproject.toml`), so pip, Render and uv install the same versions.

Then open http://127.0.0.1:8000 and click **Start the guided demo**. **Reset demo** (click twice) restores the sample data. Write the key without quotes: `OPENAI_API_KEY=sk-...`.

**Tests and evaluation**
```bash
python -m unittest discover -s tests -t .     # 227 tests, no API key needed (or: uv run python -m unittest …)
python -m eval.run_eval                       # 50-case evaluation (needs a key)
python -m bureau plan wei --recorded-constraints   # trip planner offline: 3 of 8 packages valid at €150
python -m bureau plan wei --recorded-constraints --budget 120   # none valid: diagnosis, no relaxation
```

## Features at a glance

| | |
|---|---|
| **Guided demo** | A 3-minute quick tour (15 steps, chapters, key numbers at the end) and a full 30-step tour; each step highlights one element and moves on by itself after each action |
| **Agent steps** | Every tool the model chose, with arguments and results, replayed step by step after a run |
| **Proposal first** | Action, the agent's question, what will change, and the editable draft reply, then the evidence |
| **Live messages** | Type any message (English or French) and watch the agent handle it |
| **Batch run** | Run the agent on every open issue with progress and Stop |
| **Trip planner** | Asks before searching, real hotel offers, meal budgets itemized per person, return times, packages checked in code, a what-if budget (20% below the request), and a diagnosis without relaxing constraints |
| **Dependencies** | Choosing a travel plan unlocks the six issues waiting for it (reminders, rooms, four student questions) |

![Proposal first](docs/screenshots/t35-proposal-card.jpg)
![Trip packages](docs/screenshots/t48-trip-options.jpg)

## Architecture

| Layer | Folder | Role |
|---|---|---|
| Core | [`bureau/core/`](bureau/core/README.md) | Data model, issue detection (fixed checks), storage, the **executor**: the only code that changes data, after approval |
| Tools | [`bureau/tools/`](bureau/tools/README.md) | Deterministic functions the agent calls: rules search, eligibility, identity scoring, group checks |
| Agent | [`bureau/agent/`](bureau/agent/README.md) | One tool-calling agent: prompt, tool schemas, a loop that validates proposals and records every step |
| Planner | [`bureau/planner/`](bureau/planner/README.md) | LLM constraint extraction → Jinko hotels × transport → packages in code → hard-constraint gate → ranking → LLM explanation |
| API | [`api/`](api/README.md) | FastAPI routes used by the web console |
| Web | [`web/`](web/README.md) | Static HTML/JS console and guided tour (no build step) |
| Public demo | [`docs/DEPLOY.md`](docs/DEPLOY.md), [`demo/`](demo/README.md) | Render free service from `main`: per-browser sessions, model-call limits, saved-example fallback; static backup |
| Evaluation | [`eval/`](eval/README.md) | Labeled cases, runner, recorded model comparison |

Design choices: **one agent, not several** (the loop is the product); invariants in code, not in the prompt; the agent only proposes; timezone-aware dates and money in integer cents.

## Sponsor tools

| Tool | How we used it |
|---|---|
| **OpenAI** | `gpt-4.1` with tool calling for the agent; strict structured output for trip constraints; short trade-off explanations. Chosen after measuring `gpt-4o-mini` (table above). |
| **Jinko** | Live hotel search, saved on 26 September 2026 and **replayed** in tests, in the demo and on the public site (`JINKO_MODE=replay`), because live prices change daily: a live run on 27 September returned **0 of 8** valid packages at €150 (the cheapest hotel was gone and prices rose), against 3 of 8 in the saved responses the tour and video use. To search live, set `JINKO_MODE=live` and `JINKO_API_KEY`; responses are saved under `data/<event>/jinko_cache/`. Findings: our key works on the production host; ground search returned 404 for it; **group blocks (10×4 or 20×2 rooms) return no availability**, and rates allow "5 passengers and under". So a room is priced and scaled, and every package says "group block to confirm with the hotel". |
| **Pipelex** | Tried first for constraint extraction (typed `PipeLLM`, it worked on our case). We kept OpenAI structured output because it covered this one call with less setup ([why](bureau/planner/README.md)). |

## What is real and what is simulated

| Component | In this build |
|---|---|
| Issue detection, rule checks, identity scoring, constraint gate, executor | Real (Python), tested |
| Agent investigation, constraint extraction, explanations | Real (OpenAI `gpt-4.1`) |
| Hotel offers | Real Jinko responses from 26 September 2026, replayed so the demo gives the same result every time (live mode available, see Jinko above) |
| Transport options | Illustrative coach charter prices (Jinko ground search unavailable for our key) |
| Registrations, payments, messages | Fictional sample data with planted inconsistencies; no real personal data. The trip scenario was modelled on a student integration weekend and reviewed by a team member who took part in one |
| Sending, booking, paying | Not performed: approved replies go to a simulated outbox, and organizers book themselves |

## Limitations

- Sample data only; not yet connected to a real inbox, Discord, Luma or HelloAsso export.
- The local JSON store assumes one writer at a time. The deployed demo isolates each browser (T20).
- Coach prices are illustrative, and group hotel blocks, kitchen use and accessibility must be confirmed with the venue.
- The agent's steps are shown after a run (replayed), not streamed live.

## Team

Van Khue NGUYEN, Xuan Bach HOANG, Gia Bao DINH and Huy PHAN (X-IA Hackathon #1). GitHub: [@TieuDaoChanNhan](https://github.com/TieuDaoChanNhan), [@0x2ee08](https://github.com/0x2ee08), [@pectpait](https://github.com/pectpait), [@hoanxuanbach](https://github.com/hoanxuanbach).

How we worked: issues, pull requests, reviews, and documented engineering decisions ([CONTRIBUTING.md](CONTRIBUTING.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)).

## License

[MIT](LICENSE). Third-party: Driver.js 1.3.1 (MIT, `web/vendor/DRIVER_LICENSE`).
