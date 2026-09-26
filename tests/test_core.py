"""Data model, loader and issue detection."""
import unittest

from bureau.core.detect import detect_issues
from bureau.core.loader import load_event


class DataModelTests(unittest.TestCase):
    def test_money_is_integer_cents_and_datetimes_are_aware(self):
        state = load_event("hackathon")
        self.assertTrue(all(isinstance(p.amount_cents, int) for p in state.payments))
        self.assertTrue(all(p.registered_at.tzinfo is not None for p in state.participants))


class LoaderTests(unittest.TestCase):
    def test_travel_request_is_part_of_the_event_state(self):
        self.assertIsNone(load_event("hackathon").travel)
        travel = load_event("wei").travel
        self.assertEqual(travel["destination"], "Trouville-Deauville")
        self.assertEqual(travel["constraints"]["hard"]["max_cost_per_person_cents"], 15000)


class DetectionTests(unittest.TestCase):
    def test_hackathon_issues(self):
        issues = {i.id: i for i in detect_issues(load_event("hackathon"))}
        self.assertIn("unmatched_payment:f90", issues)
        self.assertEqual(issues["unmatched_payment:f90"].status, "needs_human")
        # No reminder to someone whose payment claim is pending.
        self.assertNotIn("p01", issues["unpaid_membership"].subject_ids)
        self.assertIn("multiple_group_membership:p02", issues)
        self.assertIn("group_over_capacity:t-dragons", issues)

    def test_wei_dependencies(self):
        issues = {i.id: i for i in detect_issues(load_event("wei"))}
        self.assertTrue(issues["no_logistics_plan"].blocking)
        self.assertEqual(issues["unpaid_participation"].depends_on, ["no_logistics_plan"])
        self.assertEqual(issues["rooms_unassigned"].depends_on, ["no_logistics_plan"])

    def test_detection_is_idempotent(self):
        state = load_event("hackathon")
        first = [i.id for i in detect_issues(state)]
        second = [i.id for i in detect_issues(state)]
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(set(first)))


if __name__ == "__main__":
    unittest.main()
