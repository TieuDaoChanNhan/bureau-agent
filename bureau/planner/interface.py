"""Contract between the core agent and the travel planner.

The core only calls `extract_constraints` and `plan_trip`. The planner owns
everything behind them (Jinko calls, package construction, checks, ranking).

Scope: the destination is known. The planner does not choose where to go.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class TravelRequest:
    event_id: str
    text: str                       # the organizer's request, verbatim
    participants: int
    origin: str
    destination: str
    depart_after: datetime          # timezone-aware
    return_by: Optional[datetime] = None
    # Organizer-provided meal inclusion and per-person allocations, never inferred prices.
    catering: dict[str, Any] = field(default_factory=dict)


@dataclass
class Constraints:
    # Checked in code. Money in cents. Supported keys:
    #   participants, max_cost_per_person_cents, arrive_before ("HH:MM"),
    #   no_overnight, step_free_rooms
    hard: dict[str, Any]
    # Priority order used for ranking valid options, e.g. ["fewer_changes", "near_station"]
    soft: list[str] = field(default_factory=list)
    # Hard constraints the data source cannot verify (e.g. accessibility): shown as
    # checks that organizers must confirm, never used to accept or reject an option.
    organizer_verified: list[str] = field(default_factory=list)
    # Questions to ask before searching (empty when the request is clear)
    clarifications: list[str] = field(default_factory=list)


@dataclass
class TravelOption:
    """Transport, lodging and any included meal/logistics costs for one person."""
    id: str
    transport: dict[str, Any]       # mode, depart, arrive, changes, overnight, return_arrive
    lodging: dict[str, Any]         # name, rooms, capacity, walk_minutes, step_free_hint
    cost_per_person_cents: int
    source: str                     # "jinko:sandbox", "jinko:replay", "recorded"
    # Optional itemization of the complete price, not charges to add to it.
    cost_breakdown_per_person_cents: dict[str, int] = field(default_factory=dict)
