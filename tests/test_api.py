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
        agent = mock.patch("bureau.agent.loop.resolve_issue", side_effect=self.fake_resolve)
        self.agent = agent.start()
        self.addCleanup(agent.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    @staticmethod
    def fake_resolve(state, issue, verbose=False, client=None):
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

    def test_new_message_becomes_an_issue_that_survives_reload(self):
        body = {"sender": "parent@example.org", "channel": "email", "text": "Is lunch provided on Saturday?"}
        response = self.client.post("/api/events/hackathon/messages", json=body)
        self.assertEqual(201, response.status_code, response.text)
        issue_id = response.json()["issue_id"]
        self.assertEqual("message:live01", issue_id)
        again = self.client.get("/api/events/hackathon").json()
        issue = next(i for i in again["issues"] if i["id"] == issue_id)
        self.assertEqual("Is lunch provided on Saturday?", issue["details"]["text"])
        self.assertEqual("open", issue["status"])
        second = self.client.post("/api/events/hackathon/messages", json=body).json()
        self.assertEqual("message:live02", second["issue_id"])

    def test_new_message_is_removed_by_reset(self):
        self.client.post("/api/events/hackathon/messages", json={"sender": "a@example.org", "text": "Hello"})
        self.client.post("/api/events/hackathon/reset")
        ids = [i["id"] for i in self.client.get("/api/events/hackathon").json()["issues"]]
        self.assertNotIn("message:live01", ids)

    def test_new_message_rejects_invalid_input(self):
        for body in ({"sender": "a@example.org", "text": ""}, {"sender": "a@example.org", "text": "   "},
                     {"sender": "", "text": "Hi"}, {"sender": "a@example.org", "text": "x" * 4001},
                     {"sender": "a@example.org", "text": "Hi", "channel": "sms"}):
            with self.subTest(body=body):
                self.assertEqual(422, self.client.post("/api/events/hackathon/messages", json=body).status_code)
        self.assertEqual(404, self.client.post("/api/events/nope/messages",
                                               json={"sender": "a", "text": "b"}).status_code)

    def test_new_message_can_be_run_by_the_agent(self):
        issue_id = self.client.post("/api/events/hackathon/messages",
                                    json={"sender": "a@example.org", "text": "Can we use Python?"}).json()["issue_id"]
        with mock.patch("bureau.config.OPENAI_API_KEY", "fake-test-key"):
            response = self.client.post(f"/api/events/hackathon/run?issue_id={issue_id}")
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual([issue_id], [a["issue_id"] for a in response.json()["actions"]])

    WEI_EXTRACTED = {"hard": {"participants": 40, "max_cost_per_person_cents": 12000, "arrive_before": "21:00",
                              "no_overnight": True, "step_free_rooms": 2},
                     "soft": ["fewer_changes", "near_station", "early_return"],
                     "organizer_verified": ["step_free_rooms"], "clarifications": []}

    def plan(self, body=None, clarifications=(), explanation="Option F is the direct train; Option D is cheaper but has one change."):
        """POST /plan with a scripted planner client: extraction JSON, then the explanation."""
        from tests.fake_llm import FakeClient
        extracted = {**self.WEI_EXTRACTED, "clarifications": list(clarifications)}
        self.planner_client = FakeClient([json.dumps(extracted), explanation])
        with mock.patch("api.main._planner_client", return_value=self.planner_client):
            return self.client.post("/api/events/wei/plan", json=body or {})

    def plan_action(self, response):
        return next(a for a in response.json()["actions"] if a["id"] == response.json()["action_id"])

    def test_plan_with_requested_budget_proposes_valid_options(self):
        response = self.plan()
        self.assertEqual(200, response.status_code, response.text)
        action = self.plan_action(response)
        self.assertEqual("SELECT_TRAVEL_PLAN", action["action_type"])
        self.assertGreaterEqual(len(action["payload"]["ranked_valid"]), 1)
        self.assertEqual(12000, action["payload"]["constraints"]["hard"]["max_cost_per_person_cents"])
        self.assertEqual("llm", action["payload"]["constraints_source"])
        self.assertEqual("F", action["payload"]["ranked_valid"][0])   # Jinko hotels (replay) x recorded transport
        self.assertTrue(action["description"].startswith("Option F is the direct train"))
        self.assertIn("jinko:replay", action["payload"]["options"][0]["option"]["source"])
        self.assertEqual("proposed", next(i for i in response.json()["issues"]
                                          if i["id"] == "no_logistics_plan")["status"])

    def test_plan_what_if_budget_escalates_with_suggestions_and_replaces_the_proposal(self):
        self.plan()
        response = self.plan({"overrides": {"max_cost_per_person_cents": 9000}})
        self.assertEqual(200, response.status_code, response.text)
        plans = [a for a in response.json()["actions"] if a["issue_id"] == "no_logistics_plan"]
        self.assertEqual(["ESCALATE"], [a["action_type"] for a in plans])
        self.assertTrue(plans[0]["payload"]["suggestions"])

    def test_plan_asks_clarifications_before_searching_and_accepts_answers(self):
        question = "Does the €120 budget include meals?"
        response = self.plan(clarifications=[question])
        action = self.plan_action(response)
        self.assertEqual("ESCALATE", action["action_type"])
        self.assertEqual([question], action["payload"]["clarifications"])
        self.assertNotIn("options", action["payload"])           # nothing searched yet
        answered = action["payload"]["request_text"] + "\n\nOrganizer answers: No, travel and lodging only."
        response = self.plan({"text": answered})
        self.assertEqual("SELECT_TRAVEL_PLAN", self.plan_action(response)["action_type"])
        sent = json.loads(self.planner_client.requests[0]["messages"][1]["content"])
        self.assertTrue(sent["text"].endswith("travel and lodging only."))

    def test_plan_without_a_key_is_503_unless_recorded_constraints_are_requested(self):
        with mock.patch("api.main._planner_client", return_value=None):
            self.assertEqual(503, self.client.post("/api/events/wei/plan").status_code)
            response = self.client.post("/api/events/wei/plan", json={"recorded": True})
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual("recorded", self.plan_action(response)["payload"]["constraints_source"])

    def test_unusable_extraction_is_422_and_changes_nothing(self):
        from tests.fake_llm import FakeClient
        with mock.patch("api.main._planner_client", return_value=FakeClient(['{"hard": {}}'])):
            response = self.client.post("/api/events/wei/plan")
        self.assertEqual(422, response.status_code, response.text)
        self.assertEqual([], [a for a in self.client.get("/api/events/wei").json()["actions"]])

    def test_choosing_a_valid_option_unlocks_dependent_issues(self):
        plan = self.plan().json()
        before = {i["id"]: i for i in plan["issues"]}
        self.assertEqual(["no_logistics_plan"], before["unpaid_participation"]["depends_on"])
        best = next(a for a in plan["actions"] if a["id"] == plan["action_id"])["payload"]["ranked_valid"][0]
        response = self.client.post(f"/api/actions/{plan['action_id']}/approve", json={"option_id": best})
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual(best, response.json()["logistics"]["id"])
        self.assertNotIn("no_logistics_plan", [i["id"] for i in response.json()["issues"]])
        self.assertEqual(409, self.plan().status_code)

    def test_plan_rejects_bad_overrides_and_events_without_travel(self):
        for overrides in ({"budget": 9000}, {"max_cost_per_person_cents": "90"}, {"no_overnight": 1}):
            with self.subTest(overrides=overrides):
                self.assertEqual(422, self.plan({"overrides": overrides}).status_code)
        self.assertEqual(409, self.client.post("/api/events/hackathon/plan").status_code)
        self.assertEqual(404, self.client.post("/api/events/nope/plan").status_code)

    def test_summary_carries_event_context_for_the_cards(self):
        meta = self.client.get("/api/events/wei").json()["meta"]
        self.assertEqual("Integration weekend", meta["type"])
        self.assertEqual(8, meta["participants"])

    def test_summary_carries_display_names_for_ids(self):
        records = self.client.get("/api/events/hackathon").json()["records"]
        self.assertEqual("Antoine Nguyen", records["participants"]["p01"])
        self.assertEqual("NeuralNomads", records["groups"]["t-nomads"])
        self.assertEqual("A. Nguyen · 10.00 EUR", records["payments"]["f90"])

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
            first = self.client.post("/api/events/hackathon/run?limit=100")
        self.agent.reset_mock()
        second = self.client.post("/api/events/hackathon/run?limit=100")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json(), first.json())
        self.agent.assert_not_called()

    def test_run_limit_reports_remaining_and_continues_without_duplicates(self):
        """Each limited API batch handles only its slice of the shared runner queue."""
        with mock.patch("bureau.config.OPENAI_API_KEY", "fake-test-key"):
            first = self.client.post("/api/events/hackathon/run?limit=2")
            second = self.client.post("/api/events/hackathon/run?limit=2")

        self.assertEqual(200, first.status_code, first.text)
        self.assertEqual(200, second.status_code, second.text)
        self.assertEqual(2, len(first.json()["actions"]))
        self.assertEqual(4, len(second.json()["actions"]))
        self.assertEqual(first.json()["remaining"] - 2, second.json()["remaining"])
        action_ids = [action["id"] for action in second.json()["actions"]]
        self.assertEqual(len(action_ids), len(set(action_ids)))

    def test_run_persists_neighbors_when_the_third_agent_call_fails(self):
        """A transient agent error is logged and does not discard other proposals."""
        calls = 0

        def fail_third(state, issue, verbose=False, client=None):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise RuntimeError("rate limit")
            return self.fake_resolve(state, issue, verbose=verbose, client=client)

        self.agent.side_effect = fail_third
        with mock.patch("bureau.config.OPENAI_API_KEY", "fake-test-key"):
            response = self.client.post("/api/events/hackathon/run?limit=4")

        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual(3, len(response.json()["actions"]))
        self.assertEqual(1, len(response.json()["errors"]))
        self.assertEqual(3, len(store.load_state("hackathon").actions))
        log = [json.loads(line) for line in (self.runtime / "hackathon" / "log.jsonl").read_text().splitlines()]
        self.assertEqual("agent_error", log[0]["type"])
        self.assertEqual("rate limit", log[0]["error"])

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
