"""Model-selected tools and read-only handlers for event investigation."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from ..core.models import EventState
from ..tools.eligibility import check_eligibility
from ..tools.groups import check_groups, propose_groups
from ..tools.identity import match_person
from ..tools.rules import search_rules

ACTION_TYPES = ["SEND_MESSAGE", "LINK_PAYMENT", "MOVE_MEMBER", "UPDATE_GROUPS", "ESCALATE"]

GROUP_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "kind": {"type": "string", "enum": ["team", "room"]},
        "name": {"type": "string"},
        "members": {"type": "array", "items": {"type": "string"}},
        "capacity_min": {"type": "integer"},
        "capacity_max": {"type": "integer"},
    },
    "required": ["id", "kind", "name", "members", "capacity_min", "capacity_max"],
}


def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required},
    }}


TOOLS = [
    _tool("get_event_summary", "Event name, deadlines, settings and counts.", {}, []),
    _tool("get_participant", "Look up a participant by id or email.",
          {"id_or_email": {"type": "string"}}, ["id_or_email"]),
    _tool("get_payment", "Read payer, email, amount_cents (minor units), currency, date, reference and existing link.",
          {"payment_id": {"type": "string"}}, ["payment_id"]),
    _tool("list_groups", "Read all group ids, names, members, capacities and declaration dates.", {}, []),
    _tool("list_group_candidates", "Read ungrouped participants who explicitly want a group, with names, skills and needs.", {}, []),
    _tool("search_rules", "Keyword search of the English rules. Use English words, not just section ids.",
          {"query": {"type": "string"}}, ["query"]),
    _tool("list_rules", "Read all rule sections to verify a policy when keyword search is inconclusive.", {}, []),
    _tool("check_eligibility", "Participant ids with/without linked payments, and unmatched payment ids.", {}, []),
    _tool("match_person", "Score which participants a payment may belong to (deterministic).",
          {"payment_id": {"type": "string"}}, ["payment_id"]),
    _tool("check_groups", "List violations of group rules (several groups per person, capacity).", {}, []),
    _tool("propose_groups", "Greedy grouping proposal for the given participants.",
          {"participant_ids": {"type": "array", "items": {"type": "string"}},
           "size": {"type": "integer"}}, ["participant_ids"]),
    _tool("propose_action", "Submit one proposal alone after investigation. Unsupported policies require ESCALATE, never inferred permission.", {
        "action_type": {"type": "string", "enum": ACTION_TYPES},
        "title": {"type": "string"},
        "description": {"type": "string", "description": "Proposed outcome; include any organizer confirmation question."},
        "evidence": {"type": "array", "description": "Records and rule sections relied on.",
                     "items": {"type": "object", "properties": {
                         "source_type": {"type": "string", "enum": [
                             "participant", "payment", "group", "message", "rule", "tool"]},
                         "source_id": {"type": "string", "description": "An actual record or rule id."},
                         "description": {"type": "string"}},
                         "required": ["source_type", "source_id", "description"]}},
        "checks": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"}, "passed": {"type": "boolean"}, "detail": {"type": "string"}},
            "required": ["name", "passed"]}},
        "confidence": {"type": "number", "description": "Only for inferences. Omit for deterministic facts."},
        "payload": {
            "type": "object",
            "description": (
                "Nest fields in this payload object: SEND_MESSAGE requires to/text; LINK_PAYMENT requires payment_id/participant_id "
                "(optional reply: to/message); MOVE_MEMBER requires participant_id and from_group "
                "and/or to_group; UPDATE_GROUPS requires complete groups for each replaced kind; "
                "ESCALATE uses note."
            ),
            "properties": {
                "to": {"description": "Recipient or list of recipients for a drafted reply.",
                       "anyOf": [{"type": "string"},
                                 {"type": "array", "minItems": 1, "items": {"type": "string"}}]},
                "text": {"type": "string", "description": "Complete SEND_MESSAGE draft with AI signature."},
                "payment_id": {"type": "string"},
                "participant_id": {"type": "string"},
                "message": {"type": "string", "description": "Optional LINK_PAYMENT reply with AI signature."},
                "from_group": {"type": "string"},
                "to_group": {"type": "string"},
                "groups": {"type": "array", "items": GROUP_SCHEMA},
                "note": {"type": "string"},
            },
        },
    }, ["action_type", "title", "description", "evidence", "checks", "payload"]),
]


def build_handlers(state: EventState) -> dict[str, Callable[..., Any]]:
    """Bind tools to the supplied state without executing or modifying anything."""

    def get_participant(id_or_email: str):
        key = id_or_email.lower()
        person = next((p for p in state.participants
                       if p.id == id_or_email or key in (e.lower() for e in p.emails)), None)
        return asdict(person) if person else {"error": "Participant not found"}

    def get_payment(payment_id: str):
        payment = next((p for p in state.payments if p.id == payment_id), None)
        return asdict(payment) if payment else {"error": "Payment not found"}

    def list_group_candidates():
        kind = state.settings.get("group_kind", "team")
        grouped = {pid for group in state.groups if group.kind == kind for pid in group.members}
        return [asdict(person) for person in state.participants
                if person.looking_for_group and person.id not in grouped]

    return {
        "get_event_summary": lambda: {
            "name": state.name, "deadlines": {k: str(v) for k, v in state.deadlines.items()},
            "settings": state.settings, "participants": len(state.participants),
            "payments": len(state.payments),
            "open_issue_count": sum(i.status not in ("resolved", "dismissed") for i in state.issues),
        },
        "get_participant": get_participant,
        "get_payment": get_payment,
        "list_group_candidates": list_group_candidates,
        "list_groups": lambda: [asdict(group) for group in state.groups],
        "search_rules": lambda query: search_rules(state, query),
        "list_rules": lambda: [
            {"rule_id": rule.id, "title": rule.title, "text": rule.text, "source": rule.source}
            for rule in state.rules
        ],
        "check_eligibility": lambda: check_eligibility(state),
        "match_person": lambda payment_id: [
            {"participant_id": r.participant_id, "name": state.participant(r.participant_id).name,
             "score": r.score, "band": r.band, "signals": r.signals}
            for r in match_person(state, payment_id)],
        "check_groups": lambda: check_groups(state, state.settings.get("group_kind", "team")),
        "propose_groups": lambda participant_ids, size=3: propose_groups(state, participant_ids, size),
    }
