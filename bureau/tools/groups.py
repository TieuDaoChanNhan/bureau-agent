"""Group (team or room) invariants and a simple greedy grouping."""
from __future__ import annotations

from collections import defaultdict

from ..core.models import EventState


def check_groups(state: EventState, kind: str = "team") -> list[dict]:
    """Return every violation of: one group per person, capacity limits."""
    groups = [g for g in state.groups if g.kind == kind]
    violations: list[dict] = []

    membership: dict[str, list[str]] = defaultdict(list)
    for g in groups:
        for pid in g.members:
            membership[pid].append(g.id)
    for pid, gids in membership.items():
        if len(gids) > 1:
            violations.append({"type": "multiple_group_membership", "participant_id": pid, "group_ids": gids})

    for g in groups:
        if len(g.members) > g.capacity_max:
            violations.append({"type": "group_over_capacity", "group_id": g.id,
                               "size": len(g.members), "max": g.capacity_max})
        elif len(g.members) < g.capacity_min:
            violations.append({"type": "group_under_capacity", "group_id": g.id,
                               "size": len(g.members), "min": g.capacity_min})
    return violations


def propose_groups(state: EventState, participant_ids: list[str], size: int = 3) -> list[list[str]]:
    """Greedy: spread each skill across groups so every group gets a mix.

    Deliberately simple; it is a proposal for humans to approve, not an optimum.
    """
    people = [state.participant(pid) for pid in participant_ids]
    people = [p for p in people if p is not None]
    n_groups = max(1, round(len(people) / size))
    groups: list[list[str]] = [[] for _ in range(n_groups)]
    # Rarest skills first, so scarce profiles are spread before common ones.
    counts: dict[str, int] = defaultdict(int)
    for p in people:
        for s in p.skills[:1]:
            counts[s] += 1
    people.sort(key=lambda p: counts.get(p.skills[0], 0) if p.skills else 99)
    for p in people:
        target = min(groups, key=len)
        groups[groups.index(target)].append(p.id)
    return groups
