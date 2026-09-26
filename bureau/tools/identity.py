"""Deterministic identity scoring between a payment and a participant.

The score is computed in code; deciding what to do with a borderline score is
left to the agent and, ultimately, to a human.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ..core.models import EventState, Participant, Payment

PROPOSE_LINK = 0.98  # at or above: propose linking (still requires approval)
ASK_HUMAN = 0.70     # between ASK_HUMAN and PROPOSE_LINK: ask a human
                     # below ASK_HUMAN: treat as a different person

W_SURNAME, W_FIRST, W_EMAIL, W_TIMING = 0.40, 0.25, 0.25, 0.10


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().strip()


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", _norm(text)) if t]


def _local_tokens(email: str) -> set[str]:
    return set(_tokens(email.split("@")[0]))


@dataclass
class MatchResult:
    participant_id: str
    score: float
    signals: list[tuple[str, bool, str]]  # (name, passed, detail)

    @property
    def band(self) -> str:
        if self.score >= PROPOSE_LINK:
            return "propose_link"
        if self.score >= ASK_HUMAN:
            return "ask_human"
        return "different"


def score(payment: Payment, person: Participant) -> MatchResult:
    signals: list[tuple[str, bool, str]] = []
    got, available = 0.0, 0.0

    payer = _tokens(payment.payer_name)
    ref = _tokens(payment.reference or "")
    person_tokens = _tokens(person.name)
    first, surname = person_tokens[0], person_tokens[-1]

    # Surname: exact token, or part of a compound surname ("Dupont" in "Dupont-Lambert").
    available += W_SURNAME
    if surname in payer and payer[-1] == surname:
        got += W_SURNAME
        signals.append(("Surname matches", True, surname))
    elif surname in payer:
        got += 0.75 * W_SURNAME
        signals.append(("Surname is part of a compound surname", True, surname))
    else:
        signals.append(("Surname matches", False, f"{surname} not in {' '.join(payer)}"))

    # First name: exact, prefix of at least 3 letters (in name or reference), or initial.
    available += W_FIRST
    candidates = [t for t in payer + ref if t != surname]
    if first in candidates:
        got += W_FIRST
        signals.append(("First name matches", True, first))
    elif any(len(t) >= 3 and first.startswith(t) for t in candidates):
        got += 0.8 * W_FIRST
        signals.append(("First name compatible (prefix)", True, first))
    elif any(len(t) == 1 and first.startswith(t) for t in candidates):
        got += 0.64 * W_FIRST
        signals.append(("First name compatible (initial)", True, first))
    else:
        signals.append(("First name compatible", False, first))

    # Email local part: only counted when the payment has an email.
    if payment.payer_email:
        available += W_EMAIL
        pay_local = _local_tokens(payment.payer_email)
        best = max((len(pay_local & _local_tokens(e)) / max(len(pay_local | _local_tokens(e)), 1)
                    for e in person.emails), default=0.0)
        if best == 1.0:
            got += W_EMAIL
            signals.append(("Email local part has the same parts", True, payment.payer_email))
        elif best > 0:
            got += 0.4 * W_EMAIL
            signals.append(("Email local part partly matches", True, payment.payer_email))
        else:
            signals.append(("Email local part matches", False, payment.payer_email))

    # Timing: paying after registering is expected.
    available += W_TIMING
    if payment.paid_at >= person.registered_at:
        got += W_TIMING
        signals.append(("Paid after registering", True, ""))
    else:
        signals.append(("Paid after registering", False, "paid before registering"))

    return MatchResult(person.id, round(got / available, 2), signals)


def link_band(payment: Payment, person: Participant) -> tuple[str, float]:
    """Band and score for linking this payment to this person.

    A payer email registered by the person is an exact match. Otherwise the
    deterministic score decides; "different" (below ASK_HUMAN) must never be linked.
    """
    if payment.payer_email and payment.payer_email.lower() in {e.lower() for e in person.emails}:
        return "propose_link", 1.0
    result = score(payment, person)
    return result.band, result.score


def match_person(state: EventState, payment_id: str, top_k: int = 3) -> list[MatchResult]:
    payment = next(p for p in state.payments if p.id == payment_id)
    results = [score(payment, person) for person in state.participants]
    return sorted(results, key=lambda r: r.score, reverse=True)[:top_k]
