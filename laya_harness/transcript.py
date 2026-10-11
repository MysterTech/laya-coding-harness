"""The last assistant reply in a Claude Code transcript (spec §4.6). Reads only the tail."""

import json
import os
import stat
from datetime import datetime

TAIL_BYTES = 256 * 1024


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


def last_assistant(path):
    """Return {"model", "effort", "ts"} for the newest main-thread assistant row in the tail, or None.

    Only the last TAIL_BYTES are read. A cut-off first line, lines that are not JSON objects,
    sidechain rows and synthetic models (names starting with "<") are skipped. A path that is not
    a string or not a regular file, or a missing or unreadable file, gives None. A lagging transcript still returns its
    newest row, which may be stale; session_state's pending-switch rule handles that.
    """
    if not isinstance(path, str) or not path:
        return None
    try:
        if not stat.S_ISREG(os.stat(path).st_mode):  # a device or a FIFO would block the hook
            return None
        with open(path, "rb") as f:
            size = os.fstat(f.fileno()).st_size
            start = max(0, size - TAIL_BYTES)
            f.seek(start)
            data = f.read(TAIL_BYTES)
    except OSError:
        return None
    lines = data.split(b"\n")
    if start > 0:
        lines = lines[1:]  # the first line is probably cut off
    for raw in reversed(lines):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except (ValueError, RecursionError):
            continue
        if not isinstance(row, dict) or row.get("type") != "assistant" or row.get("isSidechain"):
            continue
        message = row.get("message")
        model = message.get("model") if isinstance(message, dict) else None
        if not isinstance(model, str) or model.startswith("<"):
            continue
        effort = row.get("effort")
        return {"model": model, "effort": effort if isinstance(effort, str) else None,
                "ts": _timestamp(row.get("timestamp"))}
    return None
