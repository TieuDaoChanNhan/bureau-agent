"""Agent loop mechanics, with a scripted fake LLM (no API key, no cost).

These tests check the plumbing (tool dispatch, results fed back, termination),
not the quality of the model's decisions: that is measured by eval/ (T08).
"""
import json
from copy import deepcopy
from dataclasses import asdict
import unittest

from bureau.agent.loop import resolve_issue
from bureau.agent.tool_specs import build_handlers
from bureau.core.detect import detect_issues
from bureau.core.loader import load_event
from tests.fake_llm import FakeClient

PROPOSAL = {
    "action_type": "LINK_PAYMENT",
    "title": "Link payment f90 to Antoine Nguyen?",
    "description": "Score 0.91: please confirm before linking.",
    "evidence": [{"source_type": "payment", "source_id": "f90", "description": "A. Nguyen, nguyen.a@gmail.com"}],
    "checks": [{"name": "identity score >= 0.98", "passed": False, "detail": "0.91"}],
    "confidence": 0.91,
    "payload": {"payment_id": "f90", "participant_id": "p01"},
}


def message_issue(state, message_id="m01"):
    return next(i for i in detect_issues(state) if i.id == f"message:{message_id}")


class AgentLoopTests(unittest.TestCase):
    def test_tool_results_are_sent_back_and_proposal_ends_the_loop(self):
        state = load_event("hackathon")
        issue = message_issue(state)
        client = FakeClient([
            [("get_participant", {"id_or_email": "a.nguyen@polytechnique.edu"})],
            [("match_person", {"payment_id": "f90"})],
            [("propose_action", PROPOSAL)],
        ])
        action = resolve_issue(state, issue, client=client, verbose=False)

        self.assertEqual(action.action_type, "LINK_PAYMENT")
        self.assertEqual(action.evidence[0].source_id, "f90")
        self.assertEqual(issue.status, "proposed")
        self.assertIn(action, state.actions)
        # The match_person result (computed in code) was returned to the model.
        tool_msgs = [m for m in client.requests[-1]["messages"] if m["role"] == "tool"]
        self.assertEqual(json.loads(tool_msgs[-1]["content"])[0]["participant_id"], "p01")

    def test_escalation_marks_issue_as_needing_a_human(self):
        state = load_event("hackathon")
        issue = message_issue(state, "m04")
        client = FakeClient([[("propose_action", {**PROPOSAL, "action_type": "ESCALATE", "payload": {}})]])
        resolve_issue(state, issue, client=client, verbose=False)
        self.assertEqual(issue.status, "needs_human")

    def test_text_answer_gets_a_reminder_to_propose(self):
        state = load_event("hackathon")
        client = FakeClient(["I think we should link it.", [("propose_action", PROPOSAL)]])
        resolve_issue(state, message_issue(state), client=client, verbose=False)
        self.assertIn("propose_action", client.requests[1]["messages"][-1]["content"])

    def test_tool_error_is_reported_to_the_model_not_raised(self):
        state = load_event("hackathon")
        client = FakeClient([[("match_person", {"payment_id": "does-not-exist"})],
                             [("propose_action", PROPOSAL)]])
        resolve_issue(state, message_issue(state), client=client, verbose=False)
        tool_msg = [m for m in client.requests[-1]["messages"] if m["role"] == "tool"][-1]
        self.assertIn("error", json.loads(tool_msg["content"]))

    def test_gives_up_after_max_steps(self):
        state = load_event("hackathon")
        client = FakeClient([[("check_groups", {})]] * 3)
        with self.assertRaises(RuntimeError):
            resolve_issue(state, message_issue(state), client=client, verbose=False, max_steps=3)

    def test_malformed_json_is_reported_and_can_be_corrected(self):
        state = load_event("hackathon")
        client = FakeClient([
            [("check_eligibility", {})],
            [("propose_action", PROPOSAL)],
        ])
        original_create = client.chat.completions.create

        def create_with_malformed_arguments(**kwargs):
            response = original_create(**kwargs)
            if len(client.requests) == 1:
                response.choices[0].message.tool_calls[0].function.arguments = "{"
            return response

        client.chat.completions.create = create_with_malformed_arguments
        action = resolve_issue(state, message_issue(state), client=client, verbose=False)
        replies = [m for m in client.requests[-1]["messages"] if m["role"] == "tool"]
        self.assertIn("error", json.loads(replies[-1]["content"]))
        self.assertEqual(action.action_type, "LINK_PAYMENT")
        self.assertEqual(state.actions, [action])

    def test_non_object_arguments_are_reported_and_can_be_corrected(self):
        state = load_event("hackathon")
        client = FakeClient([
            [("check_eligibility", [])],
            [("propose_action", PROPOSAL)],
        ])
        action = resolve_issue(state, message_issue(state), client=client, verbose=False)
        replies = [m for m in client.requests[-1]["messages"] if m["role"] == "tool"]
        self.assertIn("JSON object", json.loads(replies[-1]["content"])["error"])
        self.assertEqual(state.actions, [action])

    def test_invalid_proposals_can_be_corrected_without_partial_changes(self):
        invalid = [
            ("missing title", {k: v for k, v in PROPOSAL.items() if k != "title"}),
            ("unknown action", {**PROPOSAL, "action_type": "DELETE_EVENT"}),
            ("non-object payload", {**PROPOSAL, "payload": []}),
            ("missing payload", {
                **{k: v for k, v in PROPOSAL.items() if k != "payload"},
                "action_type": "SEND_MESSAGE",
            }),
            ("missing recipient", {
                **PROPOSAL, "action_type": "SEND_MESSAGE", "payload": {"text": "Hello"},
            }),
            ("missing text", {
                **PROPOSAL, "action_type": "SEND_MESSAGE",
                "payload": {"to": "organizer@example.org"},
            }),
            ("empty recipient list", {
                **PROPOSAL, "action_type": "SEND_MESSAGE", "payload": {"to": [], "text": "Draft"},
            }),
            ("blank recipient", {
                **PROPOSAL, "action_type": "SEND_MESSAGE", "payload": {"to": [""], "text": "Draft"},
            }),
            ("missing participant", {**PROPOSAL, "payload": {"payment_id": "f90"}}),
            ("missing payment", {**PROPOSAL, "payload": {"participant_id": "p01"}}),
            ("link reply without recipient", {
                **PROPOSAL, "payload": {**PROPOSAL["payload"], "message": "Thank you"},
            }),
            ("move without participant", {
                **PROPOSAL, "action_type": "MOVE_MEMBER", "payload": {"from_group": "t-orbit"},
            }),
            ("move without groups", {
                **PROPOSAL, "action_type": "MOVE_MEMBER", "payload": {"participant_id": "p02"},
            }),
            ("empty group replacement", {
                **PROPOSAL, "action_type": "UPDATE_GROUPS", "payload": {"groups": []},
            }),
            ("incomplete group replacement", {
                **PROPOSAL, "action_type": "UPDATE_GROUPS", "payload": {"groups": [{"id": "t-new"}]},
            }),
            ("non-boolean check", {
                **PROPOSAL, "checks": [{"name": "identity", "passed": "false"}],
            }),
        ]
        for name, proposal in invalid:
            with self.subTest(name=name):
                state = load_event("hackathon")
                issue = message_issue(state)
                initial_status = issue.status
                client = FakeClient([
                    [("propose_action", proposal)],
                    [("propose_action", PROPOSAL)],
                ])
                original_create = client.chat.completions.create

                def create_after_checking_state(**kwargs):
                    self.assertEqual(issue.status, initial_status)
                    self.assertEqual(state.actions, [])
                    return original_create(**kwargs)

                client.chat.completions.create = create_after_checking_state
                action = resolve_issue(state, issue, client=client, verbose=False)
                self.assertEqual(len(client.requests), 2)
                replies = [m for m in client.requests[-1]["messages"] if m["role"] == "tool"]
                self.assertIn("error", json.loads(replies[-1]["content"]))
                self.assertEqual(state.actions, [action])
                self.assertEqual(action.payload, PROPOSAL["payload"])
                self.assertEqual(issue.status, "proposed")

    def test_invalid_group_replacement_is_rejected_without_mutating_state(self):
        state = load_event("hackathon")
        original = deepcopy(state.groups)
        issue = message_issue(state)
        groups = [{k: v for k, v in asdict(g).items() if k != "declared_at"}
                  for g in state.groups]
        client = FakeClient([
            [("propose_action", {**PROPOSAL, "action_type": "UPDATE_GROUPS",
                                 "payload": {"groups": groups}})],
            [("propose_action", {**PROPOSAL, "action_type": "ESCALATE", "payload": {}})],
        ])
        action = resolve_issue(state, issue, client=client, verbose=False)
        replies = [m for m in client.requests[-1]["messages"] if m["role"] == "tool"]
        error = json.loads(replies[-1]["content"])["error"]
        self.assertIn("multiple_group_membership", error)
        self.assertIn("group_over_capacity", error)
        self.assertEqual(state.groups, original)
        self.assertEqual(state.actions, [action])
        self.assertEqual(action.action_type, "ESCALATE")

    def test_new_teams_cannot_replace_and_drop_existing_assignments(self):
        state = load_event("hackathon")
        original = deepcopy(state.groups)
        client = FakeClient([
            [("propose_action", {**PROPOSAL, "action_type": "UPDATE_GROUPS", "payload": {
                "groups": [{"id": "t-new", "kind": "team", "name": "New team",
                            "members": ["p13", "p14"], "capacity_min": 2, "capacity_max": 4}],
            }})],
            [("propose_action", {**PROPOSAL, "action_type": "ESCALATE", "payload": {}})],
        ])
        action = resolve_issue(state, message_issue(state), client=client, verbose=False)
        replies = [m for m in client.requests[-1]["messages"] if m["role"] == "tool"]
        self.assertIn("must retain assigned participants", json.loads(replies[-1]["content"])["error"])
        self.assertEqual(state.groups, original)
        self.assertEqual(state.actions, [action])
        self.assertEqual(action.action_type, "ESCALATE")

    def test_batched_proposal_waits_and_answers_every_tool_call(self):
        state = load_event("hackathon")
        client = FakeClient([
            [("propose_action", PROPOSAL), ("check_eligibility", {})],
            [("propose_action", PROPOSAL)],
        ])
        action = resolve_issue(state, message_issue(state), client=client, verbose=False)
        self.assertEqual(len(client.requests), 2)
        conversation = client.requests[-1]["messages"]
        calls = next(m["tool_calls"] for m in conversation if m.get("tool_calls"))
        replies = {m["tool_call_id"]: json.loads(m["content"])
                   for m in conversation if m["role"] == "tool"}
        self.assertEqual(set(replies), {call["id"] for call in calls})
        self.assertIn("error", replies[calls[0]["id"]])
        self.assertIn("unpaid", replies[calls[1]["id"]])
        self.assertEqual(state.actions, [action])
        self.assertTrue(all(request["parallel_tool_calls"] is True for request in client.requests))

    def test_final_turn_requests_a_model_selected_proposal(self):
        state = load_event("hackathon")
        client = FakeClient([
            [("check_eligibility", {})],
            [("match_person", {"payment_id": "f90"})],
            [("propose_action", PROPOSAL)],
        ])
        action = resolve_issue(state, message_issue(state), max_steps=3, client=client, verbose=False)
        self.assertEqual(client.requests[0]["tool_choice"], "auto")
        self.assertEqual(client.requests[1]["tool_choice"], "auto")
        self.assertEqual(client.requests[-1]["tool_choice"], {
            "type": "function", "function": {"name": "propose_action"},
        })
        self.assertFalse(client.requests[-1]["parallel_tool_calls"])
        self.assertIn("choose ESCALATE", client.requests[-1]["messages"][-1]["content"])
        self.assertEqual(action.action_type, "LINK_PAYMENT")
        self.assertEqual(state.actions, [action])

    def test_investigation_and_proposal_do_not_execute_changes(self):
        state = load_event("hackathon")
        original = deepcopy((state.participants, state.payments, state.groups))
        client = FakeClient([
            [("check_eligibility", {})],
            [("match_person", {"payment_id": "f90"})],
            [("propose_action", PROPOSAL)],
        ])
        action = resolve_issue(state, message_issue(state), client=client, verbose=False)
        self.assertEqual((state.participants, state.payments, state.groups), original)
        self.assertIsNone(next(p for p in state.payments if p.id == "f90").participant_id)
        self.assertTrue(action.requires_approval)
        self.assertEqual(state.actions, [action])

    def test_recipient_lists_are_preserved_for_message_and_payment_replies(self):
        recipients = ["first@participants.example", "second@participants.example"]
        for action_type in ("SEND_MESSAGE", "LINK_PAYMENT"):
            with self.subTest(action_type=action_type):
                state = load_event("hackathon")
                payload = {"to": recipients, "text": "A draft reminder."}
                if action_type == "LINK_PAYMENT":
                    payload = {**PROPOSAL["payload"], "to": recipients, "message": "A draft reply."}
                client = FakeClient([[("propose_action", {
                    **PROPOSAL, "action_type": action_type, "payload": payload,
                })]])
                action = resolve_issue(state, message_issue(state), client=client, verbose=False)
                self.assertEqual(action.payload["to"], recipients)

    def test_source_message_context_is_structured_and_scoped_to_issue(self):
        state = load_event("hackathon")
        client = FakeClient([[("propose_action", PROPOSAL)]])
        resolve_issue(state, message_issue(state), client=client, verbose=False)
        context = json.loads(client.requests[0]["messages"][1]["content"].split("\n", 1)[1])
        self.assertEqual(context["issue"]["id"], "message:m01")
        self.assertEqual(len(context["messages"]), 1)
        self.assertEqual(context["messages"][0]["sender"], "a.nguyen@polytechnique.edu")
        self.assertEqual(context["messages"][0]["channel"], "email")
        self.assertIn("+02:00", context["messages"][0]["received_at"])

    def test_complete_executor_payloads_are_preserved(self):
        payloads = {
            "SEND_MESSAGE": {"to": "person@participants.example", "text": "A complete draft."},
            "LINK_PAYMENT": {**PROPOSAL["payload"], "to": "person@participants.example",
                             "message": "A draft payment confirmation."},
            "MOVE_MEMBER": {"participant_id": "p02", "from_group": "t-nomads"},
            "UPDATE_GROUPS": {"groups": [{
                "id": "t-sample", "kind": "team", "name": "Sample", "members": ["p13", "p14"],
                "capacity_min": 2, "capacity_max": 4,
            }]},
            "ESCALATE": {"note": "Please confirm the missing policy."},
        }
        for action_type, payload in payloads.items():
            with self.subTest(action_type=action_type):
                state = load_event("hackathon")
                if action_type == "UPDATE_GROUPS":
                    state.groups = []  # A complete replacement when no groups exist yet.
                client = FakeClient([[("propose_action", {
                    **PROPOSAL, "action_type": action_type, "payload": payload,
                })]])
                action = resolve_issue(state, message_issue(state), client=client, verbose=False)
                self.assertEqual(action.payload, payload)
                self.assertEqual(action.action_type, action_type)


