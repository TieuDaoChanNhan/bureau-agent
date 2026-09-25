# tests

Unit tests use Python's built-in `unittest` (nothing to install).

```bash
python -m unittest discover -s tests -t .                  # everything
python -m unittest tests.test_core -v                      # one file
python -m unittest tests.test_core.LoaderTests -v          # one class
```

| File | Covers |
|---|---|
| `test_core.py` | Data model (cents, timezones), loader, detection, idempotency, dependencies |
| `test_tools.py` | Identity bands, eligibility, group checks, rules search |
| `test_planner.py` | Constraint gate, ranking, diagnosis, unverifiable constraints, clarifications |
| `test_agent.py` | Agent loop mechanics with a scripted fake LLM |
| `test_pending.py` | Expected behaviour of unfinished modules (store, executor), skipped until their task is done |
| `fake_llm.py` | Fake OpenAI client for tests (no key, no cost) |
| `helpers.py` | Shared fixtures (e.g. `wei_request()`) |

CI runs the suite on every push and pull request. Every new rule in the code gets a test.

## Adding a test

A test is a method whose name starts with `test_`, inside a class that inherits `unittest.TestCase`. It sets something up, calls your code, and **asserts** what must be true.

```python
import unittest

from bureau.core.loader import load_event
from bureau.core.store import load_state, reset, save_state


class StoreRoundTripTests(unittest.TestCase):
    def setUp(self):                      # runs before each test
        reset("wei")                      # start from the sample data

    def test_save_then_load_keeps_participants_and_travel(self):
        state = load_event("wei")         # 1. arrange
        save_state(state)                 # 2. act
        again = load_state("wei")
        self.assertEqual(len(again.participants), len(state.participants))   # 3. assert
        self.assertEqual(again.travel, state.travel)
```

### Where to put it
| You work on | Put tests in |
|---|---|
| `bureau/core/store.py`, `executor.py` | `test_pending.py`: remove the `@unittest.skip` line above the class, then add your tests to that class (or move the class to `test_core.py`) |
| `bureau/core/*` (other) | `test_core.py` |
| `bureau/tools/*` | `test_tools.py` |
| `bureau/planner/*` | `test_planner.py` |
| `bureau/agent/*`, batch run | `test_agent.py`, with `FakeClient` from `fake_llm.py` (never call the real API in tests) |
| `api/main.py` | new file `test_api.py`, with `fastapi.testclient.TestClient(app)` |

### Rules of thumb
- **One test = one fact**, named after it: `test_team_of_five_is_rejected`, not `test_executor2`.
- Each "Done when" line of your issue that says "Thêm test: …" becomes one test method.
- Tests must not depend on each other or on files left by a previous run: use `setUp` (e.g. `reset(...)`) to start clean.
- No network, no API keys: use sample data, `FakeClient`, and Jinko **replay** mode.
- Useful assertions: `assertEqual`, `assertTrue`, `assertIn`, `assertIsNone`, `assertRaises` (for errors, e.g. `with self.assertRaises(InvariantViolation): ...`).
- Look at the existing files for examples; `test_agent.py` shows how to script the fake LLM.
