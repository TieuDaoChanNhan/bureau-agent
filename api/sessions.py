"""Anonymous 24-hour sandboxes for the public, single-worker demo."""
from __future__ import annotations

import asyncio
from http.cookies import SimpleCookie
from pathlib import Path
import re
import secrets
import shutil
import time

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import Response

from bureau import config
from bureau.core import store
from bureau.core.session import current_session

COOKIE = "bureau_demo"
TTL = 24 * 60 * 60
SESSION_ID = re.compile(r"[a-f0-9]{32}\Z")


def created_at(path: Path) -> float:
    try:
        return float((path / ".created").read_text(encoding="ascii"))
    except (OSError, ValueError):
        return 0


def cleanup(now: float, active: set[str]) -> None:
    root = store.RUNTIME_DIR.resolve()
    if not root.exists():
        return
    for path in root.iterdir():
        if (SESSION_ID.fullmatch(path.name) and path.name not in active
                and path.is_dir() and not path.is_symlink()
                and path.resolve().parent == root and created_at(path) <= now - TTL):
            shutil.rmtree(path)


class DemoSessions:
    def __init__(self, app):
        self.app = app
        self.active: dict[str, list] = {}
        self.next_cleanup = 0.0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not config.DEMO_MODE or scope.get("path") == "/health":
            return await self.app(scope, receive, send)
        now = time.time()
        if now >= self.next_cleanup:
            cleanup(now, set(self.active))
            self.next_cleanup = now + 3600
        headers = Headers(scope=scope)
        cookie = SimpleCookie()
        try:
            cookie.load(headers.get("cookie", ""))
        except Exception:
            cookie = SimpleCookie()
        session = cookie[COOKIE].value if COOKIE in cookie else ""
        fresh = (not SESSION_ID.fullmatch(session) or
                 not now - TTL < created_at(store.RUNTIME_DIR / session) <= now)
        if fresh:
            session = secrets.token_hex(16)
            directory = store.RUNTIME_DIR / session
            directory.mkdir(parents=True)
            (directory / ".created").write_text(str(now), encoding="ascii")
        # Serialize one browser's reset/approve/run and reads. Separate browsers
        # retain independent locks; waiting requests keep their lock alive.
        entry = self.active.setdefault(session, [asyncio.Lock(), 0])
        entry[1] += 1
        token = current_session.set(session)
        async def send_session(message):
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                response_headers["Cache-Control"] = "no-store"
                if fresh:
                    response = Response()
                    response.set_cookie(COOKIE, session, max_age=TTL, httponly=True,
                                        secure=config.DEMO_COOKIE_SECURE or scope.get("scheme") == "https", samesite="lax")
                    response_headers.append("set-cookie", response.headers["set-cookie"])
            await send(message)
        try:
            async with entry[0]:
                await self.app(scope, receive, send_session)
        finally:
            current_session.reset(token)
            entry[1] -= 1
            if not entry[1]:
                self.active.pop(session, None)
