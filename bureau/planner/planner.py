"""Planner entry point used by the core: plan_trip().

Pipeline:  extract (LLM) -> search (Jinko) -> compose (code) -> check + rank (code) -> explain (LLM)

Search composes Jinko hotel results with recorded transport. Pre-built packages
from data/<event>/travel_options.json remain the offline fallback.
"""
from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import date, datetime

from ..config import DATA_DIR
from ..core.models import EventState, Evidence, ProposedAction
from .constraints import diagnose, eur, evaluate
from . import jinko
from .compose import CateringBudgetError, catering_costs, compose_packages
from .explain import explain, rejection_line
from .extract import extract_constraints
from .interface import Constraints, TravelOption, TravelRequest
from .requirements import unsupported_request_questions

__all__ = ["plan_trip", "extract_constraints", "search_options", "request_from_state", "TravelRequest",
           "HARD_KEYS", "recorded_constraints"]

# Hard constraints checked in code (see interface.Constraints); the only keys an override may set.
HARD_KEYS = {"participants": int, "max_cost_per_person_cents": int, "arrive_before": str,
             "no_overnight": bool, "step_free_rooms": int}


def recorded_constraints(state: EventState) -> Constraints:
    """Constraints recorded with the sample event, for offline demos and tests (no LLM)."""
    recorded = (state.travel or {}).get("constraints")
    if not recorded:
        raise ValueError(f"Event '{state.id}' has no recorded constraints")
    return Constraints(hard=dict(recorded["hard"]), soft=list(recorded["soft"]),
                       organizer_verified=list(recorded.get("organizer_verified", [])),
                       clarifications=list(recorded.get("clarifications", [])))


def request_from_state(state: EventState, text: str | None = None) -> TravelRequest:
    """Build the planner input from `state.travel` (runtime state, not event.json)."""
    t = state.travel
    if not t:
        raise ValueError(f"Event '{state.id}' has no travel request")
    return TravelRequest(event_id=state.id, text=text or t["request"], participants=t["participants"],
                         origin=t["origin"], destination=t["destination"],
                         depart_after=datetime.fromisoformat(t["depart_after"]),
                         return_by=datetime.fromisoformat(t["return_by"]) if t.get("return_by") else None,
                         catering=dict(t.get("catering", {})))


def recorded_packages(event_id: str) -> list[TravelOption]:
    """Pre-built illustrative packages (data/<event>/travel_options.json): the offline fallback."""
    raw = json.loads((DATA_DIR / event_id / "travel_options.json").read_text(encoding="utf-8"))
    return [TravelOption(**o) for o in raw]


def search_options(req: TravelRequest, search: dict | None = None) -> list[TravelOption]:
    """Return candidate packages: Jinko hotels x transport, composed in code (T11, T12).

    `search` comes from `state.travel["search"]`: city, country_code, station [lat, lon],
    checkin, checkout, rooms. Hotels come from Jinko (JINKO_MODE, replay by default); transport
    comes from data/<event>/transport_options.json because Jinko ground search is not available
    for our key. Without `search`, or when Jinko has nothing cached, the recorded packages are used.
    """
    if search:
        try:
            hotels = jinko.hotel_search(search["city"], search["checkin"], search["checkout"], req.participants,
                                        search["rooms"], req.event_id, country_code=search.get("country_code", "fr"),
                                        station=tuple(search["station"]) if search.get("station") else None)
            transports = json.loads((DATA_DIR / req.event_id / "transport_options.json").read_text(encoding="utf-8"))
            nights = (date.fromisoformat(search["checkout"]) - date.fromisoformat(search["checkin"])).days
            packages = compose_packages(req, transports, hotels, nights)
            if packages:
                return packages
        except (jinko.JinkoUnavailable, FileNotFoundError, KeyError):
            pass  # fall back to the recorded packages below
    options = recorded_packages(req.event_id)
    meals = catering_costs(req)
    if meals:
        updated = []
        for option in options:
            breakdown = option.cost_breakdown_per_person_cents
            if any(type(breakdown.get(key)) is not int or breakdown[key] < 0 for key in meals):
                raise CateringBudgetError("Confirm grocery and food-transport amounts already included in the recorded packages.")
            # Replace the old included allocations, retaining the recorded transport/lodging base.
            updated.append(replace(option,
                                   cost_per_person_cents=(option.cost_per_person_cents
                                                          - sum(breakdown[key] for key in meals)
                                                          + sum(meals.values())),
                                   cost_breakdown_per_person_cents={**breakdown, **meals}))
        options = updated
    return options


def plan_trip(req: TravelRequest, c: Constraints, client=None, search: dict | None = None) -> ProposedAction:
    """Return exactly one action: SELECT_TRAVEL_PLAN, or ESCALATE when nothing is valid.

    `client` (OpenAI-compatible) lets explain() phrase the trade-offs; ranking and checks
    are computed in code either way.
    """
    clarifications = list(c.clarifications)
    for key in sorted(c.hard.keys() - HARD_KEYS.keys()):
        clarifications.append(f"The planner cannot enforce the hard requirement '{key}'. "
                              "How should the organizers verify it before searching?")
    # Also guard direct/recorded callers that bypass live extraction.
    for question in unsupported_request_questions(req.text):
        if question not in clarifications:
            clarifications.append(question)
    if not clarifications:
        try:
            catering_costs(req)
            options = search_options(req, search)
        except CateringBudgetError as exc:
            clarifications.append(str(exc))
    if clarifications:
        return ProposedAction(
            id=f"{req.event_id}:clarify_travel", event_id=req.event_id, issue_id="no_logistics_plan",
            action_type="ESCALATE", title="Questions before searching",
            description="\n".join(clarifications), payload={"clarifications": clarifications},
        )

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
            description=(f"{explain(valid, results, c, client=client)} "
                         f"Organizers choose; nothing is booked automatically."),
            evidence=evidence, checks=results[best.id],
            payload={"ranked_valid": [o.id for o in valid], "options": table},
        )
    suggestions = diagnose(options, results)
    return ProposedAction(
        id=f"{req.event_id}:no_valid_plan", event_id=req.event_id,
        issue_id="no_logistics_plan", action_type="ESCALATE",
        title="No option satisfies every hard constraint",
        description=" ".join(["I did not relax any constraint.", *suggestions, rejection_line(results, [])]),
        evidence=evidence, payload={"options": table, "suggestions": suggestions},
    )
