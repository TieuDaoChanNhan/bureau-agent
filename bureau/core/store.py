"""Persistence of runtime state (TASK T02).

Design:
- data/<event>/     sample input, read-only, committed to git
- runtime/<event>/  what changes while the app runs, git-ignored:
      state.json    participants/payments/groups after approved actions
      issues.json   issue statuses keyed by issue id (fingerprint)
      actions.json  proposed actions and their decision (approved / dismissed)
      outbox.json   simulated sent messages
      log.jsonl     audit trail, one JSON object per line

Issue ids are deterministic fingerprints, so `merge_issue_status` can re-apply
stored statuses after every re-detection without creating duplicates.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import RUNTIME_DIR
from .loader import load_event
from .models import Check, EventState, Evidence, Group, Issue, Participant, Payment, ProposedAction


class _DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError(f"Datetime without timezone in runtime data: {value}")
    return dt


def _event_dir(event_id: str) -> Path:
    return RUNTIME_DIR / event_id


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, cls=_DateTimeEncoder, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _action_from_dict(a: dict) -> ProposedAction:
    return ProposedAction(
        id=a["id"], event_id=a["event_id"], issue_id=a["issue_id"], action_type=a["action_type"],
        title=a["title"], description=a["description"],
        evidence=[Evidence(**e) for e in a.get("evidence", [])],
        checks=[Check(**c) for c in a.get("checks", [])],
        confidence=a.get("confidence"), requires_approval=a.get("requires_approval", True),
        payload=a.get("payload", {}),
    )


def load_state(event_id: str) -> EventState:
    """Load runtime state if it exists, otherwise the sample data (T02)."""
    state = load_event(event_id)
    stored = _read_json(_event_dir(event_id) / "state.json", None)
    if stored is not None:
        state.participants = [
            Participant(
                id=p["id"], name=p["name"], emails=p["emails"], registered_at=_dt(p["registered_at"]),
                skills=p.get("skills", []), needs=p.get("needs", []),
                looking_for_group=p.get("looking_for_group", False),
            )
            for p in stored["participants"]
        ]
        state.payments = [
            Payment(
                id=x["id"], payer_name=x["payer_name"], amount_cents=x["amount_cents"],
                currency=x.get("currency", "EUR"), paid_at=_dt(x["paid_at"]),
                payer_email=x.get("payer_email"), reference=x.get("reference"),
                participant_id=x.get("participant_id"),
            )
            for x in stored["payments"]
        ]
        state.groups = [
            Group(
                id=g["id"], kind=g["kind"], name=g["name"], members=g["members"],
                capacity_min=g["capacity_min"], capacity_max=g["capacity_max"],
                declared_at=_dt(g.get("declared_at")),
            )
            for g in stored["groups"]
        ]
        state.travel = stored.get("travel")
        state.logistics = stored.get("logistics")

    state.issues = [Issue(**i) for i in _read_json(_event_dir(event_id) / "issues.json", [])]
    state.actions = [_action_from_dict(a) for a in _read_json(_event_dir(event_id) / "actions.json", [])]
    return state


def save_state(state: EventState) -> None:
    """Write participants, payments, groups, logistics, issues and actions to runtime/ (T02)."""
    d = _event_dir(state.id)
    _write_json(d / "state.json", {
        "participants": [asdict(p) for p in state.participants],
        "payments": [asdict(p) for p in state.payments],
        "groups": [asdict(g) for g in state.groups],
        "travel": state.travel,
        "logistics": state.logistics,
    })
    _write_json(d / "issues.json", [asdict(i) for i in state.issues])
    _write_json(d / "actions.json", [asdict(a) for a in state.actions])


def merge_issue_status(detected: list[Issue], stored: list[Issue]) -> list[Issue]:
    """Keep statuses (resolved, dismissed, resolved_by_action_id) of issues detected again (T02).

    Issues that are no longer detected disappear; new ones start as 'open'.
    """
    by_id = {i.id: i for i in stored}
    merged = []
    for issue in detected:
        prev = by_id.get(issue.id)
        if prev is not None:
            issue = replace(issue, status=prev.status, resolved_by_action_id=prev.resolved_by_action_id)
        merged.append(issue)
    return merged


def append_log(event_id: str, entry: dict) -> None:
    """Append one audit entry to runtime/<event>/log.jsonl (T02)."""
    path = _event_dir(event_id) / "log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, cls=_DateTimeEncoder, ensure_ascii=False) + "\n")


def reset(event_id: str) -> None:
    """Delete runtime/<event>/ so the demo starts again from the sample data (T02)."""
    d = _event_dir(event_id)
    if d.exists():
        shutil.rmtree(d)


def save_action(action: ProposedAction) -> None:
    """Store or update a proposed action (T02)."""
    path = _event_dir(action.event_id) / "actions.json"
    actions = [a for a in _read_json(path, []) if a["id"] != action.id]
    actions.append(asdict(action))
    _write_json(path, actions)


def append_outbox(event_id: str, message: dict) -> None:
    """Append a simulated reply with a timezone-aware sent_at timestamp."""
    path = _event_dir(event_id) / "outbox.json"
    outbox = _read_json(path, [])
    outbox.append({**message, "sent_at": datetime.now().astimezone().isoformat()})
    _write_json(path, outbox)


def load_outbox(event_id: str) -> list:
    """Read runtime/<event>/outbox.json, or [] if nothing has been sent yet (T05)."""
    return _read_json(_event_dir(event_id) / "outbox.json", [])


__all__ = ["RUNTIME_DIR", "load_state", "save_state", "merge_issue_status", "append_log", "reset", "save_action",
           "append_outbox", "load_outbox"]
