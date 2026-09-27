"""HTTP API for the web UI (TASK T05). Run: uvicorn api.main:app --reload

JSON shapes are the dataclasses of bureau/core/models.py serialized with
dataclasses.asdict. The web UI depends only on these shapes.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import logging
import re
import threading
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StrictStr

from bureau import config
from bureau.agent.loop import run_pending, runnable_issues
from bureau.core import bulk_approval, store
from bureau.core.detect import detect_issues
from bureau.core.executor import InvariantViolation, apply
from bureau.core.models import EventState, Issue, Message, ProposedAction
from bureau.core.llm_usage import LiveUnavailable, ensure_available
from bureau.config import DATA_DIR, ROOT
from bureau.planner.planner import (HARD_KEYS, extract_constraints, plan_trip, recorded_constraints,
                                    request_from_state)
from demo.replay import NoSavedExample, issue_example, mark_replay, planner_example
from .sessions import DemoSessions

app = FastAPI(title="Bureau Agent API")
app.add_middleware(DemoSessions)
logger = logging.getLogger(__name__)
# The JSON store supports one worker. Serialize overlapping bulk submissions also
# outside public demo mode; DemoSessions already serializes each public visitor.
_bulk_lock = threading.Lock()


@app.get("/health")
def health():
    return {"status": "ok"}


class NewMessage(BaseModel):
    """A message typed or pasted by an organizer (T32). It is data for the agent, never instructions."""
    sender: str = Field(min_length=1, max_length=200)
    channel: Literal["email", "discord", "form"] = "email"
    text: str = Field(min_length=1, max_length=4000)


class PlanRequest(BaseModel):
    text: StrictStr | None = Field(default=None, max_length=8000)
    overrides: dict[str, int | bool | str] | None = None
    recorded: bool = False                 # use the constraints recorded with the event (offline demo)


class ApprovalRequest(BaseModel):
    edited_description: StrictStr | None = Field(default=None, max_length=8000)
    option_id: StrictStr | None = None


class BulkReply(BaseModel):
    id: StrictStr = Field(min_length=1, max_length=250)
    revision: StrictStr = Field(pattern=r"^[a-f0-9]{64}$")


class BulkApprovalRequest(BaseModel):
    replies: list[BulkReply] = Field(min_length=1, max_length=bulk_approval.MAX_BATCH)


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
    _refresh(state)
    return state


def _refresh(state: EventState) -> None:
    refreshed = store.merge_issue_status(detect_issues(state), state.issues)
    current_ids = {i.id for i in refreshed}
    # A repaired issue disappears from detection, but its decision must survive
    # later writes (run/dismiss/approve) so an old action cannot be executed again.
    state.issues = refreshed + [i for i in state.issues
                                if i.id not in current_ids and i.status in ("resolved", "dismissed")]
    

def _records(state: EventState) -> dict:
    """Display names by id, so the UI can show "Antoine Nguyen (p01)" instead of "p01" (T23)."""
    return {
        "participants": {p.id: p.name for p in state.participants},
        "groups": {g.id: g.name for g in state.groups},
        "payments": {p.id: f"{p.payer_name} · {p.amount_cents / 100:.2f} {p.currency}" for p in state.payments},
    }


def _event_summary(state: EventState) -> dict:
    issues = store.merge_issue_status(detect_issues(state), state.issues)
    return {"id": state.id, "name": state.name, "counts": _counts(issues),
            "issues": [asdict(i) for i in issues], "actions": [asdict(a) for a in state.actions],
            "travel": state.travel, "logistics": state.logistics, "records": _records(state),
            "meta": {**state.settings.get("display", {}), "participants": len(state.participants)},
            "safe_replies": bulk_approval.preview(state)}


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


@app.post("/api/events/{event_id}/run")
def run_agent(event_id: str, limit: int = Query(5, ge=1, le=100), issue_id: str | None = None):
    """Propose up to ``limit`` runnable issues and report the remaining backlog.

    ``issue_id`` runs one issue, including one whose previous agent run failed.
    """
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    state = _load_and_refresh(event_id)
    if config.DEMO_MODE:
        if limit > 50:
            raise HTTPException(422, "Public demo batches are limited to 50 issues.")
        return _demo_run(state, limit, issue_id)
    if runnable_issues(state, issue_id) and not config.OPENAI_API_KEY:
        raise HTTPException(503, "OPENAI_API_KEY is not set")
    result = run_pending(state, issue_id=issue_id, limit=limit, verbose=False)
    summary = _event_summary(state)
    summary["remaining"] = result.remaining
    summary["errors"] = _public_errors(result.errors)
    return summary


def _public_errors(errors):
    """Issue ids of failed runs; the exception text stays in the event log."""
    return [{"issue_id": e["issue_id"], "error": "The agent run failed. Details are in the server log."}
            for e in errors]


def _demo_run(state, limit, issue_id):
    replay = False
    reason = ""
    errors = []
    skipped = []
    for issue in runnable_issues(state, issue_id)[:limit]:
        try:
            ensure_available()
            result = run_pending(state, issue_id=issue.id, limit=1, verbose=False)
            errors.extend(_public_errors(result.errors))
        except LiveUnavailable as exc:
            reason = str(exc)
            try:
                action = mark_replay(issue_example(state, issue), reason)
            except NoSavedExample as missing:
                if issue_id is None:  # a batch replays what it can and leaves the rest pending
                    skipped.append(missing)
                    continue
                raise HTTPException(429, f"Live agent unavailable ({reason}). {missing}") from missing
            state.actions = [a for a in state.actions if a.issue_id != issue.id] + [action]
            # run_pending refreshes issue objects before a mid-loop cap occurs.
            state.issue(issue.id).status = "needs_human" if action.action_type == "ESCALATE" else "proposed"
            store.save_state(state)
            store.append_log(state.id, {"type": "replay", "issue_id": issue.id, "reason": reason})
            replay = True
    if skipped and not replay:
        raise HTTPException(429, f"Live agent unavailable ({reason}). {skipped[0]}")
    return {**_event_summary(state), "remaining": len(runnable_issues(state, issue_id)),
            "errors": errors, "replay": replay, "replay_reason": reason}


def _planner_client():
    """OpenAI client for constraint extraction and explanations; None without a key.

    Tests patch this with a scripted fake client, so they never call the API.
    """
    if not config.OPENAI_API_KEY:
        return None
    from openai import OpenAI
    return OpenAI(api_key=config.OPENAI_API_KEY, timeout=45, max_retries=0 if config.DEMO_MODE else 2)


@app.post("/api/events/{event_id}/plan")
def run_planner(event_id: str, body: PlanRequest | None = None):
    """Run the travel planner and store its proposal for the `no_logistics_plan` issue.

    Body: {"text"?: str, "overrides"?: {hard constraint: value}}, e.g. a what-if budget
    {"max_cost_per_person_cents": 9000}. Replaces any earlier planner proposal; never books.
    """
    body = body or PlanRequest()
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    state = _load_and_refresh(event_id)
    issue = state.issue("no_logistics_plan")
    if not state.travel or issue is None:
        raise HTTPException(409, "this event has no open travel-planning issue")
    if issue.status in ("resolved", "dismissed"):
        raise HTTPException(409, f"issue {issue.id} is already {issue.status}")
    for key, value in (body.overrides or {}).items():
        if key not in HARD_KEYS or type(value) is not HARD_KEYS[key]:
            raise HTTPException(422, f"unsupported override: {key}={value!r}")
        if ((type(value) is int and not 0 <= value <= 1000000) or
                (key == "participants" and value < 1)):
            raise HTTPException(422, f"invalid override: {key}")
        if key == "arrive_before":
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
                raise HTTPException(422, "arrive_before must be HH:MM")
    if config.DEMO_MODE:
        return _demo_plan(state, issue, body)
    req = request_from_state(state, text=body.text)
    client = None if body.recorded else _planner_client()
    if body.recorded:
        constraints = recorded_constraints(state)
    elif client is None:
        raise HTTPException(503, 'OPENAI_API_KEY is not set (or send {"recorded": true} for the offline demo)')
    else:
        try:
            constraints = extract_constraints(req, client=client)
        except ValueError as exc:  # blank request or unusable model output
            raise HTTPException(422, str(exc)) from exc
        except Exception as exc:   # provider failure: never fall back to a sample plan
            raise HTTPException(502, "Constraint extraction failed. Retry, or send {\"recorded\": true}.") from exc
    constraints.hard.update(body.overrides or {})
    action = plan_trip(req, constraints, client=client, search=state.travel.get("search"))
    action.payload["constraints"] = asdict(constraints)
    action.payload["request_text"] = req.text
    action.payload["constraints_source"] = "recorded" if body.recorded else "llm"
    state.actions = [a for a in state.actions if a.issue_id != issue.id] + [action]
    issue.status = "proposed" if action.action_type == "SELECT_TRAVEL_PLAN" else "needs_human"
    store.save_state(state)
    summary = _event_summary(state)
    summary["action_id"] = action.id
    return summary


def _save_demo_plan(state, issue, action, reason=""):
    if reason:
        mark_replay(action, reason)
    state.actions = [a for a in state.actions if a.issue_id != issue.id] + [action]
    issue.status = "proposed" if action.action_type == "SELECT_TRAVEL_PLAN" else "needs_human"
    store.save_state(state)
    return {**_event_summary(state), "action_id": action.id, "replay": bool(reason), "replay_reason": reason}


def _demo_plan(state, issue, body):
    try:
        if body.recorded:
            raise LiveUnavailable("saved example requested")
        ensure_available()
        client = _planner_client()
        req = request_from_state(state, text=body.text)
        constraints = extract_constraints(req, client=client)
        constraints.hard.update(body.overrides or {})
        action = plan_trip(req, constraints, client=client, search=state.travel.get("search"))
        action.payload.update(constraints=asdict(constraints), request_text=req.text, constraints_source="llm")
        return _save_demo_plan(state, issue, action)
    except LiveUnavailable as exc:
        try:
            action = planner_example(state, body.text, body.overrides, recorded=body.recorded)
        except NoSavedExample as missing:
            raise HTTPException(429, f"Live planner unavailable ({exc}). {missing}") from missing
        return _save_demo_plan(state, issue, action, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "Live planning failed. Retry or skip this step.") from exc


@app.post("/api/events/{event_id}/messages", status_code=201)
def add_message(event_id: str, body: NewMessage):
    """Add an incoming message to the runtime state; detection turns it into a `message:<id>` issue.

    Returns the event summary plus the new `issue_id`. Reset removes added messages.
    """
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    if not body.text.strip() or not body.sender.strip():
        raise HTTPException(422, "sender and text must not be blank")
    state = _load_and_refresh(event_id)
    if config.DEMO_MODE and sum(m.id.startswith("live") for m in state.messages) >= 50:
        raise HTTPException(429, "This sandbox has 50 added messages. Reset the event to start again.")
    existing = {m.id for m in state.messages}
    n = 1
    while f"live{n:02d}" in existing:
        n += 1
    message = Message(id=f"live{n:02d}", channel=body.channel, sender=body.sender.strip(),
                      text=body.text.strip(), received_at=datetime.now().astimezone())
    state.messages.append(message)
    _refresh(state)
    store.save_state(state)
    summary = _event_summary(state)
    summary["issue_id"] = f"message:{message.id}"
    return summary


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


@app.get("/api/events/{event_id}/safe-replies")
def safe_replies(event_id: str):
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    return {"event_id": event_id, "replies": bulk_approval.preview(_load_and_refresh(event_id)),
            "limit": bulk_approval.MAX_BATCH}


@app.post("/api/events/{event_id}/approve-safe-replies")
def approve_safe_replies(event_id: str, body: BulkApprovalRequest):
    """Confirm only the reviewed snapshot; report failures and keep processing."""
    if event_id not in _events():
        raise HTTPException(404, "unknown event")
    approved, failed = [], []
    with _bulk_lock:
        for item in body.replies:
            title = item.id
            try:
                state = _load_and_refresh(event_id)
                action = _find_action(state, item.id)
                title = action.title
                current = next((a for a in reversed(state.actions) if a.issue_id == action.issue_id), None)
                if current is not action:
                    raise HTTPException(409, "A newer proposal replaced this reply.")
                problem = bulk_approval.reply_problem(state, action)
                if problem:
                    raise HTTPException(409, problem)
                if bulk_approval.revision(state, action) != item.revision:
                    raise HTTPException(409, "This reply changed after the preview. Review it again.")
                if any(row.get("action_id") == action.id for row in store.load_outbox(event_id)):
                    raise HTTPException(409, "This reply is already in the outbox; it was not sent again.")
                store.save_state(apply(state, action))
                approved.append({"id": item.id, "title": title})
            except HTTPException as exc:
                failed.append({"id": item.id, "title": title, "reason": str(exc.detail)})
            except (InvariantViolation, ValueError, KeyError) as exc:
                failed.append({"id": item.id, "title": title, "reason": str(exc)})
            except Exception:
                logger.exception("Bulk reply approval failed for %s", item.id)
                failed.append({"id": item.id, "title": title,
                               "reason": "Could not finish approval. Check the outbox before retrying."})
        result = {"approved": approved, "failed": failed,
                  "approved_count": len(approved), "failed_count": len(failed)}
        return {**_event_summary(_load_and_refresh(event_id)), "bulk_approval": result,
                "outbox": store.load_outbox(event_id)}


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
