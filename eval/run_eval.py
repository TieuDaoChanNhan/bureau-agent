"""Evaluate labeled fixtures without approving actions or changing runtime state.

Message evaluation calls the real configured agent; tests inject a scripted client.
These corpus metrics are not organizer approval rates or measurements of time saved.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Callable
from unittest.mock import patch

from bureau import config
from bureau.agent.loop import _default_client, resolve_issue
from bureau.agent.tool_specs import ACTION_TYPES, TOOLS
from bureau.core import executor
from bureau.core.detect import detect_issues
from bureau.core.loader import load_event
from bureau.core.models import EventState, Issue, ProposedAction
from bureau.planner.interface import Constraints, TravelRequest
from bureau.planner.planner import extract_constraints, plan_trip

CASES = Path(__file__).resolve().parent / "cases"
RESULTS = CASES.parent / "results"
MESSAGE_KEYS = {
    "id", "event", "message_id", "expected_kind", "expected_tools",
    "expected_action", "must_ask_human", "expected_rule",
}
METRIC_DEFINITIONS = {
    "action_accuracy": "Exact action_type match; all attempted cases, including errors.",
    "tool_selection": "All required tool names requested by the model; extra tools allowed; errors fail.",
    "rule_citation": "Expected rule id in rule evidence; only cases with a non-null rule label.",
    "human_handling": "ESCALATE or a question mark in organizer-facing description, compared with must_ask_human; errors fail.",
    "invariants": "Violations in final proposals: isolated executor rejection, approval bypass, or mutation during investigation. Failed runs remain unchecked.",
}
PLANNING_METRIC_DEFINITIONS = {
    "hard_constraints": "Exact hard dictionary match, including absent and extra fields; extraction errors fail.",
    "clarifications": "At least one question when the label is non-empty, otherwise none; wording is not scored and extraction errors fail.",
    "soft_preferences": "Exact ordered preference list; only cases with expected_soft labels; extraction errors fail.",
    "organizer_verification": "Exact set of organizer-verified keys; only labeled cases; extraction errors fail.",
    "feasibility": "Any valid recorded option after the clarification gate; clarification stops and errors are unassessed and excluded.",
}


def load_cases(name: str) -> list[dict]:
    """Read JSONL and identify malformed rows before any model calls."""
    path = CASES / name
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_number}: {exc.msg}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path.name}:{line_number}: expected an object")
        rows.append(row)
    return rows


def validate_message_cases(cases: list[dict]) -> None:
    """Validate labels and references; the model never receives these labels."""
    if not cases:
        raise ValueError("No message cases selected")
    seen = set()
    states = {}
    events = {p.name for p in config.DATA_DIR.iterdir() if p.is_dir()}
    tools = {tool["function"]["name"] for tool in TOOLS}
    for case in cases:
        if not isinstance(case, dict) or MESSAGE_KEYS - case.keys():
            raise ValueError("Each message case must contain all eight required keys")
        for key in ("id", "event", "message_id", "expected_kind", "expected_action"):
            if not isinstance(case[key], str) or not case[key].strip():
                raise ValueError(f"Invalid {key} in message case")
        label = case["id"]
        if label in seen:
            raise ValueError(f"Duplicate case id: {label}")
        seen.add(label)
        if case["event"] not in events:
            raise ValueError(f"{label}: unknown event")
        if case["event"] not in states:
            states[case["event"]] = load_event(case["event"])
        state = states[case["event"]]
        if case["message_id"] not in {m.id for m in state.messages}:
            raise ValueError(f"{label}: unknown message_id")
        if "text" in case and (not isinstance(case["text"], str) or not case["text"].strip()):
            raise ValueError(f"{label}: text override must be non-empty")
        if case["expected_action"] not in ACTION_TYPES:
            raise ValueError(f"{label}: unknown expected_action")
        expected_tools = case["expected_tools"]
        if not isinstance(expected_tools, list) or any(
            not isinstance(tool, str) or tool not in tools for tool in expected_tools
        ):
            raise ValueError(f"{label}: unknown or malformed expected_tools")
        if type(case["must_ask_human"]) is not bool:
            raise ValueError(f"{label}: must_ask_human must be a boolean")
        rule = case["expected_rule"]
        if rule is not None and (not isinstance(rule, str) or rule not in {r.id for r in state.rules}):
            raise ValueError(f"{label}: unknown expected_rule")


def prepare_message(case: dict) -> tuple[EventState, Issue]:
    """Build a fresh sample state, optionally paraphrasing only the source message."""
    state = load_event(case["event"])
    if "text" in case:
        state.messages = [replace(m, text=case["text"]) if m.id == case["message_id"] else m
                          for m in state.messages]
    state.issues = detect_issues(state)
    issue = next((i for i in state.issues if i.id == f"message:{case['message_id']}"), None)
    if issue is None:
        raise ValueError(f"{case['id']}: no issue for source message")
    return state, issue


class TraceClient:
    """Observe model tool requests without supplying answers from the labels."""

    def __init__(self, client):
        self.client = client
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        response = self.client.chat.completions.create(**kwargs)
        for call in response.choices[0].message.tool_calls or []:
            self.calls.append({"name": call.function.name, "arguments": call.function.arguments})
        return response


def _error(exc: Exception) -> dict:
    detail = str(exc)
    if config.OPENAI_API_KEY:
        detail = detail.replace(config.OPENAI_API_KEY, "[REDACTED]")
    return {"type": type(exc).__name__, "detail": detail}


def check_invariants(state: EventState, action: ProposedAction) -> list[dict]:
    """Dry-run the executor on a copy, with outbox and audit writes disabled.

    The fixture deliberately contains existing group conflicts. The executor's
    scoped checks avoid counting those against an unrelated reply or payment.
    """
    violations = []
    if action.requires_approval is not True:
        violations.append({"type": "approval_bypass", "detail": "Proposal does not require approval"})
    memory_store = SimpleNamespace(append_log=lambda *a, **k: None,
                                   append_outbox=lambda *a, **k: None)
    try:
        with patch.object(executor, "store", memory_store):
            executor.apply(deepcopy(state), action)
    except (executor.InvariantViolation, ValueError, KeyError, TypeError) as exc:
        violations.append(_error(exc))
    return violations


def score_message(case: dict, action: ProposedAction | None, tool_names: list[str]) -> dict:
    """Compare a prediction with labels; question detection is an explicit heuristic."""
    asks = None if action is None else (
        action.action_type == "ESCALATE" or any(mark in action.description for mark in ("?", "？"))
    )
    rule = case["expected_rule"]
    return {
        "action_correct": action is not None and action.action_type == case["expected_action"],
        "tools_correct": action is not None and set(case["expected_tools"]) <= set(tool_names),
        "rule_correct": None if rule is None else action is not None and any(
            e.source_type == "rule" and e.source_id == rule for e in action.evidence
        ),
        "human_correct": action is not None and asks == case["must_ask_human"],
        "asks_human": asks,
    }


def _event_records(state: EventState):
    return state.participants, state.payments, state.groups, state.travel, state.logistics


def evaluate_messages(cases: list[dict], *, client_factory=None, progress=None) -> list[dict]:
    """Evaluate independently; retain failures and continue with later cases."""
    validate_message_cases(cases)
    client = _default_client() if client_factory is None else None
    rows = []
    for index, case in enumerate(cases, 1):
        state, issue = prepare_message(case)
        before = deepcopy(state)
        action, error, trace, violations = None, None, None, None
        try:
            trace = TraceClient(client_factory() if client_factory else client)
            action = resolve_issue(state, issue, client=trace, verbose=False)
            violations = check_invariants(before, action)
        except Exception as exc:
            error = _error(exc)
        if _event_records(state) != _event_records(before):
            violations = (violations or []) + [{
                "type": "investigation_mutation", "detail": "Agent changed event records before approval",
            }]
        calls = trace.calls if trace is not None else []
        metrics = score_message(case, action if error is None else None, [c["name"] for c in calls])
        row = {
            "id": case["id"],
            "input": {"event": state.id, "message": asdict(next(
                m for m in before.messages if m.id == case["message_id"]
            ))},
            "expected": {key: case[key] for key in sorted(MESSAGE_KEYS)
                         if key.startswith("expected_") or key == "must_ask_human"},
            "action": asdict(action) if action is not None else None,
            "tool_calls": calls, "metrics": metrics, "violations": violations, "error": error,
        }
        rows.append(row)
        if progress:
            progress(index, len(cases), row)
    return rows


def _accuracy(values: list[bool | None]) -> dict:
    measured = [value for value in values if value is not None]
    correct = sum(value is True for value in measured)
    return {"correct": correct, "total": len(measured),
            "accuracy": correct / len(measured) if measured else None}


def summarize_messages(rows: list[dict]) -> dict:
    """Keep errors in accuracy denominators and untested proposals visible."""
    result = {name: _accuracy([row["metrics"][key] for row in rows]) for name, key in (
        ("action_accuracy", "action_correct"), ("tool_selection", "tools_correct"),
        ("rule_citation", "rule_correct"), ("human_handling", "human_correct"),
    )}
    result["invariants"] = {
        "violations": sum(len(row["violations"] or []) for row in rows),
        "checked": sum(row["violations"] is not None for row in rows),
        "unchecked": sum(row["violations"] is None for row in rows),
    }
    result["errors"] = sum(row["error"] is not None for row in rows)
    result["human_interventions"] = {
        "missed": sum(row["expected"]["must_ask_human"] and row["metrics"]["asks_human"] is False
                      for row in rows),
        "unnecessary": sum(not row["expected"]["must_ask_human"] and row["metrics"]["asks_human"] is True
                           for row in rows),
        "unknown": sum(row["metrics"]["asks_human"] is None for row in rows),
    }
    return result


def evaluate_planning(
    cases: list[dict], *, extractor: Callable[[TravelRequest], Constraints] | None = None,
) -> dict:
    """Score live extraction, then recorded options only when no clarification is needed."""
    extract = extract_constraints if extractor is None else extractor
    rows = []
    for case in cases:
        row = {
            "id": case["id"], "expected": case, "error": None,
            "constraints": None, "action": None, "feasible": None,
            "hard_correct": False, "hard_fields": {}, "clarifications_correct": False,
            "soft_correct": False if "expected_soft" in case else None,
            "organizer_verified_correct": False if "expected_organizer_verified" in case else None,
            "feasibility_correct": None,
        }
        try:
            state = load_event(case["event"])
            travel = state.travel
            request = TravelRequest(
                event_id=state.id, text=case["text"], participants=travel["participants"],
                origin=travel["origin"], destination=travel["destination"],
                depart_after=datetime.fromisoformat(travel["depart_after"]),
            )
            row["input"] = asdict(request)
            constraints = extract(request)
            row.update(
                constraints=asdict(constraints),
                hard_correct=constraints.hard == case["expected_hard"],
                hard_fields={key: key in constraints.hard and key in case["expected_hard"]
                             and constraints.hard[key] == case["expected_hard"][key]
                             for key in sorted(constraints.hard.keys() | case["expected_hard"].keys())},
                clarifications_correct=bool(constraints.clarifications) == bool(case["expected_clarifications"]),
                soft_correct=(constraints.soft == case["expected_soft"]
                              if "expected_soft" in case else None),
                organizer_verified_correct=(set(constraints.organizer_verified)
                                             == set(case["expected_organizer_verified"])
                                             if "expected_organizer_verified" in case else None),
            )
            action = plan_trip(request, constraints)
            row["action"] = asdict(action)
            # plan_trip owns the clarification gate and the recorded-option checks.
            # Do not search again here: that would bypass the organizer's answer.
            if not constraints.clarifications:
                row["feasible"] = action.action_type == "SELECT_TRAVEL_PLAN"
                row["feasibility_correct"] = row["feasible"] == case["feasible"]
        except Exception as exc:
            row["error"] = _error(exc)
        rows.append(row)
    return {
        "mode": "llm_extraction_recorded_options",
        "limitation": "Extraction uses the configured LLM; options are recorded packages, not live availability. Clarification presence is scored, not question meaning.",
        "metric_definitions": PLANNING_METRIC_DEFINITIONS,
        "cases": rows,
        "metrics": {name: _accuracy([r[key] for r in rows]) for name, key in (
            ("hard_constraints", "hard_correct"), ("clarifications", "clarifications_correct"),
            ("soft_preferences", "soft_correct"), ("organizer_verification", "organizer_verified_correct"),
            ("feasibility", "feasibility_correct"),
        )},
    }


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _print_table(title: str, metrics: dict) -> None:
    print(f"\n{title}")
    print(f"{'Metric':<25} {'Result':>10}  Count")
    print("-" * 55)
    for name, result in metrics.items():
        if isinstance(result, dict) and "accuracy" in result:
            percentage = "N/A" if result["accuracy"] is None else f"{result['accuracy']:.1%}"
            print(f"{name:<25} {percentage:>10}  {result['correct']}/{result['total']}")
    if "invariants" in metrics:
        result = metrics["invariants"]
        print(f"{'invariant_violations':<25} {result['violations']:>10}  {result['checked']} checked, {result['unchecked']} unchecked")
        print(f"{'agent_errors':<25} {metrics['errors']:>10}")
        human = metrics["human_interventions"]
        print(f"{'human_interventions':<25} {'':>10}  {human['missed']} missed, {human['unnecessary']} unnecessary, {human['unknown']} unknown")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("all", "messages", "planning"), default="all")
    parser.add_argument("--limit", type=_positive, help="Maximum number of message cases (bounds API calls)")
    parser.add_argument("--output-dir", type=Path, default=RESULTS)
    args = parser.parse_args(argv)
    started = datetime.now(timezone.utc)
    message_cases = load_cases("messages.jsonl") if args.suite != "planning" else []
    planning_cases = load_cases("planning.jsonl") if args.suite != "messages" else []
    if message_cases:
        validate_message_cases(message_cases)
        message_cases = message_cases[:args.limit]
    report = {
        "schema_version": 1, "started_at": started.isoformat(), "model": config.OPENAI_MODEL,
        "metric_definitions": METRIC_DEFINITIONS,
        "dataset_sha256": _digest({"messages": message_cases, "planning": planning_cases}),
        "messages": None, "planning": None,
    }
    try:
        report["git_revision"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=config.ROOT, stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        report["git_revision"] = None
    events = {case["event"] for case in message_cases + planning_cases}
    report["fixture_sha256"] = {
        str(path.relative_to(config.DATA_DIR).as_posix()): hashlib.sha256(path.read_bytes()).hexdigest()
        for event in sorted(events) for path in sorted((config.DATA_DIR / event).iterdir()) if path.is_file()
    }
    if message_cases:
        def progress(index, total, row):
            outcome = row["action"]["action_type"] if row["action"] else "ERROR"
            print(f"[{index}/{total}] {row['id']}: {outcome}", flush=True)

        rows = evaluate_messages(message_cases, progress=progress)
        report["messages"] = {"cases": rows, "metrics": summarize_messages(rows)}
        _print_table("Messages (labeled corpus; real configured agent)", report["messages"]["metrics"])
    if planning_cases:
        report["planning"] = evaluate_planning(planning_cases)
        _print_table("Planning (LLM extraction; recorded options)", report["planning"]["metrics"])
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / (started.strftime("%Y%m%dT%H%M%S.%fZ") + ".json")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, default=str)
        stream.write("\n")
    print(f"\nResults: {output}")
    errors = report["messages"]["metrics"]["errors"] if report["messages"] else 0
    errors += sum(row["error"] is not None for row in report["planning"]["cases"]) if report["planning"] else 0
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
