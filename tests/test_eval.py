"""Evaluation scoring and isolation checks; all model responses are scripted."""
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import asdict
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from bureau.core.loader import load_event
from bureau.core.models import Evidence, ProposedAction
from eval import run_eval
from tests.fake_llm import FakeClient


def message_case(case_id="eval-test"):
    return {
        "id": case_id, "event": "hackathon", "message_id": "m02",
        "expected_kind": "rules_question", "expected_tools": ["search_rules"],
        "expected_action": "SEND_MESSAGE", "must_ask_human": False, "expected_rule": "\u00a77",
    }


def message_action(**overrides):
    values = {
        "id": "hackathon:message:m02", "event_id": "hackathon", "issue_id": "message:m02",
        "action_type": "SEND_MESSAGE", "title": "Explain existing project rules",
        "description": "Explain the declaration required for existing work.",
        "evidence": [Evidence("rule", "\u00a77", "Existing work must be declared.")],
        "payload": {
            "to": "julien.morel@gmail.com",
            "text": "Declare the existing work; only the hackathon contribution is evaluated.",
        },
    }
    return ProposedAction(**{**values, **overrides})


def scripted_client():
    proposal = {
        key: value for key, value in asdict(message_action()).items()
        if key in ("action_type", "title", "description", "evidence", "checks", "payload")
    }
    return FakeClient([
        [("search_rules", {"query": "existing project"})], [("propose_action", proposal)],
    ])


def result_row(case_id="eval-test", *, metrics=None, violations=None, error=None):
    case = message_case(case_id)
    action = message_action()
    return {
        "id": case_id, "expected": case,
        "input": {"event": "hackathon", "message_id": "m02"},
        "action": action.to_dict(),
        "tool_calls": [{"name": "search_rules", "arguments": {"query": "existing project"}}],
        "metrics": metrics if metrics is not None else run_eval.score_message(
            case, action, ["search_rules"],
        ),
        "violations": [] if violations is None else violations, "error": error,
    }


class CaseLoadingTests(unittest.TestCase):
    def test_committed_message_corpus_has_at_least_forty_valid_unique_cases(self):
        cases = run_eval.load_cases("messages.jsonl")
        self.assertGreaterEqual(len(cases), 40)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        run_eval.validate_message_cases(cases)
        state = load_event("hackathon")
        originals = {m.id: m.text for m in state.messages}
        self.assertEqual({case["message_id"] for case in cases}, set(originals))
        prompts = [case.get("text", originals[case["message_id"]]) for case in cases]
        self.assertEqual(len(set(prompts)), len(prompts))

    def test_small_valid_selection_is_supported(self):
        run_eval.validate_message_cases([message_case()])

    def test_invalid_labels_and_references_are_rejected(self):
        invalid = [
            ("missing action", {k: v for k, v in message_case().items() if k != "expected_action"}),
            ("unknown action", {**message_case(), "expected_action": "DELETE_EVENT"}),
            ("unknown tool", {**message_case(), "expected_tools": ["invented_tool"]}),
            ("unknown rule", {**message_case(), "expected_rule": "\u00a7999"}),
            ("unknown message", {**message_case(), "message_id": "missing"}),
            ("non-boolean human label", {**message_case(), "must_ask_human": "yes"}),
        ]
        for name, case in invalid:
            with self.subTest(name=name), self.assertRaises(ValueError):
                run_eval.validate_message_cases([case])

    def test_duplicate_case_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            run_eval.validate_message_cases([message_case(), message_case()])

    def test_text_overrides_are_used_without_modifying_sample_or_other_cases(self):
        case = {**message_case(), "text": "Could we continue our existing project?"}
        before = load_event("hackathon")
        state, issue = run_eval.prepare_message(case)
        message = next(m for m in state.messages if m.id == case["message_id"])
        self.assertEqual(message.text, case["text"])
        self.assertEqual(issue.details["text"], case["text"])
        self.assertEqual(issue.subject_ids, [case["message_id"]])
        self.assertIsNotNone(message.received_at.tzinfo)
        second, _ = run_eval.prepare_message(message_case("second"))
        state.participants[0].skills.clear()
        state.groups[0].members.clear()
        self.assertEqual(second.participants, before.participants)
        self.assertEqual(second.groups, before.groups)
        self.assertEqual(second.messages, before.messages)
        self.assertEqual(load_event("hackathon"), before)


