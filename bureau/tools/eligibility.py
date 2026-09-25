"""Registration × payment reconciliation (exact matches only)."""
from __future__ import annotations

from ..core.models import EventState, Payment


def linked_payment(state: EventState, participant_id: str) -> Payment | None:
    person = state.participant(participant_id)
    if person is None:
        return None
    emails = {e.lower() for e in person.emails}
    for pay in state.payments:
        if pay.participant_id == participant_id:
            return pay
        if pay.participant_id is None and pay.payer_email and pay.payer_email.lower() in emails:
            return pay
    return None


def check_eligibility(state: EventState) -> dict[str, list[str]]:
    """Return participant ids split into paid / unpaid, and payment ids nobody matches."""
    paid, unpaid = [], []
    used: set[str] = set()
    for person in state.participants:
        pay = linked_payment(state, person.id)
        if pay:
            paid.append(person.id)
            used.add(pay.id)
        else:
            unpaid.append(person.id)
    unmatched = [p.id for p in state.payments if p.id not in used]
    return {"paid": paid, "unpaid": unpaid, "unmatched_payments": unmatched}
