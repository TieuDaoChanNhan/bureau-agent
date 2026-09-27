"""Travel planner: hard-constraint gate, ranking, diagnosis."""
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import replace
import io
import json
import unittest
from unittest import mock

from bureau import cli
from bureau.planner.constraints import evaluate
from bureau.planner.interface import Constraints
from bureau.planner.planner import plan_trip, search_options
from tests.helpers import wei_constraints, wei_request


class PlannerTests(unittest.TestCase):
    def test_valid_options_and_ranking(self):
        req = wei_request()
        action = plan_trip(req, wei_constraints())
        self.assertEqual(action.action_type, "SELECT_TRAVEL_PLAN")
        self.assertEqual(action.payload["ranked_valid"], ["D", "A", "B"])

    def test_never_relaxes_constraints(self):
        req = wei_request()
        c = wei_constraints()
        c = Constraints(hard={**c.hard, "max_cost_per_person_cents": 9000}, soft=c.soft,
                        organizer_verified=c.organizer_verified)
        action = plan_trip(req, c)
        self.assertEqual(action.action_type, "ESCALATE")
        self.assertTrue(any("Option A" in s for s in action.payload["suggestions"]))
        self.assertFalse(any(row["valid"] for row in action.payload["options"]))

    def test_food_and_its_transport_count_toward_the_budget(self):
        option = search_options(wei_request())[0]
        breakdown = {**option.cost_breakdown_per_person_cents, "groceries": 3000}
        option = replace(option, cost_breakdown_per_person_cents=breakdown,
                         cost_per_person_cents=sum(breakdown.values()))

        constraints = wei_constraints()
        constraints.hard["max_cost_per_person_cents"] = 12000
        valid, checks = evaluate([option], constraints)

        self.assertLess(breakdown["coach"] + breakdown["lodging"], 12000)
        self.assertEqual(option.cost_per_person_cents, 12200)
        self.assertEqual(valid, [])
        self.assertTrue(any(check.name.startswith("cost") and not check.passed
                            for check in checks[option.id]))

    def test_recorded_packages_replace_food_allocations_without_adding_them_twice(self):
        req = wei_request()
        original = search_options(req)[0]
        req = replace(req, catering={**req.catering, "groceries_per_person_cents": 3000})
        changed = search_options(req)[0]
        self.assertEqual(12200, changed.cost_per_person_cents)
        self.assertEqual(3000, changed.cost_breakdown_per_person_cents["groceries"])
        self.assertEqual(changed.cost_per_person_cents, sum(changed.cost_breakdown_per_person_cents.values()))
        self.assertEqual(original, search_options(wei_request())[0])
        constraints = wei_constraints()
        constraints.hard["max_cost_per_person_cents"] = 12000
        self.assertEqual([], evaluate([changed], constraints)[0])

    def test_invalid_itemization_cannot_pass_the_gate(self):
        original = search_options(wei_request())[0]
        invalid = [{**original.cost_breakdown_per_person_cents, "groceries": value}
                   for value in (True, 2000.0, -2000, 1000)] + [None, [], False]
        for breakdown in invalid:
            with self.subTest(breakdown=breakdown):
                option = replace(original, cost_breakdown_per_person_cents=breakdown)
                valid, checks = evaluate([option], wei_constraints())
                self.assertEqual(valid, [])
                self.assertTrue(any(check.name == "itemized cost matches total" and not check.passed
                                    for check in checks[option.id]))

    def test_unverifiable_constraint_never_gates(self):
        req = wei_request()
        action = plan_trip(req, wei_constraints())
        step_free = [ch for ch in action.checks if "step-free" in ch.name]
        self.assertTrue(step_free and not step_free[0].verified)

    def test_clarifications_stop_before_search(self):
        req = wei_request()
        c = wei_constraints()
        c.clarifications = ["Does the EUR150 ceiling include the coach hire?"]
        with mock.patch("bureau.planner.planner.search_options") as search:
            self.assertEqual(plan_trip(req, c).action_type, "ESCALATE")
        search.assert_not_called()

    def test_explicit_mode_restrictions_gate_even_recorded_constraints(self):
        for text in ("Train only.", "Trains only: coaches are forbidden.", "No coach, please.",
                     "Uniquement en train.", "Pas d’autocar.", "Les avions sont interdits.",
                     "We must travel by rail.", "Bus-only travel."):
            with self.subTest(text=text), mock.patch("bureau.planner.planner.search_options") as search:
                constraints = wei_constraints()
                action = plan_trip(replace(wei_request(), text=text), constraints)
                self.assertEqual(action.action_type, "ESCALATE")
                self.assertIn("transport-mode", action.payload["clarifications"][0])
                self.assertEqual(constraints.clarifications, [])
                search.assert_not_called()

    def test_mode_mentions_and_preferences_do_not_trigger_the_restriction_guard(self):
        for text in ("We need two coaches, no overnight travel.", "Prefer trains but coaches are fine.",
                     "No coach restrictions; choose the cheapest package.", "Nous préférons le train."):
            with self.subTest(text=text):
                action = plan_trip(replace(wei_request(), text=text), wei_constraints())
                self.assertEqual(action.action_type, "SELECT_TRAVEL_PLAN")
                self.assertEqual(action.payload["ranked_valid"], ["D", "A", "B"])

    def test_missing_or_invalid_meal_allocations_stop_before_search(self):
        req = wei_request()
        for invalid in (None, True, -1, 20.0):
            with self.subTest(allocation=invalid):
                catering = {**req.catering, "groceries_per_person_cents": invalid}
                with mock.patch("bureau.planner.planner.search_options") as search:
                    action = plan_trip(replace(req, catering=catering), wei_constraints())
                self.assertEqual(action.action_type, "ESCALATE")
                self.assertIn("allocations", action.payload["clarifications"][0])
                search.assert_not_called()

    def test_unknown_hard_fields_cannot_be_silently_ignored(self):
        c = wei_constraints()
        c.hard["room_type"] = "single"
        with mock.patch("bureau.planner.planner.search_options") as search:
            action = plan_trip(wei_request(), c)
        search.assert_not_called()
        self.assertEqual(action.action_type, "ESCALATE")
        self.assertIn("room_type", action.payload["clarifications"][0])


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
        self.assertEqual(request.return_by, wei_request().return_by)
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


