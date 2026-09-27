# Deploy the public demo

Primary: native Python on **one free Render web service**. Backup:
[Hugging Face Static Space](https://huggingface.co/spaces/bachbeo2007/bureau).
The live demo is https://bureau-agent.onrender.com. The static revision has passed its public tour and isolation checks; see demo/VERIFICATION.md.

## Free-tier terms checked 26 September 2026

Render advertises [free deployment without a credit card](https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026).
Its [free plan](https://render.com/docs/free) sleeps after 15 minutes idle and
takes about a minute to wake (not a latency guarantee). It includes 750 running
instance hours per workspace/calendar month: one service uses 720 hours in a
30-day month or 744 in a 31-day month. The [free instance](https://render.com/docs/blueprint-spec)
has 512 MB RAM. **Disk contents disappear on restart, redeploy or spin-down**;
Render can restart free instances at any time. There is no persistent disk.

Build minutes and outbound bandwidth have separate allowances. Without a payment
method, exhausting them disables builds or suspends services instead of billing
overages. Keep one service, no paid resources or payment method. Render may also
suspend unusually high outbound traffic.

## Test a branch before merging

Push the branch to GitHub and open a PR, leaving `main` unchanged. For a
pre-merge Render test, choose **New → Web Service**, connect the GitHub repository
through **Git Provider**, and select that branch. If a service already
exists, change its linked branch instead of creating another service.

Keep the root directory empty, choose Python and **Free**, use
`pip install -r requirements.txt` for the build and
`uvicorn api.main:app --host 0.0.0.0 --port $PORT` for startup. Set `/health` as
the health check. Copy the environment settings from `render.yaml`, but start
with `DEMO_DAILY_LLM_LIMIT=0` and no OpenAI key to test replay without spending.
The Blueprint currently pins `main`, so use this manual service setup for branch
testing. See [Render web services](https://render.com/docs/web-services).

Complete the tour and isolation checks on its public URL. Then configure the
project hard spend limit, add the key privately, set the intended call limits,
redeploy and repeat with the live agent. Record the public acceptance evidence
before merging. After review and green CI, merge the PR, change this same
service's branch to `main` and enable automatic deploys. Keep only one service.

Local replay testing does not require any push. In PowerShell, set
`$env:DEMO_MODE='1'`, `$env:DEMO_DAILY_LLM_LIMIT='0'` and
`$env:JINKO_MODE='replay'`, then run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 10000
```

Open http://127.0.0.1:10000 and run the tour. The zero limit prevents model calls
even if a local `.env` has a key. Before running the ordinary Python suite in
that shell, set `$env:DEMO_MODE='0'`; the public-demo tests enable it themselves.

## Create from main and redeploy

1. Merge the reviewed change into `main` in `TieuDaoChanNhan/bureau-agent`.
2. In Render, choose **New → Blueprint**, connect that GitHub repository, select
   `main` and `render.yaml`. Confirm the sole service has **Free** instance type.
   Do not create a database, worker, disk or paid workspace.
3. Set `OPENAI_API_KEY` only in Render's secret environment settings. The Blueprint
   declares `sync: false`; no value is stored in Git. It sets Python `3.11.9`,
   `OPENAI_MODEL=gpt-4.1`, `JINKO_MODE=replay`, and `DEMO_MODE=1`.
   An empty key uses saved examples. No Jinko key is needed.
4. Set the dedicated OpenAI project's monthly hard limit **before enabling live
   calls**: Project settings → Limits → Spend → Edit spend limit → choose the
   team's amount → **Enforce a hard limit** → Save. Use a key belonging to that
   project. This is a project/organization control, not a per-key setting;
   alerts alone do not block calls. Enforcement can slightly overshoot while
   usage propagates. See [OpenAI spend limits](https://developers.openai.com/api/docs/guides/spend-limits).
5. Deploy, copy the assigned `https://…onrender.com` URL, verify `/health`, then
   run the public checks below and update the root README with the actual link.

Render builds with `pip install -r requirements.txt` and starts
`uvicorn api.main:app --host 0.0.0.0 --port $PORT`. Each subsequent push to `main`
deploys automatically. `autoDeployTrigger: commit` is the current Blueprint
spelling of the task's `autoDeploy: true`. Keep the default single Uvicorn worker.
Redeploying also resets each browser's sample data.

Local equivalent, after installing requirements:

```sh
DEMO_MODE=1 OPENAI_API_KEY='' uvicorn api.main:app --host 0.0.0.0 --port 10000
```

PowerShell: set `$env:DEMO_MODE='1'` and `$env:OPENAI_API_KEY=''`, then run the same
`uvicorn` command without the environment prefixes. Open http://127.0.0.1:10000.
An empty key checks replay without spending credit; set a key privately to check live.

## Limits, isolation and fallback

| Render environment variable | Default | Effect |
|---|---|---|
| `DEMO_DAILY_LLM_LIMIT` | `400` | Total model attempts per UTC day on the current disk |
| `DEMO_SESSION_LLM_LIMIT` | `60` | Attempts during one browser's 24-hour session |
| `DEMO_MAX_OUTPUT_TOKENS` | `2048` | Maximum output tokens per attempt |

Change these in Render Environment and redeploy; keep Blueprint values in sync.
Set either call limit to `0` to test fallback. Failed attempts count too, and SDK
retries are disabled. Every agent turn, extraction and explanation reserves a
call atomically in `runtime/llm_usage.sqlite3`; Render logs emit `demo_llm` records
with session, UTC day, purpose and model. Reset does not clear quota usage.

**The local daily/session counters reset if Render erases the disk.** They are
not a durable cross-restart spending guarantee. The independent OpenAI project
hard limit is required to protect credit across resets. A strict daily cap across
redeploys requires durable shared accounting, outside this single ephemeral
service design.

Each browser has an opaque HttpOnly/SameSite cookie and files under
`runtime/<session>/<event>/`. HTTPS cookies are Secure. The API serializes requests
within each session; other browsers have independent state. Sessions expire 24
hours after creation; hourly request-triggered cleanup removes expired inactive
directories. Closing a browser, clearing cookies or a service reset can start a
fresh sandbox. This is anonymous isolation, not authentication.

When no key is configured or a limit blocks a call, known sample issues use the
shared `demo/replay.py` examples and recorded planner packages. Responses and
stored proposals carry `replay: true`; the console labels the source. Unknown
messages and custom planning text return 429 with an explanation and can be
skipped in the tour. Replay accepts the exact provided coach-budget answer and
explicit constraint overrides; it never pretends to interpret arbitrary text.
All approvals affect sample records and a simulated outbox; no real sends/bookings.

## Judging keep-alive

**In use:** an external monitor (UptimeRobot, free plan) requests `/health` every five minutes,
which keeps the free service awake without any model call. GitHub scheduled workflows proved
unreliable for this: on 27 September the ten-minute schedule below ran once in six hours.
The workflow stays as a backup.

The workflow `.github/workflows/keepalive.yml` requests `/api/events` every ten
minutes without a model call. It is inactive until GitHub **Settings → Secrets
and variables → Actions → Variables** contains:

- `RENDER_DEMO_URL`: the verified service URL.
- `DEMO_KEEPALIVE_ENABLED`: `true`.
- `DEMO_KEEPALIVE_UNTIL`: the results timestamp, including timezone, for example
  `2026-09-28T18:00:00+02:00` (example only; use the actual results time).

The workflow gates requests from Sunday 27 September, midnight Europe/Paris,
until that timestamp. After results, set the enable variable to `false` or disable
the workflow in Actions. Its date gate stops requests even if that is forgotten.
Scheduled jobs run from the default branch and can be delayed; they do not
guarantee an always-warm service. Do not add another free service to the workspace.

## Rebuild the static backup

The reviewed source is in `demo/`; generated `demo/site/` is committed. After
fixture, planner, rules or console changes on `main`:

```sh
python demo/publish.py --check
python -m unittest discover -s tests -t .
python demo/test_browser.py
python demo/test_live_browser.py
```

Browser checks need `pip install playwright` and `python -m playwright install
chromium`, or `DEMO_CHROME_PATH` pointing to installed Chrome. They use fake
clients and no real model calls. Commit regenerated `demo/site/` with the source.

Publish with `python demo/publish.py` after installing `huggingface_hub` and
running `hf auth login` privately with a token scoped to this Space. Alternatively
upload the **contents** of `demo/site/` using the Space's Files tab, preserving
`vendor/`. The generated README already has Static SDK front matter.
The ZIP is `demo/artifacts/bureau-static.zip`. Do not upload the whole repository.
Leave Space Variables and Secrets empty. Static assets include Geist fonts,
licenses, the real 90% evaluation metric and a CSP blocking API connections.

## Public acceptance checks

Run all 30 tour steps on the Render URL with a live key in a private window.
Keep another browser open and verify its proposals, approvals, outbox and Reset
are independent. Capture both screens. Set the daily limit to zero temporarily,
repeat the tour and capture the saved-example label; restore the intended cap.
Disable keep-alive, close all demo windows, wait at least 20 minutes, then record
the next request's elapsed wake time. Re-enable keep-alive only for judging.
Repeat the static tour on the published Space and record its deployed revision.

Record screenshots, URLs, commits, actual timings, the hard-limit confirmation
and green CI links with the change. Local fake-client screenshots
are explicitly local evidence; they cannot establish public live acceptance.
See `demo/VERIFICATION.md` for completed local checks and outstanding items.
