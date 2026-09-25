"""Tools exposed to the LLM: JSON schemas (TOOLS) and their Python handlers.

To add a tool:
  1. implement the logic in bureau/tools/ (pure function, with a unit test);
  2. add its schema to TOOLS below;
  3. add a handler in build_handlers().
`propose_action` is special: it is handled by the loop and ends the investigation.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from ..core.models import EventState
from ..tools.eligibility import check_eligibility
from ..tools.groups import check_groups, propose_groups
from ..tools.identity import match_person
from ..tools.rules import search_rules

ACTION_TYPES = ["SEND_MESSAGE", "LINK_PAYMENT", "MOVE_MEMBER", "UPDATE_GROUPS", "ESCALATE"]


def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required},
    }}


TOOLS = [
    _tool("get_event_summary", "Event name, deadlines, settings, counts and open issues.", {}, []),
    _tool("get_participant", "Look up a participant by id or email.",
          {"id_or_email": {"type": "string"}}, ["id_or_email"]),
    _tool("search_rules", "Search the rules / event information and return matching sections.",
          {"query": {"type": "string"}}, ["query"]),
    _tool("check_eligibility", "Which participants have a linked payment, which don't, and unmatched payments.", {}, []),
    _tool("match_person", "Score which participants a payment may belong to (deterministic).",
          {"payment_id": {"type": "string"}}, ["payment_id"]),
    _tool("check_groups", "List violations of group rules (several groups per person, capacity).", {}, []),
    _tool("propose_groups", "Greedy grouping proposal for the given participants.",
          {"participant_ids": {"type": "array", "items": {"type": "string"}},
           "size": {"type": "integer"}}, ["participant_ids"]),
    _tool("propose_action", "Submit the single proposed action for this issue. Ends the investigation.", {
        "action_type": {"type": "string", "enum": ACTION_TYPES},
        "title": {"type": "string"},
        "description": {"type": "string", "description": "What will happen, including any message text."},
        "evidence": {"type": "array", "description": "Records and rule sections relied on.",
                     "items": {"type": "object", "properties": {
                         "source_type": {"type": "string", "enum": [
                             "participant", "payment", "group", "message", "rule", "tool"]},
                         "source_id": {"type": "string", "description": "e.g. p01, f90, §3"},
                         "description": {"type": "string"}},
                         "required": ["source_type", "source_id", "description"]}},
        "checks": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"}, "passed": {"type": "boolean"}, "detail": {"type": "string"}},
            "required": ["name", "passed"]}},
        "confidence": {"type": "number", "description": "Only for inferences (identity, intent). Omit for facts."},
        "payload": {"type": "object", "description": "Data needed to execute, e.g. ids and message text."},
    }, ["action_type", "title", "description", "evidence", "checks"]),
]


def build_handlers(state: EventState) -> dict[str, Callable[..., Any]]:
    """Bind every tool (except propose_action) to the given event state."""

    def get_participant(id_or_email: str):
        key = id_or_email.lower()
        p = next((p for p in state.participants
                  if p.id == id_or_email or key in (e.lower() for e in p.emails)), None)
        return asdict(p) if p else {"error": "not found"}

    return {
        "get_event_summary": lambda: {
            "name": state.name, "deadlines": {k: str(v) for k, v in state.deadlines.items()},
            "settings": state.settings, "participants": len(state.participants),
            "payments": len(state.payments),
            "open_issues": [{"id": i.id, "kind": i.kind, "title": i.title} for i in state.issues
                            if i.status not in ("resolved", "dismissed")],
        },
        "get_participant": get_participant,
        "search_rules": lambda query: search_rules(state, query),
        "check_eligibility": lambda: check_eligibility(state),
        "match_person": lambda payment_id: [
            {"participant_id": r.participant_id, "name": state.participant(r.participant_id).name,
             "score": r.score, "band": r.band, "signals": r.signals}
            for r in match_person(state, payment_id)],
        "check_groups": lambda: check_groups(state, state.settings.get("group_kind", "team")),
        "propose_groups": lambda participant_ids, size=3: propose_groups(state, participant_ids, size),
    }
