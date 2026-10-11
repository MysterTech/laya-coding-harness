"""Where laya-harness keeps its state (spec §4.11).

`LAYA_HARNESS_HOME` moves the state directory in tests only: it is honoured only when
`LAYA_HARNESS_TEST=1`, and under that flag the real `~/.laya-harness` is refused.
"""

import contextlib
import os
import tempfile
from pathlib import Path

REAL_HOME = Path.home() / ".laya-harness"
TEST_FLAG = "LAYA_HARNESS_TEST"
HOME_OVERRIDE = "LAYA_HARNESS_HOME"


class StateDirError(RuntimeError):
    """A test tried to use the real state directory or port."""


def testing() -> bool:
    return os.environ.get(TEST_FLAG) == "1"


def home() -> Path:
    if not testing():
        return REAL_HOME
    override = os.environ.get(HOME_OVERRIDE)
    if not override:
        raise StateDirError("tests must set LAYA_HARNESS_HOME")
    path = Path(override).expanduser()
    resolved, real = path.resolve(), REAL_HOME.resolve()
    if resolved == real or real in resolved.parents or resolved in real.parents:
        raise StateDirError("tests must not use ~/.laya-harness, a directory inside it, or one of its parents")
    return path


def ensure_home() -> Path:
    path = home()
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.chmod(0o700)
    sessions = path / "sessions"
    sessions.mkdir(mode=0o700, exist_ok=True)
    sessions.chmod(0o700)
    return path


def config_path() -> Path:
    return home() / "config.json"


def decisions_path() -> Path:
    return home() / "decisions.jsonl"


def client_log() -> Path:
    return home() / "client.log"


def service_log() -> Path:
    return home() / "service.log"


def sessions_dir() -> Path:
    return home() / "sessions"


def models_dir() -> Path:
    return home() / "models"


def write_private(path: Path, text: str) -> None:
    """Write a file readable only by the user, replacing it atomically.

    Each write uses its own temporary file (mkstemp creates it 0600 in the same directory), so
    concurrent writers never share one, and the temporary file is removed if anything fails.
    """
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def append_private(path: Path, line: str) -> None:
    """Append one line to a file readable only by the user."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(fd, 0o600)  # tighten a file that already existed with looser permissions
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write(line if line.endswith("\n") else line + "\n")
