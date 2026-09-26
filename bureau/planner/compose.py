"""Build candidate packages from transport and lodging results, in code (TASK T12).

The LLM never composes packages or adds prices. Rules:
  - every transport result x every lodging result that fits the group (capacity)
  - cost_per_person_cents = transport price per person
                            + lodging price per night * nights / participants   (integers only)
  - keep at most N packages, but always keep the cheapest one even if it will fail
    a constraint, so the comparison table can show why it was rejected

Inputs are the normalized results of planner/jinko.py:
  transport: depart, arrive, changes, overnight, price_cents (per person), optional mode,
             return_arrive, arrives_next_day, source
  lodging:   name, rooms, capacity, walk_minutes, price_per_night_cents (whole group),
             step_free_hint, optional source
"""
from __future__ import annotations

from string import ascii_uppercase
from typing import Any

from .interface import TravelOption, TravelRequest


def _per_person_lodging(price_per_night_cents: int, nights: int, participants: int) -> int:
    """Lodging share per person, rounded up so a package is never cheaper than it is."""
    return -(-price_per_night_cents * nights // participants)


def _label(k: int) -> str:
    return ascii_uppercase[k] if k < 26 else f"P{k + 1}"


def compose_packages(req: TravelRequest, transports: list[dict[str, Any]],
                     lodgings: list[dict[str, Any]], nights: int, limit: int = 8) -> list[TravelOption]:
    """Return at most `limit` packages, labelled A, B, C… in order of cost per person.

    Selection keeps variety for the comparison table: first the cheapest package of each
    transport, then the remaining combinations by cost. The overall cheapest package is
    always kept, even when it will fail a constraint.
    """
    if nights < 1 or req.participants < 1:
        raise ValueError("nights and participants must be positive")
    fitting = [l for l in lodgings if int(l.get("capacity", 0)) >= req.participants]
    combos = []
    for t_index, t in enumerate(transports):
        for l in fitting:
            cost = int(t["price_cents"]) + _per_person_lodging(int(l["price_per_night_cents"]), nights,
                                                               req.participants)
            combos.append((cost, t_index, t, l))
    if not combos:
        return []
    combos.sort(key=lambda c: (c[0], c[1]))

    chosen, seen_transports = [], set()
    for combo in combos:                       # cheapest package of each transport
        if combo[1] not in seen_transports:
            seen_transports.add(combo[1])
            chosen.append(combo)
    chosen = chosen[:limit]
    for combo in combos:                       # fill with the next cheapest combinations
        if len(chosen) >= limit:
            break
        if combo not in chosen:
            chosen.append(combo)
    if combos[0] not in chosen:                # the cheapest is always shown
        chosen[-1] = combos[0]
    chosen.sort(key=lambda c: (c[0], c[1]))

    packages = []
    for k, (cost, _, t, l) in enumerate(chosen):
        transport = {key: value for key, value in t.items() if key not in ("price_cents", "source")}
        lodging = {key: value for key, value in l.items() if key not in ("price_per_night_cents", "source")}
        source = t.get("source") or l.get("source") or "jinko"
        packages.append(TravelOption(id=_label(k), transport=transport, lodging=lodging,
                                     cost_per_person_cents=cost, source=source))
    return packages
