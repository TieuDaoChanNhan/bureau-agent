"""Shared test fixtures."""
from datetime import datetime, timedelta, timezone

from bureau.core.loader import load_event
from bureau.planner.interface import Constraints, TravelRequest

PARIS = timezone(timedelta(hours=2))  # CEST, valid for the sample dates


def wei_request() -> TravelRequest:
    return TravelRequest(event_id="wei", text="", participants=40, origin="Paris",
                         destination="Trouville-Deauville",
                         depart_after=datetime(2026, 10, 9, 17, tzinfo=PARIS))


def wei_constraints() -> Constraints:
    """Return fresh recorded constraints for deterministic planner tests."""
    recorded = load_event("wei").travel["constraints"]
    return Constraints(hard=dict(recorded["hard"]), soft=list(recorded["soft"]),
                       organizer_verified=list(recorded.get("organizer_verified", [])),
                       clarifications=list(recorded.get("clarifications", [])))
