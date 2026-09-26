"""The event agent investigates one issue and proposes one action without executing it."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace

from .. import config
from ..core.detect import detect_issues
from ..core.models import Check, EventState, Evidence, Group, Issue, ProposedAction
from ..core.store import append_log, merge_issue_status, save_state
from ..tools.groups import check_groups
from .prompts import SYSTEM_PROMPT
from .tool_specs import ACTION_TYPES, TOOLS, build_handlers

MAX_STEPS = 8


def _valid_recipients(value) -> bool:
    recipients = value if isinstance(value, list) else [value]
    return bool(recipients) and all(isinstance(item, str) and item.strip() for item in recipients)


def _validate_payload(action_type: str, payload: dict) -> None:
    """Check executor input shape before accepting a model's proposal."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    required = {
        "SEND_MESSAGE": ("text",),
        "LINK_PAYMENT": ("payment_id", "participant_id"),
        "MOVE_MEMBER": ("participant_id",),
        "UPDATE_GROUPS": (),
        "ESCALATE": (),
    }
    for key in required[action_type]:
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise ValueError(f"{action_type} requires a non-empty payload.{key}")
    if action_type == "SEND_MESSAGE" and not _valid_recipients(payload.get("to")):
        raise ValueError("SEND_MESSAGE requires payload.to: a recipient or non-empty recipient list")
    if action_type == "LINK_PAYMENT" and payload.get("message") is not None:
        if not isinstance(payload["message"], str) or not payload["message"].strip():
            raise ValueError("LINK_PAYMENT payload.message must be non-empty text")
        if not _valid_recipients(payload.get("to")):
            raise ValueError("LINK_PAYMENT with a message requires payload.to")
    if action_type == "MOVE_MEMBER":
        if not any(payload.get(key) for key in ("from_group", "to_group")):
            raise ValueError("MOVE_MEMBER requires from_group or to_group")
        for key in ("from_group", "to_group"):
            if payload.get(key) is not None and (
                not isinstance(payload[key], str) or not payload[key].strip()
            ):
                raise ValueError(f"MOVE_MEMBER payload.{key} must be a group id")
    if action_type == "UPDATE_GROUPS":
        groups = payload.get("groups")
        if not isinstance(groups, list) or not groups:
            raise ValueError("UPDATE_GROUPS requires a non-empty payload.groups list")
        for group in groups:
            if not isinstance(group, dict):
                raise ValueError("Each group must be an object")
            for key in ("id", "kind", "name"):
                if not isinstance(group.get(key), str) or not group[key].strip():
                    raise ValueError(f"Each group requires a non-empty {key}")
            if group["kind"] not in ("team", "room"):
                raise ValueError("Group kind must be team or room")
            if not isinstance(group.get("members"), list) or not all(
                isinstance(pid, str) and pid.strip() for pid in group["members"]
            ):
                raise ValueError("Group members must be a list of participant ids")
            for key in ("capacity_min", "capacity_max"):
                if type(group.get(key)) is not int:
                    raise ValueError(f"Each group requires an integer {key}")


def _action_from_args(state: EventState, issue: Issue, args: dict) -> ProposedAction:
    action_type = args["action_type"]
    if action_type not in ACTION_TYPES:
        raise ValueError(f"Unsupported action_type: {action_type}")
    for key in ("title", "description"):
        if not isinstance(args.get(key), str) or not args[key].strip():
            raise ValueError(f"propose_action requires a non-empty {key}")
    if "payload" not in args:
        raise ValueError("Include a payload object; nest executor fields inside it, not at the top level")
    payload = args["payload"]
    _validate_payload(action_type, payload)
    if action_type == "UPDATE_GROUPS":
        replacement = [Group(
            id=g["id"], kind=g["kind"], name=g["name"], members=list(g["members"]),
            capacity_min=g["capacity_min"], capacity_max=g["capacity_max"],
        ) for g in payload["groups"]]
        kinds = {group.kind for group in replacement}
        for kind in kinds:
            existing_members = {pid for g in state.groups if g.kind == kind for pid in g.members}
            proposed_members = {pid for g in replacement if g.kind == kind for pid in g.members}
            missing = existing_members - proposed_members
            if missing:
                raise ValueError(
                    f"UPDATE_GROUPS replaces every {kind} group; it must retain assigned participants: "
                    f"{sorted(missing)}. Include existing groups. Escalate unresolved choices instead of deleting them."
                )
        preview = replace(state, groups=[g for g in state.groups if g.kind not in kinds] + replacement)
        violations = [v for kind in kinds for v in check_groups(preview, kind)]
        if violations:
            raise ValueError(f"UPDATE_GROUPS would break group invariants: {violations}")
    evidence = [Evidence(e["source_type"], e["source_id"], e.get("description", ""))
                for e in args.get("evidence", [])]
    checks = [Check(c["name"], c["passed"], c.get("detail", "")) for c in args.get("checks", [])]
    if any(type(check.passed) is not bool for check in checks):
        raise ValueError("Each check.passed must be a boolean")
    return ProposedAction(
        id=f"{state.id}:{issue.id}", event_id=state.id, issue_id=issue.id,
        action_type=action_type, title=args["title"], description=args["description"],
        evidence=evidence, checks=checks,
        confidence=args.get("confidence"), requires_approval=True, payload=payload,
    )


