"""LLM step 1 of the planner: organizer's words -> Constraints (TASK T10).

Two acceptable implementations, behind the same function:
  a) Pipelex pipe (sponsor tool; time-box the attempt), or
  b) OpenAI structured output with a JSON schema matching `Constraints`.

Rules for the model:
  - extract only what the organizer said; never invent a constraint;
  - put anything ambiguous in `clarifications` (e.g. "does the budget include meals?");
  - money in cents; times as "HH:MM";
  - accessibility-type constraints go to `organizer_verified` (the API cannot verify them).
"""
from __future__ import annotations

import json

from ..config import DATA_DIR
from .interface import Constraints, TravelRequest


def extract_constraints(req: TravelRequest) -> Constraints:
    """Return constraints for the request.

    Placeholder until T10: returns the recorded constraints of the sample event.
    """
    meta = json.loads((DATA_DIR / req.event_id / "event.json").read_text(encoding="utf-8"))
    c = meta["travel"]["constraints"]
    return Constraints(hard=dict(c["hard"]), soft=list(c["soft"]),
                       organizer_verified=list(c.get("organizer_verified", [])))
