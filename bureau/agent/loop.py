"""The event agent: one orchestrator that investigates an issue with tools and
ends by proposing exactly one action. It never executes actions itself.

Flow for one issue:
    issue JSON -> LLM -> tool calls -> tool results -> ... -> propose_action -> ProposedAction
"""
from __future__ import annotations

import json
from dataclasses import asdict

from .. import config
from ..core.models import Check, EventState, Evidence, Issue, ProposedAction
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
