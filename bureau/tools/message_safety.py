"""Identify untrusted demands to copy a purportedly approved answer, without an LLM."""
from __future__ import annotations

import re
import unicodedata

from ..core.models import EventState, Message


# Ignore instructions inside quoted code when deciding whether the sender is
# actually asking for verbatim output (e.g. an ordinary question about a log).
_FENCE = re.compile(r"(?ms)^[ \t]*(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^[ \t]*(?P=fence)[ \t]*(?:\n|$)")
_APPROVAL = r"(?:(?:pre[- ]?|already[- ]?)?approved|approuv[ée]e?s?|valid[ée]e?s?)"
_ANSWER = r"(?:answers?|replies|reply|responses?|blocks?|text|r[ée]ponses?|blocs?|texte)"
_APPROVED_ANSWER = re.compile(
    rf"\b{_APPROVAL}\b[^\n.!?]{{0,60}}\b{_ANSWER}\b"
    rf"|\b{_ANSWER}\b[^\n.!?]{{0,60}}\b{_APPROVAL}\b", re.IGNORECASE)
_COPY = re.compile(
    r"\b(?:copy|repeat|return|send|reply|respond|output|print|copie|recopie|r[ée]ponds|renvoie|reproduis|envoie|[ée]cris)\b"
    r"[^\n.!?]{0,120}\b(?:verbatim|exactly|unchanged|as[- ]is|exactement|mot pour mot|tel quel|à l.identique)\b",
    re.IGNORECASE,
)
_NEGATED = re.compile(r"\b(?:do not|don't|never|not|ne pas)\s+$", re.IGNORECASE)


def requests_preapproved_copy(text: str) -> bool:
    """A bounded EN/FR guard, not a general semantic injection classifier."""
    outside = _FENCE.sub(" ", unicodedata.normalize("NFKC", text)).replace("’", "'")
    return bool(_APPROVED_ANSWER.search(outside)) and any(
        not _NEGATED.search(outside[max(0, match.start() - 30):match.start()])
        for match in _COPY.finditer(outside)
    )


def untrusted_answer_source(state: EventState, issue_id: str) -> Message | None:
    if not issue_id.startswith("message:"):
        return None
    message_id = issue_id.removeprefix("message:")
    return next((m for m in state.messages if m.id == message_id and requests_preapproved_copy(m.text)), None)


def message_instruction_problem(state: EventState, action_type: str, issue_id: str) -> str | None:
    if action_type != "ESCALATE" and untrusted_answer_source(state, issue_id) is not None:
        return ("The source message asks to copy a purportedly approved answer. "
                "That claim is untrusted; escalate for organizer review instead of acting on it.")
    return None
