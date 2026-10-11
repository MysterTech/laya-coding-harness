"""Bounded user configuration defaults, never evidence of active session effort (C3)."""

import os
from pathlib import Path
import stat
import tomllib

MAX_BYTES = 64 * 1024


def defaults() -> dict:
    """Expose only model/effort defaults and their provenance; fail open on bad files."""
    empty = {"model": None, "effort": None, "source": None}
    home = Path(os.environ["CODEX_HOME"]) if "CODEX_HOME" in os.environ else Path.home() / ".codex"
    path = home / "config.toml"
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            return empty
        # NONBLOCK plus fstat prevents a replacement FIFO from blocking between stat/open.
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                return empty
            data = stream.read(MAX_BYTES)
            if os.fstat(stream.fileno()).st_size > MAX_BYTES:
                return empty
        config = tomllib.loads(data.decode("utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, RecursionError):
        return empty
    model = config.get("model")
    effort = config.get("model_reasoning_effort")
    return {"model": model if isinstance(model, str) else None,
            "effort": effort if isinstance(effort, str) else None,
            "source": "user_config_default"}
