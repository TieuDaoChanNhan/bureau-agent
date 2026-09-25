"""Travel planner: hard-constraint gate, ranking, diagnosis."""
import unittest

from bureau.planner.interface import Constraints
from bureau.planner.planner import extract_constraints, plan_trip
from tests.helpers import wei_request


class PlannerTests(unittest.TestCase):
    def test_valid_options_and_ranking(self):
        req = wei_request()
        action = plan_trip(req, extract_constraints(req))
        self.assertEqual(action.action_type, "SELECT_TRAVEL_PLAN")
        self.assertEqual(action.payload["ranked_valid"], ["A", "B"])

    def test_never_relaxes_constraints(self):
        req = wei_request()
        c = extract_constraints(req)
        c = Constraints(hard={**c.hard, "max_cost_per_person_cents": 9000}, soft=c.soft,
                        organizer_verified=c.organizer_verified)
        action = plan_trip(req, c)
        self.assertEqual(action.action_type, "ESCALATE")
        self.assertTrue(any("Option A" in s for s in action.payload["suggestions"]))
        self.assertFalse(any(row["valid"] for row in action.payload["options"]))

    def test_unverifiable_constraint_never_gates(self):
        req = wei_request()
        action = plan_trip(req, extract_constraints(req))
        step_free = [ch for ch in action.checks if "step-free" in ch.name]
        self.assertTrue(step_free and not step_free[0].verified)

    def test_clarifications_stop_before_search(self):
        req = wei_request()
        c = extract_constraints(req)
        c.clarifications = ["Does the budget include meals?"]
        self.assertEqual(plan_trip(req, c).action_type, "ESCALATE")


if __name__ == "__main__":
    unittest.main()
