"""Deterministic issue detection: turns an EventState into a list of Issues.

Structural problems (unpaid, duplicate team member, team too large...) are found
by code. Free-text messages become `unprocessed_message` issues that the agent
reads and classifies.
"""
from __future__ import annotations

from .models import EventState, Issue
from ..tools.eligibility import check_eligibility
from ..tools.groups import check_groups
from ..tools.identity import match_person


def detect_issues(state: EventState) -> list[Issue]:
    s = state.settings
    issues: list[Issue] = []

    logistics_issue_id = None
    if s.get("needs_logistics") and not state.logistics:
        logistics_issue_id = "no_logistics_plan"
        issues.append(Issue(
            id=logistics_issue_id, kind="no_logistics_plan", blocking=True,
            title="No validated travel and lodging plan", status="open",
        ))

    # Payments nobody matches exactly: score candidates, never link automatically.
    elig = check_eligibility(state)
    pending: set[str] = set()
    for pay_id in elig["unmatched_payments"]:
        pay = next(p for p in state.payments if p.id == pay_id)
        best = match_person(state, pay_id, top_k=1)
        top = best[0] if best else None
        if top and top.band != "different" and top.participant_id in elig["unpaid"]:
            pending.add(top.participant_id)
            person = state.participant(top.participant_id)
            issues.append(Issue(
                id=f"unmatched_payment:{pay_id}", kind="unmatched_payment", blocking=True,
                title=f"Payment from \"{pay.payer_name}\" may belong to {person.name}",
                subject_ids=[pay_id, top.participant_id], status="needs_human",
                details={"payment_id": pay_id, "candidate": top.participant_id,
                         "score": top.score, "band": top.band,
                         "signals": [list(x) for x in top.signals]},
            ))
        else:
            issues.append(Issue(
                id=f"unmatched_payment:{pay_id}", kind="unmatched_payment", blocking=False,
                title=f"Payment from \"{pay.payer_name}\" matches no registrant",
                subject_ids=[pay_id], status="needs_human",
                details={"payment_id": pay_id, "best_score": top.score if top else None},
            ))

    # Unpaid participants, excluding people with a pending payment match.
    unpaid = [pid for pid in elig["unpaid"] if pid not in pending]
    if unpaid:
        kind = s.get("unpaid_kind", "unpaid_membership")
        issues.append(Issue(
            id=kind, kind=kind, blocking=True,
            title=f"{len(unpaid)} participants haven't paid",
            subject_ids=unpaid, status="open",
            details={"excluded_pending_match": sorted(pending)},
            depends_on=[logistics_issue_id] if logistics_issue_id else [],
        ))

    # Group invariants.
    group_kind = s.get("group_kind", "team")
    for v in check_groups(state, group_kind):
        if v["type"] == "multiple_group_membership":
            p = state.participant(v["participant_id"])
            issues.append(Issue(
                id=f"multiple_group_membership:{v['participant_id']}", kind="multiple_group_membership",
                blocking=True, title=f"{p.name} is in {len(v['group_ids'])} {group_kind}s",
                subject_ids=[v["participant_id"], *v["group_ids"]], details=v,
            ))
        elif v["type"] == "group_over_capacity":
            g = next(x for x in state.groups if x.id == v["group_id"])
            issues.append(Issue(
                id=f"group_over_capacity:{g.id}", kind="group_over_capacity", blocking=True,
                title=f"{g.name} has {v['size']} members (max {v['max']})",
                subject_ids=[g.id], details=v,
            ))

    if s.get("needs_logistics") and not any(g.kind == "room" for g in state.groups):
        issues.append(Issue(
            id="rooms_unassigned", kind="rooms_unassigned", blocking=True,
            title=f"{len(state.participants)} participants have no room",
            subject_ids=[p.id for p in state.participants],
            depends_on=[logistics_issue_id] if logistics_issue_id else [],
        ))

    grouped = {pid for g in state.groups if g.kind == group_kind for pid in g.members}
    solo = [p.id for p in state.participants if p.looking_for_group and p.id not in grouped]
    if solo and group_kind == "team":
        issues.append(Issue(
            id="solo_participants", kind="solo_participants", blocking=False,
            title=f"{len(solo)} participants are looking for a team", subject_ids=solo,
        ))

    for m in state.messages:
        issues.append(Issue(
            id=f"message:{m.id}", kind="unprocessed_message", blocking=False,
            title=f"New {m.channel} message from {m.sender}", subject_ids=[m.id],
            details={"text": m.text},
            depends_on=[logistics_issue_id] if logistics_issue_id and m.id in s.get("messages_need_plan", []) else [],
        ))

    return issues
