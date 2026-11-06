"""Settings: .env loading and the model name."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "gpt-6-luna"


def load_env():
    """Reads KEY=value lines from .env into the environment (no override)."""
    env = ROOT / ".env"
    if not env.exists():
        raise SystemExit("Missing .env: copy .env.example to .env and set OPENAI_API_KEY.")
    for line in env.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is empty in .env.")


def model():
    """Read after load_env(), so OPENAI_MODEL in .env is honored."""
    return os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
