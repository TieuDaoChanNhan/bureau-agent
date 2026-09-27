"""Curated samples shared by the static build and live demo fallback.

Only exact sample messages/requests have saved answers. Arbitrary input must
never be silently replaced with a proposal for a different issue.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import re

from bureau.config import ROOT
from bureau.core.models import Check, Evidence, ProposedAction
from bureau.core.store import _action_from_dict
from bureau.planner.planner import plan_trip, recorded_constraints, request_from_state

SIGNATURE = "\n— Drafted with AI assistance, approved by the organizers."
BUDGET_ANSWER = "Yes, the €150 per person includes round-trip coach hire, lodging, groceries and food transport."
BUDGET_QUESTION = "Does the €150 per person include round-trip coach hire as well as lodging, groceries and food transport?"
PERSONAL = "Hello, could you send us the phone numbers of all participants so we can call them about internships?"
TEAM = "Hi! Can our team have five people if the fifth one only does the pitch?"
FRENCH = "Salut, est-ce qu'on a le droit d'utiliser un modèle open source au lieu d'OpenAI pour le projet ?"


class NoSavedExample(ValueError):
    pass


def payment_example() -> dict:
    payment = json.loads((ROOT / "docs/api-examples/action_LINK_PAYMENT.json").read_text(encoding="utf-8"))
    payment["payload"].update({"to": "a.nguyen@polytechnique.example",
        "message": "Bonjour Antoine, votre cotisation 2026 est bien associée à votre inscription. Merci pour votre patience !" + SIGNATURE})
    payment["description"] = ('Payment from “A. Nguyen” (€10) has an identity score of 0.91, below the 0.98 '
                              'high-confidence threshold. Please review the evidence and confirm the match before linking.')
    return payment


def scenarios_and_rules():
    scenarios = json.loads((ROOT / "demo/scenarios.json").read_text(encoding="utf-8"))
    rules_text = (ROOT / "data/hackathon/rules.md").read_text(encoding="utf-8")
    rules = {section: body.strip() for section, body in
             re.findall(r"^## (§\d+)[^\n]*\n(.*?)(?=^## |\Z)", rules_text, re.M | re.S)}
    return scenarios, rules


def issue_example(state, issue):
    if state.id != "hackathon":
        raise NoSavedExample("No saved example for this event's issue.")
    if issue.id in ("message:m01", "unmatched_payment:f90"):
        value = payment_example()
        value.update(id=f"{state.id}:{issue.id}", event_id=state.id, issue_id=issue.id)
        return _action_from_dict(value)
    text = issue.details.get("text", "")
    # The sender lives on the message record, not in the issue details.
    message_id = issue.id.removeprefix("message:")
    sender = next((m.sender for m in state.messages if m.id == message_id), "")
    scenarios, rules = scenarios_and_rules()
    sample = scenarios.get(issue.id.removeprefix("message:"))
    kind = "ESCALATE"
    if sample:
        kind, title, rule = "SEND_MESSAGE", sample["title"], sample["rule"]
        payload = {"to": sender, "text": sample["text"] + SIGNATURE}
    elif text == PERSONAL or issue.id == "message:m05":
        title, rule = "A sponsor requests participants' personal data", "§10"
        payload = {"note": "Please decide how to respond under the association's personal-data rules."}
    elif text == TEAM:
        kind, title, rule = "SEND_MESSAGE", "Review a reply to the rules question", "§3"
        payload = {"to": sender, "text": "Hi! Teams may have at most four members, including anyone preparing the pitch. Please form a team within that limit." + SIGNATURE}
    elif text == FRENCH:
        title, rule = "Confirm which models are permitted", "§2"
        payload = {"note": "Merci de confirmer avec les organisateurs si le modèle open source envisagé est autorisé."}
    else:
        raise NoSavedExample("No saved example for this issue. Try a sample inbox question or skip this step.")
    return ProposedAction(id=f"{state.id}:{issue.id}", event_id=state.id, issue_id=issue.id,
                          action_type=kind, title=title, description="Saved sample proposal; review before approval.",
                          payload=payload, evidence=[Evidence("rule", rule, rules[rule])],
                          checks=[Check("Saved rule reference exists", rule in rules, rule)] if kind == "SEND_MESSAGE" else [],
                          trace=[{"step": 1, "tool": "search_rules", "arguments": {"section": rule},
                                  "result": rules[rule], "ok": True},
                                 {"step": 2, "tool": "propose_action", "arguments": {"action_type": kind},
                                  "result": "Curated sample; organizer approval required", "ok": True}])


def planner_example(state, text=None, overrides=None, *, recorded=False, saved_hotels=True):
    if state.id != "wei" or not state.travel:
        raise NoSavedExample("No saved planning example for this event.")
    base = state.travel["request"]
    expected = base + "\n\nOrganizer answers: " + BUDGET_ANSWER
    # The live console sends precisely this answer format. Accept the static
    # fixture's exact answer as well, but never substring-match arbitrary input.
    answered = text in (expected, BUDGET_ANSWER)
    if text not in (None, base, expected, BUDGET_ANSWER):
        raise NoSavedExample("No saved example for this custom planning request. Use the sample answer or skip this step.")
    constraints = recorded_constraints(state)
    constraints.hard.update(overrides or {})
    if not answered and not recorded:
        constraints.clarifications = [BUDGET_QUESTION]
    # Server replay: the same packages as a live run (saved Jinko hotel responses x recorded transport).
    # The static backup (saved_hotels=False) keeps its five illustrative packages.
    search = state.travel.get("search") if saved_hotels else None
    action = plan_trip(request_from_state(state, text=text), constraints, client=None, search=search)
    action.payload.update(constraints=asdict(constraints), request_text=text or base,
                          constraints_source="recorded", answered=answered)
    return action


def mark_replay(action, reason):
    action.payload["replay"] = True
    action.payload["replay_reason"] = reason
    return action
