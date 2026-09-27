"""Clarify explicit transport restrictions the current option checker cannot enforce."""
from __future__ import annotations

import re


_MODE = r"(?:trains?|rail|coaches|coach|buses|bus|flights?|planes?|autocars?|avions?)"
_TRANSPORT_RESTRICTION = re.compile(
    rf"\b{_MODE}(?:[-\s]+travel)?[-\s]+(?:only|uniquement|seulement|obligatoires?)\b"
    rf"|\b(?:only|uniquement|seulement|exclusivement)\s+(?:(?:by|en|par)\s+)?{_MODE}\b"
    rf"|\b(?:no|without|sans|aucun|aucune)\s+{_MODE}\b(?!\s+(?:restrictions?|limits?))"
    rf"|\bpas\s+d(?:e\s+|['’]){_MODE}\b"
    rf"|\b{_MODE}\s+(?:(?:are|is|est|sont)\s+)?(?:forbidden|prohibited|not allowed|interdits?|interdites?)\b"
    rf"|\bmust\s+(?:travel|go)\s+by\s+{_MODE}\b",
    re.IGNORECASE,
)


def unsupported_request_questions(text: str) -> list[str]:
    """Catch explicit EN/FR mode limits even when extraction omits them.

    This deliberately stops for organizer clarification rather than guessing a
    supported mode or relaxing the request. It is a bounded lexical backstop;
    other unsupported requirements must be preserved by structured extraction.
    """
    if not _TRANSPORT_RESTRICTION.search(text):
        return []
    return ["The planner cannot enforce the requested transport-mode restriction. "
            "Can the organizers verify suitable transport or explicitly revise this requirement before searching?"]
