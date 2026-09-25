"""Shared test fixtures."""
from datetime import datetime, timedelta, timezone

from bureau.planner.interface import TravelRequest

PARIS = timezone(timedelta(hours=2))  # CEST, valid for the sample dates


def wei_request() -> TravelRequest:
    return TravelRequest(event_id="wei", text="", participants=40, origin="Paris",
                         destination="Trouville-Deauville",
                         depart_after=datetime(2026, 10, 9, 17, tzinfo=PARIS))
