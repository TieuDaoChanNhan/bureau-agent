"""T24 eligibility and confirmed batches; temporary storage, no model calls."""
import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from bureau.agent.loop import _action_from_args
from bureau.core import bulk_approval, store
from bureau.core.detect import detect_issues
from bureau.core.executor import InvariantViolation, apply
from bureau.core.loader import load_event
from bureau.core.models import Check, Evidence
from demo.replay import issue_example


def sample_state():
    state = load_event("hackathon")
    state.issues = detect_issues(state)
    for mid in ("m02", "m07", "m18"):
        issue = state.issue(f"message:{mid}")
        state.actions.append(issue_example(state, issue))
        issue.status = "proposed"
    return state


class BulkEligibilityTests(unittest.TestCase):
    def setUp(self):
        self.state = sample_state()
        self.action = self.state.actions[0]

    def test_rule_reply_is_eligible_and_preview_does_not_mutate_state(self):
        before = copy.deepcopy(self.state)
        preview = bulk_approval.preview(self.state)
        self.assertEqual(3, len(preview))
        self.assertEqual(self.action.payload["text"], preview[0]["text"])
        self.assertEqual(["§7"], preview[0]["rules"])
        self.assertEqual(before, self.state)

    def test_uncertain_or_sensitive_proposals_are_excluded(self):
        def change_rule(a, section):
            a.evidence = [Evidence("rule", section, "A cited rule")]

        cases = {
            "payment": lambda a: setattr(a, "action_type", "LINK_PAYMENT"),
            "escalation": lambda a: setattr(a, "action_type", "ESCALATE"),
            "inference": lambda a: setattr(a, "confidence", 0.99),
            "zero confidence": lambda a: setattr(a, "confidence", 0),
            "no human approval": lambda a: setattr(a, "requires_approval", False),
            "empty checks": lambda a: setattr(a, "checks", []),
            "failed check": lambda a: setattr(a, "checks", [Check("rule", False)]),
            "unverified": lambda a: setattr(a, "checks", [Check("rule", True, verified=False)]),
            "truthy passed": lambda a: setattr(a, "checks", [Check("rule", "true")]),
            "truthy verified": lambda a: setattr(a, "checks", [Check("rule", True, verified=1)]),
            "incomplete check": lambda a: setattr(a, "checks", [Check("", True)]),
            "malformed detail": lambda a: setattr(a, "checks", [Check("rule", True, detail=None)]),
            "missing evidence": lambda a: setattr(a, "evidence", []),
            "malformed evidence": lambda a: setattr(a, "evidence", [Evidence("rule", ["§7"], "")]),
            "unknown rule": lambda a: change_rule(a, "§999"),
            "financial rule": lambda a: change_rule(a, "§3"),
            "privacy rule": lambda a: change_rule(a, "§10"),
            "personal record": lambda a: a.evidence.append(Evidence("participant", "p01", "Record")),
            "other message": lambda a: a.evidence.append(Evidence("message", "m01", "Other message")),
            "other recipient": lambda a: a.payload.update(to="other@example.org"),
            "several recipients": lambda a: a.payload.update(to=[a.payload["to"], "other@example.org"]),
            "extra payload": lambda a: a.payload.update(participant_id="p01"),
            "blank draft": lambda a: a.payload.update(text=" "),
            "identity lookup": lambda a: a.trace.append({"tool": "match_person", "ok": True}),
            "failed lookup": lambda a: a.trace.append({"tool": "search_rules", "ok": False}),
            "malformed trace": lambda a: a.trace.append(None),
            "financial prose": lambda a: a.payload.update(text="Your payment is confirmed."),
            "financial French": lambda a: a.payload.update(text="Votre remboursement est confirmé."),
            "identity prose": lambda a: a.payload.update(text="Your identity is confirmed."),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                action = copy.deepcopy(self.action)
                mutate(action)
                self.assertIsNotNone(bulk_approval.reply_problem(self.state, action))

    def test_resolved_missing_and_blocked_issues_are_excluded(self):
        issue = self.state.issue(self.action.issue_id)
        for status in ("open", "needs_human", "resolved", "dismissed", "agent_failed"):
            with self.subTest(status=status):
                issue.status = status
                self.assertIsNotNone(bulk_approval.reply_problem(self.state, self.action))
        issue.status = "proposed"
        for dependencies in (["missing"], ["message:m07"]):
            issue.depends_on = dependencies
            self.assertIsNotNone(bulk_approval.reply_problem(self.state, self.action))
        self.state.issues.remove(issue)
        self.assertIsNotNone(bulk_approval.reply_problem(self.state, self.action))

    def test_financial_source_message_and_removed_rule_are_excluded(self):
        message = next(m for m in self.state.messages if m.id == "m02")
        message.text = "Please refund me."
        self.assertIsNotNone(bulk_approval.reply_problem(self.state, self.action))
        message.text = "Can I build on my existing project?"
        self.state.rules = [r for r in self.state.rules if r.id != "§7"]
        self.assertIsNotNone(bulk_approval.reply_problem(self.state, self.action))

    def test_revision_changes_with_draft_source_or_cited_rule(self):
        original = bulk_approval.revision(self.state, self.action)
        for target in ("draft", "source", "rule"):
            with self.subTest(target=target):
                state = copy.deepcopy(self.state)
                if target == "draft":
                    state.actions[0].payload["text"] += " Changed."
                elif target == "source":
                    next(m for m in state.messages if m.id == "m02").text += " Changed."
                else:
                    next(r for r in state.rules if r.id == "§7").text += " Changed."
                self.assertNotEqual(original, bulk_approval.revision(state, state.actions[0]))

    def test_agent_parser_preserves_unverified_checks(self):
        args = asdict(self.action)
        args["checks"][0]["verified"] = False
        action = _action_from_args(self.state, self.state.issue(self.action.issue_id), args)
        self.assertFalse(action.checks[0].verified)
        self.assertIsNotNone(bulk_approval.reply_problem(self.state, action))

    def test_agent_parser_does_not_assume_an_omitted_verification(self):
        args = asdict(self.action)
        del args["checks"][0]["verified"]
        action = _action_from_args(self.state, self.state.issue(self.action.issue_id), args)
        self.assertFalse(action.checks[0].verified)
        self.assertIsNotNone(bulk_approval.reply_problem(self.state, action))

    def test_legacy_stored_checks_without_verification_are_not_bulk_candidates(self):
        saved = asdict(self.action)
        del saved["checks"][0]["verified"]
        restored = store._action_from_dict(saved)
        self.assertFalse(restored.checks[0].verified)
        self.assertIsNotNone(bulk_approval.reply_problem(self.state, restored))

    def test_unknown_event_has_no_reviewed_bulk_rules(self):
        self.state.id = "new-event"
        self.action.event_id = self.state.id
        self.assertIsNotNone(bulk_approval.reply_problem(self.state, self.action))


class BulkApprovalApiTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.runtime = Path(directory.name)
        for name, value in (("bureau.core.store.RUNTIME_DIR", self.runtime),
                            ("bureau.config.DEMO_MODE", False), ("bureau.config.OPENAI_API_KEY", "")):
            handle = patch(name, value)
            handle.start()
            self.addCleanup(handle.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.state = sample_state()
        # Mixed input: payment and escalation proposals must remain unchanged.
        for iid in ("message:m01", "message:m05"):
            issue = self.state.issue(iid)
            action = issue_example(self.state, issue)
            self.state.actions.append(action)
            issue.status = "needs_human" if action.action_type == "ESCALATE" else "proposed"
        store.save_state(self.state)

    def preview(self):
        response = self.client.get("/api/events/hackathon/safe-replies")
        self.assertEqual(200, response.status_code, response.text)
        return response.json()["replies"]

    def approve(self, items):
        response = self.client.post("/api/events/hackathon/approve-safe-replies", json={
            "replies": [{"id": i["id"], "revision": i["revision"]} for i in items]})
        self.assertEqual(200, response.status_code, response.text)
        return response.json()

    def test_preview_is_read_only_and_only_safe_snapshot_is_approved(self):
        before = {p.name: p.read_bytes() for p in (self.runtime / "hackathon").iterdir()}
        items = self.preview()
        self.assertEqual(3, len(items))
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.runtime / "hackathon").iterdir()})
        self.assertEqual([], store.load_outbox("hackathon"))
        result = self.approve(items)
        self.assertEqual(3, result["bulk_approval"]["approved_count"])
        self.assertEqual([], result["bulk_approval"]["failed"])
        self.assertEqual({i["id"] for i in items}, {m["action_id"] for m in result["outbox"]})
        after = store.load_state("hackathon")
        for iid in ("message:m01", "message:m05"):
            self.assertEqual(self.state.issue(iid), after.issue(iid))
        self.assertEqual(self.state.payments, after.payments)
        self.assertEqual(self.state.groups, after.groups)

    def test_rejected_candidate_does_not_stop_other_replies(self):
        items = self.preview()
        unsafe = self.state.actions[-2]
        items.insert(1, {"id": unsafe.id, "revision": bulk_approval.revision(self.state, unsafe)})
        result = self.approve(items)["bulk_approval"]
        self.assertEqual(3, result["approved_count"])
        self.assertEqual(1, result["failed_count"])
        self.assertEqual(unsafe.title, result["failed"][0]["title"])

    def test_stale_draft_is_not_approved_and_new_proposals_are_not_added(self):
        items = self.preview()
        state = store.load_state("hackathon")
        state.actions[0].payload["text"] += " A changed draft."
        issue = state.issue("message:m19")
        state.actions.append(issue_example(state, issue))
        issue.status = "proposed"
        store.save_state(state)
        result = self.approve(items)["bulk_approval"]
        self.assertEqual(2, result["approved_count"])
        self.assertIn("changed after", result["failed"][0]["reason"])
        self.assertEqual("proposed", store.load_state("hackathon").issue("message:m19").status)

    def test_duplicate_entries_and_retries_never_duplicate_outbox(self):
        items = self.preview()
        result = self.approve([items[0], items[0], *items[1:]])["bulk_approval"]
        self.assertEqual((3, 1), (result["approved_count"], result["failed_count"]))
        result = self.approve(items)["bulk_approval"]
        self.assertEqual((0, 3), (result["approved_count"], result["failed_count"]))
        self.assertEqual(3, len(store.load_outbox("hackathon")))

    def test_overlapping_bulk_requests_do_not_duplicate_replies(self):
        body = {"replies": [{"id": i["id"], "revision": i["revision"]} for i in self.preview()]}
        barrier = threading.Barrier(2)
        def submit():
            with TestClient(app) as client:
                barrier.wait(timeout=5)
                return client.post("/api/events/hackathon/approve-safe-replies", json=body)
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: submit(), range(2)))
        self.assertTrue(all(r.status_code == 200 for r in responses))
        self.assertEqual(3, sum(r.json()["bulk_approval"]["approved_count"] for r in responses))
        self.assertEqual(3, len(store.load_outbox("hackathon")))

    def test_public_browser_cannot_approve_another_browsers_preview(self):
        with patch("bureau.config.DEMO_MODE", True), patch("bureau.config.DEMO_DAILY_LLM_LIMIT", 0):
            with TestClient(app) as other:
                response = self.client.post("/api/events/hackathon/run?issue_id=message:m07")
                self.assertEqual(200, response.status_code, response.text)
                items = self.preview()
                self.assertEqual(1, len(items))
                body = {"replies": [{"id": i["id"], "revision": i["revision"]} for i in items]}
                result = other.post("/api/events/hackathon/approve-safe-replies", json=body).json()
                self.assertEqual(0, result["bulk_approval"]["approved_count"])
                self.assertEqual([], result["outbox"])
                self.assertEqual(1, self.approve(items)["bulk_approval"]["approved_count"])
                self.assertEqual([], other.get("/api/events/hackathon/outbox").json())

    def test_executor_failure_continues_and_is_reported_by_title(self):
        items = self.preview()
        def reject_middle(state, action):
            if action.id == items[1]["id"]:
                raise InvariantViolation("Example per-item failure")
            return apply(state, action)
        with patch("api.main.apply", side_effect=reject_middle):
            result = self.approve(items)["bulk_approval"]
        self.assertEqual(2, result["approved_count"])
        self.assertEqual([{"id": items[1]["id"], "title": items[1]["title"],
                           "reason": "Example per-item failure"}], result["failed"])
        self.assertEqual("proposed", store.load_state("hackathon").issue("message:m07").status)

    def test_unexpected_failure_continues_without_exposing_internal_details(self):
        items = self.preview()
        def reject_first(state, action):
            if action.id == items[0]["id"]:
                raise RuntimeError("internal details")
            return apply(state, action)
        with patch("api.main.apply", side_effect=reject_first), self.assertLogs("api.main", level="ERROR"):
            result = self.approve(items)["bulk_approval"]
        self.assertEqual(2, result["approved_count"])
        self.assertNotIn("internal details", result["failed"][0]["reason"])

    def test_reply_written_before_storage_failure_is_not_sent_twice(self):
        item = self.preview()[0]
        with patch("api.main.store.save_state", side_effect=OSError("disk failure")), self.assertLogs("api.main", level="ERROR"):
            result = self.approve([item])["bulk_approval"]
        self.assertEqual(0, result["approved_count"])
        self.assertEqual(1, len(store.load_outbox("hackathon")))
        result = self.approve([item])["bulk_approval"]
        self.assertEqual(0, result["approved_count"])
        self.assertIn("already in the outbox", result["failed"][0]["reason"])
        self.assertEqual(1, len(store.load_outbox("hackathon")))

    def test_unknown_dismissed_and_cross_event_candidates_are_reported(self):
        items = self.preview()
        self.client.post(f"/api/actions/{items[0]['id']}/dismiss")
        result = self.approve([items[0], {"id": "wei:message:m02", "revision": "0" * 64}, items[1]])["bulk_approval"]
        self.assertEqual((1, 2), (result["approved_count"], result["failed_count"]))

    def test_invalid_batch_is_rejected_before_any_approval(self):
        for body in ({}, {"replies": []}, {"replies": [{"id": "x", "revision": "wrong"}]},
                     {"replies": [{"id": "x", "revision": "0" * 64}] * 101}):
            with self.subTest(body=str(body)[:60]):
                self.assertEqual(422, self.client.post("/api/events/hackathon/approve-safe-replies", json=body).status_code)
        self.assertEqual([], store.load_outbox("hackathon"))
        self.assertEqual(404, self.client.get("/api/events/missing/safe-replies").status_code)


if __name__ == "__main__":
    unittest.main()
