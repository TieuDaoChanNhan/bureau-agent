"""A scripted stand-in for the OpenAI client, to test the agent loop without an API key.

Usage:
    client = FakeClient([
        [("match_person", {"payment_id": "f90"})],          # step 1: one tool call
        [("propose_action", {...})],                        # step 2: final proposal
    ])
    resolve_issue(state, issue, client=client, verbose=False)

Each step is a list of (tool_name, arguments) tool calls, or a string for a plain
text answer. `client.requests` keeps every request so tests can inspect the
messages sent back to the model (e.g. tool results).
"""
from __future__ import annotations

import copy
import json
from types import SimpleNamespace


class FakeClient:
    def __init__(self, script: list):
        self.script = list(script)
        self.requests: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(copy.deepcopy(kwargs))  # snapshot: the loop keeps mutating messages
        step = self.script.pop(0)
        if isinstance(step, str):
            message = SimpleNamespace(content=step, tool_calls=None, refusal=None)
        else:
            calls = [SimpleNamespace(id=f"call_{len(self.requests)}_{i}", type="function",
                                     function=SimpleNamespace(name=name, arguments=json.dumps(args)))
                     for i, (name, args) in enumerate(step)]
            message = SimpleNamespace(content=None, tool_calls=calls, refusal=None)
        # finish_reason/refusal match the real SDK; structured extraction (T10) checks them.
        return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")])


class FakeStructuredClient:
    """One structured completion, including refusal/truncation failure modes."""

    def __init__(self, content, *, refusal=None, finish_reason="stop"):
        self.content = content
        self.refusal = refusal
        self.finish_reason = finish_reason
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(copy.deepcopy(kwargs))
        if isinstance(self.content, Exception):
            raise self.content
        content = json.dumps(self.content) if isinstance(self.content, dict) else self.content
        message = SimpleNamespace(content=content, refusal=self.refusal)
        return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason=self.finish_reason)])
