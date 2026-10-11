"""The decision log and the client's diagnostics (spec §4.10). Both stay on this Mac, 0600."""

import json
from datetime import datetime, timezone

from . import paths

SCHEMA_VERSION = 1


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def append(row: dict) -> None:
    paths.ensure_home()
    paths.append_private(paths.decisions_path(), json.dumps(row))  # ASCII: a lone surrogate cannot break the write


def problem(message: str) -> None:
    paths.ensure_home()
    paths.append_private(paths.client_log(), f"{datetime.now(timezone.utc).isoformat()} {message}")
