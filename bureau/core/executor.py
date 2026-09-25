"""Apply an approved ProposedAction to the event state.

This is the only place where state changes. The agent and the planner never
call it; the API calls it after an organizer approves.

Effects by action_type (payload keys in brackets):
    SEND_MESSAGE        [to, text]                          -> append to outbox
    LINK_PAYMENT        [payment_id, participant_id, to?, message?] -> link payment; optional outbox reply
    MOVE_MEMBER         [participant_id, from_group, to_group?] -> update group members
    UPDATE_GROUPS       [groups]                            -> replace groups of that kind
    SELECT_TRAVEL_PLAN  [options, option_id?]               -> state.logistics = valid chosen option
    ESCALATE            [note?]                             -> no data change; issue marked handled

Payments may only be linked to existing participants and cannot change owners
(explicit participant_id, otherwise an exact email match). Travel selections
must have valid=True. Group checks are scoped to the affected groups/members.
Invalid actions leave the input state, outbox and audit log unchanged.
edited_description replaces SEND_MESSAGE text or an optional LINK_PAYMENT reply.
"""
from __future__ import annotations

import copy
from typing import Optional

from . import store
from .models import EventState, Group, ProposedAction
from ..tools.groups import check_groups


class InvariantViolation(Exception):
    """Raised when an approved action would leave the state inconsistent."""


def _find(items: list, item_id: str, attr: str = "id"):
    found = next((x for x in items if getattr(x, attr) == item_id), None)
    if found is None:
        raise ValueError(f"Unknown id: {item_id}")
    return found


def _apply_send_message(state: EventState, action: ProposedAction, text: str) -> None:
    store.append_outbox(state.id, {
        "action_id": action.id, "to": action.payload["to"], "text": text,
    })


def _apply_link_payment(state: EventState, action: ProposedAction) -> None:
    payment = _find(state.payments, action.payload["payment_id"])
    pid = action.payload["participant_id"]
    if state.participant(pid) is None:
        raise ValueError(f"Unknown participant_id: {pid}")
    owners = {payment.participant_id} if payment.participant_id is not None else {
        person.id for person in state.participants
        if payment.payer_email and payment.payer_email.lower() in {e.lower() for e in person.emails}
    }
    if owners - {pid}:
        raise InvariantViolation(f"Payment {payment.id} already belongs to another participant")
    if action.payload.get("message") is not None and not action.payload.get("to"):
        raise ValueError("LINK_PAYMENT with a message requires a recipient (to)")
    payment.participant_id = pid


def _apply_move_member(state: EventState, action: ProposedAction) -> None:
    pid = action.payload["participant_id"]
    from_group_id = action.payload.get("from_group")
    to_group_id = action.payload.get("to_group")
    touched_ids = {gid for gid in (from_group_id, to_group_id) if gid}

    if from_group_id:
        group = _find(state.groups, from_group_id)
        group.members = [m for m in group.members if m != pid]
    if to_group_id:
        group = _find(state.groups, to_group_id)
        if pid not in group.members:
            group.members.append(pid)

    kind = next((g.kind for g in state.groups if g.id in touched_ids), None)
    if kind is None:
        return
    violations = [
        v for v in check_groups(state, kind)
        if (v["type"] == "group_over_capacity" and v["group_id"] in touched_ids)
        or (v["type"] == "multiple_group_membership" and v["participant_id"] == pid)
    ]
    if violations:
        raise InvariantViolation(f"MOVE_MEMBER for {pid} would break: {violations}")


def _apply_update_groups(state: EventState, action: ProposedAction) -> None:
    new_groups_data = action.payload["groups"]
    kinds = {g["kind"] for g in new_groups_data}
    existing = {g.id: g for g in state.groups}
    replacement = [
        Group(
            id=g["id"], kind=g["kind"], name=g["name"], members=list(g["members"]),
            capacity_min=g["capacity_min"], capacity_max=g["capacity_max"],
            declared_at=existing[g["id"]].declared_at if g["id"] in existing else g.get("declared_at"),
        )
        for g in new_groups_data
    ]
    state.groups = [g for g in state.groups if g.kind not in kinds] + replacement

    violations = [v for kind in kinds for v in check_groups(state, kind)]
    if violations:
        raise InvariantViolation(f"UPDATE_GROUPS would break: {violations}")


def _apply_select_travel_plan(state: EventState, action: ProposedAction, option_id: Optional[str]) -> None:
    chosen_id = option_id or action.payload.get("option_id")
    if not chosen_id:
        raise ValueError("SELECT_TRAVEL_PLAN requires an option_id")
    row = next((o for o in action.payload.get("options", []) if o["option"]["id"] == chosen_id), None)
    if row is None:
        raise ValueError(f"Unknown option_id: {chosen_id}")
    if row.get("valid") is not True:
        raise InvariantViolation(f"Travel option {chosen_id} is not valid")
    state.logistics = copy.deepcopy(row["option"])


def apply(state: EventState, action: ProposedAction, edited_description: Optional[str] = None,
          option_id: Optional[str] = None) -> EventState:
    """Return the new state. Must not mutate `state` if an invariant would break (T03)."""
    new_state = copy.deepcopy(state)

    if action.action_type == "SEND_MESSAGE":
        text = edited_description if edited_description is not None else action.payload["text"]
        _apply_send_message(new_state, action, text)
    elif action.action_type == "LINK_PAYMENT":
        _apply_link_payment(new_state, action)
        if action.payload.get("message") is not None:
            text = edited_description if edited_description is not None else action.payload["message"]
            _apply_send_message(new_state, action, text)
    elif action.action_type == "MOVE_MEMBER":
        _apply_move_member(new_state, action)
    elif action.action_type == "UPDATE_GROUPS":
        _apply_update_groups(new_state, action)
    elif action.action_type == "SELECT_TRAVEL_PLAN":
        _apply_select_travel_plan(new_state, action, option_id)
    elif action.action_type == "ESCALATE":
        pass  # no data change: a human takes over
    else:
        raise ValueError(f"Unknown action_type: {action.action_type}")

    issue = new_state.issue(action.issue_id)
    if issue is not None:
        issue.status = "resolved"
        issue.resolved_by_action_id = action.id

    store.append_log(new_state.id, {
        "action_id": action.id, "action_type": action.action_type, "issue_id": action.issue_id,
    })
    return new_state
