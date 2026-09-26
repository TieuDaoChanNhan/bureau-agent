"""Shared test fixtures."""
from bureau.core.loader import load_event
from bureau.planner.interface import Constraints, TravelRequest
from bureau.planner.planner import request_from_state


def wei_request() -> TravelRequest:
    return request_from_state(load_event("wei"))


def wei_constraints() -> Constraints:
    """Return fresh recorded constraints for deterministic planner tests."""
    recorded = load_event("wei").travel["constraints"]
    return Constraints(hard=dict(recorded["hard"]), soft=list(recorded["soft"]),
                       organizer_verified=list(recorded.get("organizer_verified", [])),
                       clarifications=list(recorded.get("clarifications", [])))