class ScoringTests(unittest.TestCase):
    def test_wrong_predictions_fail_instead_of_reusing_expected_labels(self):
        action = message_action(
            action_type="ESCALATE", description="An organizer decision is needed.",
            evidence=[], payload={"note": "Review this request."},
        )
        scores = run_eval.score_message(message_case(), action, ["get_event_summary"])
        self.assertFalse(scores["action_correct"])
        self.assertFalse(scores["tools_correct"])
        self.assertFalse(scores["rule_correct"])
        self.assertFalse(scores["human_correct"])
        self.assertTrue(scores["asks_human"])

    def test_required_tools_allow_additional_investigation(self):
        scores = run_eval.score_message(
            message_case(), message_action(),
            ["get_event_summary", "search_rules", "list_rules", "propose_action"],
        )
        self.assertTrue(scores["tools_correct"])
        self.assertTrue(scores["action_correct"])
        self.assertTrue(scores["rule_correct"])

    def test_rule_id_must_be_cited_as_rule_evidence(self):
        action = message_action(evidence=[Evidence("message", "\u00a77", "Wrong source type.")])
        scores = run_eval.score_message(message_case(), action, ["search_rules"])
        self.assertFalse(scores["rule_correct"])
        case = {**message_case(), "expected_rule": None}
        self.assertIsNone(run_eval.score_message(case, action, ["search_rules"])["rule_correct"])

    def test_approval_and_participant_questions_do_not_mean_organizer_escalation(self):
        action = message_action(
            description="Draft a participant reply.",
            payload={"to": "person@participants.example", "text": "Could you send your receipt?"},
        )
        self.assertTrue(action.requires_approval)
        scores = run_eval.score_message(message_case(), action, ["search_rules"])
        self.assertFalse(scores["asks_human"])
        self.assertTrue(scores["human_correct"])

    def test_explicit_organizer_question_satisfies_human_label(self):
        case = {**message_case(), "must_ask_human": True}
        action = message_action(description="Organizers, can you confirm this payment match?")
        scores = run_eval.score_message(case, action, ["search_rules"])
        self.assertTrue(scores["asks_human"])
        self.assertTrue(scores["human_correct"])

    def test_missing_prediction_is_not_a_correct_negative_human_decision(self):
        scores = run_eval.score_message(message_case(), None, [])
        self.assertFalse(scores["action_correct"])
        self.assertFalse(scores["tools_correct"])
        self.assertFalse(scores["rule_correct"])
        self.assertFalse(scores["human_correct"])

    def test_aggregates_include_failed_cases_and_exclude_unlabeled_rules(self):
        correct = result_row("correct")
        wrong = result_row("wrong", metrics={
            "action_correct": False, "tools_correct": False, "rule_correct": None,
            "human_correct": False, "asks_human": True,
        }, violations=[{"type": "InvariantViolation", "detail": "Team capacity exceeded."}])
        failed = result_row("failed", metrics={
            "action_correct": False, "tools_correct": False, "rule_correct": False,
            "human_correct": False, "asks_human": None,
        }, error={"type": "RuntimeError", "detail": "Synthetic failure."})
        failed["action"] = None
        failed["violations"] = None
        summary = run_eval.summarize_messages([correct, wrong, failed])
        for name in ("action_accuracy", "tool_selection", "human_handling"):
            with self.subTest(metric=name):
                self.assertEqual(summary[name]["correct"], 1)
                self.assertEqual(summary[name]["total"], 3)
                self.assertAlmostEqual(summary[name]["accuracy"], 1 / 3)
        self.assertEqual(summary["rule_citation"], {"correct": 1, "total": 2, "accuracy": 0.5})
        self.assertEqual(summary["invariants"], {"violations": 1, "checked": 2, "unchecked": 1})
        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["human_interventions"], {"missed": 0, "unnecessary": 1, "unknown": 1})


