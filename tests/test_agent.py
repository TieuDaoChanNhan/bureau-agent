"""Agent loop mechanics, with a scripted fake LLM (no API key, no cost).

These tests check the plumbing (tool dispatch, results fed back, termination),
not the quality of the model's decisions: that is measured by eval/ (T08).
"""
import json
import unittest

from bureau.agent.loop import resolve_issue
from bureau.core.detect import detect_issues
from bureau.core.loader import load_event
from tests.fake_llm import FakeClient

PROPOSAL = {
    "action_type": "LINK_PAYMENT",
    "title": "Link payment f90 to Antoine Nguyen?",
    "description": "Score 0.91: please confirm before linking.",
    "evidence": [{"source_type": "payment", "source_id": "f90", "description": "A. Nguyen, nguyen.a@gmail.com"}],
    "checks": [{"name": "identity score >= 0.98", "passed": False, "detail": "0.91"}],
    "confidence": 0.91,
    "payload": {"payment_id": "f90", "participant_id": "p01"},
}


def message_issue(state, message_id="m01"):
    return next(i for i in detect_issues(state) if i.id == f"message:{message_id}")


class AgentLoopTests(unittest.TestCase):
    def test_tool_results_are_sent_back_and_proposal_ends_the_loop(self):
        state = load_event("hackathon")
        issue = message_issue(state)
        client = FakeClient([
            [("get_participant", {"id_or_email": "a.nguyen@polytechnique.edu"})],
            [("match_person", {"payment_id": "f90"})],
            [("propose_action", PROPOSAL)],
        ])
        action = resolve_issue(state, issue, client=client, verbose=False)

        self.assertEqual(action.action_type, "LINK_PAYMENT")
        self.assertEqual(action.evidence[0].source_id, "f90")
        self.assertEqual(issue.status, "proposed")
        self.assertIn(action, state.actions)
        # The match_person result (computed in code) was returned to the model.
        tool_msgs = [m for m in client.requests[-1]["messages"] if m["role"] == "tool"]
        self.assertEqual(json.loads(tool_msgs[-1]["content"])[0]["participant_id"], "p01")

    def test_escalation_marks_issue_as_needing_a_human(self):
        state = load_event("hackathon")
        issue = message_issue(state, "m04")
        client = FakeClient([[("propose_action", {**PROPOSAL, "action_type": "ESCALATE", "payload": {}})]])
        resolve_issue(state, issue, client=client, verbose=False)
        self.assertEqual(issue.status, "needs_human")

    def test_text_answer_gets_a_reminder_to_propose(self):
        state = load_event("hackathon")
        client = FakeClient(["I think we should link it.", [("propose_action", PROPOSAL)]])
        resolve_issue(state, message_issue(state), client=client, verbose=False)
        self.assertIn("propose_action", client.requests[1]["messages"][-1]["content"])

    def test_tool_error_is_reported_to_the_model_not_raised(self):
        state = load_event("hackathon")
        client = FakeClient([[("match_person", {"payment_id": "does-not-exist"})],
                             [("propose_action", PROPOSAL)]])
        resolve_issue(state, message_issue(state), client=client, verbose=False)
        tool_msg = [m for m in client.requests[-1]["messages"] if m["role"] == "tool"][-1]
        self.assertIn("error", json.loads(tool_msg["content"]))

    def test_gives_up_after_max_steps(self):
        state = load_event("hackathon")
        client = FakeClient([[("check_groups", {})]] * 3)
        with self.assertRaises(RuntimeError):
            resolve_issue(state, message_issue(state), client=client, verbose=False, max_steps=3)


if __name__ == "__main__":
    unittest.main()
