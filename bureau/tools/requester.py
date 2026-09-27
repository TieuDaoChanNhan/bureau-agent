"""Who is asking? Checks on the sender of a message before acting on it (T50).

Found by the held-out safety evaluation (T46): the agent acted on requests from addresses that were
not registered for the participant concerned (a confirmation sent to an unknown address, a team change
asked by a look-alike address). These rules are invariants, enforced in code at two layers, like the
identity threshold (T29): when the model proposes (so it can revise, usually into ESCALATE) and when an
organizer approves (the executor).

- A LINK_PAYMENT reply about a participant goes only to that participant's registered addresses.
- A team change triggered by a message needs the message to come from a registered address of the
  member being moved (MOVE_MEMBER), or of a member of the new groups (UPDATE_GROUPS).

Discord or form handles are not registered addresses, so such requests go to the organizers.
"""
from __future__ import annotations

from typing import Optional

from ..core.models import EventState


def message_sender(state: EventState, issue_id: str) -> Optional[str]:
    """The sender of the message behind a message issue, else None (other issues are not requests)."""
    if not issue_id.startswith("message:"):
        return None
    message_id = issue_id.removeprefix("message:")
    return next((m.sender for m in state.messages if m.id == message_id), None)


def is_registered(state: EventState, participant_id: str, address: str) -> bool:
    person = state.participant(participant_id)
    return person is not None and address.strip().lower() in {e.lower() for e in person.emails}


def _recipients(value) -> list[str]:
    return [value] if isinstance(value, str) else [str(v) for v in (value or [])]


def requester_problem(state: EventState, action_type: str, payload: dict, issue_id: str) -> Optional[str]:
    """Return why the proposal acts for someone who did not ask, or None if it is fine."""
    if action_type == "LINK_PAYMENT" and payload.get("to"):
        pid = payload.get("participant_id", "")
        # The participant id itself means "this participant" (their registered address).
        unknown = [r for r in _recipients(payload["to"]) if r != pid and not is_registered(state, pid, r)]
        if unknown:
            return (f"The reply about {pid} would go to {', '.join(unknown)}, which is not a registered address "
                    f"of {pid}. Reply only to {pid}'s registered email, or ESCALATE and say that the sender "
                    "could not be verified.")
    sender = message_sender(state, issue_id)
    if sender is None:
        return None
    if action_type == "MOVE_MEMBER":
        pid = payload.get("participant_id", "")
        if not is_registered(state, pid, sender):
            return (f"The request comes from {sender}, which is not a registered address of {pid}. A team change "
                    "needs a request from the member. ESCALATE and say that the sender could not be verified.")
    if action_type == "UPDATE_GROUPS":
        members = {pid for g in payload.get("groups", []) for pid in g.get("members", [])}
        if not any(is_registered(state, pid, sender) for pid in members):
            return (f"The request comes from {sender}, which is not a registered address of any member of these "
                    "groups. ESCALATE and say that the sender could not be verified.")
    return None
