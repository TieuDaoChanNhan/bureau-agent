"""Hard-constraint gate, ranking and infeasibility diagnosis (all deterministic)."""
from __future__ import annotations

from ..core.models import Check
from .interface import Constraints, TravelOption


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def eur(cents: int) -> str:
    return f"€{cents / 100:g}"


def check_option(opt: TravelOption, c: Constraints) -> list[Check]:
    hard = c.hard
    checks: list[Check] = []
    if "max_cost_per_person_cents" in hard:
        limit = hard["max_cost_per_person_cents"]
        cost = opt.cost_per_person_cents
        ok = cost <= limit
        checks.append(Check(f"cost ≤ {eur(limit)}/person", ok,
                            eur(cost) + ("" if ok else f" (+{eur(cost - limit)})")))
    if "arrive_before" in hard:
        arrive = opt.transport["arrive"]
        # Arrivals after midnight count as late.
        ok = not opt.transport.get("arrives_next_day") and _minutes(arrive) <= _minutes(hard["arrive_before"])
        checks.append(Check(f"arrive before {hard['arrive_before']}", ok, arrive))
    if hard.get("no_overnight"):
        ok = not opt.transport.get("overnight", False)
        checks.append(Check("no overnight travel", ok, "" if ok else "overnight"))
    if "participants" in hard:
        ok = opt.lodging.get("capacity", 0) >= hard["participants"]
        checks.append(Check(f"lodging for {hard['participants']}", ok, str(opt.lodging.get("capacity"))))
    if "step_free_rooms" in hard:
        # Jinko only exposes accessibility as free-text facilities: a hint, not a guarantee.
        hint = bool(opt.lodging.get("step_free_hint"))
        checks.append(Check(f"≥ {hard['step_free_rooms']} step-free rooms", hint,
                            "listed in facilities; confirm with the venue" if hint else "not listed",
                            verified="step_free_rooms" not in c.organizer_verified))
    return checks


SOFT_KEYS = {
    "fewer_changes": lambda o: o.transport.get("changes", 0),
    "near_station": lambda o: o.lodging.get("walk_minutes", 99),
    "early_return": lambda o: _minutes(o.transport.get("return_arrive", "23:59")),
    "lower_cost": lambda o: o.cost_per_person_cents,
}


def rank(valid: list[TravelOption], soft: list[str]) -> list[TravelOption]:
    """Order valid options by the organizers' current priorities, then by cost.

    This is an ordering under stated preferences, not a claim of an objective best.
    """
    keys = [SOFT_KEYS[k] for k in soft if k in SOFT_KEYS] + [SOFT_KEYS["lower_cost"]]
    return sorted(valid, key=lambda o: tuple(k(o) for k in keys))


def is_valid(checks: list[Check]) -> bool:
    """Only verified checks can reject an option."""
    return all(ch.passed for ch in checks if ch.verified)


def evaluate(options: list[TravelOption], c: Constraints) -> tuple[list[TravelOption], dict[str, list[Check]]]:
    results = {o.id: check_option(o, c) for o in options}
    valid = [o for o in options if is_valid(results[o.id])]
    return rank(valid, c.soft), results


def diagnose(options: list[TravelOption], results: dict[str, list[Check]]) -> list[str]:
    """When nothing is valid: which single relaxation would unlock an option?

    Suggestions only. The planner never relaxes a constraint by itself.
    """
    suggestions = []
    for o in sorted(options, key=lambda x: x.cost_per_person_cents):
        failed = [ch for ch in results[o.id] if ch.verified and not ch.passed]
        if len(failed) == 1:
            suggestions.append(f"Option {o.id} ({eur(o.cost_per_person_cents)}/person) only fails "
                               f"\"{failed[0].name}\" ({failed[0].detail}).")
    return suggestions or ["Every option fails at least two hard constraints; consider other dates."]
