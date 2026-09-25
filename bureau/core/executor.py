"""Apply an approved ProposedAction to the event state (TASK T03).

This is the only place where state changes. The agent and the planner never
call it; the API calls it after an organizer approves.

Effects by action_type (payload keys in brackets):
    SEND_MESSAGE        [to, text]                          -> append to outbox
    LINK_PAYMENT        [payment_id, participant_id]        -> payment.participant_id = ...
    MOVE_MEMBER         [participant_id, from_group, to_group?] -> update group members
    UPDATE_GROUPS       [groups]                            -> replace groups of that kind
    SELECT_TRAVEL_PLAN  [option_id]                         -> state.logistics = chosen option
    ESCALATE            [note?]                             -> no data change; issue marked handled

After applying, invariants are checked again (tools.groups.check_groups, ...).
If the action would break one, raise InvariantViolation and change nothing.
"""
from __future__ import annotations

from typing import Optional

from .models import EventState, ProposedAction


class InvariantViolation(Exception):
    """Raised when an approved action would leave the state inconsistent."""


def apply(state: EventState, action: ProposedAction, edited_description: Optional[str] = None,
          option_id: Optional[str] = None) -> EventState:
    """Return the new state. Must not mutate `state` if an invariant would break (T03)."""
    raise NotImplementedError("TASK T03")
