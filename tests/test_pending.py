"""Expected behaviour of modules that are not written yet.

Each test is skipped until its task is done. Whoever takes the task removes the
@skip and makes the test pass (more tests are welcome).
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bureau.core.detect import detect_issues
from bureau.core.loader import load_event


class StoreTests(unittest.TestCase):
    def setUp(self):
        # Point runtime/ at a scratch directory so tests never touch the real one.
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = mock.patch("bureau.core.store.RUNTIME_DIR", Path(self._tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_statuses_survive_re_detection(self):
        from bureau.core.store import merge_issue_status
        state = load_event("hackathon")
        stored = detect_issues(state)
        stored[0].status = "resolved"
        merged = merge_issue_status(detect_issues(state), stored)
        self.assertEqual(next(i for i in merged if i.id == stored[0].id).status, "resolved")

    def test_issue_no_longer_detected_disappears_after_merge(self):
        from bureau.core.store import merge_issue_status
        state = load_event("hackathon")
        stored = detect_issues(state)
        detected_again = [i for i in stored if i.id != stored[0].id]  # simulate it being fixed
        merged = merge_issue_status(detected_again, stored)
        self.assertNotIn(stored[0].id, [i.id for i in merged])

    def test_save_state_then_load_state_round_trips(self):
        from bureau.core.store import load_state, save_state
        state = load_event("hackathon")
        state.payments[0].participant_id = "p01"
        save_state(state)

        loaded = load_state("hackathon")

        self.assertEqual(len(loaded.participants), len(state.participants))
        self.assertEqual(len(loaded.payments), len(state.payments))
        self.assertEqual(loaded.payments[0].participant_id, "p01")
        self.assertEqual(
            {g.id: sorted(g.members) for g in loaded.groups},
            {g.id: sorted(g.members) for g in state.groups},
        )

    def test_save_state_then_load_state_keeps_travel_and_logistics(self):
        from bureau.core.store import load_state, save_state
        state = load_event("wei")
        state.logistics = {"option_id": "opt-1"}
        save_state(state)

        loaded = load_state("wei")

        self.assertEqual(loaded.travel, state.travel)
        self.assertEqual(loaded.logistics, state.logistics)

    def test_reset_then_load_state_returns_sample_data(self):
        from bureau.core.store import load_state, reset, save_state
        state = load_event("hackathon")
        state.participants = state.participants[:1]
        save_state(state)

        reset("hackathon")
        loaded = load_state("hackathon")

        sample = load_event("hackathon")
        self.assertEqual(len(loaded.participants), len(sample.participants))
        self.assertEqual(loaded.issues, [])
        self.assertEqual(loaded.actions, [])


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
