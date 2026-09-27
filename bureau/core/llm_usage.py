"""Reserve each model attempt atomically before calling the provider.

SQLite survives process restarts on the same disk, never a Render disk reset.
Provider project hard spend limits are the independent monetary backstop.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import logging
import sqlite3
import time

from .. import config
from . import store
from .session import current_session

logger = logging.getLogger("uvicorn.error")


class LiveUnavailable(RuntimeError):
    """A known unavailable live path: serve an explicitly labeled example."""


@contextmanager
def database():
    store.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(store.RUNTIME_DIR / "llm_usage.sqlite3", timeout=10)
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, "
                           "session TEXT, day TEXT, created REAL, model TEXT, purpose TEXT, status TEXT)")
        connection.execute("CREATE INDEX IF NOT EXISTS calls_day ON calls(day)")
        connection.execute("CREATE INDEX IF NOT EXISTS calls_session ON calls(session)")
        connection.commit()
        yield connection
    finally:
        connection.close()


def _check(connection, session: str, day: str):
    daily = connection.execute("SELECT count(*) FROM calls WHERE day=?", (day,)).fetchone()[0]
    personal = connection.execute("SELECT count(*) FROM calls WHERE session=?", (session,)).fetchone()[0]
    if daily >= config.DEMO_DAILY_LLM_LIMIT or personal >= config.DEMO_SESSION_LLM_LIMIT:
        raise LiveUnavailable("live limit reached")


def ensure_available():
    if not config.OPENAI_API_KEY:
        raise LiveUnavailable("no API key configured")
    session = current_session.get()
    if config.DEMO_MODE and session:
        try:
            with database() as connection:
                _check(connection, session, datetime.now(timezone.utc).date().isoformat())
        except sqlite3.Error as exc:
            raise LiveUnavailable("usage accounting unavailable") from exc


def create_completion(client, *, purpose: str, **kwargs):
    session = current_session.get()
    if not config.DEMO_MODE or not session:
        return client.chat.completions.create(**kwargs)
    ensure_available()
    now = time.time()
    day = datetime.fromtimestamp(now, timezone.utc).date().isoformat()
    try:
        with database() as connection:
            # One transaction covers global + session checks and reservation.
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM calls WHERE created < ?", (now - 3 * 86400,))
            _check(connection, session, day)
            row = connection.execute("INSERT INTO calls(session,day,created,model,purpose,status) "
                                     "VALUES(?,?,?,?,?,?)", (session, day, now, kwargs.get("model"), purpose, "attempt"))
            call_id = row.lastrowid
            connection.commit()
    except sqlite3.Error as exc:
        raise LiveUnavailable("usage accounting unavailable") from exc
    kwargs["max_completion_tokens"] = min(kwargs.get("max_completion_tokens", config.DEMO_MAX_OUTPUT_TOKENS),
                                          config.DEMO_MAX_OUTPUT_TOKENS)
    # Failed attempts are charged to the call cap as well; never refund/retry.
    logger.info("demo_llm %s", json.dumps({"session": session, "call": call_id, "day": day,
                                         "model": kwargs.get("model"), "purpose": purpose}))
    try:
        return client.chat.completions.create(**kwargs)
    except Exception as exc:
        if getattr(exc, "status_code", None) == 429:
            raise LiveUnavailable("live limit reached") from exc
        raise
