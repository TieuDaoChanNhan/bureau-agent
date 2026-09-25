"""Read settings from environment variables, falling back to a local .env file."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repository root
DATA_DIR = ROOT / "data"        # sample events (read-only)
RUNTIME_DIR = ROOT / "runtime"  # state written while the app runs (git-ignored)


def _load_dotenv() -> None:
    for path in (ROOT / ".env", ROOT.parent / ".env"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
# Which models the hackathon credits cover is not confirmed yet: set OPENAI_MODEL in .env.
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
