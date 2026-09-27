# Contributing

Thank you for helping improve Bureau Agent. This repository is public and is read by judges, so keep every tracked file current, useful, and written in English.

## Setup

Choose one supported install path:

```bash
uv sync
uv run python -m unittest discover -s tests -t .
```

or:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -t .
```

Copy `.env.example` to `.env` for optional live OpenAI or Jinko calls. Never commit `.env`, API keys, or real personal data. Enable the local hook after creating the environment:

```bash
git config core.hooksPath .githooks
```

On Windows, set `PYTHONIOENCODING=utf-8` if accented output is displayed incorrectly.

## Dependencies

`pyproject.toml` and `uv.lock` are the source of truth. `requirements.txt` is generated from the lock, pins exact versions, and is used by pip, Render, and CI.

To add or change a dependency, edit `pyproject.toml`, then run:

```bash
uv lock
uv export --no-hashes --no-dev --no-emit-project --format requirements-txt -o requirements.txt
```

Commit `pyproject.toml`, `uv.lock`, and `requirements.txt` together. Do not edit `requirements.txt` by hand: CI checks that it matches the lock. Both `uv sync`/`uv run` and a virtual environment with `pip install -r requirements.txt` are supported.

## Web changes and the static backup

`demo/site/` is generated from `web/` (`index.html`, `app.js`, `style.css`, `tour.js`, and `vendor/`) by `demo/build.py`. After changing anything under `web/`, run:

```bash
python demo/publish.py --check
```

This rebuilds the static backup and verifies its public assets. Commit the resulting `demo/site/` updates in the same pull request. The `browser` CI job rebuilds the backup and runs `git diff --exit-code -- demo/site`; stale generated files fail CI.

`demo/build.py` patches selected console strings for the public experience. If it stops with `Console changed; review the static adaptation`, update the corresponding `replace(...)` call in `demo/build.py` and rerun the check.

## Claiming work

1. Choose an unassigned GitHub issue and check its dependencies.
2. Assign yourself and comment `Taking this` with an ETA.
3. Work on one active issue at a time. You may claim the next issue after opening the previous pull request.
4. If you cannot push progress for three hours, unassign yourself and explain the blocker on the issue.

## Workflow

1. Update `main` and create the suggested branch:
   ```bash
   git switch main
   git pull --ff-only
   git switch -c txx-short-description
   ```
2. Make focused commits with English messages beginning with the task id, for example `T42: remove obsolete public documents`.
3. Run the relevant tests, then the full suite before opening a pull request.
4. Push the branch and open a pull request into `main`. Use the template, include `Closes #<issue>`, and check each completion criterion from the GitHub issue.
5. CI must pass. A project maintainer or another contributor reviews the pull request; merge with **Squash and merge**. Do not push directly to `main`.

GitHub issues, rather than a committed task tracker, are the source of truth for scope and progress.

## Engineering rules

- The agent proposes actions only. `bureau/core/executor.py` is the only layer that applies state changes after organizer approval.
- Put exact business rules in code and tests, not in prompts.
- Money is integer cents and datetimes must be timezone-aware.
- Changes to `bureau/core/models.py` or `bureau/planner/interface.py` are shared-contract changes: tell the team and regenerate API examples with `python docs/api-examples/generate.py`.
- Add or update tests with behavior changes. Tests must not call live services; use fixtures, replay mode, or `tests/fake_llm.py`.
- Update the README of any folder whose public purpose or workflow changes.
- Keep comments, commits, documentation, issue titles, and user-facing text in English. French sample messages remain intentional test data.
