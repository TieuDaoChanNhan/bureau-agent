"""LLM step 2 of the planner: explain the trade-offs between valid options (TASK T13).

The explanation must not change the ranking or the checks computed in code.
Pipelex or OpenAI, like extract.py.
"""
from __future__ import annotations

from ..core.models import Check
from .interface import Constraints, TravelOption


def explain(ranked: list[TravelOption], checks: dict[str, list[Check]], c: Constraints) -> str:
    """Return 2-4 plain sentences for organizers.

    Placeholder until T13: a template sentence, no LLM call.
    """
    if not ranked:
        return "No option satisfies every hard constraint."
    best = ranked[0]
    return f"Option {best.id} ranks first under the current priorities ({', '.join(c.soft) or 'lower cost'})."
