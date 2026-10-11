"""Per-session state owned by the client (spec §4.6).

The model and effort start unknown: the desktop app gives hooks neither on a session's first
prompt. A PostModelSwitch stays authoritative until the transcript holds an assistant row
timestamped after the first prompt submitted after that switch.
"""

import contextlib
import fcntl
import hashlib
import json
import os
import re
import time

from . import paths

DEFAULT = {
    "model": None,
    "effort": None,
    "model_source": None,
    "switched_at": None,
    "first_prompt_after_switch_at": None,
    "prompt_count": 0,
    "model_line_shown": False,
    "plan_shown": False,
    "updated": None,
}
_SAFE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_NUMBER = (int, float)
_TYPES = {
    "model": (str, type(None)),
    "effort": (str, type(None)),
    "model_source": (str, type(None)),
    "switched_at": _NUMBER + (type(None),),
    "first_prompt_after_switch_at": _NUMBER + (type(None),),
    "model_line_shown": (bool,),
    "plan_shown": (bool,),
    "updated": _NUMBER + (type(None),),
}


def _valid(state: dict) -> bool:
    count = state["prompt_count"]
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return False
    for key, types in _TYPES.items():
        value = state[key]
        if not isinstance(value, types) or (isinstance(value, bool) and bool not in types):
            return False
    return True


def _file(session_id: str):
    name = session_id if _SAFE.match(session_id or "") else hashlib.sha256(
        (session_id or "").encode()
    ).hexdigest()
    return paths.sessions_dir() / f"{name}.json"


def load(session_id: str) -> dict:
    """The session's state, or the defaults if the file is missing, not a JSON object, or mistyped."""
    path = _file(session_id)
    if not path.is_file():
        return dict(DEFAULT)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return dict(DEFAULT)
    if not isinstance(data, dict):
        return dict(DEFAULT)
    state = dict(DEFAULT)
    state.update({key: data[key] for key in DEFAULT if key in data})
    return state if _valid(state) else dict(DEFAULT)


def save(session_id: str, state: dict) -> None:
    paths.ensure_home()
    state["updated"] = time.time()
    paths.write_private(_file(session_id), json.dumps(state, sort_keys=True))


@contextlib.contextmanager
def transaction(session_id: str):
    """Read/modify/write one session under a separate, private lock, waiting at most 50 ms."""
    paths.ensure_home()
    fd = os.open(_file(session_id).with_suffix(".lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        os.fchmod(fd, 0o600)
        deadline = time.monotonic() + 0.05
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("session lock unavailable after 50 ms")
                time.sleep(min(0.005, remaining))
        state = load(session_id)
        yield state
        save(session_id, state)
    finally:
        os.close(fd)  # closing also releases flock, including when the transaction raises


def on_session_start(state: dict, source) -> dict:
    if source in ("startup", "fork"):
        state["prompt_count"] = 0
        state["model_line_shown"] = False
        state["plan_shown"] = False
    return state


def on_model_switch(state: dict, to_model, now: float) -> dict:
    if to_model:
        state["model"] = to_model
        state["model_source"] = "post_model_switch"
        state["switched_at"] = now
        state["first_prompt_after_switch_at"] = None
    return state


def switch_pending(state: dict, reply) -> bool:
    if state["switched_at"] is None:
        return False
    first = state["first_prompt_after_switch_at"]
    return not (reply and reply.get("ts") is not None and first is not None and reply["ts"] > first)


def on_human_prompt(state: dict, now: float, reply) -> dict:
    """Count the prompt and fold in the transcript's last reply (from the 2nd prompt on)."""
    state["prompt_count"] += 1
    if state["switched_at"] is not None and state["first_prompt_after_switch_at"] is None:
        state["first_prompt_after_switch_at"] = now
    if state["prompt_count"] < 2 or not reply:
        return state
    state["effort"] = reply.get("effort")  # as the row carries it, so a stale effort never lingers
    if not switch_pending(state, reply) and reply.get("model"):
        state["model"] = reply["model"]
        state["model_source"] = "transcript"
        state["switched_at"] = None
        state["first_prompt_after_switch_at"] = None
    return state