def _transport(price_cents, depart="18:10", **extra):
    return {"mode": "train", "depart": depart, "arrive": "20:15", "changes": 0, "overnight": False,
            "price_cents": price_cents, "source": "jinko:replay", **extra}


def _lodging(name, price_per_night_cents, capacity=40, **extra):
    return {"name": name, "rooms": 10, "capacity": capacity, "walk_minutes": 6,
            "price_per_night_cents": price_per_night_cents, "step_free_hint": True, **extra}


def _travel_only_request():
    """Historic composer examples keep their 40-person transport/lodging context."""
    return replace(wei_request(), participants=40, catering={})


class ComposeTests(unittest.TestCase):
    def test_cost_per_person_is_transport_plus_lodging_share_in_integer_cents(self):
        from bureau.planner.compose import compose_packages
        # 5000 + 40000 * 2 nights / 40 people = 5000 + 2000
        [option] = compose_packages(_travel_only_request(), [_transport(5000)], [_lodging("Hostel", 40000)], nights=2)
        self.assertEqual(7000, option.cost_per_person_cents)
        self.assertIsInstance(option.cost_per_person_cents, int)
        self.assertNotIn("price_cents", option.transport)
        self.assertNotIn("price_per_night_cents", option.lodging)
        self.assertEqual("jinko:replay", option.source)

    def test_lodging_share_is_rounded_up_never_down(self):
        from bureau.planner.compose import compose_packages
        # 40001 * 1 / 40 = 1000.025 -> 1001
        [option] = compose_packages(_travel_only_request(), [_transport(0)], [_lodging("Hostel", 40001)], nights=1)
        self.assertEqual(1001, option.cost_per_person_cents)

    def test_cheapest_package_is_kept_even_beyond_the_limit(self):
        from bureau.planner.compose import compose_packages
        transports = [_transport(p, depart=f"1{k}:00") for k, p in enumerate([9000, 8000, 7000, 1000])]
        lodgings = [_lodging(f"L{k}", 40000 + 4000 * k) for k in range(3)]
        options = compose_packages(_travel_only_request(), transports, lodgings, nights=2, limit=2)
        self.assertEqual(2, len(options))
        self.assertEqual(1000 + 2000, min(o.cost_per_person_cents for o in options))
        self.assertEqual(["A", "B"], [o.id for o in options])
        self.assertLessEqual(options[0].cost_per_person_cents, options[1].cost_per_person_cents)

    def test_lodging_without_enough_capacity_is_dropped(self):
        from bureau.planner.compose import compose_packages
        options = compose_packages(_travel_only_request(), [_transport(5000)],
                                   [_lodging("Too small", 10000, capacity=30), _lodging("Fits", 50000)], nights=2)
        self.assertEqual(["Fits"], [o.lodging["name"] for o in options])
        self.assertEqual([], compose_packages(_travel_only_request(), [_transport(5000)],
                                              [_lodging("Too small", 10000, capacity=30)], nights=2))

    def test_each_transport_is_represented_before_filling_by_cost(self):
        from bureau.planner.compose import compose_packages
        transports = [_transport(1000, depart="17:00"), _transport(6000, depart="18:00")]
        lodgings = [_lodging(f"L{k}", 40000 + 400 * k) for k in range(5)]
        options = compose_packages(_travel_only_request(), transports, lodgings, nights=1, limit=3)
        self.assertEqual({"17:00", "18:00"}, {o.transport["depart"] for o in options})

    def test_composed_packages_go_through_the_same_checks(self):
        from bureau.planner.compose import compose_packages
        from bureau.planner.constraints import evaluate
        req = _travel_only_request()
        options = compose_packages(req, [_transport(10000), _transport(3000, overnight=True)],
                                   [_lodging("Hostel", 40000)], nights=2)
        constraints = wei_constraints()
        constraints.hard["participants"] = req.participants
        valid, _ = evaluate(options, constraints)
        self.assertEqual([12000], [o.cost_per_person_cents for o in valid])

    def test_catering_is_added_once_and_can_make_the_complete_package_over_budget(self):
        from bureau.planner.compose import compose_packages
        req = wei_request()
        [option] = compose_packages(req, [_transport(3500, mode="coach", capacity=106)],
                                    [_lodging("Group venue", 300000, capacity=100)], nights=2)
        self.assertEqual(11700, option.cost_per_person_cents)
        self.assertEqual({"coach": 3500, "lodging": 6000, "groceries": 2000, "food_transport": 200},
                         option.cost_breakdown_per_person_cents)
        constraints = wei_constraints()
        constraints.hard["max_cost_per_person_cents"] = 12000
        valid, _ = evaluate([option], constraints)
        self.assertEqual([option], valid)
        req = replace(req, catering={**req.catering, "groceries_per_person_cents": 3000})
        [expensive] = compose_packages(req, [_transport(3500, mode="coach", capacity=106)],
                                       [_lodging("Group venue", 300000, capacity=100)], nights=2)
        self.assertEqual(12700, expensive.cost_per_person_cents)
        self.assertEqual([], evaluate([expensive], constraints)[0])

    def test_coach_capacity_must_fit_all_registered_students(self):
        from bureau.planner.compose import compose_packages
        options = compose_packages(wei_request(), [_transport(1000, capacity=53), _transport(2000, capacity=106)],
                                   [_lodging("Group venue", 100000, capacity=100)], nights=2)
        self.assertEqual([106], [option.transport["capacity"] for option in options])