def _default_client():
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set (add it to .env).")
    from openai import OpenAI  # keep offline tools/tests independent of the SDK
    return OpenAI(api_key=config.OPENAI_API_KEY)


def resolve_issue(state: EventState, issue: Issue, max_steps: int = MAX_STEPS,
                  verbose: bool = True, client=None) -> ProposedAction:
    """Investigate with model-selected tools; return one proposal for approval.

    Tests inject a fake client with the chat.completions.create interface.
    Invalid tool arguments and proposals are returned to the model for repair.
    """
    client = client or _default_client()
    handlers = build_handlers(state)
    context = {
        "issue": asdict(issue),
        "messages": [asdict(message) for message in state.messages if message.id in issue.subject_ids],
    }
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Resolve this issue:\n"
         + json.dumps(context, default=str, ensure_ascii=False)},
    ]

    for step in range(max_steps):
        final_turn = step == max_steps - 1
        if final_turn:
            messages.append({
                "role": "user",
                "content": (
                    "This is the final turn. Resolve only the original issue and its subjects. "
                    "Call propose_action with the evidence already collected and a nested payload. "
                    "If facts, policy or participant choices are still missing, choose ESCALATE "
                    "and ask the organizers. Do not invent permission or claim any action executed."
                ),
            })
        # The model selects investigation tools and the final action type.
        # Reserve the last turn for a proposal instead of another unbounded lookup.
        resp = client.chat.completions.create(
            model=config.OPENAI_MODEL, messages=messages, tools=TOOLS,
            parallel_tool_calls=not final_turn,
            tool_choice={"type": "function", "function": {"name": "propose_action"}} if final_turn else "auto",
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or ""})
            messages.append({"role": "user", "content": "Finish by calling propose_action."})
            continue

        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls]})

        for tc in msg.tool_calls:
            if verbose:
                print(f"  -> {tc.function.name}({tc.function.arguments or '{}'})")
            try:
                args = json.loads(tc.function.arguments or "{}")
                if not isinstance(args, dict):
                    raise ValueError("Tool arguments must be a JSON object")
                if tc.function.name == "propose_action":
                    if len(msg.tool_calls) != 1:
                        raise ValueError("Call propose_action alone after reading tool results")
                    action = _action_from_args(state, issue, args)
                    issue.status = "needs_human" if action.action_type == "ESCALATE" else "proposed"
                    state.actions.append(action)
                    return action
                result = handlers[tc.function.name](**args)
            except Exception as exc:
                result = {"error": str(exc) or type(exc).__name__}
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
    """Return issues eligible for agent proposals from the current state.

    An issue whose last agent run failed is retried only when requested by id,
    so a permanent failure cannot be re-sent (and re-billed) on every batch.
    """
    issues_by_id = {issue.id: issue for issue in state.issues}
    proposed_issue_ids = {action.issue_id for action in state.actions}
    statuses = ("open", "needs_human", "agent_failed") if issue_id else ("open", "needs_human")
    return [
        issue for issue in state.issues
        if (issue_id is None or issue.id == issue_id)
        and issue.status in statuses
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
    how many issues one caller attempts; ``None`` means no bound. A failed issue
    is marked ``agent_failed`` and is only retried when requested by ``issue_id``.
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
            issue.status = "agent_failed"
            save_state(state)
            continue
        actions.append(action)
        # Do not lose earlier paid API calls if a later issue fails.
        save_state(state)

    return BatchRunResult(actions=actions, errors=errors,
                          remaining=len(runnable_issues(state, issue_id)))
