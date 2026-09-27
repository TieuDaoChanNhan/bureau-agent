# Static customer demo

Target Space: https://huggingface.co/spaces/bachbeo2007/bureau

This is a browser-only adaptation of the existing operations console and its
30-step Demo tour. It shows two fictional events, evidence, editable replies,
approval/dismissal, a simulated outbox, local activity, clarification, and trip
budget comparisons. It makes **no model calls** and needs **no secrets**.

Each tab owns its own state and random session id. Browser `sessionStorage`
preserves proposals, saved reply edits, decisions, outbox, activity and planning
constraints across refreshes. Sessions expire after 24 hours without interaction;
expired, corrupt or incompatible snapshots start fresh. Reset affects only the
selected event. Visitors and separate tabs cannot change each other's data.
Duplicating a tab can copy its initial snapshot, but subsequent changes remain
independent. Closing a tab may discard its session depending on browser restore
behavior. If storage is unavailable/full, the demo continues in memory and the
banner explains that refresh will lose progress. No cookies are required.

## Build and preview

From the repository root, using Python 3.11 or newer:

```sh
python demo/build.py
python -m http.server 8080 --directory demo/site --bind 127.0.0.1
```

Open http://127.0.0.1:8080 and click **Start the guided demo**. End users need
only a browser; Python is a maintainer build/preview tool. The output uses local
assets, no CDN, no build-time packages, and a CSP that disallows connections.

## Files and maintenance

| File | Purpose |
|---|---|
| `build.py` | Copies the live console, adjusts public-demo wording and builds sample snapshots from the Python loader/detector. Never calls a model. |
| `offline.js` | Isolated in-memory adapter for the console's API-shaped requests; sample approvals, outbox, activity, reset and constraint checks. |
| `session.js` | Tab-scoped persistence, random ids, 24-hour expiry and storage fallback. |
| `scenarios.json` | 13 curated sample-inbox replies with references to the repository's rules. |
| `customer-ui.js` | Session notice and editable budget/group-size/arrival controls. |
| `publish.py` | Offline release checks, an upload ZIP, and authenticated upload of an explicit asset list to an existing public Static Space. |
| `tour-steps.js` | All 30 customer tour steps; explains exactly what is simulated. |
| `test_browser.py` | Browser tests for the complete tour, isolation, invalid approvals, reset, escaped text, and network isolation. |
| `VERIFICATION.md` | Local results and remaining public-deployment checks. |
| `site/` | Generated, committed, self-contained files to upload. Includes the vendored Driver.js license. Do not edit generated files directly. |

Rebuild after changing any source or the upstream `web/` console. The generator
fails when a required replacement no longer matches, so upstream changes need
review rather than silently breaking the demo. Keep `TASKS.md` unchanged.

## What is simulated

Initial issues come from the real deterministic detector and fictional input
in `data/`. Antoine's payment proposal and the five illustrative travel packages
come from shared `demo/replay.py` fixtures and the deterministic planner on `data/wei/travel_options.json`. Those examples are curated fixtures, not newly
recorded live model outputs. The three new-message examples and 13 sample inbox
messages use curated proposals; unsupported messages explicitly fall back to
organizer review. The planner uses one fixed clarification answer, then checks
budgets from €1 to €1,000, groups from 1 to 200, and a chosen arrival deadline.
These are deterministic checks on saved packages. Sample per-person prices stay
fixed when group size changes; changing the group size checks capacity only.
No live Jinko offers, free-form language understanding or production Python
executor runs in the static backup. Approval changes only sample browser state.

## Browser verification

```sh
python -m pip install playwright
python -m playwright install chromium
python demo/test_browser.py
```

Alternatively set `DEMO_CHROME_PATH` to an installed Chrome executable to avoid
downloading Chromium. The tests start a temporary local HTTP server themselves,
use no API keys, and write screenshots to ignored `demo/artifacts/`.
The existing Python suite still runs with `python -m unittest discover -s tests -t .`.
Set `DEMO_BASE_URL` to the direct `https://<space-host>.hf.space` app URL to run
the same tests against the deployed demo. The Space landing page is an iframe
wrapper, so it is checked separately in a public browser session.

## Publish

Follow [the deployment instructions](../docs/DEPLOY.md). Upload **only the contents
of `site/`** to the Space root; its README already declares `sdk: static` and
`app_file: index.html`. Never upload `.env`, runtime files or API credentials.
The Space remains on Static HTML with no hardware upgrade and no variables/secrets.

For a checked ZIP without any network or authentication:

```sh
python demo/publish.py --check
```

For automatic upload after a private `hf auth login`:

```sh
python demo/publish.py
```

The uploader first checks the assets, refuses a non-public or non-static target,
and uploads only the 12 known public files. Deployment credentials stay on the
maintainer's computer. A file manifest and uploaded commit id are recorded under
ignored `demo/artifacts/`. The archive is an alternative for manual deployment:
extract it and upload its contents, not the ZIP file itself.

## Live primary and shared replay

The primary target is now the free Render service; this directory supplies the
static backup and saved examples. See [deployment](../docs/DEPLOY.md).
`replay.py` shares payment and rules fixtures with `build.py` and provides the
server's recorded planning fallback. Unknown server requests return 429.
`testing_app.py` is a fake-client test factory, never the production entry point.
`test_live_browser.py` exercises the real HTTP console, all 30 steps, replay at a
zero-call cap and separate browsers. Run it with `python demo/test_live_browser.py`
after installing requirements and Playwright. No real model calls are made.

Geist fonts and SIL licenses come from `web/vendor/`; the static build embeds
the fonts in CSS to avoid Hugging Face binary-asset CDN redirects. Both builds keep the
90% evaluation result. Browser tests verify that Geist actually loads. Rebuild
and publish from reviewed `main` after any fixture, planner or console change.
