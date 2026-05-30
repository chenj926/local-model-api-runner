from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


class EnvError(RuntimeError):
    """Raised when required environment values are missing."""


def load_env_file(path: Path) -> None:
    """Load a simple KEY=VALUE .env file without overriding existing env vars."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_env_value(value.strip())
        if key:
            os.environ.setdefault(key, value)


def first_existing_env(names: Iterable[str]) -> tuple[str, str]:
    for name in names:
        value = os.getenv(name)
        if value:
            return name, value
    raise EnvError(f"Missing API key. Expected one of: {', '.join(names)}")


def first_existing_env_name(names: Iterable[str]) -> str | None:
    for name in names:
        if os.getenv(name):
            return name
    return None


def _strip_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
