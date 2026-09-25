"""HTTP integration tests using isolated runtime storage and a fake agent."""
import copy
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from api.main import app
from bureau.config import ROOT
from bureau.core import store
from bureau.core.detect import detect_issues
from bureau.core.loader import load_event
from bureau.core.models import ProposedAction


class ApiTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.runtime = Path(tmp.name)
        patcher = mock.patch("bureau.core.store.RUNTIME_DIR", self.runtime)
        patcher.start()
        self.addCleanup(patcher.stop)
        key = mock.patch("bureau.config.OPENAI_API_KEY", "")
        key.start()
        self.addCleanup(key.stop)
        agent = mock.patch("api.main.resolve_issue", side_effect=self.fake_resolve)
        self.agent = agent.start()
        self.addCleanup(agent.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    @staticmethod
    def fake_resolve(state, issue, verbose=False):
        action = ProposedAction(
            id=f"{state.id}:{issue.id}", event_id=state.id, issue_id=issue.id,
            action_type="ESCALATE", title="Organizer review", description="Needs review",
        )
        state.actions.append(action)
        issue.status = "needs_human"
        return action

    def seed_action(self, action_type="LINK_PAYMENT", issue_id="unmatched_payment:f90", payload=None,
                    event_id="hackathon"):
        state = store.load_state(event_id)
        state.issues = store.merge_issue_status(detect_issues(state), state.issues)
        action = ProposedAction(
            id=f"{event_id}:{issue_id}", event_id=event_id, issue_id=issue_id,
            action_type=action_type, title="Review action", description="Draft description",
            payload=payload if payload is not None else {"payment_id": "f90", "participant_id": "p01"},
        )
        state.actions.append(action)
        state.issue(issue_id).status = "proposed"
        store.save_state(state)
        return action

    def post_action(self, action, operation="approve", **kwargs):
        return self.client.post(f"/api/actions/{action.id}/{operation}", **kwargs)

    def test_get_event_and_list_use_runtime_without_writing(self):
        state = load_event("hackathon")
        state.groups = []
        store.save_state(state)
        summary = self.client.get("/api/events/hackathon").json()
        self.assertNotIn("group_over_capacity:t-dragons", [i["id"] for i in summary["issues"]])
        events = self.client.get("/api/events").json()
        self.assertEqual(next(e for e in events if e["id"] == "hackathon")["counts"], summary["counts"])
        self.assertFalse((self.runtime / "wei").exists())

    def test_approve_removes_payment_issue_on_next_get(self):
        action = self.seed_action()
        response = self.post_action(action)
        self.assertEqual(response.status_code, 200, response.text)
        summary = self.client.get("/api/events/hackathon").json()
        self.assertNotIn(action.issue_id, [i["id"] for i in summary["issues"]])
        self.assertEqual(response.json(), summary)
        payment = next(p for p in store.load_state("hackathon").payments if p.id == "f90")
        self.assertEqual(payment.participant_id, "p01")

    def test_reset_restores_sample_data_and_clears_actions_outbox_and_log(self):
        baseline = self.client.get("/api/events/hackathon").json()
        action = self.seed_action(payload={"payment_id": "f90", "participant_id": "p01",
                                           "to": ["p01"], "message": "Confirmed"})
        self.assertEqual(self.post_action(action).status_code, 200)
        self.assertTrue((self.runtime / "hackathon" / "log.jsonl").exists())
        response = self.client.post("/api/events/hackathon/reset")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), baseline)
        self.assertEqual(self.client.get("/api/events/hackathon").json(), baseline)
        self.assertEqual(store.load_state("hackathon"), load_event("hackathon"))
        self.assertFalse((self.runtime / "hackathon").exists())
        self.assertEqual(self.client.get("/api/events/hackathon/outbox").json(), [])

    def test_dismiss_changes_only_issue_status(self):
        action = self.seed_action()
        before = store.load_state("hackathon")
        response = self.post_action(action, "dismiss")
        self.assertEqual(response.status_code, 200, response.text)
        expected = copy.deepcopy(before)
        expected.issue(action.issue_id).status = "dismissed"
        expected.issue(action.issue_id).resolved_by_action_id = action.id
        self.assertEqual(store.load_state("hackathon"), expected)
        self.assertEqual(self.client.get("/api/events/hackathon/outbox").json(), [])
        self.assertFalse((self.runtime / "hackathon" / "log.jsonl").exists())
        summary = self.client.get("/api/events/hackathon").json()
        self.assertEqual(next(i for i in summary["issues"] if i["id"] == action.issue_id)["status"], "dismissed")
        self.assertEqual(self.post_action(action).status_code, 409)

    def test_action_detail_matches_example_contract(self):
        example = json.loads((ROOT / "docs/api-examples/action_LINK_PAYMENT.json").read_text())
        action = store._action_from_dict(example)
        store.save_action(action)
        response = self.client.get(f"/api/actions/{action.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), example)

    def test_run_then_approve_another_action_preserves_all_proposals(self):
        existing = self.seed_action()
        with mock.patch("bureau.config.OPENAI_API_KEY", "fake-test-key"):
            response = self.client.post("/api/events/hackathon/run")
        self.assertEqual(response.status_code, 200, response.text)
        proposals = response.json()["actions"]
        self.assertGreater(len(proposals), 1)
        self.assertTrue(self.agent.called)
        self.assertEqual(self.post_action(existing).status_code, 200)
        summary = self.client.get("/api/events/hackathon").json()
        self.assertEqual(summary["actions"], proposals)

    def test_run_includes_needs_human_issues_without_a_proposal_and_never_executes(self):
        before = load_event("hackathon")
        with mock.patch("bureau.config.OPENAI_API_KEY", "fake-test-key"):
            response = self.client.post("/api/events/hackathon/run")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("unmatched_payment:f90", [a["issue_id"] for a in response.json()["actions"]])
        after = store.load_state("hackathon")
        self.assertEqual(after.payments, before.payments)
        self.assertEqual(after.groups, before.groups)
        self.assertFalse((self.runtime / "hackathon" / "log.jsonl").exists())
        self.assertEqual(store.load_outbox("hackathon"), [])

    def test_run_skips_existing_proposals_and_needs_no_key_when_nothing_remains(self):
        with mock.patch("bureau.config.OPENAI_API_KEY", "fake-test-key"):
            first = self.client.post("/api/events/hackathon/run")
        self.agent.reset_mock()
        second = self.client.post("/api/events/hackathon/run")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json(), first.json())
        self.agent.assert_not_called()

    def test_run_skips_dismissed_and_resolved_issues(self):
        dismissed = self.seed_action(issue_id="message:m01", action_type="ESCALATE", payload={})
        resolved = self.seed_action(issue_id="message:m02", action_type="ESCALATE", payload={})
        self.post_action(dismissed, "dismiss")
        self.post_action(resolved)
        with mock.patch("bureau.config.OPENAI_API_KEY", "fake-test-key"):
            self.assertEqual(self.client.post("/api/events/hackathon/run").status_code, 200)
        targeted = {call.args[1].id for call in self.agent.call_args_list}
        self.assertTrue(targeted)
        self.assertTrue(targeted.isdisjoint({dismissed.issue_id, resolved.issue_id}))

    def test_run_skips_planner_and_issues_waiting_for_logistics(self):
        with mock.patch("bureau.config.OPENAI_API_KEY", "fake-test-key"):
            response = self.client.post("/api/events/wei/run")
        self.assertEqual(response.status_code, 200)
        for call in self.agent.call_args_list:
            issue = call.args[1]
            self.assertNotEqual(issue.kind, "no_logistics_plan")
            self.assertEqual(issue.depends_on, [])

    def test_run_without_key_returns_503_without_writing(self):
        response = self.client.post("/api/events/hackathon/run")
        self.assertEqual(response.status_code, 503)
        self.agent.assert_not_called()
        self.assertEqual(list(self.runtime.iterdir()), [])

    def test_approved_reply_has_edited_text_and_timezone(self):
        action = self.seed_action(payload={"payment_id": "f90", "participant_id": "p01",
                                           "to": ["p01"], "message": "Draft"})
        response = self.post_action(action, json={"edited_description": "Approved reply"})
        self.assertEqual(response.status_code, 200)
        outbox = self.client.get("/api/events/hackathon/outbox").json()
        self.assertEqual(len(outbox), 1)
        self.assertEqual(outbox[0]["text"], "Approved reply")
        self.assertEqual(outbox[0]["action_id"], action.id)
        self.assertEqual(outbox[0]["to"], ["p01"])
        self.assertIsNotNone(datetime.fromisoformat(outbox[0]["sent_at"]).tzinfo)

    def test_repeated_approval_is_rejected_after_issue_disappears_and_other_writes(self):
        action = self.seed_action(payload={"payment_id": "f90", "participant_id": "p01",
                                           "to": ["p01"], "message": "Confirmed"})
        other = self.seed_action(issue_id="message:m02", action_type="ESCALATE", payload={})
        self.assertEqual(self.post_action(action).status_code, 200)
        self.assertEqual(self.post_action(other, "dismiss").status_code, 200)
        with mock.patch("bureau.config.OPENAI_API_KEY", "fake-test-key"):
            self.assertEqual(self.client.post("/api/events/hackathon/run").status_code, 200)
        self.assertEqual(self.post_action(action).status_code, 409)
        self.assertEqual(self.post_action(action, "dismiss").status_code, 409)
        self.assertEqual(len(store.load_outbox("hackathon")), 1)
        self.assertEqual(len((self.runtime / "hackathon" / "log.jsonl").read_text().splitlines()), 1)

    def test_invalid_travel_selection_returns_409_without_persisting(self):
        action = self.seed_action(event_id="wei", issue_id="no_logistics_plan",
                                  action_type="SELECT_TRAVEL_PLAN",
                                  payload={"options": [{"option": {"id": "C"}, "valid": False}]})
        before = store.load_state("wei")
        response = self.post_action(action, json={"option_id": "C"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(store.load_state("wei"), before)
        self.assertFalse((self.runtime / "wei" / "log.jsonl").exists())

    def test_valid_travel_selection_unlocks_dependent_issues_in_response(self):
        action = self.seed_action(event_id="wei", issue_id="no_logistics_plan",
                                  action_type="SELECT_TRAVEL_PLAN",
                                  payload={"options": [{"option": {"id": "A"}, "valid": True}]})
        response = self.post_action(action, json={"option_id": "A"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.client.get("/api/events/wei").json())
        self.assertNotIn("no_logistics_plan", [i["id"] for i in response.json()["issues"]])
        self.assertTrue(all(not i["depends_on"] for i in response.json()["issues"]))

    def test_unknown_participant_returns_422_without_persisting(self):
        action = self.seed_action(payload={"payment_id": "f90", "participant_id": "missing"})
        before = store.load_state("hackathon")
        self.assertEqual(self.post_action(action).status_code, 422)
        self.assertEqual(store.load_state("hackathon"), before)

    def test_missing_action_payload_field_returns_422_without_side_effects(self):
        action = self.seed_action(payload={"participant_id": "p01"})
        before = store.load_state("hackathon")
        self.assertEqual(self.post_action(action).status_code, 422)
        self.assertEqual(store.load_state("hackathon"), before)
        self.assertEqual(store.load_outbox("hackathon"), [])
        self.assertFalse((self.runtime / "hackathon" / "log.jsonl").exists())

    def test_stale_proposal_cannot_be_approved_or_dismissed(self):
        action = self.seed_action()
        state = store.load_state("hackathon")
        next(p for p in state.payments if p.id == "f90").participant_id = "p01"
        store.save_state(state)
        for operation in ("approve", "dismiss"):
            self.assertEqual(self.post_action(action, operation).status_code, 409)
        self.assertEqual(store.load_state("hackathon"), state)

    def test_malformed_approval_body_returns_422(self):
        action = self.seed_action()
        for body in ({"edited_description": []}, {"option_id": 123}, []):
            with self.subTest(body=body):
                self.assertEqual(self.post_action(action, json=body).status_code, 422)

    def test_unknown_events_and_actions_return_404(self):
        for method, path in (
            ("GET", "/api/events/missing"), ("POST", "/api/events/missing/run"),
            ("POST", "/api/events/missing/reset"), ("GET", "/api/events/missing/outbox"),
            ("GET", "/api/actions/missing:x"), ("GET", "/api/actions/hackathon:missing"),
            ("POST", "/api/actions/hackathon:missing/approve"),
            ("POST", "/api/actions/hackathon:missing/dismiss"),
        ):
            with self.subTest(method=method, path=path):
                self.assertEqual(self.client.request(method, path).status_code, 404)
