"""HTTP API for the web UI (TASK T05). Run: uvicorn api.main:app --reload

JSON shapes are the dataclasses of bureau/core/models.py serialized with
dataclasses.asdict. The web UI depends only on these shapes.
"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, StrictStr

from bureau import config
from bureau.agent.loop import run_pending, runnable_issues
from bureau.core import store
from bureau.core.detect import detect_issues
from bureau.core.executor import InvariantViolation, apply
from bureau.core.models import EventState, Issue, ProposedAction
from bureau.config import DATA_DIR, ROOT

app = FastAPI(title="Bureau Agent API")


class ApprovalRequest(BaseModel):
    edited_description: StrictStr | None = None
    option_id: StrictStr | None = None


def _events() -> list[str]:
    return sorted(p.name for p in DATA_DIR.iterdir() if (p / "event.json").exists())


def _counts(issues) -> dict:
    open_ = [i for i in issues if i.status not in ("resolved", "dismissed")]
    return {
        "blocking": sum(i.blocking for i in open_),
        "non_blocking": sum(not i.blocking for i in open_),
        "resolved": sum(i.status == "resolved" for i in issues),
    }


def _load_and_refresh(event_id: str) -> EventState:
    """Re-detect issues while retaining terminal decisions to prevent re-approval."""
    state = store.load_state(event_id)
    refreshed = store.merge_issue_status(detect_issues(state), state.issues)
    current_ids = {i.id for i in refreshed}
    # A repaired issue disappears from detection, but its decision must survive
    # later writes (run/dismiss/approve) so an old action cannot be executed again.
    state.issues = refreshed + [i for i in state.issues
                                if i.id not in current_ids and i.status in ("resolved", "dismissed")]
    return state


def _event_summary(state: EventState) -> dict:
    issues = store.merge_issue_status(detect_issues(state), state.issues)
    return {"id": state.id, "name": state.name, "counts": _counts(issues),
            "issues": [asdict(i) for i in issues], "actions": [asdict(a) for a in state.actions]}


def _event_id_of_action(action_id: str) -> str:
    """Action ids are "<event_id>:<issue_id>" (see agent/loop.py)."""
    event_id = action_id.split(":", 1)[0]
    if event_id not in _events():
        raise HTTPException(404, "unknown action")
    return event_id


def _find_action(state: EventState, action_id: str) -> ProposedAction:
    action = next((a for a in state.actions if a.id == action_id), None)
    if action is None:
        raise HTTPException(404, "unknown action")
    return action


def _pending_issue(state: EventState, action: ProposedAction) -> Issue:
    issue = state.issue(action.issue_id)
    if issue is None:
        raise HTTPException(409, "action no longer has a current issue")
    if issue.status in ("resolved", "dismissed"):
        raise HTTPException(409, f"issue {issue.id} is already {issue.status}")
    return issue


@app.get("/api/events")
def list_events():
    """Events with issue counts, from runtime state (falls back to sample data)."""
    out = []
    for event_id in _events():
        state = _load_and_refresh(event_id)
        out.append({"id": event_id, "name": state.name, "counts": _event_summary(state)["counts"]})
    return out


@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    """Event summary and issues, from runtime state (falls back to sample data)."""
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    return _event_summary(_load_and_refresh(event_id))


def _todo(task: str):
    raise HTTPException(501, f"Not implemented yet: see TASKS.md {task}")


@app.post("/api/events/{event_id}/run")
def run_agent(event_id: str, limit: int = Query(5, ge=1), issue_id: str | None = None):
    """Propose up to ``limit`` runnable issues and report the remaining backlog.

    ``issue_id`` runs one issue, including one whose previous agent run failed.
    """
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    state = _load_and_refresh(event_id)
    if runnable_issues(state, issue_id) and not config.OPENAI_API_KEY:
        raise HTTPException(503, "OPENAI_API_KEY is not set")
    result = run_pending(state, issue_id=issue_id, limit=limit, verbose=False)
    summary = _event_summary(state)
    summary["remaining"] = result.remaining
    summary["errors"] = result.errors
    return summary


@app.post("/api/events/{event_id}/plan")
def run_planner(event_id: str, body: dict | None = None):
    """Run the travel planner. Body: {"text"?: str, "overrides"?: {"max_cost_per_person_cents": int}}."""
    _todo("T14")


@app.get("/api/actions/{action_id}")
def get_action(action_id: str):
    event_id = _event_id_of_action(action_id)
    state = store.load_state(event_id)
    return asdict(_find_action(state, action_id))


@app.post("/api/actions/{action_id}/approve")
def approve(action_id: str, body: ApprovalRequest | None = None):
    """Body: {"edited_description"?: str, "option_id"?: str}. Calls core.executor.apply."""
    body = body or ApprovalRequest()
    event_id = _event_id_of_action(action_id)
    state = _load_and_refresh(event_id)
    action = _find_action(state, action_id)
    _pending_issue(state, action)
    try:
        new_state = apply(state, action, edited_description=body.edited_description,
                          option_id=body.option_id)
    except InvariantViolation as exc:
        raise HTTPException(409, str(exc)) from exc
    except (ValueError, KeyError) as exc:
        raise HTTPException(422, str(exc)) from exc
    store.save_state(new_state)
    return _event_summary(new_state)


@app.post("/api/actions/{action_id}/dismiss")
def dismiss(action_id: str):
    event_id = _event_id_of_action(action_id)
    state = _load_and_refresh(event_id)
    action = _find_action(state, action_id)
    issue = _pending_issue(state, action)
    issue.status = "dismissed"
    issue.resolved_by_action_id = action.id
    store.save_state(state)
    return _event_summary(state)


@app.get("/api/events/{event_id}/outbox")
def outbox(event_id: str):
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    return store.load_outbox(event_id)


@app.post("/api/events/{event_id}/reset")
def reset(event_id: str):
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    store.reset(event_id)
    return _event_summary(_load_and_refresh(event_id))


# The web UI is served from /web; "/" redirects to it.
app.mount("/web", StaticFiles(directory=ROOT / "web", html=True), name="web")


@app.get("/")
def index():
    return FileResponse(ROOT / "web" / "index.html")
