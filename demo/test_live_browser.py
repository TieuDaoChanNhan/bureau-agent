"""Real HTTP/console/tour with fake OpenAI completions, plus exhausted-budget replay."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "demo/artifacts"


class LiveConsoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True, executable_path=os.environ.get("DEMO_CHROME_PATH") or None)
        ARTIFACTS.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def server(self, mode):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = {**os.environ, "DEMO_TEST_RUNTIME": directory.name, "DEMO_TEST_MODE": mode,
               "OPENAI_API_KEY": "", "JINKO_MODE": "replay"}
        log = open(Path(directory.name) / "server.log", "w", encoding="utf-8")
        self.addCleanup(log.close)
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "demo.testing_app:create_app", "--factory",
                                    "--host", "127.0.0.1", "--port", str(port)],
                                   cwd=ROOT, env=env, stdout=log, stderr=log,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        def stop():
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        self.addCleanup(stop)
        url = f"http://127.0.0.1:{port}"
        for _ in range(100):
            try:
                with urlopen(url + "/health", timeout=1):
                    return url, Path(directory.name)
            except OSError:
                if process.poll() is not None:
                    self.fail("Test server stopped: " + (Path(directory.name) / "server.log").read_text())
                time.sleep(0.1)
        self.fail("Test server did not start")

    def page(self, url):
        context = self.browser.new_context(viewport={"width": 1440, "height": 1000})
        self.addCleanup(context.close)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        self.addCleanup(lambda: self.assertEqual(errors, []))
        page.goto(url)
        page.wait_for_function("Object.keys(ui.summaries).length === 2 && !ui.busy")
        return page

    def tour(self, page, prefix):
        page.locator("#fullTourLink").click()  # the hero button opens the 15-step quick tour
        clicks = {4: '[data-act="retry"]', 8: '[data-act="edit"]', 9: '.tour-act',
                  10: '[data-act="approve"]', 12: '#outboxBtn', 14: '#composeBtn',
                  15: '#composeForm button[type="submit"]', 18: '[data-ev="wei"]',
                  20: '[data-act="plan"]', 21: '#answerForm button[type="submit"]',
                  24: '[data-budget]:not([data-budget=""])', 26: '[data-budget=""]', 27: '[data-act="choose"]'}
        self.assertEqual(30, page.evaluate("STEPS.length"))
        for index in range(30):
            with self.subTest(step=index + 1):
                page.wait_for_function("i => tourState.driver?.getActiveIndex() === i && !ui.busy", arg=index)
                page.locator(".driver-popover-title").wait_for(state="visible")
                if index == 9:
                    page.locator("#draft").fill("Browser one approved this edited reply.")
                if index == 13:
                    self.assertIn("Browser one approved", page.locator("#detail").inner_text())
                if index == 25:
                    self.assertIn("No valid option", page.locator(".diag").inner_text())
                if index == 23:
                    self.assertGreater(page.locator('[data-act="choose"]').count(), 0)
                    page.screenshot(path=str(ARTIFACTS / f"{prefix}-options.png"))
                page.locator(clicks.get(index, ".driver-popover-next-btn")).first.click()
        page.wait_for_function("tourState.driver === null")
        self.assertTrue(page.evaluate("!!summary('wei').logistics"))

    def test_full_tour_with_fake_live_agent_and_second_browser(self):
        url, runtime = self.server("live")
        first, second = self.page(url), self.page(url)
        pristine = second.evaluate("JSON.stringify(ui.summaries)")
        self.tour(first, "server-fake-live")
        self.assertTrue((runtime / "fake_calls.jsonl").exists())
        first.evaluate("async () => { await selectEvent('hackathon'); ui.outbox = await api('/api/events/hackathon/outbox'); ui.view='outbox'; render(); }")
        first.locator("#console").scroll_into_view_if_needed()
        first.screenshot(path=str(ARTIFACTS / "server-browser-one.png"))
        second.reload()
        second.wait_for_function("Object.keys(ui.summaries).length === 2 && !ui.busy")
        self.assertEqual(pristine, second.evaluate("JSON.stringify(ui.summaries)"))
        self.assertEqual([], second.evaluate("api('/api/events/hackathon/outbox')"))
        second.locator("#console").scroll_into_view_if_needed()
        second.screenshot(path=str(ARTIFACTS / "server-browser-two.png"))
        second.evaluate("api('/api/events/hackathon/reset', {method:'POST'})")
        self.assertEqual(1, len(first.evaluate("api('/api/events/hackathon/outbox')")))

    def test_full_tour_replays_at_zero_limit_and_font_loads(self):
        url, runtime = self.server("limit")
        page = self.page(url)
        self.tour(page, "server-replay")
        self.assertFalse((runtime / "fake_calls.jsonl").exists())
        self.assertIn("Saved example (live limit reached)", page.locator("#demoModeNotice").inner_text())
        page.evaluate("document.fonts.ready")
        self.assertTrue(page.evaluate("[...document.fonts].some(f => f.family === 'Geist' && f.status === 'loaded')"))
        self.assertIn("90%", page.locator(".metrics").inner_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
