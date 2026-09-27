# Demo verification

## Static backup refresh — 27 September 2026

[T45 / #82](https://github.com/TieuDaoChanNhan/bureau-agent/issues/82) is verified
on the [public Space](https://huggingface.co/spaces/bachbeo2007/bureau) and its
[direct app URL](https://bachbeo2007-bureau.static.hf.space).

- Built and published from `t45-backup` at source commit
  `eec1309636da3074f7e124777f3442a667613bbd`, which incorporates the fetched `main`.
  The task stayed on this branch; `main` was not changed.
- Published Space revision:
  [`113d71c9c93f6a27355f8e70526c8f1b17fc0852`](https://huggingface.co/spaces/bachbeo2007/bureau/commit/113d71c9c93f6a27355f8e70526c8f1b17fc0852).
  The Space remains public and uses the Static SDK.
- `demo/publish.py` rebuilt, checked and uploaded all 15 allowlisted files.
  The generated content already matched the committed build; no generated
  content changes were needed.
- All 14 app assets matched the upload's SHA-256 hashes after removing the
  platform-injected public-variable script from `index.html`. The raw Space
  README also matched; the app host renders Markdown as HTML.
- Every sample email domain in the served fixtures ends in `.example`.
  Scanning all uploaded text assets found only reserved example domains,
  including the `example.org` input placeholder. The public-asset credential
  scan passed.
- **227 Python tests and 10 local static browser tests passed.**
- **All 10 static browser tests passed against the public URL**, including
  the full tour, independent tabs/private contexts, approvals, Reset and fonts.
- Additional fresh private-context checks completed **all 30 steps from each
  entry point**: **Start the guided demo** and **Demo tour**. Neither run
  produced console errors, JavaScript exceptions, external requests or API calls.
- The public Hugging Face landing page successfully loaded the embedded demo.
- Ten fresh-context page-ready measurements ranged from **1.608 to 3.253 seconds**;
  the first was **2.590 seconds**. These are static-page loads, not Render
  wake-up measurements.

Public screenshots: [tour step 30](../docs/screenshots/t45-public-static-tour.png),
[browser one](../docs/screenshots/t45-public-static-session-one.png),
[browser two](../docs/screenshots/t45-public-static-session-two.png),
[Space landing page](../docs/screenshots/t45-public-static-landing.png).

The upload manifest, deployment revision, detailed acceptance report and load
measurements are retained locally in ignored `demo/artifacts/` as
`deployment.json`, `t45-public-verification.json` and `static-load-times.json`.
This refresh makes no model calls and changes no Render configuration.

## Historical verification — 26 September 2026

The following report records the earlier deployment and its then-outstanding
Render checks. It does not describe the current status of the live service.

This branch incorporates `main` at `b150cf1` (T16's 100-student WEI with meals
included, and T36's product page). The complete budget is €150 per person;
the clarification asks whether coach hire is included. Recorded packages retain
itemized coach, lodging, groceries and food-transport costs.

### Local checks

Python 3.14 and installed Chrome on Windows:

- **205 Python tests passed**, including fake-client API isolation and budgets.
- **12 browser tests passed**: 10 static tests, plus the full 30-step HTTP tour
  with a fake live provider and at a zero-call limit. No tour steps skipped.
- The production entry point also started with the requested native command,
  `uvicorn api.main:app --host 0.0.0.0 --port 10000`, in demo mode with an empty
  key. Health, replay and independent browsers passed a smoke check.
- Isolation covers approvals, outbox, Reset, overlapping requests and file paths.
- Cost tests cover global/session limits, concurrent reservations, failed
  attempts, UTC-day rollover, Reset, mid-agent and mid-planner caps, provider 429,
  saved fallback and unsupported inputs. No real model calls were made.
- Static tests cover refresh/expiry, corrupt/full/unavailable browser storage,
  invalid/duplicate approval, custom constraints, text escaping and mobile layout.
- Geist loaded in both modes. Static fonts are embedded in CSS to avoid Spaces'
  binary-font CDN redirects; the policy still disallows outgoing API connections.
- The 90% evaluation metric is retained. A scan of tracked/new source and the
  15 public assets found no credential-shaped values. The task's broad literal
  grep still matches existing documentation, dummy test keys and scanning code;
  these are not credentials. The scan findings are documented rather than hidden.

Local server evidence (fake providers, **not public Render acceptance**):
[browser one](../docs/screenshots/t20-local-server-session-one.png),
[browser two](../docs/screenshots/t20-local-server-session-two.png),
[zero-limit replay](../docs/screenshots/t20-local-server-replay.png).

### Public static backup — passed

- [Public Space](https://huggingface.co/spaces/bachbeo2007/bureau)
- [Direct demo](https://bachbeo2007-bureau.static.hf.space)
- Published revision: `d6df07df90d762be946d7093eb0119dbe8a3e160`.
- **All 10 browser tests passed against the public URL**, including the complete
  30-step tour, separate private-browser contexts, approvals, Reset and font load.
- All observed requests stayed on the static site; no API/model calls.
- Ten fresh-context page-ready measurements: 1.406–2.234 seconds; the first was
  2.114 seconds. These measure the static page, **not a Render cold start**.

Public evidence: [browser one](../docs/screenshots/t20-public-static-session-one.png),
[browser two](../docs/screenshots/t20-public-static-session-two.png),
[tour step 24](../docs/screenshots/t20-public-static-tour.png).
The raw local run report is in ignored `demo/artifacts/static-load-times.json`.
Rebuild from reviewed `main` after merge and after future fixture/UI changes.

### Outstanding release checks at that time

- Create the one free Render service and record its assigned URL in the README.
- Set the project-scoped OpenAI key and confirm the team's monthly **hard** limit.
- On Render, complete the live tour, simultaneous-browser isolation and zero-limit
  fallback; capture public screenshots.
- With keep-alive off and no other traffic, idle for at least 20 minutes and
  measure the wake-up time. This has not been measured locally or inferred.
- Configure the keep-alive URL, enable flag and actual results timestamp in
  GitHub variables. Keep-alive is inactive until configured.
- Link green GitHub CI results in the draft PR before merge.

The single-service design stores daily accounting on Render's ephemeral disk.
Disk erasure resets those counters. It therefore does **not** guarantee a daily
total across restarts. OpenAI's project hard spend cap is the independent credit
backstop and has not been configured by this local implementation. See the
dated free-tier and spending-limit sources in [DEPLOY.md](../docs/DEPLOY.md).
