"""Build candidate packages from transport and lodging results, in code (TASK T12).

The LLM never composes packages or adds prices. Rules:
  - every transport result x every lodging result that fits the group (capacity)
  - cost_per_person_cents = transport price per person
                            + lodging price per night * nights / participants   (integers only)
  - keep at most N packages, but always keep the cheapest one even if it will fail
    a constraint, so the comparison table can show why it was rejected
"""
from __future__ import annotations

from typing import Any

from .interface import TravelOption, TravelRequest


def compose_packages(req: TravelRequest, transports: list[dict[str, Any]],
                     lodgings: list[dict[str, Any]], nights: int, limit: int = 8) -> list[TravelOption]:
    raise NotImplementedError("TASK T12")
