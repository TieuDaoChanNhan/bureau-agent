"""Planner entry point used by the core: plan_trip().

Pipeline:  extract (LLM) -> search (Jinko) -> compose (code) -> check + rank (code) -> explain (LLM)

Until T11/T12 are done, `search_options` reads pre-built packages from
data/<event>/travel_options.json.
"""
from __future__ import annotations

import json
from dataclasses import asdict

from ..config import DATA_DIR
from ..core.models import Evidence, ProposedAction
from .constraints import diagnose, eur, evaluate
from .explain import explain
from .extract import extract_constraints
from .interface import Constraints, TravelOption, TravelRequest

__all__ = ["plan_trip", "extract_constraints", "search_options", "TravelRequest"]


def search_options(req: TravelRequest) -> list[TravelOption]:
    """Return candidate packages. TODO(T11, T12): jinko.* + compose.compose_packages."""
    raw = json.loads((DATA_DIR / req.event_id / "travel_options.json").read_text(encoding="utf-8"))
    return [TravelOption(**o) for o in raw]


def plan_trip(req: TravelRequest, c: Constraints) -> ProposedAction:
    """Return exactly one action: SELECT_TRAVEL_PLAN, or ESCALATE when nothing is valid."""
    if c.clarifications:
        return ProposedAction(
            id=f"{req.event_id}:clarify_travel", event_id=req.event_id, issue_id="no_logistics_plan",
            action_type="ESCALATE", title="Questions before searching",
            description="\n".join(c.clarifications), payload={"clarifications": c.clarifications},
        )

    options = search_options(req)
    valid, results = evaluate(options, c)
    evidence = [Evidence("travel_option", o.id, o.source) for o in options]
    table = [{"option": asdict(o), "checks": [asdict(ch) for ch in results[o.id]], "valid": o in valid}
             for o in options]

    if valid:
        best = valid[0]
        return ProposedAction(
            id=f"{req.event_id}:select_travel_plan", event_id=req.event_id,
            issue_id="no_logistics_plan", action_type="SELECT_TRAVEL_PLAN",
            title=f"{len(valid)} of {len(options)} options pass every verified hard constraint",
            description=(f"{explain(valid, results, c)} Best: {eur(best.cost_per_person_cents)}/person. "
                         f"Organizers choose; nothing is booked automatically."),
            evidence=evidence, checks=results[best.id],
            payload={"ranked_valid": [o.id for o in valid], "options": table},
        )
    suggestions = diagnose(options, results)
    return ProposedAction(
        id=f"{req.event_id}:no_valid_plan", event_id=req.event_id,
        issue_id="no_logistics_plan", action_type="ESCALATE",
        title="No option satisfies every hard constraint",
        description="I did not relax any constraint. " + " ".join(suggestions),
        evidence=evidence, payload={"options": table, "suggestions": suggestions},
    )
