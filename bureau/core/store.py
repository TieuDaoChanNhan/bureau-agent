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

from ..config import RUNTIME_DIR
from .models import EventState, Issue, ProposedAction


def load_state(event_id: str) -> EventState:
    """Load runtime state if it exists, otherwise the sample data (T02)."""
    raise NotImplementedError("TASK T02: load runtime/<event>/state.json, fall back to core.loader.load_event")


def save_state(state: EventState) -> None:
    """Write participants, payments, groups, logistics, issues and actions to runtime/ (T02)."""
    raise NotImplementedError("TASK T02")


def merge_issue_status(detected: list[Issue], stored: list[Issue]) -> list[Issue]:
    """Keep statuses (resolved, dismissed, resolved_by_action_id) of issues detected again (T02).

    Issues that are no longer detected disappear; new ones start as 'open'.
    """
    raise NotImplementedError("TASK T02")


def append_log(event_id: str, entry: dict) -> None:
    """Append one audit entry to runtime/<event>/log.jsonl (T02)."""
    raise NotImplementedError("TASK T02")


def reset(event_id: str) -> None:
    """Delete runtime/<event>/ so the demo starts again from the sample data (T02)."""
    raise NotImplementedError("TASK T02")


def save_action(action: ProposedAction) -> None:
    """Store or update a proposed action (T02)."""
    raise NotImplementedError("TASK T02")


__all__ = ["RUNTIME_DIR", "load_state", "save_state", "merge_issue_status", "append_log", "reset", "save_action"]