class ExplainTests(unittest.TestCase):
    def setUp(self):
        from bureau.planner.constraints import evaluate
        from bureau.planner.planner import search_options
        self.req = wei_request()
        self.c = wei_constraints()
        self.valid, self.checks = evaluate(search_options(self.req), self.c)

    def assert_names_present(self, text):
        self.assertIn(f"Option {self.valid[0].id}", text)
        for option_id, option_checks in self.checks.items():
            if option_id in {o.id for o in self.valid}:
                continue
            self.assertIn(f"Option {option_id}", text)
            for ch in option_checks:
                if ch.verified and not ch.passed:
                    self.assertIn(ch.name, text)

    def test_template_names_the_top_option_and_every_broken_constraint(self):
        from bureau.planner.explain import explain
        self.assert_names_present(explain(self.valid, self.checks, self.c))

    def test_llm_prose_is_used_and_the_rejection_list_is_still_exact(self):
        from bureau.planner.explain import explain
        from tests.fake_llm import FakeClient
        client = FakeClient(["Option D returns earliest; Option A costs less and returns later."])
        text = explain(self.valid, self.checks, self.c, client=client)
        self.assertTrue(text.startswith("Option D returns earliest"))
        self.assert_names_present(text)
        facts = json.loads(client.requests[0]["messages"][1]["content"])
        self.assertEqual(["D", "A", "B"], [o["option"] for o in facts["valid_options_ranked"]])

    def test_llm_text_without_the_top_option_falls_back_to_the_template(self):
        from bureau.planner.explain import explain
        from tests.fake_llm import FakeClient
        text = explain(self.valid, self.checks, self.c, client=FakeClient(["The hotel is nice."]))
        self.assertNotIn("The hotel is nice", text)
        self.assert_names_present(text)

    def test_llm_failure_falls_back_to_the_template(self):
        from bureau.planner.explain import explain
        from tests.fake_llm import FakeClient
        text = explain(self.valid, self.checks, self.c, client=FakeClient([]))  # empty script: raises
        self.assert_names_present(text)

    def test_explain_never_changes_ranking_or_checks(self):
        from bureau.planner.explain import explain
        from tests.fake_llm import FakeClient
        ranked_before, checks_before = deepcopy(self.valid), deepcopy(self.checks)
        explain(self.valid, self.checks, self.c, client=FakeClient(["Option A wins."]))
        self.assertEqual(ranked_before, self.valid)
        self.assertEqual(checks_before, self.checks)

    def test_priorities_are_plain_words_for_the_model_and_the_template(self):
        from bureau.planner.explain import explain
        from bureau.planner.extract import SOFT_KEYS
        from tests.fake_llm import FakeClient
        client = FakeClient(["The hotel is nice."])  # rejected prose: the template is used
        text = explain(self.valid, self.checks, self.c, client=client)
        facts = client.requests[0]["messages"][1]["content"]
        for key in SOFT_KEYS:
            self.assertNotIn(key, text)
            self.assertNotIn(key, facts)
        self.assertIn("fewer changes", facts)

    def test_plan_trip_passes_the_client_to_explain(self):
        from tests.fake_llm import FakeClient
        action = plan_trip(self.req, self.c, client=FakeClient(["Option D returns earliest by coach."]))
        self.assertTrue(action.description.startswith("Option D returns earliest by coach."))
        self.assertEqual(["D", "A", "B"], action.payload["ranked_valid"])



