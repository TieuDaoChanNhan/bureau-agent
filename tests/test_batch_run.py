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
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from bureau.agent.loop import run_pending
from bureau.core.loader import load_event
from bureau.core.models import Issue, ProposedAction
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


def _propose(state, issue, verbose=False, client=None) -> ProposedAction:
    action = ProposedAction(
        id=f"{state.id}:{issue.id}", event_id=state.id, issue_id=issue.id,
        action_type="ESCALATE", title="Organizer review", description="Needs review",
    )
    state.actions.append(action)
    issue.status = "needs_human"
    return action


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

        self.assertEqual(2, len(first.actions))
        self.assertEqual(0, len(second.actions))
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

        self.assertEqual(["runnable"], [action.issue_id for action in first.actions])
        self.assertEqual([], second.actions)
        self.assertEqual("open", next(issue for issue in state.issues if issue.id == "dependent").status)
        self.assertEqual(1, len(client.requests))

    def test_terminal_history_missing_from_detection_is_saved_after_a_batch(self):
        """A batch save must not discard resolved/dismissed issues from history."""
        from bureau.core import store

        terminal = [
            Issue(id="fixed", kind="unprocessed_message", blocking=False,
                  title="Fixed", status="resolved"),
            Issue(id="dismissed", kind="unprocessed_message", blocking=False,
                  title="Dismissed", status="dismissed"),
        ]
        runnable = Issue(id="new", kind="unprocessed_message", blocking=False,
                         title="New", status="open")
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(store, "RUNTIME_DIR", pathlib.Path(tmp)), \
                 patch("bureau.agent.loop.detect_issues", return_value=[runnable]), \
                 patch("bureau.agent.loop.resolve_issue", side_effect=_propose):
                state = load_event("hackathon")
                state.issues = terminal
                result = run_pending(state, verbose=False)
                saved = store.load_state("hackathon")

        self.assertEqual(["new"], [action.issue_id for action in result.actions])
        self.assertEqual("resolved", next(issue for issue in saved.issues if issue.id == "fixed").status)
        self.assertEqual("dismissed", next(issue for issue in saved.issues if issue.id == "dismissed").status)

    def test_failure_does_not_lose_other_proposals_and_is_logged(self):
        """A failed issue logs an error while successful neighbors are persisted."""
        from bureau.core import store

        issues = [
            Issue(id=f"issue:{number}", kind="unprocessed_message", blocking=False,
                  title=str(number), status="open")
            for number in range(1, 5)
        ]

        def fail_third(state, issue, verbose=False, client=None):
            if issue.id == "issue:3":
                raise RuntimeError("rate limit")
            return _propose(state, issue, verbose=verbose, client=client)

        with tempfile.TemporaryDirectory() as tmp:
            runtime = pathlib.Path(tmp)
            with patch.object(store, "RUNTIME_DIR", runtime), \
                 patch("bureau.agent.loop.detect_issues", return_value=issues), \
                 patch("bureau.agent.loop.resolve_issue", side_effect=fail_third):
                state = load_event("hackathon")
                result = run_pending(state, verbose=False)
                saved = store.load_state("hackathon")
                log = [json.loads(line) for line in (runtime / "hackathon" / "log.jsonl").read_text().splitlines()]

        self.assertEqual(["issue:1", "issue:2", "issue:4"], [action.issue_id for action in result.actions])
        self.assertEqual([{"issue_id": "issue:3", "error": "rate limit"}], result.errors)
        self.assertEqual(["issue:1", "issue:2", "issue:4"], [action.issue_id for action in saved.actions])
        self.assertEqual([{"type": "agent_error", "issue_id": "issue:3", "error": "rate limit"}], log)
