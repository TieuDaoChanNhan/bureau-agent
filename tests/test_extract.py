"""Extraction boundary tests: scripted responses, no API calls or credentials."""
import copy
import json
import unittest
from dataclasses import replace
from unittest.mock import patch

from bureau.planner.extract import ConstraintExtractionError, extract_constraints
from bureau.planner.planner import plan_trip
from tests.fake_llm import FakeStructuredClient
from tests.helpers import wei_request


def response(**hard):
    return {
        "hard": {"participants": 40, "max_cost_per_person_cents": None,
                 "arrive_before": None, "no_overnight": None, "step_free_rooms": None, **hard},
        "soft": [], "organizer_verified": [], "clarifications": [], "unsupported_requirements": [],
    }


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.request = replace(wei_request(), event_id="not-a-recorded-event", participants=40,
                               text="For 40 people: EUR 99.50 per person, meals excluded. Arrive by 22:30.",
                               catering={"included_in_participation_fee": False})

    def test_request_is_source_of_truth_and_schema_is_strict(self):
        payload = response(max_cost_per_person_cents=9950, arrive_before="22:30")
        client = FakeStructuredClient(payload)
        with patch("pathlib.Path.read_text", side_effect=AssertionError("No fixture reads")):
            constraints = extract_constraints(self.request, client=client)
        self.assertEqual(constraints.hard, {"participants": 40, "max_cost_per_person_cents": 9950,
                                            "arrive_before": "22:30"})
        sent = client.requests[0]
        self.assertEqual(json.loads(sent["messages"][1]["content"])["text"], self.request.text)
        self.assertEqual([m["role"] for m in sent["messages"]], ["system", "user"])
        schema = sent["response_format"]["json_schema"]
        self.assertTrue(schema["strict"])
        self.assertFalse(schema["schema"]["additionalProperties"])
        self.assertFalse(schema["schema"]["properties"]["hard"]["additionalProperties"])

    def test_preserves_false_zero_and_preference_priority(self):
        payload = response(no_overnight=False, max_cost_per_person_cents=0, step_free_rooms=0)
        payload["soft"] = ["near_station", "lower_cost"]
        c = extract_constraints(self.request, client=FakeStructuredClient(payload))
        self.assertIs(c.hard["no_overnight"], False)
        self.assertEqual(c.hard["max_cost_per_person_cents"], 0)
        self.assertEqual(c.soft, ["near_station", "lower_cost"])

    def test_accessibility_cannot_lose_organizer_verification(self):
        c = extract_constraints(self.request, client=FakeStructuredClient(response(step_free_rooms=2)))
        self.assertEqual(c.organizer_verified, ["step_free_rooms"])

    def test_unsupported_facility_is_preserved_as_an_unverified_check(self):
        payload = response(max_cost_per_person_cents=16000)
        payload["unsupported_requirements"] = ["A private kitchen exclusively for our group"]
        req = replace(wei_request(), text="EUR 160 each including meals. A private kitchen is mandatory.")
        constraints = extract_constraints(req, client=FakeStructuredClient(payload))
        self.assertEqual(constraints.hard["max_cost_per_person_cents"], 16000)
        self.assertEqual(constraints.clarifications, [])
        action = plan_trip(req, constraints)
        self.assertEqual(action.action_type, "SELECT_TRAVEL_PLAN")
        for row in action.payload["options"]:
            check = next(check for check in row["checks"] if "private kitchen" in check["name"])
            self.assertFalse(check["verified"])
            self.assertFalse(check["passed"])

    def test_demo_budget_answer_reaches_f_c_e_with_kitchen_and_coach_confirmation_notes(self):
        from bureau.core.loader import load_event
        from demo.replay import BUDGET_ANSWER
        request = wei_request()
        payload = response(participants=100, arrive_before="21:00", no_overnight=True, step_free_rooms=2)
        payload["soft"] = ["fewer_changes", "early_return", "lower_cost"]
        payload["unsupported_requirements"] = ["A shared kitchen and activity spaces", "Two coaches"]
        payload["clarifications"] = ["Does the EUR150 ceiling include coach hire?"]
        first = extract_constraints(request, client=FakeStructuredClient(payload))
        with patch("bureau.planner.planner.search_options") as search:
            self.assertEqual(plan_trip(request, first).action_type, "ESCALATE")
        search.assert_not_called()

        payload["hard"]["max_cost_per_person_cents"] = 15000
        payload["clarifications"] = []
        answered = replace(request, text=request.text + "\n" + BUDGET_ANSWER)
        constraints = extract_constraints(answered, client=FakeStructuredClient(payload))
        with patch("bureau.planner.jinko.JINKO_MODE", "replay"):
            action = plan_trip(answered, constraints, search=load_event("wei").travel["search"])
        self.assertEqual(action.action_type, "SELECT_TRAVEL_PLAN")
        self.assertEqual(action.payload["ranked_valid"], ["F", "C", "E"])
        for row in action.payload["options"]:
            for requirement in payload["unsupported_requirements"]:
                check = next(c for c in row["checks"] if c["name"] == requirement)
                self.assertFalse(check["verified"])
                self.assertFalse(check["passed"])

    def test_train_only_cannot_disappear_when_model_omits_the_restriction(self):
        req = replace(self.request, participants=100, text=(
            "For 100 students, max EUR 160 per person including transport, lodging, groceries and food transport. "
            "Arrive by 21:00; no overnight travel. Trains only: coaches are forbidden. "
            "Ask us before proceeding if that transport restriction cannot be enforced."))
        c = extract_constraints(req, client=FakeStructuredClient(response(
            participants=100, max_cost_per_person_cents=16000, arrive_before="21:00", no_overnight=True)))
        self.assertTrue(c.clarifications)
        with patch("bureau.planner.planner.search_options") as search:
            action = plan_trip(req, c)
        search.assert_not_called()
        self.assertEqual(action.action_type, "ESCALATE")
        self.assertNotIn("ranked_valid", action.payload)

    def test_clarification_stops_search_and_is_not_replaced_by_sample(self):
        payload = response()
        payload["clarifications"] = ["Is the budget per person or for the group?"]
        c = extract_constraints(self.request, client=FakeStructuredClient(payload))
        with patch("bureau.planner.planner.search_options", side_effect=AssertionError("Search blocked")):
            action = plan_trip(self.request, c)
        self.assertEqual(action.action_type, "ESCALATE")
        self.assertEqual(action.payload["clarifications"], payload["clarifications"])
        self.assertNotIn("max_cost_per_person_cents", c.hard)

    def test_wei_clarification_preserves_known_catering_and_waits_for_the_budget_answer(self):
        """Script the provider response to verify the clarification boundary, not model semantics."""
        request = wei_request()
        payload = response(participants=100)
        payload["clarifications"] = ["Does the EUR150 ceiling include the coach hire?"]
        client = FakeStructuredClient(payload)
        constraints = extract_constraints(request, client=client)
        with patch("bureau.planner.planner.search_options") as search:
            action = plan_trip(request, constraints)

        search.assert_not_called()
        self.assertEqual(action.action_type, "ESCALATE")
        self.assertNotIn("max_cost_per_person_cents", constraints.hard)
        sent = json.loads(client.requests[0]["messages"][1]["content"])
        self.assertEqual(sent["text"], request.text)
        self.assertTrue(sent["catering"]["included_in_participation_fee"])
        self.assertEqual(sent["catering"]["groceries_per_person_cents"], 2000)
        self.assertEqual(sent["catering"]["food_transport_per_person_cents"], 200)

        answered = replace(request, text=request.text + "\nThe EUR150 ceiling includes round-trip "
                           "coach hire, lodging, groceries and food transport.")
        constraints = extract_constraints(answered, client=FakeStructuredClient(
            response(participants=100, max_cost_per_person_cents=15000)))
        self.assertEqual(constraints.hard["max_cost_per_person_cents"], 15000)
        self.assertEqual(constraints.clarifications, [])

    def test_rejects_invalid_hard_values_without_coercion(self):
        for key, value in (("participants", True), ("participants", 0),
                           ("max_cost_per_person_cents", "9950"), ("max_cost_per_person_cents", 99.5),
                           ("max_cost_per_person_cents", -1), ("arrive_before", "24:00"),
                           ("arrive_before", "9:30"), ("no_overnight", "false"), ("step_free_rooms", -2)):
            with self.subTest(key=key, value=value), self.assertRaises(ConstraintExtractionError):
                extract_constraints(self.request, client=FakeStructuredClient(response(**{key: value})))

    def test_rejects_unsupported_or_malformed_output(self):
        valid = response()
        missing = copy.deepcopy(valid)
        del missing["hard"]["no_overnight"]
        extra_hard = copy.deepcopy(valid)
        extra_hard["hard"]["made_up"] = 1
        invalid = [None, "not JSON", "[]", {**valid, "extra": True}, missing, extra_hard,
                   {**valid, "soft": ["invented"]}, {**valid, "organizer_verified": ["budget"]},
                   {**valid, "clarifications": ["  "]}, {**valid, "clarifications": "question?"},
                   {**valid, "unsupported_requirements": "train only"},
                   {**valid, "unsupported_requirements": [""]}]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ConstraintExtractionError):
                extract_constraints(self.request, client=FakeStructuredClient(payload))

    def test_refusal_and_truncation_are_failures_even_with_valid_json(self):
        for kwargs in ({"refusal": "Cannot comply"}, {"finish_reason": "length"},
                       {"finish_reason": "content_filter"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ConstraintExtractionError):
                extract_constraints(self.request, client=FakeStructuredClient(response(), **kwargs))

    def test_provider_failure_propagates(self):
        with self.assertRaisesRegex(ConnectionError, "unavailable"):
            extract_constraints(self.request, client=FakeStructuredClient(ConnectionError("unavailable")))

    def test_missing_key_never_falls_back_to_recorded_constraints(self):
        with patch("bureau.planner.extract.config.OPENAI_API_KEY", ""):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                extract_constraints(replace(self.request, event_id="wei"))

    def test_blank_input_never_calls_provider(self):
        client = FakeStructuredClient(response())
        with self.assertRaisesRegex(ValueError, "request"):
            extract_constraints(replace(self.request, text="  "), client=client)
        self.assertEqual(client.requests, [])


if __name__ == "__main__":
    unittest.main()
