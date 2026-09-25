"""Regression tests for the executor's final validation before changing data."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bureau.core.detect import detect_issues
from bureau.core.executor import InvariantViolation, apply
from bureau.core.loader import load_event
from bureau.core.models import ProposedAction


class ExecutorHardeningTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.runtime = Path(tmp.name)
        patcher = mock.patch("bureau.core.store.RUNTIME_DIR", self.runtime)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.state = load_event("hackathon")
        self.state.issues = detect_issues(self.state)
        self.action = ProposedAction(
            id="hackathon:unmatched_payment:f90", event_id="hackathon",
            issue_id="unmatched_payment:f90", action_type="LINK_PAYMENT",
            title="Link payment", description="Organizer explanation",
            payload={"payment_id": "f90", "participant_id": "p01"},
        )

    def assert_rejected(self, exception, **kwargs):
        before = copy.deepcopy(self.state)
        with self.assertRaises(exception):
            apply(self.state, self.action, **kwargs)
        self.assertEqual(self.state, before)
        self.assertEqual(list(self.runtime.iterdir()), [])

    def test_invalid_travel_option_leaves_state_and_side_effects_unchanged(self):
        self.state = load_event("wei")
        self.state.issues = detect_issues(self.state)
        self.action = ProposedAction(
            id="wei:no_logistics_plan", event_id="wei", issue_id="no_logistics_plan",
            action_type="SELECT_TRAVEL_PLAN", title="", description="",
            payload={"options": [{"option": {"id": "C"}, "valid": False}]},
        )
        self.assert_rejected(InvariantViolation, option_id="C")
        self.action.payload["option_id"] = "C"
        self.assert_rejected(InvariantViolation)

    def test_travel_option_requires_explicit_boolean_validity(self):
        self.state = load_event("wei")
        self.action.action_type = "SELECT_TRAVEL_PLAN"
        for validity in (None, "false", 1):
            with self.subTest(validity=validity):
                row = {"option": {"id": "A"}}
                if validity is not None:
                    row["valid"] = validity
                self.action.payload = {"option_id": "A", "options": [row]}
                self.assert_rejected(InvariantViolation)

    def test_link_payment_rejects_unknown_participant(self):
        self.action.payload["participant_id"] = "missing"
        self.assert_rejected(ValueError)

    def test_link_payment_rejects_another_explicit_owner_before_reply(self):
        next(p for p in self.state.payments if p.id == "f90").participant_id = "p02"
        self.action.payload.update(to=["p01"], message="Do not send")
        self.assert_rejected(InvariantViolation)

    def test_link_payment_rejects_another_email_owner_even_with_other_payments(self):
        payment = next(p for p in self.state.payments if p.id == "f90")
        # p02 already has an earlier matching payment: inspect this specific
        # payment's ownership rather than only their first linked_payment().
        payment.payer_email = self.state.participant("p02").emails[0].upper()
        self.assert_rejected(InvariantViolation)

    def test_link_payment_accepts_the_same_owner_without_sending_a_reply(self):
        for explicit in (False, True):
            with self.subTest(explicit=explicit):
                payment = next(p for p in self.state.payments if p.id == "f90")
                payment.participant_id = "p01" if explicit else None
                payment.payer_email = self.state.participant("p01").emails[0].upper()
                result = apply(self.state, self.action)
                self.assertEqual(next(p for p in result.payments if p.id == "f90").participant_id, "p01")
                self.assertFalse((self.runtime / "hackathon" / "outbox.json").exists())

    def assert_reply(self, edited_description=None):
        self.action.payload.update(to=["p01"], message="Payment confirmed")
        before = copy.deepcopy(self.state)
        result = apply(self.state, self.action, edited_description=edited_description)
        self.assertEqual(self.state, before)
        self.assertEqual(next(p for p in result.payments if p.id == "f90").participant_id, "p01")
        issue = result.issue(self.action.issue_id)
        self.assertEqual((issue.status, issue.resolved_by_action_id), ("resolved", self.action.id))
        outbox = json.loads((self.runtime / "hackathon" / "outbox.json").read_text())
        self.assertEqual(len(outbox), 1)
        self.assertEqual(outbox[0]["action_id"], self.action.id)
        self.assertEqual(outbox[0]["to"], ["p01"])
        self.assertEqual(outbox[0]["text"],
                         edited_description if edited_description is not None else "Payment confirmed")
        self.assertEqual(len((self.runtime / "hackathon" / "log.jsonl").read_text().splitlines()), 1)

    def test_link_payment_appends_exactly_one_reply(self):
        self.assert_reply()

    def test_link_payment_uses_edited_reply(self):
        self.assert_reply("Approved reply")

    def test_link_payment_honors_an_empty_edited_reply(self):
        self.assert_reply("")

    def test_link_payment_reply_requires_a_recipient(self):
        self.action.payload["message"] = "Payment confirmed"
        self.assert_rejected(ValueError)
