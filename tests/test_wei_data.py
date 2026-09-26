"""WEI demo consistency across registrations, payments and recorded planning."""
import unittest

from bureau.core.detect import detect_issues
from bureau.core.loader import load_event
from bureau.planner.planner import plan_trip
from bureau.tools.eligibility import check_eligibility
from tests.helpers import wei_constraints, wei_request


class WEIFixtureTests(unittest.TestCase):
    def test_registered_group_matches_the_planned_trip(self):
        state = load_event("wei")
        request = wei_request()
        constraints = wei_constraints()

        self.assertEqual(len(state.participants), 100)
        self.assertEqual(len({p.id for p in state.participants}), 100)
        self.assertEqual(request.participants, len(state.participants))
        self.assertEqual(constraints.hard["participants"], request.participants)
        self.assertIsNotNone(request.depart_after.tzinfo)
        self.assertIsNotNone(request.return_by)
        self.assertIsNotNone(request.return_by.tzinfo)
        self.assertEqual(request.catering, state.travel["catering"])
        self.assertGreater(request.return_by, request.depart_after)
        self.assertLess(state.deadlines["payment"], request.depart_after)
        self.assertEqual(
            {p.id for p in state.participants if "step_free" in p.needs}, {"w03", "w05"},
        )

    def test_payment_sample_preserves_pending_match_and_unpaid_registrations(self):
        state = load_event("wei")
        eligibility = check_eligibility(state)
        issues = {issue.id: issue for issue in detect_issues(state)}

        self.assertEqual(len(state.payments), 97)
        self.assertEqual(len({payment.id for payment in state.payments}), 97)
        self.assertEqual(state.settings["fee_amount_cents"], 15000)
        self.assertTrue(all(payment.amount_cents == state.settings["fee_amount_cents"]
                            for payment in state.payments))
        self.assertEqual(len(eligibility["paid"]), 96)
        self.assertEqual(set(eligibility["unpaid"]), {"w01", "w06", "w07", "w08"})
        self.assertEqual(eligibility["unmatched_payments"], ["b90"])
        self.assertEqual(issues["unmatched_payment:b90"].status, "needs_human")
        self.assertEqual(issues["unmatched_payment:b90"].details["candidate"], "w01")
        self.assertEqual(set(issues["unpaid_participation"].subject_ids), {"w06", "w07", "w08"})
        for issue_id in ("unpaid_participation", "rooms_unassigned", "message:wm01"):
            with self.subTest(issue=issue_id):
                self.assertEqual(issues[issue_id].depends_on, ["no_logistics_plan"])
        self.assertIn("message:wm02", issues)

    def test_recorded_packages_carry_charter_and_unverified_venue_requirements(self):
        request = wei_request()
        action = plan_trip(request, wei_constraints())

        self.assertEqual(action.action_type, "SELECT_TRAVEL_PLAN")
        self.assertTrue(action.payload["ranked_valid"])
        for row in action.payload["options"]:
            option = row["option"]
            with self.subTest(option=option["id"]):
                transport = option["transport"]
                self.assertEqual(transport["mode"], "coach")
                self.assertIs(transport["charter"], True)
                self.assertIs(transport["round_trip"], True)
                self.assertEqual(transport["vehicles"], 2)
                self.assertEqual(transport["capacity"],
                                 transport["vehicles"] * transport["seats_per_vehicle"])
                self.assertGreaterEqual(transport["capacity"], request.participants)
                lodging = option["lodging"]
                self.assertGreaterEqual(lodging["capacity"], request.participants)
                self.assertIs(lodging["kitchen_hint"], True)
                self.assertIs(lodging["activity_space_hint"], True)
                self.assertIs(lodging["facilities_verified"], False)
                self.assertIs(type(option["cost_per_person_cents"]), int)
                self.assertFalse(option["source"].startswith("jinko:"))

    def test_public_demo_uses_a_neutral_association_and_unconfirmed_details(self):
        state = load_event("wei")
        travel = state.travel
        provenance = travel["provenance"]

        self.assertEqual(provenance["status"], "unconfirmed_demo")
        self.assertEqual(provenance["association"], "Unnamed student association")
        self.assertEqual(state.name, "Student association WEI (demo)")
        self.assertEqual(travel["origin"], "Campus in Palaiseau")
        self.assertIn("WEI", provenance["event"])
        self.assertTrue(provenance["source"])
        self.assertTrue(travel["organizer_checks"])
        self.assertTrue(all(isinstance(check, str) and check.strip()
                            for check in travel["organizer_checks"]))

    def test_organizer_brief_is_short_and_preserves_the_budget_question(self):
        request = wei_request()

        self.assertGreaterEqual(len(request.text.split()), 60)
        self.assertLessEqual(len(request.text.split()), 90)
        self.assertIn("€150 each, meals included", request.text)
        self.assertIn("unsure whether coach hire is covered", request.text)
        self.assertEqual(wei_constraints().hard["max_cost_per_person_cents"], 15000)
        self.assertEqual(wei_constraints().clarifications, [])

    def test_meals_and_food_transport_are_included_in_the_student_fee(self):
        state = load_event("wei")
        catering = state.travel["catering"]
        self.assertIs(catering["included_in_participation_fee"], True)
        self.assertEqual(catering["purchased_by"], "student organizers")
        self.assertEqual(catering["transported_by"], "student organizers")
        self.assertEqual(catering["budget_status"], "unconfirmed_demo")
        self.assertIsNone(catering["transport_method"])

        action = plan_trip(wei_request(), wei_constraints())
        for row in action.payload["options"]:
            option = row["option"]
            with self.subTest(option=option["id"]):
                costs = option["cost_breakdown_per_person_cents"]
                self.assertEqual(set(costs), set(state.settings["fee_includes"]))
                self.assertTrue(all(type(value) is int and value >= 0 for value in costs.values()))
                self.assertEqual(costs["groceries"], catering["groceries_per_person_cents"])
                self.assertEqual(costs["food_transport"], catering["food_transport_per_person_cents"])
                self.assertEqual(sum(costs.values()), option["cost_per_person_cents"])
        self.assertEqual(state.settings["fee_amount_cents"], 15000)
        self.assertEqual(state.settings["fee_status"], "provisional_demo")


if __name__ == "__main__":
    unittest.main()
