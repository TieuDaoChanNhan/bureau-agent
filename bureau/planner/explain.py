"""LLM step 2 of the planner: explain the trade-offs between valid options (TASK T13).

The explanation must not change the ranking or the checks computed in code.
Pipelex or OpenAI, like extract.py.

Design:
  - facts come from code only: the ranked valid options and every option's checks;
  - the LLM (OpenAI Chat Completions) writes 2-4 plain sentences about the trade-offs;
  - the list of rejected options and the constraint each one breaks is appended by code,
    so it is always complete and exact whatever the model writes;
  - without a client (tests, CLI, no key) a deterministic template is used.
"""
from __future__ import annotations

import json

from .. import config
from ..core.models import Check
from .constraints import eur
from .interface import Constraints, TravelOption

SYSTEM = (
    "You explain travel options to volunteer event organizers. Use only the facts given. "
    "Write 2 to 4 short plain sentences: why the first option ranks first under the stated "
    "priorities, and the main trade-off against the other valid options. Mention options by "
    "their letter (\"Option A\"). Do not recommend relaxing a constraint, do not invent prices, "
    "times or facilities, and do not say anything is booked. Name priorities in plain words as "
    "given; never quote field names."
)

# Plain words for the soft-preference keys (see extract.SOFT_KEYS), for organizers and the model.
PRIORITY_LABEL = {
    "fewer_changes": "fewer changes",
    "near_station": "lodging near the station",
    "early_return": "an earlier return",
    "lower_cost": "lower cost",
}


def priority_labels(soft: list[str]) -> list[str]:
    return [PRIORITY_LABEL.get(k, k.replace("_", " ")) for k in soft]


def _rejections(checks: dict[str, list[Check]], ranked_ids: set[str]) -> list[tuple[str, list[str]]]:
    out = []
    for option_id, option_checks in checks.items():
        if option_id in ranked_ids:
            continue
        failed = [ch.name for ch in option_checks if ch.verified and not ch.passed]
        if failed:
            out.append((option_id, failed))
    return out


def rejection_line(checks: dict[str, list[Check]], ranked: list[TravelOption]) -> str:
    """Exact, code-generated list of rejected options and the constraints they break."""
    rejected = _rejections(checks, {o.id for o in ranked})
    if not rejected:
        return ""
    return "Rejected: " + "; ".join(f"Option {oid} ({', '.join(names)})" for oid, names in rejected) + "."


def _template(ranked: list[TravelOption], c: Constraints) -> str:
    best = ranked[0]
    text = (f"Option {best.id} ranks first under the current priorities "
            f"({', '.join(priority_labels(c.soft)) or 'lower cost'}) at {eur(best.cost_per_person_cents)}/person.")
    if len(ranked) > 1:
        text += " Other valid options: " + ", ".join(
            f"Option {o.id} ({eur(o.cost_per_person_cents)})" for o in ranked[1:]) + "."
    return text


def _facts(ranked: list[TravelOption], checks: dict[str, list[Check]], c: Constraints) -> dict:
    return {
        "priorities_in_order": priority_labels(c.soft),
        "hard_constraints": c.hard,
        "valid_options_ranked": [
            {"option": o.id, "cost_per_person": eur(o.cost_per_person_cents), "transport": o.transport,
             "lodging": o.lodging} for o in ranked],
        "organizers_must_confirm": c.organizer_verified,
        "rejected": [{"option": oid, "breaks": names} for oid, names in _rejections(checks, {o.id for o in ranked})],
    }


def explain(ranked: list[TravelOption], checks: dict[str, list[Check]], c: Constraints,
            client=None) -> str:
    """Return a short explanation for organizers; never changes `ranked` or `checks`.

    `client` is an OpenAI-compatible client. Without one, or if the call fails, the
    deterministic template is used. The rejection list is always appended by code.
    """
    if not ranked:
        return " ".join(x for x in ["No option satisfies every hard constraint.", rejection_line(checks, ranked)] if x)
    prose = _template(ranked, c)
    if client is not None:
        try:
            resp = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": json.dumps(_facts(ranked, checks, c), ensure_ascii=False,
                                                                 default=str)}],
            )
            text = (resp.choices[0].message.content or "").strip()
            # The top option must be named; otherwise keep the template.
            if text and f"Option {ranked[0].id}" in text:
                prose = text
        except Exception:  # an explanation is optional; the ranking stands without it
            pass
    return " ".join(x for x in [prose, rejection_line(checks, ranked)] if x)
