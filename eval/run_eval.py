"""Offline evaluation (TASK T08). Run: python -m eval.run_eval

Reads labelled cases from eval/cases/, runs the agent / planner, prints a
metrics table and writes eval/results/<timestamp>.json.

Offline metrics only (labels written by the team). Do not report them as
"user approval rates": those come from a real organizer (TASK T18).
"""
from __future__ import annotations

import json
from pathlib import Path

CASES = Path(__file__).resolve().parent / "cases"


def load_cases(name: str) -> list[dict]:
    path = CASES / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    raise NotImplementedError("TASK T08: agent metrics on messages.jsonl, planner metrics on planning.jsonl")


if __name__ == "__main__":
    main()
