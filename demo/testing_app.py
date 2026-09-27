"""Offline browser-test server factory. Never use this entry point on Render."""
import json
import os
from pathlib import Path
from types import SimpleNamespace


def create_app():
    from api import main
    from bureau import config
    from bureau.agent import loop
    from bureau.core import store
    from demo.replay import issue_example, BUDGET_ANSWER
    from tests.fake_llm import FakeClient

    # Explicit opt-in is required; ordinary uvicorn/api startup never uses fakes.
    store.RUNTIME_DIR = Path(os.environ["DEMO_TEST_RUNTIME"])
    config.DEMO_MODE = True
    config.OPENAI_API_KEY = "offline-test-only"
    config.DEMO_DAILY_LLM_LIMIT = 0 if os.environ.get("DEMO_TEST_MODE") == "limit" else 400
    config.DEMO_SESSION_LLM_LIMIT = 60

    def create(**kwargs):
        with (store.RUNTIME_DIR / "fake_calls.jsonl").open("a") as log:
            log.write(json.dumps({"model": kwargs["model"]}) + "\n")
        if "response_format" in kwargs:
            request = json.loads(kwargs["messages"][1]["content"])
            extracted = {"hard": {"participants": 100, "max_cost_per_person_cents": 15000,
                                  "arrive_before": "21:00", "no_overnight": True, "step_free_rooms": 2},
                         "soft": ["fewer_changes", "early_return", "lower_cost"],
                         "organizer_verified": ["step_free_rooms"],
                         "unsupported_requirements": [],
                         "clarifications": [] if BUDGET_ANSWER in request["text"] else ["Does the budget include coach hire?"]}
            step = json.dumps(extracted)
        elif "tools" in kwargs:
            context = json.loads(kwargs["messages"][1]["content"].split("\n", 1)[1])
            from bureau.core.models import Issue
            issue = Issue(**context["issue"])
            action = issue_example(store.load_state("hackathon"), issue)
            from dataclasses import asdict
            step = [("propose_action", asdict(action))]
        else:
            step = "Option F ranks first for fewer changes; Option D costs less."
        return FakeClient([step]).chat.completions.create(**kwargs)

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    main._planner_client = lambda: client
    loop._default_client = lambda: client
    return main.app
