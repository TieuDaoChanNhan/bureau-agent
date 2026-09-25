# tests

```bash
python -m unittest discover -s tests -t .
```

| File | Covers |
|---|---|
| `test_core.py` | Data model (cents, timezones), detection, idempotency, dependencies |
| `test_tools.py` | Identity bands, eligibility, group checks, rules search |
| `test_planner.py` | Constraint gate, ranking, diagnosis, unverifiable constraints, clarifications |
| `test_pending.py` | Expected behaviour of unfinished modules, skipped until their task is done |
| `helpers.py` | Shared fixtures |

Every new invariant gets a test. CI runs the suite on every pull request.
