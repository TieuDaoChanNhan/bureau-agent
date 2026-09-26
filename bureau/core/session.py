"""Request-local storage namespace. CLI callers have no browser session."""
from contextvars import ContextVar

current_session: ContextVar[str | None] = ContextVar("demo_session", default=None)