class EvaluationIsolationTests(unittest.TestCase):
    def test_trace_client_forwards_requests_and_records_observed_tool_calls(self):
        fake = FakeClient([[("search_rules", {"query": "existing project"})]])
        traced = run_eval.TraceClient(fake)
        response = traced.chat.completions.create(model="fake-model", messages=[])
        self.assertEqual(fake.requests[0]["model"], "fake-model")
        self.assertEqual(response.choices[0].message.tool_calls[0].function.name, "search_rules")
        self.assertEqual([call["name"] for call in traced.calls], ["search_rules"])
        self.assertEqual(json.loads(traced.calls[0]["arguments"]), {"query": "existing project"})

    def test_real_loop_uses_fake_client_without_label_leakage_or_runtime_writes(self):
        fake = scripted_client()
        before = load_event("hackathon")
        with mock.patch("bureau.core.store.save_state") as save, \
             mock.patch("bureau.core.store.append_log") as log, \
             mock.patch("bureau.core.store.append_outbox") as outbox:
            rows = run_eval.evaluate_messages([message_case()], client_factory=lambda: fake)
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["error"])
        self.assertEqual(rows[0]["action"]["action_type"], "SEND_MESSAGE")
        self.assertIn("search_rules", [call["name"] for call in rows[0]["tool_calls"]])
        self.assertTrue(rows[0]["metrics"]["action_correct"])
        self.assertEqual(rows[0]["violations"], [])
        context = "\n".join(message["content"] for message in fake.requests[0]["messages"]
                            if message["role"] == "user")
        for label in ("expected_action", "expected_tools", "expected_rule", "must_ask_human"):
            self.assertNotIn(label, context)
        save.assert_not_called()
        log.assert_not_called()
        outbox.assert_not_called()
        self.assertEqual(load_event("hackathon"), before)

    def test_model_failure_is_recorded_and_later_cases_still_run(self):
        failing = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=mock.Mock(side_effect=RuntimeError("Synthetic model failure.")),
        )))
        clients = iter([failing, scripted_client()])
        rows = run_eval.evaluate_messages(
            [message_case("failed"), message_case("successful")],
            client_factory=lambda: next(clients),
        )
        self.assertEqual([row["id"] for row in rows], ["failed", "successful"])
        self.assertIsNotNone(rows[0]["error"])
        self.assertIsNone(rows[0]["action"])
        self.assertIsNone(rows[0]["violations"])
        self.assertIsNone(rows[1]["error"])
        summary = run_eval.summarize_messages(rows)
        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["action_accuracy"]["correct"], 1)
        self.assertEqual(summary["action_accuracy"]["total"], 2)

    def test_unrelated_existing_group_defects_do_not_count_against_a_reply(self):
        state, _ = run_eval.prepare_message(message_case())
        before = deepcopy(state)
        with mock.patch("bureau.core.store.append_log") as log, \
             mock.patch("bureau.core.store.append_outbox") as outbox:
            violations = run_eval.check_invariants(state, message_action())
        self.assertEqual(violations, [])
        self.assertEqual(state, before)
        log.assert_not_called()
        outbox.assert_not_called()

    def test_over_capacity_move_is_counted_without_mutating_state(self):
        state, _ = run_eval.prepare_message(message_case())
        before = deepcopy(state)
        action = message_action(
            action_type="MOVE_MEMBER", payload={"participant_id": "p13", "to_group": "t-nomads"},
        )
        violations = run_eval.check_invariants(state, action)
        self.assertEqual(len(violations), 1)
        self.assertIn("capacity", violations[0]["detail"].lower())
        self.assertEqual(state, before)

    def test_invalid_executor_payload_is_reported_instead_of_raising(self):
        state, _ = run_eval.prepare_message(message_case())
        action = message_action(action_type="LINK_PAYMENT", payload={"payment_id": "f90"})
        violations = run_eval.check_invariants(state, action)
        self.assertTrue(violations)
        self.assertIn("type", violations[0])
        self.assertIn("detail", violations[0])


class EvaluationCliTests(unittest.TestCase):
    def test_messages_command_prints_metrics_and_saves_timestamped_report(self):
        rows = [result_row()]
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(run_eval, "load_cases", return_value=[message_case()]), \
                 mock.patch.object(run_eval, "evaluate_messages", return_value=rows) as evaluate, \
                 redirect_stdout(output):
                exit_code = run_eval.main([
                    "--suite", "messages", "--limit", "1", "--output-dir", tmp,
                ])
            self.assertEqual(exit_code, 0)
            evaluate.assert_called_once()
            reports = list(Path(tmp).glob("*.json"))
            self.assertEqual(len(reports), 1)
            self.assertNotIn(":", reports[0].name)
            report = json.loads(reports[0].read_text(encoding="utf-8"))
        self.assertEqual(report["messages"]["cases"], rows)
        self.assertEqual(report["messages"]["metrics"], run_eval.summarize_messages(rows))
        self.assertIsNone(report["planning"])
        self.assertIn("action", output.getvalue().lower())
        self.assertIn("rule", output.getvalue().lower())

    def test_non_positive_limit_is_rejected_before_evaluation(self):
        for limit in ("0", "-1"):
            with self.subTest(limit=limit), \
                 mock.patch.object(run_eval, "evaluate_messages") as evaluate, \
                 redirect_stdout(io.StringIO()), \
                 mock.patch("sys.stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit) as raised:
                    run_eval.main(["--suite", "messages", "--limit", limit])
                self.assertEqual(raised.exception.code, 2)
                evaluate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
