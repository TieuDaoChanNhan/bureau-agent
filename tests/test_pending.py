"""Expected behaviour of modules that are not written yet.

Each test is skipped until its task is done. Whoever takes the task removes the
@skip and makes the test pass (more tests are welcome).
"""
import json
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

    def test_actions_saved_before_traces_existed_still_load(self):
        from bureau.core.store import load_state
        path = Path(self._tmp.name) / "hackathon" / "actions.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps([{
            "id": "hackathon:message:m02", "event_id": "hackathon", "issue_id": "message:m02",
            "action_type": "SEND_MESSAGE", "title": "t", "description": "d",
            "payload": {"to": "x@example.org", "text": "hi"},
        }]), encoding="utf-8")
        self.assertEqual(load_state("hackathon").actions[0].trace, [])

    def test_trace_round_trips_through_the_store(self):
        from bureau.core.models import ProposedAction
        from bureau.core.store import load_state, save_state
        state = load_event("hackathon")
        trace = [{"step": 1, "tool": "search_rules", "arguments": {"query": "team size"}, "result": "1 result", "ok": True}]
        state.actions = [ProposedAction(id="hackathon:x", event_id="hackathon", issue_id="x", action_type="ESCALATE",
                                        title="t", description="d", trace=trace)]
        save_state(state)
        self.assertEqual(load_state("hackathon").actions[0].trace, trace)

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


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        # Point runtime/ at a scratch directory so tests never touch the real one.
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = mock.patch("bureau.core.store.RUNTIME_DIR", Path(self._tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)

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
        moved_once = apply(state, action)
        with self.assertRaises(InvariantViolation):
            apply(moved_once, ProposedAction(**{**action.__dict__, "id": "a3",
                                                          "payload": {"participant_id": "p14", "from_group": None,
                                                                      "to_group": "t-orbit"}}))
        # the state passed to the rejected apply() is left untouched
        t_orbit = next(g for g in moved_once.groups if g.id == "t-orbit")
        self.assertEqual(t_orbit.members, ["p02", "p03", "p04", "p13"])

    def test_send_message_appends_edited_text_to_outbox(self):
        from bureau.core.executor import apply
        from bureau.core.models import ProposedAction
        state = load_event("hackathon")
        action = ProposedAction(id="a4", event_id="hackathon", issue_id="message:m01",
                                action_type="SEND_MESSAGE", title="", description="",
                                payload={"to": "p01", "text": "draft text"})
        apply(state, action, edited_description="final text, approved by a human")
        outbox = json.loads((Path(self._tmp.name) / "hackathon" / "outbox.json").read_text(encoding="utf-8"))
        entry = outbox[-1]
        self.assertEqual(entry["action_id"], "a4")
        self.assertEqual(entry["to"], "p01")
        self.assertEqual(entry["text"], "final text, approved by a human")
        self.assertIn("sent_at", entry)  # stamped by store.append_outbox

    def test_update_groups_replaces_groups_of_that_kind(self):
        from bureau.core.executor import apply
        from bureau.core.models import ProposedAction
        state = load_event("hackathon")
        action = ProposedAction(id="a5", event_id="hackathon", issue_id="solo_participants",
                                action_type="UPDATE_GROUPS", title="", description="",
                                payload={"groups": [
                                    {"id": "t-newteam", "kind": "team", "name": "NewTeam",
                                     "members": ["p13", "p14", "p15"], "capacity_min": 2, "capacity_max": 4},
                                ]})
        new_state = apply(state, action)
        self.assertEqual([g.id for g in new_state.groups if g.kind == "team"], ["t-newteam"])

    def test_select_travel_plan_sets_logistics(self):
        from bureau.core.executor import apply
        from bureau.core.models import ProposedAction
        state = load_event("wei")
        option = {"id": "A", "cost_per_person_cents": 11200}
        action = ProposedAction(id="a6", event_id="wei", issue_id="no_logistics_plan",
                                action_type="SELECT_TRAVEL_PLAN", title="", description="",
                                payload={"options": [{"option": option, "checks": [], "valid": True}]})
        new_state = apply(state, action, option_id="A")
        self.assertEqual(new_state.logistics, option)

    def test_escalate_marks_the_issue_resolved_without_changing_data(self):
        from bureau.core.executor import apply
        from bureau.core.models import ProposedAction
        state = load_event("hackathon")
        state.issues = detect_issues(state)
        target = state.issues[0]
        action = ProposedAction(id="a7", event_id="hackathon", issue_id=target.id,
                                action_type="ESCALATE", title="", description="",
                                payload={"note": "ask organizer"})
        new_state = apply(state, action)
        self.assertEqual(new_state.issue(target.id).status, "resolved")
        self.assertEqual(new_state.issue(target.id).resolved_by_action_id, "a7")
        self.assertEqual(new_state.participants, state.participants)


if __name__ == "__main__":
    unittest.main()