class AgentToolContextTests(unittest.TestCase):
    def test_payment_and_group_records_are_available_without_mutating_state(self):
        state = load_event("hackathon")
        original = deepcopy((state.payments, state.groups))
        handlers = build_handlers(state)
        payment = handlers["get_payment"]("f90")
        self.assertEqual(payment["amount_cents"], 1000)
        self.assertEqual(payment["payer_email"], "nguyen.a@gmail.com")
        self.assertIsNone(payment["participant_id"])
        self.assertIn("error", handlers["get_payment"]("missing"))
        groups = handlers["list_groups"]()
        orbit = next(g for g in groups if g["id"] == "t-orbit")
        self.assertEqual(orbit["members"], ["p02", "p03", "p04"])
        self.assertEqual(orbit["capacity_max"], 4)
        orbit["members"].clear()
        payment["participant_id"] = "p01"
        self.assertEqual((state.payments, state.groups), original)

    def test_group_candidates_respect_preferences_and_existing_membership(self):
        state = load_event("hackathon")
        state.participant("p02").looking_for_group = True
        handlers = build_handlers(state)
        candidates = handlers["list_group_candidates"]()
        ids = {person["id"] for person in candidates}
        self.assertEqual(ids, {"p13", "p14", "p15", "p16", "p17", "p18", "p48", "p49"})
        self.assertNotIn("p50", ids)  # Explicitly wants to remain solo.
        self.assertNotIn("p02", ids)  # Already grouped even though the flag is set.
        candidates[0]["skills"].clear()
        self.assertTrue(state.participant(candidates[0]["id"]).skills)

    def test_all_rules_can_be_read_when_keyword_search_is_inconclusive(self):
        state = load_event("hackathon")
        handlers = build_handlers(state)
        self.assertEqual(handlers["search_rules"]("unspecifiedlanguage"), [])
        rules = handlers["list_rules"]()
        self.assertEqual({r["rule_id"] for r in rules}, {r.id for r in state.rules})
        existing_work = next(r for r in rules if r["rule_id"] == "§7")
        self.assertIn("existing project", existing_work["text"])
        self.assertEqual(existing_work["source"], "rules.md")


if __name__ == "__main__":
    unittest.main()
