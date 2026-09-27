# Workflows

- `tests.yml` runs the existing Python unit suite on pushes and pull requests.
- `demo.yml` rebuilds and validates the static upload package, checks that committed generated assets
  match, and runs the complete 30-step tour and browser isolation tests in Chromium.
  Screenshots are uploaded as an artifact. No deployment credentials or model
  keys are needed, and this workflow does not publish to Hugging Face.

It also runs the live HTTP console's full tour with fake model responses and
with a zero-call cap (replay), including separate-browser isolation and local
Geist font loading. Python requirements and Playwright are installed in CI.

`keepalive.yml` pings one free Render service every 10 minutes during the judging
window only. It requires the `RENDER_DEMO_URL`, `DEMO_KEEPALIVE_ENABLED` and
`DEMO_KEEPALIVE_UNTIL` repository variables; no credentials are needed. It starts
no earlier than 27 September 2026 in Europe/Paris and stops at the configured
results timestamp. Disable it afterwards. Setup and free-tier limits are in
[`docs/DEPLOY.md`](../../docs/DEPLOY.md).

The public demo is kept awake by an external monitor (UptimeRobot) that requests `/health`
every five minutes; GitHub schedules proved unreliable, so `keepalive.yml` is only a backup.
