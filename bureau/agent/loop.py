"""The event agent investigates one issue and proposes one action without executing it."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace

from .. import config
from ..core.detect import detect_issues
from ..core.llm_usage import LiveUnavailable, create_completion
from ..core.models import Check, EventState, Evidence, Group, Issue, ProposedAction
from ..core.store import append_log, merge_issue_status, save_state
from ..tools.groups import check_groups
from ..tools.identity import ASK_HUMAN, link_band
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


def _check_identity(state: EventState, payload: dict) -> None:
    """The identity threshold is an invariant: enforce it here, not only in the prompt."""
    payment = next((p for p in state.payments if p.id == payload["payment_id"]), None)
    person = state.participant(payload["participant_id"])
    if payment is None or person is None:
        raise ValueError("LINK_PAYMENT refers to an unknown payment_id or participant_id")
    band, value = link_band(payment, person)
    if band == "different":
        raise ValueError(
            f"Payment {payment.id} and participant {person.id} score {value} < {ASK_HUMAN}: they are "
            "treated as different people. Do not link them; ESCALATE or ask for payment details instead.")


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
    if action_type == "LINK_PAYMENT":
        _check_identity(state, payload)
        if issue.kind == "unprocessed_message" and not (payload.get("message") and payload.get("to")):
            # The sender asked something: the organizer must be able to review and edit the answer.
            raise ValueError("This issue is a message: include payload.to (the sender) and payload.message "
                             "(a draft reply in the sender's language, ending with the AI signature)")
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


TRACE_RESULT_CHARS = 240


def _names(items, key="name", limit=3) -> str:
    shown = ", ".join(str(i.get(key, "?")) for i in items[:limit])
    return shown + (f" (+{len(items) - limit} more)" if len(items) > limit else "")


def _readable(tool: str, result):
    """One line an organizer can read in the timeline; None falls back to JSON."""
    if isinstance(result, dict) and "error" in result:
        return f"error: {result['error']}"
    if tool == "get_participant":
        return f"{result['id']} · {result['name']} · {', '.join(result.get('emails', []))}"
    if tool == "get_payment":
        owner = result.get("participant_id") or "not linked"
        return (f"{result['id']} · {result['payer_name']} · {result.get('payer_email') or 'no email'} · "
                f"{result['amount_cents'] / 100:.2f} {result.get('currency', '')} · {owner}")
    if tool == "check_eligibility" and isinstance(result, dict):
        parts = [f"{len(v)} {k.replace('_', ' ')}" + (f": {', '.join(map(str, v))}" if len(v) <= 4 else "")
                 for k, v in result.items() if isinstance(v, list)]
        return "; ".join(parts)
    if tool == "match_person" and isinstance(result, list):
        return "; ".join(f"{r['name']} ({r['participant_id']}) {r['score']} {r['band']}" for r in result[:3])
    if tool in ("search_rules", "list_rules") and isinstance(result, list):
        return f"{len(result)} section{'s' if len(result) != 1 else ''}: " + _names(result, "title")
    if tool == "check_groups" and isinstance(result, list):
        return f"{len(result)} violation{'s' if len(result) != 1 else ''}" + (
            ": " + ", ".join(v["type"] for v in result[:3]) if result else "")
    if tool == "list_groups" and isinstance(result, list):
        return f"{len(result)} groups: " + _names(result)
    if tool == "list_group_candidates" and isinstance(result, list):
        return f"{len(result)} people looking for a team: " + _names(result)
    if tool == "propose_groups" and isinstance(result, list):
        return f"{len(result)} draft group{'s' if len(result) != 1 else ''}: " + " | ".join(", ".join(g) for g in result)
    return None


def _summarize(result, tool: str = "") -> str:
    """Short view of a tool result for the organizer timeline."""
    try:
        text = _readable(tool, result)
    except (KeyError, TypeError, AttributeError):
        text = None
    if text is None:
        if isinstance(result, list):
            head = json.dumps(result[:3], default=str, ensure_ascii=False)
            text = f"{len(result)} result{'s' if len(result) != 1 else ''}: {head}"
        else:
            text = json.dumps(result, default=str, ensure_ascii=False)
    return text if len(text) <= TRACE_RESULT_CHARS else text[:TRACE_RESULT_CHARS - 1] + "…"


def _default_client():
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set (add it to .env).")
    from openai import OpenAI  # keep offline tools/tests independent of the SDK
    return OpenAI(api_key=config.OPENAI_API_KEY, timeout=45, max_retries=0 if config.DEMO_MODE else 2)


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

    trace: list[dict] = []
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
        resp = create_completion(client, purpose=f"agent:{state.id}:{issue.id}",
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
            entry = {"step": step + 1, "tool": tc.function.name,
                     "arguments": tc.function.arguments or "{}", "result": "", "ok": True}
            trace.append(entry)
            try:
                args = json.loads(tc.function.arguments or "{}")
                if not isinstance(args, dict):
                    raise ValueError("Tool arguments must be a JSON object")
                entry["arguments"] = args
                if tc.function.name == "propose_action":
                    if len(msg.tool_calls) != 1:
                        raise ValueError("Call propose_action alone after reading tool results")
                    action = _action_from_args(state, issue, args)
                    entry["arguments"] = {"action_type": action.action_type}
                    entry["result"] = "proposal recorded for organizer approval"
                    action.trace = trace
                    issue.status = "needs_human" if action.action_type == "ESCALATE" else "proposed"
                    state.actions.append(action)
                    return action
                result = handlers[tc.function.name](**args)
            except Exception as exc:
                result = {"error": str(exc) or type(exc).__name__}
            if tc.function.name == "propose_action":
                # Keep the rejected proposal's type, not its whole payload.
                entry["arguments"] = {"action_type": (entry["arguments"] or {}).get("action_type")
                                      if isinstance(entry["arguments"], dict) else None}
            entry["ok"] = not (isinstance(result, dict) and "error" in result)
            entry["result"] = _summarize(result, tc.function.name)
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
        except LiveUnavailable:
            raise  # the HTTP boundary selects a saved example; never hide a cap
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
