"""Public server isolation, replay and atomic model budgets; no real API calls."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from api.sessions import COOKIE, TTL, cleanup
from bureau.core import store
from bureau.core.llm_usage import LiveUnavailable, create_completion, database
from bureau.core.session import current_session
from demo.replay import BUDGET_ANSWER
from tests.fake_llm import FakeClient

EXTRACTED = {"hard": {"participants": 100, "max_cost_per_person_cents": 15000, "arrive_before": "21:00",
                      "no_overnight": True, "step_free_rooms": 2},
             "soft": ["fewer_changes", "early_return", "lower_cost"],
             "organizer_verified": ["step_free_rooms"], "clarifications": []}
PROPOSAL = [("propose_action", {"action_type": "ESCALATE", "title": "Ask an organizer",
                              "description": "A fake live proposal.", "payload": {}})]


class PublicDemoTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.runtime = Path(tmp.name)
        self.fake = FakeClient([])
        for target, value in (("bureau.core.store.RUNTIME_DIR", self.runtime),
                              ("bureau.config.DEMO_MODE", True),
                              ("bureau.config.OPENAI_API_KEY", ""),
                              ("bureau.config.DEMO_DAILY_LLM_LIMIT", 400),
                              ("bureau.config.DEMO_SESSION_LLM_LIMIT", 60)):
            handle = patch(target, value)
            handle.start()
            self.addCleanup(handle.stop)
        for target in ("bureau.agent.loop._default_client", "api.main._planner_client"):
            handle = patch(target, return_value=self.fake)
            handle.start()
            self.addCleanup(handle.stop)
        self.client = self.browser()

    def browser(self):
        client = TestClient(app, base_url="https://demo.test")
        self.addCleanup(client.close)
        return client

    def run_issue(self, issue="message:m01", client=None):
        return (client or self.client).post("/api/events/hackathon/run", params={"issue_id": issue})

    def test_two_browsers_approve_reset_outbox_and_paths_are_isolated(self):
        other = self.browser()
        pristine = other.get("/api/events/hackathon").json()
        response = self.run_issue()
        self.assertEqual(200, response.status_code, response.text)
        self.assertTrue(response.json()["replay"])
        action = response.json()["actions"][0]
        self.assertEqual(404, other.get(f"/api/actions/{action['id']}").status_code)
        approved = self.client.post(f"/api/actions/{action['id']}/approve", json={"edited_description": "Only browser one"})
        self.assertEqual(200, approved.status_code, approved.text)
        self.assertEqual(pristine, other.get("/api/events/hackathon").json())
        self.assertEqual([], other.get("/api/events/hackathon/outbox").json())
        self.assertEqual("Only browser one", self.client.get("/api/events/hackathon/outbox").json()[0]["text"])
        self.assertNotEqual(self.client.cookies.get(COOKIE), other.cookies.get(COOKIE))
        self.assertTrue((self.runtime / self.client.cookies.get(COOKIE) / "hackathon/state.json").exists())
        other.post("/api/events/hackathon/reset")
        self.assertEqual(1, len(self.client.get("/api/events/hackathon/outbox").json()))
        self.assertEqual(409, self.client.post(f"/api/actions/{action['id']}/approve").status_code)
        self.assertEqual([], self.fake.requests)

    def test_cookie_expiry_cleanup_and_path_injection(self):
        self.client.cookies.set(COOKIE, "../../outside")
        response = self.client.get("/api/events")
        header = response.headers["set-cookie"]
        self.assertIn("HttpOnly", header)
        self.assertIn("Secure", header)
        self.assertIn("SameSite=lax", header)
        self.assertIn("Max-Age=86400", header)
        # Read the server's cookie, excluding the malicious manually inserted one.
        session = response.cookies.get(COOKIE)
        self.assertRegex(session, r"^[a-f0-9]{32}$")
        self.client.cookies.clear()
        self.client.cookies.set(COOKIE, session)
        (self.runtime / session / ".created").write_text(str(time.time() - TTL - 1))
        fresh = self.client.get("/api/events").cookies.get(COOKIE)
        self.assertNotEqual(session, fresh)
        unrelated = self.runtime / "hackathon"
        unrelated.mkdir()
        cleanup(time.time(), {fresh})
        self.assertFalse((self.runtime / session).exists())
        self.assertTrue((self.runtime / fresh).exists())
        self.assertTrue(unrelated.exists())

    def test_replayed_message_reply_goes_to_the_message_sender(self):
        # Regression: the sender is on the message record, not in the issue details.
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch("bureau.config.DEMO_DAILY_LLM_LIMIT", 0):
            response = self.run_issue("message:m02")
        self.assertEqual(200, response.status_code, response.text)
        action = next(a for a in response.json()["actions"] if a["issue_id"] == "message:m02")
        sender = next(m["sender"] for m in json.loads((Path(__file__).resolve().parents[1] / "data/hackathon/messages.json").read_text(encoding="utf-8"))
                      if m["id"] == "m02")
        self.assertEqual(sender, action["payload"]["to"])
        self.assertEqual([], self.fake.requests)

    def test_zero_daily_limit_replays_run_and_plan_without_model(self):
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch("bureau.config.DEMO_DAILY_LLM_LIMIT", 0):
            response = self.run_issue()
            self.assertTrue(response.json()["replay"])
            self.assertEqual("live limit reached", response.json()["replay_reason"])
            question = self.client.post("/api/events/wei/plan").json()
            action = next(a for a in question["actions"] if a["id"] == question["action_id"])
            text = action["payload"]["request_text"] + "\n\nOrganizer answers: " + BUDGET_ANSWER
            response = self.client.post("/api/events/wei/plan", json={"text": text})
            self.assertEqual(200, response.status_code, response.text)
            self.assertTrue(response.json()["replay"])
            options = response.json()["actions"][0]["payload"]["ranked_valid"]
            self.assertEqual(["F", "C", "E"], options)  # same as a live run on the saved Jinko responses
            response = self.client.post("/api/events/wei/plan", json={"text": text, "overrides": {"max_cost_per_person_cents": 9000}})
            self.assertEqual("ESCALATE", response.json()["actions"][0]["action_type"])
        self.assertEqual([], self.fake.requests)

    def test_unknown_input_returns_429_without_call_or_saved_proposal(self):
        message = self.client.post("/api/events/hackathon/messages", json={"sender": "test@example.org", "text": "An entirely new request"}).json()
        response = self.run_issue(message["issue_id"])
        self.assertEqual(429, response.status_code)
        self.assertIn("No saved example", response.json()["detail"])
        response = self.client.post("/api/events/wei/plan", json={"text": "A trip for 99 people to another city"})
        self.assertEqual(429, response.status_code)
        self.assertEqual([], self.client.get("/api/events/wei").json()["actions"])
        self.assertEqual([], self.fake.requests)

    def test_session_cap_is_shared_between_run_and_plan_and_survives_reset(self):
        self.fake.script = [PROPOSAL]
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch("bureau.config.DEMO_SESSION_LLM_LIMIT", 1):
            with self.assertLogs("uvicorn.error", level="INFO") as log:
                live = self.run_issue("message:m02")
            self.assertFalse(live.json()["replay"])
            self.assertIn(self.client.cookies.get(COOKIE), "".join(log.output))
            self.client.post("/api/events/hackathon/reset")
            replay = self.client.post("/api/events/wei/plan")
            self.assertTrue(replay.json()["replay"])
            self.assertEqual(1, len(self.fake.requests))
            self.assertEqual(2048, self.fake.requests[0]["max_completion_tokens"])
            other = self.browser()
            self.fake.script = [PROPOSAL]
            self.assertFalse(self.run_issue("message:m02", other).json()["replay"])

    def test_global_cap_applies_to_another_browser(self):
        self.fake.script = [PROPOSAL]
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch("bureau.config.DEMO_DAILY_LLM_LIMIT", 1):
            self.assertFalse(self.run_issue("message:m02").json()["replay"])
            self.assertTrue(self.run_issue(client=self.browser()).json()["replay"])
        self.assertEqual(1, len(self.fake.requests))

    def test_overlapping_requests_keep_their_session_context(self):
        other = self.browser()
        for client in (self.client, other):
            client.get("/api/events")
        barrier = threading.Barrier(2)
        def resolve(state, issue, **kwargs):
            from demo.replay import issue_example
            session = current_session.get()
            barrier.wait(timeout=5)
            action = issue_example(state, issue)
            action.description = session
            state.actions.append(action)
            issue.status = "proposed"
            return action
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch("bureau.agent.loop.resolve_issue", side_effect=resolve):
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(self.run_issue, client=client) for client in (self.client, other)]
                for client, future in zip((self.client, other), futures):
                    result = future.result()
                    self.assertEqual(200, result.status_code, result.text)
                    self.assertEqual(client.cookies.get(COOKIE), result.json()["actions"][0]["description"])

    def test_provider_limit_uses_replay_and_counts_the_attempt(self):
        error = RuntimeError("provider limit")
        error.status_code = 429
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch.object(self.fake.chat.completions, "create", side_effect=error) as create:
            response = self.run_issue()
        self.assertTrue(response.json()["replay"])
        self.assertEqual("live limit reached", response.json()["replay_reason"])
        create.assert_called_once()
        with database() as connection:
            self.assertEqual(1, connection.execute("SELECT count(*) FROM calls").fetchone()[0])

    def test_cap_in_middle_of_agent_loop_returns_saved_proposal(self):
        self.fake.script = ["Investigating"]
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch("bureau.config.DEMO_DAILY_LLM_LIMIT", 1):
            response = self.run_issue()
        self.assertTrue(response.json()["replay"])
        self.assertEqual("LINK_PAYMENT", response.json()["actions"][0]["action_type"])
        self.assertEqual(1, len(self.fake.requests))

    def test_cap_between_extraction_and_explanation_does_not_call_twice(self):
        self.fake.script = [json.dumps(EXTRACTED)]
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch("bureau.config.DEMO_DAILY_LLM_LIMIT", 1):
            response = self.client.post("/api/events/wei/plan", json={"text": BUDGET_ANSWER})
        self.assertEqual(200, response.status_code, response.text)
        self.assertTrue(response.json()["replay"])
        self.assertEqual(1, len(self.fake.requests))

    def test_live_planner_counts_both_model_calls(self):
        self.fake.script = [json.dumps(EXTRACTED), "Option F is the best match."]
        with patch("bureau.config.OPENAI_API_KEY", "test-only"):
            response = self.client.post("/api/events/wei/plan")
        self.assertEqual(200, response.status_code, response.text)
        self.assertFalse(response.json()["replay"])
        self.assertEqual(2, len(self.fake.requests))
        with database() as connection:
            self.assertEqual(2, connection.execute("SELECT count(*) FROM calls").fetchone()[0])

    def test_parallel_reservations_cannot_overspend(self):
        def attempt(number):
            token = current_session.set(f"{number:032x}")
            try:
                client = FakeClient(["OK"])
                create_completion(client, purpose="test", model="fake", messages=[])
                return len(client.requests)
            except LiveUnavailable:
                return 0
            finally:
                current_session.reset(token)
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch("bureau.config.DEMO_DAILY_LLM_LIMIT", 3):
            with ThreadPoolExecutor(max_workers=8) as executor:
                self.assertEqual(3, sum(executor.map(attempt, range(20))))

    def test_failed_call_counts_and_next_utc_day_reopens_global_budget(self):
        token = current_session.set("a" * 32)
        self.addCleanup(current_session.reset, token)
        with patch("bureau.config.OPENAI_API_KEY", "test-only"), patch("bureau.config.DEMO_DAILY_LLM_LIMIT", 1):
            with self.assertRaises(IndexError):
                create_completion(self.fake, purpose="failure", model="fake", messages=[])
            with self.assertRaises(LiveUnavailable):
                create_completion(self.fake, purpose="blocked", model="fake", messages=[])
            with database() as connection:
                connection.execute("UPDATE calls SET day='2000-01-01'")
                connection.commit()
            self.fake.script = ["OK"]
            create_completion(self.fake, purpose="new-day", model="fake", messages=[])
        self.assertEqual(2, len(self.fake.requests))


if __name__ == "__main__":
    unittest.main()
