"""Conservative eligibility for organizer-confirmed bulk replies (T24).

This is the single safety policy. The static build certifies exact saved proposals
with it; the browser never decides that a new, model-written reply is safe.
Eligibility is a review filter, not proof of the truth of a model's prose.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import re
import unicodedata

from .models import EventState, ProposedAction


# Reviewed public, non-financial sections. Unknown events/sections fail closed.
RULES = {"hackathon": frozenset({"§2", "§4", "§6", "§7"})}
MAX_BATCH = 100
READ_ONLY_RULE_TOOLS = {"get_event_summary", "search_rules", "list_rules", "propose_action"}
SENSITIVE = re.compile(
    r"[€$£¥]|\b(?:pay\w*|paid|unpaid|refund\w*|reimburs\w*|money|fees?|costs?|"
    r"euros?|dollars?|credits?|bank\w*|account\s+number|membership|cotis\w*|"
    r"pai\w*|paye\w*|rembours\w*|argent|tarifs?|prix|factur\w*|"
    r"identit\w*|passport\w*|passeport\w*|personal\s+data|donnees\s+personnelles|"
    r"phone\w*|telephon\w*|medical\w*|exception\w*)\b", re.I)


def _sensitive(text: str) -> bool:
    folded = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return bool(SENSITIVE.search(folded))


def reply_problem(state: EventState, action: ProposedAction) -> str | None:
    """Return an exclusion reason, or None for a candidate for human review."""
    issue = state.issue(action.issue_id)
    if (action.event_id != state.id or action.action_type != "SEND_MESSAGE"
            or action.requires_approval is not True):
        return "Only replies requiring organizer approval can be included."
    if not issue or issue.kind != "unprocessed_message" or issue.status != "proposed":
        return "The reply is no longer pending."
    if any(not state.issue(dep) or state.issue(dep).status not in ("resolved", "dismissed")
           for dep in issue.depends_on):
        return "Resolve the prerequisites first."
    if action.confidence is not None:
        return "Inferences require individual review."
    if not action.checks or any(c.passed is not True or c.verified is not True
                               or not isinstance(c.name, str) or not c.name.strip()
                               or not isinstance(c.detail, str) for c in action.checks):
        return "Every reply needs at least one passed, verified check."
    message = next((m for m in state.messages if issue.id == f"message:{m.id}"), None)
    payload = action.payload
    if not message or not message.sender.strip() or not isinstance(payload, dict):
        return "The source message is missing."
    if set(payload) - {"to", "text", "replay", "replay_reason"}:
        return "This proposal contains fields requiring individual review."
    if payload.get("to") not in (message.sender, [message.sender]):
        return "A bulk reply must go only to the original sender."
    if not isinstance(payload.get("text"), str) or not 0 < len(payload["text"].strip()) <= 8000:
        return "The reply draft is missing or too long."
    allowed = RULES.get(state.id, frozenset())
    actual_rules = {r.id for r in state.rules}
    rule_ids = set()
    if not isinstance(action.evidence, list):
        return "Rule evidence is missing."
    for evidence in action.evidence:
        if not all(isinstance(value, str) for value in
                   (evidence.source_type, evidence.source_id, evidence.description)):
            return "Rule evidence is incomplete."
        if evidence.source_type == "rule":
            if evidence.source_id not in allowed or evidence.source_id not in actual_rules:
                return "The cited rule is not approved for bulk replies."
            rule_ids.add(evidence.source_id)
        elif evidence.source_type != "message" or evidence.source_id not in (message.id, issue.id):
            return "Replies based on personal records require individual review."
    if not rule_ids:
        return "A reply must cite an existing, reviewed public rule."
    if not isinstance(action.trace, list) or any(
            not isinstance(step, dict) or not isinstance(step.get("tool"), str)
            or step["tool"] not in READ_ONLY_RULE_TOOLS or step.get("ok") is not True
            for step in action.trace):
        return "The investigation includes failed or non-rule tools."
    if not isinstance(action.title, str) or not isinstance(action.description, str):
        return "The proposal is incomplete."
    # Also exclude explicitly sensitive subjects in otherwise rule-shaped proposals.
    text = "\n".join([message.text, action.title, action.description, payload["text"],
                      *(c.name + " " + c.detail for c in action.checks),
                      *(e.description for e in action.evidence),
                      *(r.text for r in state.rules if r.id in rule_ids)])
    if _sensitive(text):
        return "Money, identity, personal data and exceptions require individual review."
    return None


def revision(state: EventState, action: ProposedAction) -> str:
    """Bind confirmation to the proposal, source message, issue and cited rules."""
    issue = state.issue(action.issue_id)
    message = next((m for m in state.messages if action.issue_id == f"message:{m.id}"), None)
    rule_ids = {e.source_id for e in action.evidence if e.source_type == "rule"}
    snapshot = {"action": asdict(action), "issue": asdict(issue) if issue else None,
                "message": asdict(message) if message else None,
                "rules": [asdict(r) for r in state.rules if r.id in rule_ids]}
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                                     default=str).encode()).hexdigest()


def preview(state: EventState) -> list[dict]:
    """Read-only candidates, including exactly the text the organizer will approve."""
    latest = {a.issue_id: a for a in state.actions}
    return [{"id": a.id, "title": a.title, "to": a.payload["to"], "text": a.payload["text"],
             "rules": sorted({e.source_id for e in a.evidence if e.source_type == "rule"}),
             "revision": revision(state, a)}
            for a in latest.values() if reply_problem(state, a) is None]
