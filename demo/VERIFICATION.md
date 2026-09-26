# Static demo verification

Checked locally on 2026-09-26 with Python 3.14 and installed Chrome on Windows.

- Existing Python suite: **171 tests passed**, no real model calls.
- Static browser suite: **10 tests passed**, including all 30 tour steps with
  actual button clicks and an edited reply, without skipping steps.
- Two simultaneous tabs and separate private-browser contexts: approving and
  resetting in one leaves the other unchanged; random session ids are separate.
- Invalid travel approval and duplicate approval: rejected without extra side effects.
- Refresh: preserves proposals, saved reply edits, approved replies, planning
  constraints and session id. Reset: restores only the selected event.
- Sessions: expire after 24 hours of inactivity, including in an open page.
  Corrupt snapshots start fresh; unavailable/full storage falls back to memory.
- Planner: custom budgets and group sizes change valid options, rejected packages
  cannot be selected, and budget shortcuts preserve other custom constraints.
- Saved inbox: curated rules replies cite actual sample rule sections; custom
  unsupported text still goes to human review with no model call.
- Custom HTML-like messages: displayed as text; no script execution.
- Mobile: no horizontal overflow at 400 px; tour closes with Escape.
- Network: all loaded resources local to the site; no `/api/` HTTP requests or
  external requests observed during the browser tests.
- Build: repeated generation produced identical file hashes.
- Publish directory: 12 text assets, including the vendored tour library and its
  license. Credential-pattern scan found no secret-looking values.
- `git diff --check`: passed.

Screenshots are generated in ignored `demo/artifacts/`: `edited-reply.png`,
`trip-options.png`, `session-one.png`, `session-two.png`, and `mobile.png`.
The browser CI workflow uploads these as an artifact. GitHub CI itself has not
been run remotely from this workspace.

## Public deployment

The Hugging Face API confirmed `bachbeo2007/bureau` is public, uses SDK `static`,
and reports `RUNNING` with no compute hardware. This only verifies the Space's
configuration, not deployment of this new demo.

Upload and public tour verification remain pending local Hugging Face login.
`python demo/publish.py --check` builds and checks the explicit public asset list
and produces an upload ZIP plus manifest. `python demo/publish.py` uploads only
after local authentication and checking the target is public and static.
After upload, record the deployed revision, measured initial load time and
public tour/isolation results here. Do not claim local screenshots demonstrate
the public deployment. There is no sleeping Python server in a Static Space.
