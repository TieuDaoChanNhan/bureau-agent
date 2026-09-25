"""Command line entry point.

  python -m bureau detect hackathon          # issues found by fixed code (no LLM)
  python -m bureau run hackathon [--issue ID] # agent proposes actions (needs OPENAI_API_KEY)
  python -m bureau plan wei [--budget 90]     # travel planner on recorded options (no LLM)
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .core.detect import detect_issues
from .config import DATA_DIR
from .core.loader import load_event
from .planner.interface import TravelRequest
from .planner.planner import extract_constraints, plan_trip


def _print_issues(issues) -> None:
    for group, flag in (("BLOCKING", True), ("NON-BLOCKING", False)):
        subset = [i for i in issues if i.blocking == flag]
        print(f"\n{group} ({len(subset)})")
        for i in subset:
            wait = f"  [waits for {', '.join(i.depends_on)}]" if i.depends_on else ""
            print(f"  · {i.id:<38} {i.status:<12} {i.title}{wait}")


def cmd_detect(args) -> None:
    state = load_event(args.event)
    state.issues = detect_issues(state)
    print(f"{state.name}: {len(state.participants)} participants, {len(state.payments)} payments, "
          f"{len(state.groups)} groups, {len(state.messages)} messages")
    _print_issues(state.issues)


def cmd_run(args) -> None:
    from . import config
    from .agent.loop import resolve_issue

    if not config.OPENAI_API_KEY:
        sys.exit("OPENAI_API_KEY is not set. Copy .env.example to .env and add the key.")
    state = load_event(args.event)
    state.issues = detect_issues(state)
    targets = [i for i in state.issues if (args.issue is None or i.id == args.issue)
               and not i.depends_on and i.kind != "no_logistics_plan"]
    if not targets:
        sys.exit("No matching issue that can be resolved now.")
    for issue in targets:
        print(f"\n■ {issue.id} — {issue.title}")
        action = resolve_issue(state, issue)
        print(json.dumps(action.to_dict(), indent=2, ensure_ascii=False, default=str))


def cmd_plan(args) -> None:
    state = load_event(args.event)
    t = json.loads((DATA_DIR / args.event / "event.json")
                   .read_text(encoding="utf-8"))["travel"]
    from datetime import datetime
    req = TravelRequest(event_id=state.id, text=t["request"], participants=t["participants"],
                        origin=t["origin"], destination=t["destination"],
                        depart_after=datetime.fromisoformat(t["depart_after"]))
    c = extract_constraints(req)
    if args.budget is not None:
        c.hard["max_cost_per_person_cents"] = int(round(args.budget * 100))
    print(f"{req.origin} -> {req.destination}\nHard: {c.hard}\nSoft (priority order): {c.soft}\n"
          f"Organizer-verified: {c.organizer_verified}\n")
    action = plan_trip(req, c)
    print(f"{action.action_type}: {action.title}\n{action.description}\n")
    for row in action.payload.get("options", []):
        o = row["option"]
        fails = [ch["name"] + (f" ({ch['detail']})" if ch["detail"] else "")
                 for ch in row["checks"] if ch["verified"] and not ch["passed"]]
        todo = [ch["name"] for ch in row["checks"] if not ch["verified"]]
        verdict = "VALID" if row["valid"] else "REJECTED: " + "; ".join(fails)
        extra = f"  [organizers confirm: {', '.join(todo)}]" if todo and row["valid"] else ""
        print(f"  {o['id']}  €{o['cost_per_person_cents'] / 100:<5g} arrive {o['transport']['arrive']:<6} {verdict}{extra}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="bureau")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("detect"); p.add_argument("event"); p.set_defaults(fn=cmd_detect)
    p = sub.add_parser("run"); p.add_argument("event"); p.add_argument("--issue"); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("plan"); p.add_argument("event"); p.add_argument("--budget", type=float); p.set_defaults(fn=cmd_plan)
    args = parser.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
