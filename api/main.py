"""HTTP API for the web UI (TASK T05). Run: uvicorn api.main:app --reload

JSON shapes are the dataclasses of bureau/core/models.py serialized with
dataclasses.asdict. The web UI depends only on these shapes.

Two read-only routes are implemented as examples; the others return 501 until done.
"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bureau.config import DATA_DIR, ROOT
from bureau.core.detect import detect_issues
from bureau.core.loader import load_event

app = FastAPI(title="Bureau Agent API")


def _events() -> list[str]:
    return sorted(p.name for p in DATA_DIR.iterdir() if (p / "event.json").exists())


def _counts(issues) -> dict:
    open_ = [i for i in issues if i.status not in ("resolved", "dismissed")]
    return {
        "blocking": sum(i.blocking for i in open_),
        "non_blocking": sum(not i.blocking for i in open_),
        "resolved": sum(i.status == "resolved" for i in issues),
    }


@app.get("/api/events")
def list_events():
    """Events with issue counts. Example route (uses sample data, no runtime state yet)."""
    out = []
    for event_id in _events():
        state = load_event(event_id)
        out.append({"id": event_id, "name": state.name, "counts": _counts(detect_issues(state))})
    return out


@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    """Event summary and issues. TODO(T05): read from core.store instead of sample data."""
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    state = load_event(event_id)
    issues = detect_issues(state)
    return {"id": event_id, "name": state.name, "counts": _counts(issues),
            "issues": [asdict(i) for i in issues], "actions": [asdict(a) for a in state.actions]}


def _todo(task: str):
    raise HTTPException(501, f"Not implemented yet: see TASKS.md {task}")


@app.post("/api/events/{event_id}/run")
def run_agent(event_id: str):
    """Re-detect issues and run the agent on open issues without a proposal."""
    _todo("T05")


@app.post("/api/events/{event_id}/plan")
def run_planner(event_id: str, body: dict | None = None):
    """Run the travel planner. Body: {"text"?: str, "overrides"?: {"max_cost_per_person_cents": int}}."""
    _todo("T05")


@app.get("/api/actions/{action_id}")
def get_action(action_id: str):
    _todo("T05")


@app.post("/api/actions/{action_id}/approve")
def approve(action_id: str, body: dict | None = None):
    """Body: {"edited_description"?: str, "option_id"?: str}. Calls core.executor.apply."""
    _todo("T05")


@app.post("/api/actions/{action_id}/dismiss")
def dismiss(action_id: str):
    _todo("T05")


@app.get("/api/events/{event_id}/outbox")
def outbox(event_id: str):
    _todo("T05")


@app.post("/api/events/{event_id}/reset")
def reset(event_id: str):
    _todo("T05")


# The web UI is served from /web; "/" redirects to it.
app.mount("/web", StaticFiles(directory=ROOT / "web", html=True), name="web")


@app.get("/")
def index():
    return FileResponse(ROOT / "web" / "index.html")
