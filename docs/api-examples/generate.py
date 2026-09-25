"""Regenerate the example API payloads from the real code.

Run from the repository root:  python -m docs.api-examples.generate  (or: python docs/api-examples/generate.py)
Re-run after changing bureau/core/models.py so the web UI mocks stay in sync.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bureau.core.detect import detect_issues  # noqa: E402
from bureau.core.loader import load_event  # noqa: E402
from bureau.core.models import Check, Evidence, ProposedAction  # noqa: E402
from bureau.planner.interface import Constraints, TravelRequest  # noqa: E402
from bureau.planner.planner import extract_constraints, plan_trip  # noqa: E402

OUT = Path(__file__).resolve().parent


def dump(name: str, data) -> None:
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print("wrote", name)


def counts(issues):
    open_ = [i for i in issues if i.status not in ("resolved", "dismissed")]
    return {"blocking": sum(i.blocking for i in open_), "non_blocking": sum(not i.blocking for i in open_),
            "resolved": sum(i.status == "resolved" for i in issues)}


def main() -> None:
    events = []
    for event_id in ("hackathon", "wei"):
        state = load_event(event_id)
        issues = detect_issues(state)
        events.append({"id": event_id, "name": state.name, "counts": counts(issues)})
        if event_id == "hackathon":
            dump("GET_event_hackathon.json", {"id": event_id, "name": state.name, "counts": counts(issues),
                                              "issues": [asdict(i) for i in issues], "actions": []})
    dump("GET_events.json", events)

    # What the agent proposes for message m01 (hand-written example of a real agent output).
    link = ProposedAction(
        id="hackathon:message:m01", event_id="hackathon", issue_id="message:m01", action_type="LINK_PAYMENT",
        title="Link payment f90 to Antoine Nguyen?",
        description=("Antoine says he paid from his personal address. Payment f90 (\"A. Nguyen\", "
                     "nguyen.a@gmail.com, €10) scores 0.91: please confirm before I link it.\n\n"
                     "Reply to send after confirmation:\nBonjour Antoine, votre cotisation 2026 est bien associée "
                     "à votre inscription. Vous êtes éligible pour le hackathon.\n"
                     "— Drafted with AI assistance, approved by the organizers."),
        evidence=[Evidence("message", "m01", "Claims payment from a personal address"),
                  Evidence("participant", "p01", "Antoine Nguyen, registered, no linked fee"),
                  Evidence("payment", "f90", "A. Nguyen · nguyen.a@gmail.com · €10 · 19 Sep"),
                  Evidence("rule", "§3", "Membership fee required to take part")],
        checks=[Check("Surname matches", True, "nguyen"), Check("First name compatible (initial)", True, "antoine"),
                Check("Email local part has the same parts", True, "nguyen.a@gmail.com"),
                Check("Identity score ≥ 0.98", False, "0.91: ask a human")],
        confidence=0.91, payload={"payment_id": "f90", "participant_id": "p01"},
    )
    dump("action_LINK_PAYMENT.json", asdict(link))

    wei = load_event("wei")
    t = wei.travel
    from datetime import datetime
    req = TravelRequest(event_id="wei", text=t["request"], participants=t["participants"], origin=t["origin"],
                        destination=t["destination"], depart_after=datetime.fromisoformat(t["depart_after"]))
    c = extract_constraints(req)
    dump("action_SELECT_TRAVEL_PLAN.json", asdict(plan_trip(req, c)))
    c90 = Constraints(hard={**c.hard, "max_cost_per_person_cents": 9000}, soft=c.soft,
                      organizer_verified=c.organizer_verified)
    dump("action_ESCALATE_no_valid_plan.json", asdict(plan_trip(req, c90)))

    dump("POST_approve_request.json", {"edited_description": None, "option_id": "A"})
    dump("GET_outbox.json", [{"action_id": "hackathon:message:m01", "to": ["a.nguyen@polytechnique.edu"],
                              "text": "Bonjour Antoine, ...", "sent_at": "2026-09-25T21:08:00+02:00"}])
    del wei


if __name__ == "__main__":
    main()
