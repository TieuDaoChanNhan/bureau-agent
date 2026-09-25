"""Expected behaviour of modules that are not written yet.

Each test is skipped until its task is done. Whoever takes the task removes the
@skip and makes the test pass (more tests are welcome).
"""
import unittest

from bureau.core.detect import detect_issues
from bureau.core.loader import load_event


@unittest.skip("TASK T02: store")
class StoreTests(unittest.TestCase):
    def test_statuses_survive_re_detection(self):
        from bureau.core.store import merge_issue_status
        state = load_event("hackathon")
        stored = detect_issues(state)
        stored[0].status = "resolved"
        merged = merge_issue_status(detect_issues(state), stored)
        self.assertEqual(next(i for i in merged if i.id == stored[0].id).status, "resolved")


@unittest.skip("TASK T03: executor")
class ExecutorTests(unittest.TestCase):
    def test_link_payment_removes_the_issue(self):
        from bureau.core.executor import apply
        from bureau.core.models import ProposedAction
        state = load_event("hackathon")
        action = ProposedAction(id="a1", event_id="hackathon", issue_id="unmatched_payment:f90",
                                action_type="LINK_PAYMENT", title="", description="",
                                payload={"payment_id": "f90", "participant_id": "p01"})
        new_state = apply(state, action)
        self.assertNotIn("unmatched_payment:f90", [i.id for i in detect_issues(new_state)])

    def test_action_breaking_an_invariant_is_refused(self):
        from bureau.core.executor import InvariantViolation, apply
        from bureau.core.models import ProposedAction
        state = load_event("hackathon")
        action = ProposedAction(id="a2", event_id="hackathon", issue_id="x", action_type="MOVE_MEMBER",
                                title="", description="",
                                payload={"participant_id": "p13", "from_group": None, "to_group": "t-orbit"})
        with self.assertRaises(InvariantViolation):
            apply(apply(state, action), ProposedAction(**{**action.__dict__, "id": "a3",
                                                          "payload": {"participant_id": "p14", "from_group": None,
                                                                      "to_group": "t-orbit"}}))


if __name__ == "__main__":
    unittest.main()