class SearchOptionsTests(unittest.TestCase):
    SEARCH = {"city": "Deauville", "country_code": "fr", "station": [49.3583, 0.0858],
              "checkin": "2026-10-09", "checkout": "2026-10-11", "rooms": 50}

    def test_search_composes_recorded_transport_with_cached_jinko_hotels(self):
        from bureau.planner.planner import search_options
        options = search_options(wei_request(), self.SEARCH)
        self.assertGreater(len(options), 5)
        self.assertTrue(all("jinko:replay" in o.source and "recorded transport" in o.source for o in options))
        self.assertTrue(all(o.lodging["group_block_confirmed"] is False for o in options))
        for option in options:
            self.assertGreaterEqual(option.transport["capacity"], 100)
            self.assertEqual(2000, option.cost_breakdown_per_person_cents["groceries"])
            self.assertEqual(200, option.cost_breakdown_per_person_cents["food_transport"])
            self.assertEqual(option.cost_per_person_cents, sum(option.cost_breakdown_per_person_cents.values()))

    def test_search_falls_back_to_recorded_packages_without_a_cache_or_parameters(self):
        from bureau.planner.planner import recorded_packages, search_options
        recorded = recorded_packages("wei")
        self.assertEqual(recorded, search_options(wei_request()))
        self.assertEqual(recorded, search_options(wei_request(), {**self.SEARCH, "city": "Nowhere"}))

    def test_jinko_plan_gates_and_diagnoses_like_the_recorded_one(self):
        c = wei_constraints()
        action = plan_trip(wei_request(), c, search=self.SEARCH)
        self.assertEqual(15000, c.hard["max_cost_per_person_cents"])
        self.assertEqual("SELECT_TRAVEL_PLAN", action.action_type)
        self.assertEqual(["F", "C", "E"], action.payload["ranked_valid"])
        valid_prices = [row["option"]["cost_per_person_cents"] for row in action.payload["options"]
                        if row["valid"]]
        self.assertEqual([13559, 14059, 14259], valid_prices)
        for budget in (12000, 9000):
            with self.subTest(budget=budget):
                c.hard["max_cost_per_person_cents"] = budget
                rejected = plan_trip(wei_request(), c, search=self.SEARCH)
                self.assertEqual("ESCALATE", rejected.action_type)
                self.assertTrue(all(not row["valid"] for row in rejected.payload["options"]))


if __name__ == "__main__":
    unittest.main()
