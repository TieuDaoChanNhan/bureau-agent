"""Travel planner: hard-constraint gate, ranking, diagnosis."""
from contextlib import redirect_stdout
import io
import unittest
from unittest import mock

from bureau import cli
from bureau.planner.interface import Constraints
from bureau.planner.planner import plan_trip
from tests.helpers import wei_constraints, wei_request


class PlannerTests(unittest.TestCase):
    def test_valid_options_and_ranking(self):
        req = wei_request()
        action = plan_trip(req, wei_constraints())
        self.assertEqual(action.action_type, "SELECT_TRAVEL_PLAN")
        self.assertEqual(action.payload["ranked_valid"], ["A", "B"])

    def test_never_relaxes_constraints(self):
        req = wei_request()
        c = wei_constraints()
        c = Constraints(hard={**c.hard, "max_cost_per_person_cents": 9000}, soft=c.soft,
                        organizer_verified=c.organizer_verified)
        action = plan_trip(req, c)
        self.assertEqual(action.action_type, "ESCALATE")
        self.assertTrue(any("Option A" in s for s in action.payload["suggestions"]))
        self.assertFalse(any(row["valid"] for row in action.payload["options"]))

    def test_unverifiable_constraint_never_gates(self):
        req = wei_request()
        action = plan_trip(req, wei_constraints())
        step_free = [ch for ch in action.checks if "step-free" in ch.name]
        self.assertTrue(step_free and not step_free[0].verified)

    def test_clarifications_stop_before_search(self):
        req = wei_request()
        c = wei_constraints()
        c.clarifications = ["Does the budget include meals?"]
        self.assertEqual(plan_trip(req, c).action_type, "ESCALATE")


class PlannerCliTests(unittest.TestCase):
    def test_default_plan_extracts_the_sample_request(self):
        output = io.StringIO()
        with mock.patch.object(cli, "extract_constraints", return_value=wei_constraints()) as extract, \
             redirect_stdout(output):
            cli.main(["plan", "wei"])
        extract.assert_called_once()
        request = extract.call_args.args[0]
        self.assertEqual(request.event_id, "wei")
        self.assertTrue(request.text)
        self.assertIn("Constraints: LLM extraction", output.getvalue())

    def test_explicit_recorded_mode_runs_without_extraction(self):
        output = io.StringIO()
        with mock.patch.object(cli, "extract_constraints") as extract, redirect_stdout(output):
            cli.main(["plan", "wei", "--recorded-constraints"])
        extract.assert_not_called()
        self.assertIn("recorded fixture (offline demo)", output.getvalue())
        self.assertIn("SELECT_TRAVEL_PLAN", output.getvalue())

    def test_recorded_budget_demo_remains_infeasible_and_leaves_fixture_unchanged(self):
        before = wei_constraints()
        output = io.StringIO()
        with mock.patch.object(cli, "extract_constraints") as extract, redirect_stdout(output):
            cli.main(["plan", "wei", "--recorded-constraints", "--budget", "90"])
        extract.assert_not_called()
        self.assertIn("ESCALATE", output.getvalue())
        self.assertIn("No option satisfies every hard constraint", output.getvalue())
        self.assertEqual(wei_constraints(), before)


if __name__ == "__main__":
    unittest.main()
