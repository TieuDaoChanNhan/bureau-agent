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
# gpt-4.1 is the model the agent was validated with (T04 live run, T08 evaluation).
# Another model needs its own run: OPENAI_MODEL=<model> python -m eval.run_eval
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1")

# Enabled by the public Render Blueprint; CLI/development keep their usual state.
DEMO_MODE = os.environ.get("DEMO_MODE", "0").lower() in ("1", "true", "yes")
DEMO_COOKIE_SECURE = os.environ.get("RENDER", "").lower() == "true"
DEMO_DAILY_LLM_LIMIT = max(0, int(os.environ.get("DEMO_DAILY_LLM_LIMIT", "400")))
DEMO_SESSION_LLM_LIMIT = max(0, int(os.environ.get("DEMO_SESSION_LLM_LIMIT", "60")))
DEMO_MAX_OUTPUT_TOKENS = max(1, int(os.environ.get("DEMO_MAX_OUTPUT_TOKENS", "2048")))
