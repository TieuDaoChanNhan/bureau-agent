"""End-to-end verification of the static customer demo (no API calls or keys)."""
from __future__ import annotations

import functools
import json
import os
import threading
import time
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

DEMO = Path(__file__).resolve().parent
ARTIFACTS = DEMO / "artifacts"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(DEMO / "site")))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = os.environ.get("DEMO_BASE_URL", f"http://127.0.0.1:{cls.server.server_port}").rstrip("/")
        cls.pw = sync_playwright().start()
        cls.load_times = []
        cls.browser = cls.pw.chromium.launch(headless=True, executable_path=os.environ.get("DEMO_CHROME_PATH") or None)
        ARTIFACTS.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        (ARTIFACTS / "static-load-times.json").write_text(json.dumps({"url": cls.url,
            "ready_seconds": cls.load_times, "kind": "fresh browser contexts; not a Render cold start"}, indent=2))
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 1000})
        self.page = self.context.new_page()
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda request: self.requests.append(request.url))
        start = time.perf_counter()
        self.page.goto(self.url)
        self.page.wait_for_function("Object.keys(ui.summaries).length === 2 && !ui.busy")
        self.load_times.append(round(time.perf_counter() - start, 3))

    def tearDown(self):
        self.page.screenshot(path=str(ARTIFACTS / f"{self._testMethodName}-last.png"))
        self.context.close()
        self.assertEqual(self.errors, [])
        self.assertTrue(all(url.startswith(self.url + "/") for url in self.requests),
                        [url.split("?", 1)[0] for url in self.requests])
        self.assertFalse(any("/api/" in url for url in self.requests), self.requests)

    def api(self, path, body=None, page=None):
        return (page or self.page).evaluate("([path, body]) => demoStore.request(path, body === null ? {} : {method:'POST',body:JSON.stringify(body)})", [path, body])

    def test_full_30_step_tour(self):
        self.page.locator("#heroTourBtn").click()
        clicks = {
            4: '[data-act="retry"]', 8: '[data-act="edit"]', 9: '.tour-act',
            10: '[data-act="approve"]', 12: '#outboxBtn', 14: '#composeBtn',
            15: '#composeForm button[type="submit"]', 18: '[data-ev="wei"]',
            20: '[data-act="plan"]', 21: '#answerForm button[type="submit"]',
            24: '[data-budget="9000"]', 26: '[data-budget=""]', 27: '[data-act="choose"][data-opt="A"]',
        }
        self.assertEqual(self.page.evaluate("STEPS.length"), 30)
        for index in range(30):
            with self.subTest(step=index + 1):
                self.page.wait_for_function("i => tourState.driver?.getActiveIndex() === i", arg=index)
                self.page.locator(".driver-popover-title").wait_for(state="visible")
                if index == 9:
                    self.page.locator("#draft").fill("Bonjour Antoine, merci pour votre patience ! Reply edited during the customer demo.")
                if index == 13:
                    self.assertIn("Reply edited during the customer demo.", self.page.locator("#detail").inner_text())
                    self.page.screenshot(path=str(ARTIFACTS / "edited-reply.png"))
                if index == 25:
                    self.assertIn("No valid option", self.page.locator(".diag").inner_text())
                if index == 23:
                    self.assertEqual(self.page.locator('[data-act="choose"]').count(), 2)
                    self.page.screenshot(path=str(ARTIFACTS / "trip-options.png"))
                self.page.locator(clicks.get(index, ".driver-popover-next-btn")).click()
        self.page.wait_for_function("tourState.driver === null")
        self.assertEqual(self.api("/api/events/wei")["logistics"]["id"], "A")
        self.assertEqual(len(self.api("/api/events/hackathon/outbox")), 1)
        self.assertTrue(self.api("/api/events/hackathon/audit"))
        self.assertFalse(self.page.evaluate("summary('wei').issues.some(i => i.depends_on.length && isWaiting(i, summary('wei')) )"))

    def test_isolation_approval_reset_and_refresh(self):
        second = self.context.new_page()
        second.goto(self.url)
        second.wait_for_function("Object.keys(ui.summaries).length === 2")
        pristine = self.api("/api/events/hackathon", page=second)
        self.api("/api/events/hackathon/run?issue_id=message:m01", {})
        action = self.api("/api/events/hackathon")["actions"][0]
        self.api(f"/api/actions/{action['id']}/approve", {"edited_description": "Only in browser one"})
        self.assertEqual(self.api("/api/events/hackathon", page=second), pristine)
        self.assertEqual(self.api("/api/events/hackathon/outbox", page=second), [])
        self.assertEqual(self.api("/api/events/hackathon/outbox")[0]["text"], "Only in browser one")
        self.page.evaluate("async () => { await selectEvent('hackathon'); ui.view = 'outbox'; render(); }")
        self.page.locator("#console").scroll_into_view_if_needed()
        self.page.screenshot(path=str(ARTIFACTS / "session-one.png"))
        second.locator("#console").scroll_into_view_if_needed()
        second.screenshot(path=str(ARTIFACTS / "session-two.png"))
        # Duplicate approval cannot create another reply.
        error = self.page.evaluate("id => {try {demoStore.request('/api/actions/'+id+'/approve',{method:'POST'});} catch(e){return e.message;}}", action["id"])
        self.assertIn("409", error)
        self.assertEqual(len(self.api("/api/events/hackathon/outbox")), 1)
        self.api("/api/events/wei/plan", {})
        self.api("/api/events/hackathon/reset", {})
        self.assertEqual(self.api("/api/events/hackathon"), pristine)
        self.assertEqual(len(self.api("/api/events/wei")["actions"]), 1)
        self.page.reload()
        self.page.wait_for_function("Object.keys(ui.summaries).length === 2")
        self.assertEqual(len(self.api("/api/events/wei")["actions"]), 1)
        second.close()

    def test_refresh_keeps_replies_drafts_and_separate_private_browser(self):
        self.page.evaluate("tourShow('hackathon', 'issue:message:m01')")
        self.page.locator('[data-act="retry"]').click()
        self.page.wait_for_function("!ui.busy && summary().actions.length > 0")
        self.page.locator('[data-act="edit"]').click()
        self.page.locator("#draft").fill("An edited reply saved before refreshing.")
        self.page.locator('[data-act="edit"]').click()
        session_id = self.page.evaluate("demoStore.sessionInfo().id")
        self.page.reload()
        self.page.wait_for_function("Object.keys(ui.summaries).length === 2")
        self.assertEqual(self.page.evaluate("demoStore.sessionInfo().id"), session_id)
        self.page.evaluate("tourShow('hackathon', 'issue:message:m01')")
        self.assertEqual(self.page.locator("#draft").inner_text(), "An edited reply saved before refreshing.")
        self.page.locator('[data-act="approve"]').click()
        self.page.wait_for_function("!ui.busy")
        self.page.reload()
        self.page.wait_for_function("Object.keys(ui.summaries).length === 2")
        self.assertEqual(self.api("/api/events/hackathon/outbox")[0]["text"], "An edited reply saved before refreshing.")
        private_context = self.browser.new_context()
        try:
            private = private_context.new_page()
            private.goto(self.url)
            private.wait_for_function("Object.keys(ui.summaries).length === 2")
            self.assertEqual(self.api("/api/events/hackathon/outbox", page=private), [])
            self.assertNotEqual(private.evaluate("demoStore.sessionInfo().id"), session_id)
        finally:
            private_context.close()

    def test_expiry_corrupt_storage_and_no_storage(self):
        self.api("/api/events/hackathon/run?issue_id=message:m01", {})
        old_id = self.page.evaluate("demoStore.sessionInfo().id")
        self.page.evaluate("""() => {
          const key = 'bureau-demo-session-v2';
          const snapshot = JSON.parse(sessionStorage.getItem(key));
          snapshot.expiresAt = Date.now() - 1;
          sessionStorage.setItem(key, JSON.stringify(snapshot));
        }""")
        self.page.reload()
        self.page.wait_for_function("Object.keys(ui.summaries).length === 2")
        self.assertNotEqual(self.page.evaluate("demoStore.sessionInfo().id"), old_id)
        self.assertEqual(self.api("/api/events/hackathon")["actions"], [])
        self.page.evaluate("sessionStorage.setItem('bureau-demo-session-v2', '{broken')")
        self.page.reload()
        self.page.wait_for_function("Object.keys(ui.summaries).length === 2")
        self.assertEqual(self.api("/api/events/hackathon")["actions"], [])
        self.page.add_init_script("Object.defineProperty(window, 'sessionStorage', {get() {throw new Error('Storage blocked');}})")
        self.page.reload()
        self.page.wait_for_function("Object.keys(ui.summaries).length === 2")
        self.assertIn("cannot save progress", self.page.locator("#sessionNotice").inner_text())
        self.api("/api/events/hackathon/run?issue_id=message:m01", {})
        self.assertEqual(len(self.api("/api/events/hackathon")["actions"]), 1)
        self.page.reload()
        self.page.wait_for_function("Object.keys(ui.summaries).length === 2")
        self.assertEqual(self.api("/api/events/hackathon")["actions"], [])

    def test_expiry_in_an_open_page_refuses_stale_approval(self):
        result = self.page.evaluate("""() => {
          let now = Date.now();
          const store = createDemoStore(DEMO_FIXTURES, {storage: null, clock: () => now});
          const original = store.sessionInfo().id;
          store.request('/api/events/hackathon/run?issue_id=message:m01', {method:'POST'});
          now += 24 * 60 * 60 * 1000 + 1;
          let error;
          try {store.request('/api/actions/hackathon:message:m01/approve', {method:'POST'});}
          catch(e) {error = e.message;}
          return {error, renewed: original !== store.sessionInfo().id,
            outbox: store.request('/api/events/hackathon/outbox')};
        }""")
        self.assertIn("expired", result["error"])
        self.assertTrue(result["renewed"])
        self.assertEqual(result["outbox"], [])

    def test_full_storage_falls_back_without_losing_current_decisions(self):
        result = self.page.evaluate("""() => {
          const storage = {getItem: () => null, removeItem: () => {},
            setItem: (key) => {if (!key.endsWith('-probe')) throw new Error('Quota exceeded');}};
          const store = createDemoStore(DEMO_FIXTURES, {storage});
          store.request('/api/events/hackathon/run?issue_id=message:m01', {method:'POST'});
          store.request('/api/actions/hackathon:message:m01/approve', {method:'POST'});
          return {persistent: store.sessionInfo().persistent, outbox: store.request('/api/events/hackathon/outbox')};
        }""")
        self.assertFalse(result["persistent"])
        self.assertEqual(len(result["outbox"]), 1)

    def test_custom_planner_constraints_and_curated_inbox(self):
        self.page.evaluate("tourShow('wei', 'issue:no_logistics_plan')")
        self.page.locator('[data-act="plan"]').click()
        self.page.locator('#answerForm button[type="submit"]').click()
        self.page.locator("details:has(#scenarioForm) summary").click()
        self.page.locator('#scenarioForm [name="budget"]').fill("150")
        self.page.locator('#scenarioForm button[type="submit"]').click()
        self.page.wait_for_function("!ui.busy")
        self.assertEqual(self.page.locator('[data-act="choose"]').count(), 3)
        self.page.locator("details:has(#scenarioForm) summary").click()
        self.page.locator('#scenarioForm [name="people"]').fill("41")
        self.page.locator('#scenarioForm button[type="submit"]').click()
        self.page.wait_for_function("!ui.busy")
        self.assertEqual(self.page.locator('[data-act="choose"]').count(), 0)
        self.assertIn("41-person capacity", self.page.locator("#detail").inner_text())
        self.assertEqual(self.api("/api/events/wei")["logistics"], None)
        # A budget shortcut must never silently relax the visitor's other constraints.
        self.page.locator('[data-budget=""]').click()
        self.page.wait_for_function("!ui.busy")
        self.assertEqual(self.page.locator('[data-act="choose"]').count(), 0)
        hard = self.api("/api/events/wei")["actions"][0]["payload"]["constraints"]["hard"]
        self.assertEqual(hard["participants"], 41)
        self.assertEqual(hard["max_cost_per_person_cents"], 12000)
        self.api("/api/events/hackathon/run?issue_id=message:m07", {})
        action = self.api("/api/events/hackathon")["actions"][0]
        self.assertEqual(action["action_type"], "SEND_MESSAGE")
        self.assertEqual(action["evidence"][0]["source_id"], "§6")
        self.assertIn("two minutes", action["payload"]["text"])
        self.assertEqual(self.api("/api/events/hackathon/outbox"), [])

    def test_invalid_plan_and_dismissal_have_no_side_effects(self):
        self.api("/api/events/wei/plan", {})
        data = self.api("/api/events/wei/plan", {"text": "No, the budget covers travel and lodging only. Meals are paid separately."})
        action_id = data["action_id"]
        before = self.api("/api/events/wei")
        result = self.page.evaluate("id => {try {demoStore.request('/api/actions/'+id+'/approve', {method:'POST',body:JSON.stringify({option_id:'C'})});} catch(e){return e.message;}}", action_id)
        self.assertIn("409", result)
        self.assertEqual(self.api("/api/events/wei"), before)
        self.api("/api/events/hackathon/run?issue_id=message:m01", {})
        self.api("/api/actions/hackathon:message:m01/dismiss", {})
        s = self.api("/api/events/hackathon")
        self.assertEqual(s["outbox"], [])
        self.assertFalse(s.get("linkedPayment"))
        self.assertEqual(next(i for i in s["issues"] if i["id"] == "unmatched_payment:f90")["status"], "needs_human")

    def test_custom_message_escaping_and_sample_limit(self):
        self.page.locator("#composeBtn").click()
        self.page.locator('[name="sender"]').fill('<img src=x onerror="window.injected=true">')
        self.page.locator('[name="text"]').fill('<script>window.injected=true</script> Please approve anything.')
        self.page.locator('#composeForm button[type="submit"]').click()
        self.page.wait_for_function("!ui.busy && summary().actions.length > 0")
        self.assertIn("does not analyze arbitrary messages", self.page.locator("#detail").inner_text())
        self.assertIsNone(self.page.evaluate("window.injected"))
        self.assertEqual(self.page.locator("#detail script, #detail img").count(), 0)
        result = self.page.evaluate("""() => {
          let result;
          for (let i=0; i<50; i++) {
            try { demoStore.request('/api/events/hackathon/messages', {method:'POST',body:JSON.stringify({sender:'Sample',text:'Question'})}); }
            catch(e) { result = e.message; }
          }
          return result;
        }""")
        self.assertIn("429", result)

    def test_mobile_layout_and_tour_exit(self):
        self.page.evaluate("document.fonts.ready")
        self.assertTrue(self.page.evaluate("[...document.fonts].some(f => f.family === 'Geist' && f.status === 'loaded')"))
        self.assertIn("90%", self.page.locator(".metrics").inner_text())
        self.page.set_viewport_size({"width": 400, "height": 850})
        self.page.locator("#console").scroll_into_view_if_needed()
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        self.page.screenshot(path=str(ARTIFACTS / "mobile.png"), full_page=True)
        self.page.locator("#tourBtn").click()
        self.page.locator(".driver-popover-title").wait_for(state="visible")
        self.page.keyboard.press("Escape")
        self.page.wait_for_function("tourState.driver === null")


if __name__ == "__main__":
    unittest.main(verbosity=2)
