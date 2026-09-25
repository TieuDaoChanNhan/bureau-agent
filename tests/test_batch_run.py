"""T09 batch agent runner tests using the scripted fake LLM."""
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from bureau.core.models import Issue, ProposedAction


def _fake_resolve(state, issue, verbose=True, client=None, max_steps=8):
    a = ProposedAction(
        id=f"hackathon:{issue.id}", event_id="hackathon", issue_id=issue.id,
        action_type="LINK_PAYMENT", title="t", description="d",
        evidence=[], checks=[], payload={},
    )
    state.actions.append(a)
    issue.status = "proposed"
    return a


"""T09 batch agent runner tests using the scripted fake LLM."""
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from bureau.agent.loop import run_pending
from bureau.core.loader import load_event
from bureau.core.models import Issue
from tests.fake_llm import FakeClient

PROPOSAL = {
    "action_type": "ESCALATE",
    "title": "Need an organizer decision",
    "description": "Please decide.",
    "evidence": [],
    "checks": [],
    "payload": {},
}


def _client_for(count: int) -> FakeClient:
    return FakeClient([[('propose_action', PROPOSAL)] for _ in range(count)])


class BatchRunTests(unittest.TestCase):
    def _run_in_temp_runtime(self, issues: list[Issue], client: FakeClient):
        from bureau.core import store

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(store, "RUNTIME_DIR", pathlib.Path(tmp)), \
                 patch("bureau.agent.loop.detect_issues", return_value=issues):
                state = load_event("hackathon")
                state.issues = list(issues)
                first = run_pending(state, client=client, verbose=False)
                second = run_pending(state, client=client, verbose=False)
        return first, second, state

    def test_running_twice_does_not_duplicate_proposals(self):
        """The second batch run must not send already-proposed issues to the LLM."""
        issues = [
            Issue(id="issue:one", kind="unprocessed_message", blocking=False, title="One", status="open"),
            Issue(id="issue:two", kind="unprocessed_message", blocking=False, title="Two", status="open"),
        ]
        client = _client_for(2)

        first, second, state = self._run_in_temp_runtime(issues, client)

        self.assertEqual(2, len(first))
        self.assertEqual(0, len(second))
        self.assertEqual(2, len(state.actions))
        self.assertEqual(2, len(client.requests))

    def test_unresolved_dependency_is_not_sent_to_agent(self):
        """A dependent issue remains untouched until its prerequisite is terminal."""
        issues = [
            Issue(id="prerequisite", kind="no_logistics_plan", blocking=True,
                  title="Plan travel", status="open"),
            Issue(id="dependent", kind="unprocessed_message", blocking=False,
                  title="Book rooms", status="open", depends_on=["prerequisite"]),
            Issue(id="runnable", kind="unprocessed_message", blocking=False,
                  title="Reply", status="open"),
        ]
        client = _client_for(1)

        first, second, state = self._run_in_temp_runtime(issues, client)

        self.assertEqual(["runnable"], [action.issue_id for action in first])
        self.assertEqual([], second)
        self.assertEqual("open", next(issue for issue in state.issues if issue.id == "dependent").status)
        self.assertEqual(1, len(client.requests))
