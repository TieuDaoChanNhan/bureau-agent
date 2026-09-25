"""Fixed-code tools: identity scoring, eligibility, groups, rules search."""
import unittest

from bureau.core.loader import load_event
from bureau.tools.eligibility import check_eligibility
from bureau.tools.groups import check_groups, propose_groups
from bureau.tools.identity import match_person
from bureau.tools.rules import search_rules


class IdentityTests(unittest.TestCase):
    def test_swapped_email_parts_is_ask_human_not_auto_link(self):
        top = match_person(load_event("hackathon"), "f90")[0]
        self.assertEqual(top.participant_id, "p01")
        self.assertEqual(top.band, "ask_human")

    def test_compound_surname_and_reference_first_name(self):
        top = match_person(load_event("wei"), "b90")[0]
        self.assertEqual(top.participant_id, "w01")
        self.assertEqual(top.band, "ask_human")

    def test_unrelated_payment_is_different(self):
        self.assertEqual(match_person(load_event("hackathon"), "f91")[0].band, "different")


class EligibilityTests(unittest.TestCase):
    def test_unpaid_list(self):
        elig = check_eligibility(load_event("hackathon"))
        self.assertEqual(sorted(elig["unpaid"]), ["p01", "p07", "p12", "p15", "p18"])
        self.assertEqual(sorted(elig["unmatched_payments"]), ["f90", "f91"])


class GroupTests(unittest.TestCase):
    def test_group_violations(self):
        kinds = {v["type"] for v in check_groups(load_event("hackathon"))}
        self.assertEqual(kinds, {"multiple_group_membership", "group_over_capacity"})

    def test_proposed_groups_cover_everyone_once(self):
        solo = ["p13", "p14", "p15", "p16", "p17", "p18"]
        groups = propose_groups(load_event("hackathon"), solo, size=3)
        self.assertEqual(sorted(p for g in groups for p in g), sorted(solo))
        self.assertTrue(all(2 <= len(g) <= 4 for g in groups))


class RulesTests(unittest.TestCase):
    def test_rules_are_structured_and_citable(self):
        state = load_event("hackathon")
        self.assertIn("§3", [r.id for r in state.rules])
        self.assertEqual(search_rules(state, "one team only")[0]["rule_id"], "§3")


if __name__ == "__main__":
    unittest.main()
