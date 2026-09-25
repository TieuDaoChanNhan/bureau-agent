# api

FastAPI app serving the JSON API and the web UI.

```bash
uvicorn api.main:app --reload     # http://127.0.0.1:8000  (docs at /docs)
```

| Method | Path | Status |
|---|---|---|
| GET | `/api/events` | done (sample data) |
| GET | `/api/events/{event_id}` | done (sample data; switch to store in T05) |
| POST | `/api/events/{event_id}/run` | 501 (T05) |
| POST | `/api/events/{event_id}/plan` | 501 (T05) |
| GET | `/api/actions/{action_id}` | 501 (T05) |
| POST | `/api/actions/{action_id}/approve` | 501 (T05) |
| POST | `/api/actions/{action_id}/dismiss` | 501 (T05) |
| GET | `/api/events/{event_id}/outbox` | 501 (T05) |
| POST | `/api/events/{event_id}/reset` | 501 (T05) |

JSON bodies are the dataclasses of `bureau/core/models.py` (`dataclasses.asdict`). Keep it that way so the web UI has one source of truth.
