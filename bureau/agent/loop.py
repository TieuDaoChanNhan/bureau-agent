"""The event agent: one orchestrator that investigates an issue with tools and
ends by proposing exactly one action. It never executes actions itself.

Flow for one issue:
    issue JSON -> LLM -> tool calls -> tool results -> ... -> propose_action -> ProposedAction
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .. import config
from ..core.detect import detect_issues
from ..core.models import Check, EventState, Evidence, Issue, ProposedAction
from ..core.store import append_log, merge_issue_status, save_state
from .prompts import SYSTEM_PROMPT
from .tool_specs import TOOLS, build_handlers

MAX_STEPS = 8


def _action_from_args(state: EventState, issue: Issue, args: dict) -> ProposedAction:
    return ProposedAction(
        id=f"{state.id}:{issue.id}", event_id=state.id, issue_id=issue.id,
        action_type=args["action_type"], title=args["title"], description=args["description"],
        evidence=[Evidence(e["source_type"], e["source_id"], e.get("description", ""))
                  for e in args.get("evidence", [])],
        checks=[Check(c["name"], c["passed"], c.get("detail", "")) for c in args.get("checks", [])],
        confidence=args.get("confidence"), requires_approval=True,
        payload=args.get("payload", {}),
    )


def _default_client():
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set (add it to .env).")
    from openai import OpenAI  # imported lazily so the rest of the package works without it
    return OpenAI(api_key=config.OPENAI_API_KEY)


def resolve_issue(state: EventState, issue: Issue, max_steps: int = MAX_STEPS,
                  verbose: bool = True, client=None) -> ProposedAction:
    """Run the tool-calling loop for one issue and return the proposed action.

    `client` defaults to a real OpenAI client. Tests pass a fake object with the same
    `chat.completions.create(...)` interface to check the loop without an API key.
    """
    client = client or _default_client()
    handlers = build_handlers(state)
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Resolve this issue:\n"
         + json.dumps(asdict(issue), default=str, ensure_ascii=False)},
    ]

    for _ in range(max_steps):
        resp = client.chat.completions.create(model=config.OPENAI_MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        if not msg.tool_calls:
            # The model answered in text: remind it that it must end with propose_action.
            messages.append({"role": "assistant", "content": msg.content or ""})
            messages.append({"role": "user", "content": "Finish by calling propose_action."})
            continue

        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls]})

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            if verbose:
                print(f"  -> {tc.function.name}({json.dumps(args, ensure_ascii=False)[:120]})")
            if tc.function.name == "propose_action":
                action = _action_from_args(state, issue, args)
                issue.status = "needs_human" if action.action_type == "ESCALATE" else "proposed"
                state.actions.append(action)
                return action
            try:
                result = handlers[tc.function.name](**args)
            except Exception as exc:  # report tool errors back to the model instead of crashing
                result = {"error": str(exc)}
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(result, default=str, ensure_ascii=False)})

    raise RuntimeError(f"No action proposed for {issue.id} after {max_steps} steps.")


def _is_blocked(issue: Issue, issues_by_id: dict[str, Issue]) -> bool:
    """Return whether an issue still waits for a detected dependency."""
    for dependency_id in issue.depends_on:
        dependency = issues_by_id.get(dependency_id)
        if dependency is not None and dependency.status not in ("resolved", "dismissed"):
            return True
    return False


@dataclass
class BatchRunResult:
    """Actions, recoverable errors, and remaining runnable issues from one batch."""

    actions: list[ProposedAction]
    errors: list[dict[str, str]]
    remaining: int


def _refresh_issues(state: EventState) -> None:
    """Re-detect issues while retaining terminal decisions missing from detection."""
    refreshed = merge_issue_status(detect_issues(state), state.issues)
    current_ids = {issue.id for issue in refreshed}
    terminal = [
        issue for issue in state.issues
        if issue.id not in current_ids and issue.status in ("resolved", "dismissed")
    ]
    state.issues = refreshed + terminal


def runnable_issues(state: EventState, issue_id: str | None = None) -> list[Issue]:
    """Return issues eligible for agent proposals from the current state."""
    issues_by_id = {issue.id: issue for issue in state.issues}
    proposed_issue_ids = {action.issue_id for action in state.actions}
    return [
        issue for issue in state.issues
        if (issue_id is None or issue.id == issue_id)
        and issue.status in ("open", "needs_human")
        and issue.id not in proposed_issue_ids
        and issue.kind != "no_logistics_plan"
        and not _is_blocked(issue, issues_by_id)
    ]


def run_pending(state: EventState, issue_id: str | None = None, *, limit: int | None = None,
                client=None, verbose: bool = True) -> BatchRunResult:
    """Propose runnable issues, persisting each success and logging each failure.

    An issue is runnable when it is open or needs human input, has no existing
    proposal, and is not waiting for an unresolved dependency. The travel-plan
    issue itself is left to the planner rather than the agent. ``limit`` bounds
    how many issues one caller attempts; ``None`` means no bound.
    """
    _refresh_issues(state)
    targets = runnable_issues(state, issue_id)
    if limit is not None:
        targets = targets[:limit]

    actions: list[ProposedAction] = []
    errors: list[dict[str, str]] = []
    for issue in targets:
        try:
            action = resolve_issue(state, issue, client=client, verbose=verbose)
        except Exception as exc:
            error = {"issue_id": issue.id, "error": str(exc)}
            append_log(state.id, {"type": "agent_error", **error})
            errors.append(error)
            continue
        actions.append(action)
        # Do not lose earlier paid API calls if a later issue fails.
        save_state(state)

    return BatchRunResult(actions=actions, errors=errors,
                          remaining=len(runnable_issues(state, issue_id)))
