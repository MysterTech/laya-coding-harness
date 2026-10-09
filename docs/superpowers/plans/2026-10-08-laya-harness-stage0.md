# laya-harness Stage 0 Implementation Plan

> **For agentic workers:** execute with the two-agent SWE workflow
> (`~/.claude/workflows/two-agent-swe-workflow.md`) and this repo's signed-off gate profile
> (`docs/workflows/two-agent-swe-workflow.md`). Per the user's global CLAUDE.md this replaces
> `superpowers:subagent-driven-development` / `superpowers:executing-plans`. Subagents never run
> git add/commit/checkout; the controller commits once, at the end. Steps use checkbox (`- [ ]`) syntax.

**Goal:** the first working version of laya-harness for Claude Code: prompt → hook → local laya
service → three questions → at most two advisory lines → one decision-log row, failing open
everywhere.

**Architecture:** a standard-library hook client (`python -I -m laya_harness hook claude-code
<Event>`) talks over 127.0.0.1 to a local service that loads the pinned laya-mlx checkpoint
once, starts itself detached when it is not running, and exits after 15 idle minutes.
Deterministic Claude Code adapter rules turn Laya's answers into lines, choosing the model from a
catalog and fit table (cheapest that fits). Laya stays above the harness: advice only, never a
block, never added context.

**Tech Stack:** Python 3.11.17 (`.venv`), laya-mlx 0.3.0 / MLX 0.32.3, the standard library
(`http.server`, `http.client`, `subprocess`), pytest 9.1.1.

**Spec:** `docs/superpowers/specs/2026-10-08-laya-harness-design.md` (the contract; read §1.1 and §4
before any task). **Mockup:** spec §4.12 plus `docs/mockups/stage0-check1-*.png`.

**How this plan was verified (plan preflight):** every code block below was executed in a
throwaway copy of the repo at commit `1606ae9` (every later commit changes only `docs/` and `README.md`) before being written here, and is copied from those
files, not retyped. In that copy the full suite passed repeatedly (`255 passed, 1 deselected` with every task, after the review rounds of Tasks 1–7), the
controller-only gate passed (`.venv/bin/python -m pytest -q -m real_model` → `1 passed`, cold start
to ready plus a warm call in 3.6 s), and each task's tests were run against the stubs in plan order
with later tasks absent: every test failed, none passed against a stub (the RED counts below).

## Scope (2026-10-08, spec D14 as amended by D15)

D14 adopted a target architecture (a Bridge behind front doors, **Laya as the tier router**,
**Obsidian as the memory**) and parked the hooks. D15 lifts that parking: the harness is built
first, and the web HUD is a later stage after stage 2 with its own spec and mockups.

- **Execute:** Tasks 1–8 in full, as written. The hook client starts the service itself (§4.3);
  the Bridge later reuses or replaces that start-up path. Gate counts are the ones each task
  states.
- **Then stop** before the final commit: the user reviews the implementation with Codex first.

## Global Constraints

- Interpreter: `.venv/bin/python` (Python 3.11.17); dependency `laya-mlx==0.3.0`; never call a bare `python` or `pytest`.
- The hook client uses the standard library only and never imports `laya_mlx` or `mlx`.
- A hook always exits 0. Its stdout is empty or exactly one JSON object `{"systemMessage": "..."}`; SessionStart and PostModelSwitch print nothing.
- Hooks are registered in exec form, `[<venv python>, "-I", "-m", "laya_harness", "hook", "claude-code", <Event>]`, with timeouts SessionStart 8 s, UserPromptSubmit 3 s, PostModelSwitch 3 s.
- The service listens on 127.0.0.1 only, on the port from `~/.laya-harness/config.json` (default 47913); it binds before importing laya_mlx and never writes to stdout.
- Profile deadline 1.5 s; SessionStart waits at most 4 s, on `startup` only; idle exit after 900 s, never mid-request.
- Checkpoint `aac6fef/laya-mlx` at `047678560251f28113ee8f5df4be82102c7bf336`, weights sha256 `b9c07bf14be2fa5c78a9193a3e6d840ac80e89e62fc40f425834c3d8a6eaa3de`, loaded from an absolute local directory with `HF_HUB_OFFLINE=1`; `batch_size=1`, `pad_to_multiple=128`, `max_len=512`; every padded length warmed before `ready`.
- Gates: tier sum ≥ 0.8 (rounded to four decimals); plan-first noul ≥ 0.85, first human prompt or ≥ 200 characters, once per session, never in Plan mode; parallel is logged, never shown. Gate on laya-mlx's four-decimal values; display two decimals.
- Copy: exactly the §4.12 strings, each ≤ 120 characters. Never Fable. Never a `decision` key. Never `additionalContext` in stage 0.
- State: `~/.laya-harness` mode 0700, its files 0600. Tests use `LAYA_HARNESS_HOME` with `LAYA_HARNESS_TEST=1` and never touch `~/.laya-harness` or port 47913. No test reaches the network.

---

## File structure

| Path | Responsibility | Task |
|---|---|---|
| `pyproject.toml` | console script and package data | 1 |
| `laya_harness/paths.py` | state directory, test guard, private file writes | 1 |
| `laya_harness/config.py` | `config.json`: defaults, modes, port, interpreter | 1 |
| `laya_harness/questions/profile_v0.json` | the three questions and their display thresholds | 2 |
| `laya_harness/checkpoint.json` | pinned checkpoint, required files, check-6 settings | 2 |
| `laya_harness/data/claude_code_models.json` | model catalog (picker, prices, effort levels, allowed) | 2 |
| `laya_harness/data/claude_code_fit.json` | fit table: acceptable options per class | 2 |
| `laya_harness/resources.py` | loaders and hashes for the packaged data | 2 |
| `laya_harness/source.py` | human vs machine prompts | 3 |
| `laya_harness/transcript.py` | last assistant reply from the transcript tail | 3 |
| `laya_harness/session_state.py` | per-session file, switch precedence | 3 |
| `laya_harness/catalog.py` | cheapest allowed option, canonical names | 4 |
| `laya_harness/copytext.py` | the copy-deck strings | 4 |
| `laya_harness/adapter_claude_code.py` | tier gate, model and plan lines, mismatches | 4 |
| `laya_harness/predictor.py` | fake and real (laya-mlx) predictors | 5 |
| `laya_harness/service.py` | the local HTTP service | 5 |
| `laya_harness/hookargv.py` | the registered hook command and settings snippet | 6 |
| `laya_harness/spawn.py` | detached service start | 6 |
| `laya_harness/service_client.py` | stdlib calls to the service | 6 |
| `laya_harness/decision_log.py` | decision rows and client diagnostics | 6 |
| `laya_harness/client.py` | the three hook handlers | 6 |
| `laya_harness/__main__.py` | entry point; the hook path never fails | 6, 7 |
| `laya_harness/commands.py` | setup, status, stop, mode | 7 |
| `tests/conftest.py`, `tests/procs.py`, `tests/fixtures/payloads.json` | fixtures and process helpers | 1, 5, 3 |

**Controller, before Task 1:** initialise the WIP refs and run directory per the gate profile
(`PLAN=stage0`, `refs/laywip/stage0/task-0` at HEAD, run directory
`/private/tmp/claude-501/-Users-thunderstruck-Code-Playground-laya-harness/agent-run/stage0/`).
At every task boundary, diff this plan's code blocks against the files on disk and report drift.

---

### Task 1: State directory and config

**Files:**
- Create: `laya_harness/paths.py`
- Create: `laya_harness/config.py`
- Create: `tests/test_paths_config.py`
- Modify: `pyproject.toml`
- Modify: `tests/conftest.py`
- Test: `tests/test_paths_config.py`

**Spec:** §4.2 (port from config), §4.4, §4.5, §4.11

**Interfaces:**
- Consumes: nothing new (the scaffold's `laya_harness/__init__.py` with `__version__ = "0.0.0"`).
- Produces:
- `paths`: `REAL_HOME`, `TEST_FLAG`, `HOME_OVERRIDE`, `StateDirError`, `testing() -> bool`,
  `home() -> Path`, `ensure_home() -> Path`, `config_path()`, `decisions_path()`, `client_log()`,
  `service_log()`, `sessions_dir()`, `models_dir()` (all `-> Path`),
  `write_private(path, text) -> None`, `append_private(path, line) -> None`.
- `config`: `DEFAULT_PORT = 47913`, `MODES = ("show", "log-only", "off")`, `DEFAULTS`,
  `load() -> dict`, `save(cfg) -> None`, `port(cfg) -> int`, `interpreter(cfg) -> str`.
- `tests/conftest.py`: fixtures `home`, `free_port`, `configured`; constant `FAKE_ANSWERS`;
  helper `write_config(home, **changes) -> dict`. Later tasks import these.

> Revised after review round 1 (findings P2-1 to P2-4 and P3-5 to P3-8): a unique temporary file per atomic write, the real-home guard also refusing its parents and children, existing directories and log files tightened to 0700/0600, the port range checked, no ambient LAYA_HARNESS_HOME in tests, and tests pinning each of these. The `[project.scripts]` entry registers the `laya-harness` console script; the controller reinstalls the package in Task 7 (pip is not a subagent gate). Tests do not need it.

- [ ] **Step 1: Write the supporting files**

`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "laya-harness"
version = "0.0.0"
description = "Local execution router for agentic coding harnesses, built on laya-mlx."
requires-python = ">=3.11"
dependencies = ["laya-mlx==0.3.0"]

[project.optional-dependencies]
dev = ["pytest>=8"]

[project.scripts]
laya-harness = "laya_harness.__main__:main"

[tool.setuptools.packages.find]
include = ["laya_harness*"]

[tool.setuptools.package-data]
laya_harness = ["*.json", "questions/*.json", "data/*.json"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["real_model: loads the pinned checkpoint from ~/.laya-harness; controller-only gate"]
addopts = "-m 'not real_model'"
```

`tests/conftest.py`:

```python
"""Test-wide guards (spec §4.4, §4.11).

Enforced here: HF_HUB_OFFLINE=1 (no downloads); LAYA_HARNESS_TEST=1, under which
`paths.home()` refuses ~/.laya-harness and `config.port()` refuses 47913; and no ambient
LAYA_HARNESS_HOME. Code that opens a socket must take its port from `config.port()` or the
`free_port` fixture.
"""

import json
import os
import socket
import sys

import pytest

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["LAYA_HARNESS_TEST"] = "1"

FAKE_ANSWERS = {
    "difficulty": {
        "type": "choice",
        "choice": "quick",
        "probabilities": {"quick": 0.6, "routine": 0.26, "multi_file": 0.08, "architecture": 0.06},
    },
    "plan_first": {"type": "noul", "noul": 0.2},
    "parallel": {"type": "noul", "noul": 0.1},
}


@pytest.fixture(autouse=True)
def _no_ambient_home(monkeypatch):
    """A test that forgets the `home` fixture fails instead of using a shell's LAYA_HARNESS_HOME."""
    monkeypatch.delenv("LAYA_HARNESS_HOME", raising=False)


@pytest.fixture
def home(tmp_path, monkeypatch):
    path = tmp_path / "home"
    monkeypatch.setenv("LAYA_HARNESS_HOME", str(path))
    return path


@pytest.fixture
def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def configured(home, free_port):
    """A fake-model config on a free port, written to the temporary state directory."""
    home.mkdir(mode=0o700, parents=True)
    (home / "sessions").mkdir(mode=0o700)
    cfg = {
        "port": free_port,
        "mode": "show",
        "model_mode": "fake",
        "fake_answers": FAKE_ANSWERS,
        "idle_seconds": 30,
        "interpreter": sys.executable,
    }
    (home / "config.json").write_text(json.dumps(cfg))
    return cfg


def write_config(home, **changes):
    path = home / "config.json"
    cfg = json.loads(path.read_text())
    cfg.update(changes)
    path.write_text(json.dumps(cfg))
    return cfg
```

- [ ] **Step 2: Write the failing tests**

`tests/test_paths_config.py`:

```python
import json
import os
import stat
import sys

import pytest

from laya_harness import config, paths


def mode_of(path):
    return stat.S_IMODE(path.stat().st_mode)


def test_home_honours_override_under_test_flag(home):
    assert paths.home() == home


@pytest.mark.parametrize("alias", [
    str(paths.REAL_HOME),
    "~/.laya-harness",
    f"{paths.REAL_HOME}/.",
    str(paths.REAL_HOME / "inside"),
    str(paths.REAL_HOME.parent),
])
def test_home_refuses_real_state_dir_its_children_and_parents(monkeypatch, alias):
    monkeypatch.setenv("LAYA_HARNESS_HOME", alias)
    with pytest.raises(paths.StateDirError):
        paths.home()


def test_home_refuses_a_symlink_to_the_real_state_dir(monkeypatch, tmp_path):
    link = tmp_path / "link"
    link.symlink_to(paths.REAL_HOME)
    monkeypatch.setenv("LAYA_HARNESS_HOME", str(link))
    with pytest.raises(paths.StateDirError):
        paths.home()


def test_home_requires_override_under_test_flag(monkeypatch):
    monkeypatch.delenv("LAYA_HARNESS_HOME", raising=False)
    with pytest.raises(paths.StateDirError):
        paths.home()


def test_override_ignored_without_test_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("LAYA_HARNESS_TEST", "0")
    monkeypatch.setenv("LAYA_HARNESS_HOME", str(tmp_path))
    assert paths.home() == paths.REAL_HOME


def test_state_file_names(home):
    names = [p.name for p in (paths.config_path(), paths.decisions_path(), paths.client_log(),
                              paths.service_log(), paths.sessions_dir(), paths.models_dir())]
    assert names == ["config.json", "decisions.jsonl", "client.log", "service.log", "sessions", "models"]
    assert {p.parent for p in (paths.config_path(), paths.sessions_dir(), paths.models_dir())} == {home}


def test_ensure_home_is_private(home):
    paths.ensure_home()
    assert mode_of(home) == 0o700 and mode_of(home / "sessions") == 0o700


def test_ensure_home_tightens_existing_dirs(home):
    (home / "sessions").mkdir(parents=True)
    home.chmod(0o755)
    (home / "sessions").chmod(0o755)
    paths.ensure_home()
    assert mode_of(home) == 0o700 and mode_of(home / "sessions") == 0o700


def test_load_returns_defaults_without_file(home):
    cfg = config.load()
    assert cfg["port"] == 47913 and cfg["mode"] == "show" and cfg["model_mode"] == "real"
    assert cfg["idle_seconds"] == 900
    assert cfg["interpreter"] is None and cfg["model_dir"] is None


def test_load_does_not_share_the_defaults(home):
    cfg = config.load()
    cfg["port"] = 1
    assert config.DEFAULTS["port"] == 47913 and config.load()["port"] == 47913


def test_save_round_trips_and_is_private(home):
    config.save({"port": 5555, "mode": "log-only"})
    assert config.load()["mode"] == "log-only"
    assert mode_of(home / "config.json") == 0o600
    assert json.loads((home / "config.json").read_text())["port"] == 5555


@pytest.mark.parametrize("mode", ["show", "log-only", "off"])
def test_every_spec_mode_is_accepted(home, mode):
    config.save({"mode": mode})
    assert config.load()["mode"] == mode


def test_unknown_mode_rejected(home):
    home.mkdir(parents=True)
    (home / "config.json").write_text(json.dumps({"mode": "loud"}))
    with pytest.raises(ValueError):
        config.load()


def test_port_refuses_real_port_under_test_flag(home):
    with pytest.raises(paths.StateDirError):
        config.port({"port": 47913})
    with pytest.raises(paths.StateDirError):
        config.port({"port": "47913"})
    assert config.port({"port": 5555}) == 5555


def test_port_allows_the_default_outside_tests(monkeypatch):
    monkeypatch.setenv("LAYA_HARNESS_TEST", "0")
    assert config.port({"port": 47913}) == 47913


@pytest.mark.parametrize("bad", [0, -1, 65536])
def test_port_out_of_range_is_rejected(bad):
    with pytest.raises(ValueError):
        config.port({"port": bad})


def test_interpreter_defaults_to_the_running_python():
    assert config.interpreter({"interpreter": None}) == sys.executable
    assert config.interpreter({"interpreter": "/x/python"}) == "/x/python"


def test_write_private_uses_unique_temps_and_cleans_up(home, monkeypatch):
    paths.ensure_home()
    target = home / "state.json"
    seen, real_replace = [], os.replace

    def recording(src, dst):
        seen.append(os.path.basename(src))
        real_replace(src, dst)

    monkeypatch.setattr(paths.os, "replace", recording)
    paths.write_private(target, "a")
    paths.write_private(target, "b")
    assert len(set(seen)) == 2 and target.read_text() == "b" and mode_of(target) == 0o600

    def failing(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(paths.os, "replace", failing)
    with pytest.raises(OSError):
        paths.write_private(target, "c")
    assert target.read_text() == "b" and list(home.glob("*.tmp")) == []


def test_append_private_creates_user_only_file(home):
    paths.ensure_home()
    target = home / "log.jsonl"
    paths.append_private(target, "a")
    paths.append_private(target, "b\n")
    assert target.read_text() == "a\nb\n" and mode_of(target) == 0o600


def test_append_private_tightens_an_existing_file(home):
    paths.ensure_home()
    target = home / "loose.log"
    target.write_text("old\n")
    target.chmod(0o644)
    paths.append_private(target, "new")
    assert target.read_text() == "old\nnew\n" and mode_of(target) == 0o600
```

- [ ] **Step 3: Create the modules as stubs**, so the tests fail on behaviour rather than on an import error (golden rule 4)

`laya_harness/paths.py` (stub — bodies raise `NotImplementedError`):

```python
"""Where laya-harness keeps its state (spec §4.11).

`LAYA_HARNESS_HOME` moves the state directory in tests only: it is honoured only when
`LAYA_HARNESS_TEST=1`, and under that flag the real `~/.laya-harness` is refused.
"""
import contextlib
import os
import tempfile
from pathlib import Path
REAL_HOME = Path.home() / '.laya-harness'
TEST_FLAG = 'LAYA_HARNESS_TEST'
HOME_OVERRIDE = 'LAYA_HARNESS_HOME'

class StateDirError(RuntimeError):
    """A test tried to use the real state directory or port."""

def testing() -> bool:
    raise NotImplementedError

def home() -> Path:
    raise NotImplementedError

def ensure_home() -> Path:
    raise NotImplementedError

def config_path() -> Path:
    raise NotImplementedError

def decisions_path() -> Path:
    raise NotImplementedError

def client_log() -> Path:
    raise NotImplementedError

def service_log() -> Path:
    raise NotImplementedError

def sessions_dir() -> Path:
    raise NotImplementedError

def models_dir() -> Path:
    raise NotImplementedError

def write_private(path: Path, text: str) -> None:
    """Write a file readable only by the user, replacing it atomically.

    Each write uses its own temporary file (mkstemp creates it 0600 in the same directory), so
    concurrent writers never share one, and the temporary file is removed if anything fails.
    """
    raise NotImplementedError

def append_private(path: Path, line: str) -> None:
    """Append one line to a file readable only by the user."""
    raise NotImplementedError
```

`laya_harness/config.py` (stub — bodies raise `NotImplementedError`):

```python
"""`~/.laya-harness/config.json` (spec §4.2, §4.4, §4.5, §4.11).

The port always comes from this file: hooks in the desktop app do not inherit variables
exported in the user's shell.
"""
import json
import sys
from . import paths
DEFAULT_PORT = 47913
MODES = ('show', 'log-only', 'off')
DEFAULTS = {'port': DEFAULT_PORT, 'mode': 'show', 'model_mode': 'real', 'idle_seconds': 900, 'interpreter': None, 'model_dir': None}

def load() -> dict:
    raise NotImplementedError

def save(cfg: dict) -> None:
    raise NotImplementedError

def port(cfg: dict) -> int:
    raise NotImplementedError

def interpreter(cfg: dict) -> str:
    raise NotImplementedError
```

- [ ] **Step 4: Run the tests and confirm RED**

Run: `.venv/bin/python -m pytest -q tests/test_paths_config.py`

Expected: `28 failed`; every failure is `NotImplementedError`. Record the output in the task report.

- [ ] **Step 5: Implement**, replacing the stubs with exactly this code

`laya_harness/paths.py`:

```python
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
```

`laya_harness/config.py`:

```python
"""`~/.laya-harness/config.json` (spec §4.2, §4.4, §4.5, §4.11).

The port always comes from this file: hooks in the desktop app do not inherit variables
exported in the user's shell.
"""

import json
import sys

from . import paths

DEFAULT_PORT = 47913
MODES = ("show", "log-only", "off")
DEFAULTS = {
    "port": DEFAULT_PORT,
    "mode": "show",
    "model_mode": "real",  # "real" loads laya-mlx; "fake" returns `fake_answers`
    "idle_seconds": 900,
    "interpreter": None,  # None means the interpreter running the client
    "model_dir": None,
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    path = paths.config_path()
    if path.is_file():
        cfg.update(json.loads(path.read_text(encoding="utf-8")))
    if cfg["mode"] not in MODES:
        raise ValueError(f"unknown mode: {cfg['mode']!r}")
    return cfg


def save(cfg: dict) -> None:
    paths.ensure_home()
    paths.write_private(paths.config_path(), json.dumps(cfg, indent=2, sort_keys=True) + "\n")


def port(cfg: dict) -> int:
    value = int(cfg["port"])
    if not 1 <= value <= 65535:
        raise ValueError(f"port out of range: {value}")
    if paths.testing() and value == DEFAULT_PORT:
        raise paths.StateDirError("tests must not use port 47913")
    return value


def interpreter(cfg: dict) -> str:
    return cfg.get("interpreter") or sys.executable
```

- [ ] **Step 6: Run the tests and confirm GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_paths_config.py`

Expected: `28 passed`.

Run: `.venv/bin/python -m pytest -q`

Expected: `29 passed, 1 deselected`.

- [ ] **Step 7: Self-review and report — no commit** (golden rule 2)

Run: `git diff --check` (expected: no output). Report to the controller: files changed, the exact RED and GREEN commands with their output, and anything skipped and why. The controller snapshots the task boundary on `refs/laywip/stage0/task-1` and dispatches the reviewers.

---

### Task 2: Packaged data: question set, checkpoint, catalog, fit table

**Files:**
- Create: `laya_harness/questions/profile_v0.json`
- Create: `laya_harness/checkpoint.json`
- Create: `laya_harness/data/claude_code_models.json`
- Create: `laya_harness/data/claude_code_fit.json`
- Create: `laya_harness/resources.py`
- Create: `tests/test_resources.py`
- Test: `tests/test_resources.py`

**Spec:** §4.5 (checkpoint), §4.8 (questions), §4.13 (catalog and fit table)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
- `resources`: `QUESTIONS`, `CHECKPOINT`, `CATALOG`, `FIT` (paths), `sha256_file(path) -> str`,
  `questions() -> dict`, `questions_sha256() -> str`, `checkpoint() -> dict`, `catalog() -> dict`,
  `fit() -> dict`, `catalog_sha256() -> str`.
- Data shapes later tasks rely on: `questions()["questions"]` (passed to laya), `questions()["display"]`
  (`difficulty.min_tier_p`, `plan_first.show_threshold`, `plan_first.min_chars`); checkpoint
  `required`, `files`, `settings`, `warmup_words`, `weights_sha256`; catalog `models[]` with
  `id, display, family, version, price.input, effort_levels, in_picker, allowed`; fit
  `classes.<class>[]` options of `{"family"|"model", "effort"}`.

> Revised after review round 1: the tests now compare the question set, the checkpoint and every catalog row by equality with tables copied from the spec, pin the option order, and check the hashes against hashlib (including a multi-chunk file and a fit-table edit). The data files are written in the GREEN step (the stub step creates only `resources.py`).

- [ ] **Step 1: Write the failing tests**

`tests/test_resources.py`:

```python
"""The packaged data, compared field by field with tables copied from the spec (§4.5, §4.8, §4.13)."""

import hashlib

from laya_harness import resources

ALL_EFFORT = ["low", "medium", "high", "xhigh", "max"]
NO_XHIGH = ["low", "medium", "high", "max"]

EXPECTED_QUESTIONS = {
    "id": "profile_v0",
    "questions": {
        "difficulty": {
            "type": "choice",
            "instructions": "How much work does the request in this message need?",
            "criteria": {
                "quick": "quick question or tiny edit",
                "routine": "routine single-area change",
                "multi_file": "multi-file feature or debugging",
                "architecture": "architecture, migration or hard reasoning",
            },
        },
        "plan_first": {"type": "noul", "instructions": "Should this request be planned before any file is edited?"},
        "parallel": {"type": "noul", "instructions": "Does it contain independent subtasks that could run in parallel?"},
    },
    "display": {
        "difficulty": {"min_tier_p": 0.8},
        "plan_first": {"show_threshold": 0.85, "min_chars": 200},
        "parallel": {"show_threshold": 0.85, "shown": False},
    },
}

EXPECTED_CHECKPOINT = {
    "repo": "aac6fef/laya-mlx",
    "revision": "047678560251f28113ee8f5df4be82102c7bf336",
    "weights_sha256": "b9c07bf14be2fa5c78a9193a3e6d840ac80e89e62fc40f425834c3d8a6eaa3de",
    "files": ["model.safetensors", "rl_agent_config.json", "encoder/config.json", "tokenizer/*", "mlx_config.json"],
    "required": ["model.safetensors", "rl_agent_config.json", "encoder/config.json",
                 "tokenizer/tokenizer.json", "tokenizer/tokenizer_config.json"],
    "settings": {"dtype": "float16", "batch_size": 1, "pad_to_multiple": 128, "max_len": 512},
    "warmup_words": [0, 60, 150, 260, 380, 600],
}


def _row(display, family, version, price, effort, menu, allowed):
    return {"display": display, "family": family, "version": version, "price": price,
            "effort_levels": effort, "in_picker": True, "menu": menu, "allowed": allowed}


EXPECTED_MODELS = {  # spec §4.13 starting catalog
    "claude-opus-5-5": _row("Opus 5.5", "opus", "5.5", {"input": 4.0, "output": 20.0}, ALL_EFFORT, "main", True),
    "claude-sonnet-5-5": _row("Sonnet 5.5", "sonnet", "5.5", {"input": 2.0, "output": 10.0}, ALL_EFFORT, "main", True),
    "claude-haiku-5-5": _row("Haiku 5.5", "haiku", "5.5", {"input": 0.1, "output": 0.5, "input_above_100k": 0.5,
                                                         "output_above_100k": 2.5}, ALL_EFFORT, "main", True),
    "claude-opus-5": _row("Opus 5", "opus", "5", {"input": 5.0, "output": 25.0}, ALL_EFFORT, "more", False),
    "claude-opus-4-8": _row("Opus 4.8", "opus", "4.8", {"input": 5.0, "output": 25.0}, ALL_EFFORT, "more", False),
    "claude-opus-4-7": _row("Opus 4.7", "opus", "4.7", {"input": 5.0, "output": 25.0}, ALL_EFFORT, "more", False),
    "claude-opus-4-6": _row("Opus 4.6", "opus", "4.6", {"input": 5.0, "output": 25.0}, NO_XHIGH, "more", False),
    "claude-sonnet-5": _row("Sonnet 5", "sonnet", "5", {"input": 2.0, "output": 10.0}, ALL_EFFORT, "more", False),
    "claude-sonnet-4-6": _row("Sonnet 4.6", "sonnet", "4.6", {"input": 3.0, "output": 15.0}, NO_XHIGH, "more", False),
    "claude-haiku-4-5": _row("Haiku 4.5", "haiku", "4.5", {"input": 1.0, "output": 5.0}, [], "more", False),
    "claude-fable-5-1": _row("Fable 5.1", "fable", "5.1", {"input": 10.0, "output": 50.0}, ALL_EFFORT, "main", False),
    "claude-fable-5": _row("Fable 5", "fable", "5", {"input": 10.0, "output": 50.0}, ALL_EFFORT, "more", False),
}


def test_question_set_matches_spec_4_8():
    q = resources.questions()
    assert q == EXPECTED_QUESTIONS
    assert list(q["questions"]["difficulty"]["criteria"]) == ["quick", "routine", "multi_file", "architecture"]


def test_checkpoint_is_pinned_per_spec_4_5():
    assert resources.checkpoint() == EXPECTED_CHECKPOINT


def test_catalog_matches_spec_4_13():
    catalog = resources.catalog()
    assert "docs/reference/model-picker-2026-10-08.png" in catalog["source"]
    rows = {m["id"]: m for m in catalog["models"]}
    assert len(rows) == len(catalog["models"]) == 12
    assert set(rows) == set(EXPECTED_MODELS)
    for model_id, expected in EXPECTED_MODELS.items():
        assert rows[model_id] == {"id": model_id, **expected}, model_id


def test_fit_table_defaults_match_spec_4_13():
    assert resources.fit()["classes"] == {
        "quick": [{"family": "haiku", "effort": "low"}, {"family": "sonnet", "effort": "low"}],
        "routine": [{"family": "sonnet", "effort": "medium"}],
        "multi_file": [{"family": "opus", "effort": "high"}],
        "architecture": [{"family": "opus", "effort": "xhigh"}],
    }


def test_hashes_match_hashlib(tmp_path, monkeypatch):
    assert resources.questions_sha256() == hashlib.sha256(resources.QUESTIONS.read_bytes()).hexdigest()
    both = resources.CATALOG.read_bytes() + resources.FIT.read_bytes()
    assert resources.catalog_sha256() == hashlib.sha256(both).hexdigest()

    before = resources.catalog_sha256()
    edited = tmp_path / "fit.json"
    edited.write_bytes(resources.FIT.read_bytes() + b" ")
    monkeypatch.setattr(resources, "FIT", edited)
    assert resources.catalog_sha256() != before  # editing the fit table changes the recorded hash

    big = tmp_path / "big.bin"
    big.write_bytes(b"x" * (3 * (1 << 20) + 7))  # several 1 MiB chunks, as for the weights
    assert resources.sha256_file(big) == hashlib.sha256(big.read_bytes()).hexdigest()
```

- [ ] **Step 2: Create the modules as stubs**, so the tests fail on behaviour rather than on an import error (golden rule 4)

`laya_harness/resources.py` (stub — bodies raise `NotImplementedError`):

```python
"""Data shipped inside the package: the question set, the pinned checkpoint, and the Claude
Code model catalog and fit table (spec §4.5, §4.8, §4.13)."""
import hashlib
import json
from pathlib import Path
PACKAGE = Path(__file__).parent
QUESTIONS = PACKAGE / 'questions' / 'profile_v0.json'
CHECKPOINT = PACKAGE / 'checkpoint.json'
CATALOG = PACKAGE / 'data' / 'claude_code_models.json'
FIT = PACKAGE / 'data' / 'claude_code_fit.json'

def _read(path: Path) -> dict:
    raise NotImplementedError

def sha256_file(path: Path) -> str:
    raise NotImplementedError

def questions() -> dict:
    raise NotImplementedError

def questions_sha256() -> str:
    raise NotImplementedError

def checkpoint() -> dict:
    raise NotImplementedError

def catalog() -> dict:
    raise NotImplementedError

def fit() -> dict:
    raise NotImplementedError

def catalog_sha256() -> str:
    """One hash over the catalog and the fit table, recorded in every decision row."""
    raise NotImplementedError
```

- [ ] **Step 3: Run the tests and confirm RED**

Run: `.venv/bin/python -m pytest -q tests/test_resources.py`

Expected: `5 failed`; every failure is `NotImplementedError`. Record the output in the task report.

- [ ] **Step 4: Implement**, replacing the stubs with exactly this code

`laya_harness/resources.py`:

```python
"""Data shipped inside the package: the question set, the pinned checkpoint, and the Claude
Code model catalog and fit table (spec §4.5, §4.8, §4.13)."""

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).parent
QUESTIONS = PACKAGE / "questions" / "profile_v0.json"
CHECKPOINT = PACKAGE / "checkpoint.json"
CATALOG = PACKAGE / "data" / "claude_code_models.json"
FIT = PACKAGE / "data" / "claude_code_fit.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def questions() -> dict:
    return _read(QUESTIONS)


def questions_sha256() -> str:
    return sha256_file(QUESTIONS)


def checkpoint() -> dict:
    return _read(CHECKPOINT)


def catalog() -> dict:
    return _read(CATALOG)


def fit() -> dict:
    return _read(FIT)


def catalog_sha256() -> str:
    """One hash over the catalog and the fit table, recorded in every decision row."""
    digest = hashlib.sha256()
    digest.update(CATALOG.read_bytes())
    digest.update(FIT.read_bytes())
    return digest.hexdigest()
```

`laya_harness/questions/profile_v0.json`:

```json
{
  "id": "profile_v0",
  "questions": {
    "difficulty": {
      "type": "choice",
      "instructions": "How much work does the request in this message need?",
      "criteria": {
        "quick": "quick question or tiny edit",
        "routine": "routine single-area change",
        "multi_file": "multi-file feature or debugging",
        "architecture": "architecture, migration or hard reasoning"
      }
    },
    "plan_first": {
      "type": "noul",
      "instructions": "Should this request be planned before any file is edited?"
    },
    "parallel": {
      "type": "noul",
      "instructions": "Does it contain independent subtasks that could run in parallel?"
    }
  },
  "display": {
    "difficulty": {"min_tier_p": 0.8},
    "plan_first": {"show_threshold": 0.85, "min_chars": 200},
    "parallel": {"show_threshold": 0.85, "shown": false}
  }
}
```

`laya_harness/checkpoint.json`:

```json
{
  "repo": "aac6fef/laya-mlx",
  "revision": "047678560251f28113ee8f5df4be82102c7bf336",
  "weights_sha256": "b9c07bf14be2fa5c78a9193a3e6d840ac80e89e62fc40f425834c3d8a6eaa3de",
  "files": [
    "model.safetensors",
    "rl_agent_config.json",
    "encoder/config.json",
    "tokenizer/*",
    "mlx_config.json"
  ],
  "required": [
    "model.safetensors",
    "rl_agent_config.json",
    "encoder/config.json",
    "tokenizer/tokenizer.json",
    "tokenizer/tokenizer_config.json"
  ],
  "settings": {"dtype": "float16", "batch_size": 1, "pad_to_multiple": 128, "max_len": 512},
  "warmup_words": [0, 60, 150, 260, 380, 600]
}
```

`laya_harness/data/claude_code_models.json`:

```json
{
  "source": "Picker: docs/reference/model-picker-2026-10-08.png. IDs and prices: platform.claude.com models overview and Haiku 5.5 page (2026-10-08). Older versions' effort levels: platform.claude.com effort docs (2026-10-08).",
  "models": [
    {"id": "claude-opus-5-5", "display": "Opus 5.5", "family": "opus", "version": "5.5", "price": {"input": 4.0, "output": 20.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "menu": "main", "allowed": true},
    {"id": "claude-sonnet-5-5", "display": "Sonnet 5.5", "family": "sonnet", "version": "5.5", "price": {"input": 2.0, "output": 10.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "menu": "main", "allowed": true},
    {"id": "claude-haiku-5-5", "display": "Haiku 5.5", "family": "haiku", "version": "5.5", "price": {"input": 0.1, "output": 0.5, "input_above_100k": 0.5, "output_above_100k": 2.5}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "menu": "main", "allowed": true},
    {"id": "claude-opus-5", "display": "Opus 5", "family": "opus", "version": "5", "price": {"input": 5.0, "output": 25.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "menu": "more", "allowed": false},
    {"id": "claude-opus-4-8", "display": "Opus 4.8", "family": "opus", "version": "4.8", "price": {"input": 5.0, "output": 25.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "menu": "more", "allowed": false},
    {"id": "claude-opus-4-7", "display": "Opus 4.7", "family": "opus", "version": "4.7", "price": {"input": 5.0, "output": 25.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "menu": "more", "allowed": false},
    {"id": "claude-opus-4-6", "display": "Opus 4.6", "family": "opus", "version": "4.6", "price": {"input": 5.0, "output": 25.0}, "effort_levels": ["low", "medium", "high", "max"], "in_picker": true, "menu": "more", "allowed": false},
    {"id": "claude-sonnet-5", "display": "Sonnet 5", "family": "sonnet", "version": "5", "price": {"input": 2.0, "output": 10.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "menu": "more", "allowed": false},
    {"id": "claude-sonnet-4-6", "display": "Sonnet 4.6", "family": "sonnet", "version": "4.6", "price": {"input": 3.0, "output": 15.0}, "effort_levels": ["low", "medium", "high", "max"], "in_picker": true, "menu": "more", "allowed": false},
    {"id": "claude-haiku-4-5", "display": "Haiku 4.5", "family": "haiku", "version": "4.5", "price": {"input": 1.0, "output": 5.0}, "effort_levels": [], "in_picker": true, "menu": "more", "allowed": false},
    {"id": "claude-fable-5-1", "display": "Fable 5.1", "family": "fable", "version": "5.1", "price": {"input": 10.0, "output": 50.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "menu": "main", "allowed": false},
    {"id": "claude-fable-5", "display": "Fable 5", "family": "fable", "version": "5", "price": {"input": 10.0, "output": 50.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "menu": "more", "allowed": false}
  ]
}
```

`laya_harness/data/claude_code_fit.json`:

```json
{
  "classes": {
    "quick": [{"family": "haiku", "effort": "low"}, {"family": "sonnet", "effort": "low"}],
    "routine": [{"family": "sonnet", "effort": "medium"}],
    "multi_file": [{"family": "opus", "effort": "high"}],
    "architecture": [{"family": "opus", "effort": "xhigh"}]
  }
}
```

- [ ] **Step 5: Run the tests and confirm GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_resources.py`

Expected: `5 passed`.

Run: `.venv/bin/python -m pytest -q`

Expected: `34 passed, 1 deselected`.

- [ ] **Step 6: Self-review and report — no commit** (golden rule 2)

Run: `git diff --check` (expected: no output). Report to the controller: files changed, the exact RED and GREEN commands with their output, and anything skipped and why. The controller snapshots the task boundary on `refs/laywip/stage0/task-2` and dispatches the reviewers.

---

### Task 3: Prompt source, transcript tail, session state

**Files:**
- Create: `tests/fixtures/payloads.json`
- Create: `laya_harness/source.py`
- Create: `laya_harness/transcript.py`
- Create: `laya_harness/session_state.py`
- Create: `tests/test_source_session.py`
- Test: `tests/test_source_session.py`

**Spec:** §4.6 (session state, switch precedence, transcript tail), §4.7 (prompt source), Appendix C

**Interfaces:**
- Consumes: `paths.sessions_dir()`, `paths.ensure_home()`, `paths.write_private()` (Task 1).
- Produces:
- `source.classify(payload: dict) -> str`: one of `human`, `task-notification`, `agent`, `peer`, `subagent`.
- `transcript.TAIL_BYTES = 262144`; `transcript.last_assistant(path) -> dict | None` with keys
  `model`, `effort`, `ts` (epoch float or None).
- `session_state.DEFAULT` (keys `model, effort, model_source, switched_at,
  first_prompt_after_switch_at, prompt_count, model_line_shown, plan_shown, updated`),
  `load(session_id) -> dict`, `save(session_id, state) -> None`,
  `on_session_start(state, source) -> dict`, `on_model_switch(state, to_model, now) -> dict`,
  `switch_pending(state, reply) -> bool`, `on_human_prompt(state, now, reply) -> dict`.

> Revised after review round 1: subagents are recognised by `agent_id` or a `/subagents/` path, never `agent_type` alone; the tail reader skips non-object rows and refuses non-string paths; a mistyped session file falls back to the defaults; a reply's effort is taken as carried; and 33 tests pin the switch edge cases, the tail reader, the session-start resets and a valid state's round trip (review round 2). From the Task 6 review: the tail reader opens regular files only and reads at most TAIL_BYTES, so a FIFO or a device in `transcript_path` can never block the hook (one more test). `tests/fixtures/payloads.json` holds the payload shapes captured in check 4, with identifiers and prompt text replaced.

- [ ] **Step 1: Write the supporting files**

`tests/fixtures/payloads.json`:

```json
{
  "_source": "Shapes captured in check 4 (spec Appendix C) in the desktop Code tab on 2026-10-08; identifiers and prompt text replaced.",
  "session_start_startup": {
    "session_id": "sess-1",
    "transcript_path": "TRANSCRIPT",
    "cwd": "/tmp/project",
    "scratchpad_dir": "/tmp/scratch",
    "hook_event_name": "SessionStart",
    "source": "startup"
  },
  "session_start_resume": {
    "session_id": "sess-1",
    "transcript_path": "TRANSCRIPT",
    "cwd": "/tmp/project",
    "scratchpad_dir": "/tmp/scratch",
    "hook_event_name": "SessionStart",
    "source": "resume",
    "session_title": "Title",
    "seconds_since_last_response": 190,
    "context_tokens": 117824,
    "prompt_cache_likely_expired": false,
    "estimated_cache_write_usd": 1.1782
  },
  "user_prompt_human": {
    "session_id": "sess-1",
    "transcript_path": "TRANSCRIPT",
    "cwd": "/tmp/project",
    "scratchpad_dir": "/tmp/scratch",
    "prompt_id": "prompt-1",
    "permission_mode": "auto",
    "hook_event_name": "UserPromptSubmit",
    "prompt": "rename the variable foo to bar in utils.py",
    "session_title": "Title"
  },
  "user_prompt_task_notification": {
    "session_id": "sess-1",
    "transcript_path": "TRANSCRIPT",
    "cwd": "/tmp/project",
    "scratchpad_dir": "/tmp/scratch",
    "prompt_id": "prompt-2",
    "permission_mode": "auto",
    "hook_event_name": "UserPromptSubmit",
    "prompt": "<task-notification>\n<task-id>br0jok66y</task-id>\n<status>completed</status>\n</task-notification>",
    "session_title": "Title"
  },
  "user_prompt_agent_message": {
    "session_id": "sess-1",
    "transcript_path": "TRANSCRIPT",
    "cwd": "/tmp/project",
    "scratchpad_dir": "/tmp/scratch",
    "prompt_id": "prompt-3",
    "permission_mode": "auto",
    "hook_event_name": "UserPromptSubmit",
    "prompt": "<agent-message from=\"afa14421701a5128d\">\n[Subagent hand-back] done\n</agent-message>",
    "session_title": "Title"
  },
  "user_prompt_cross_session": {
    "session_id": "sess-1",
    "transcript_path": "TRANSCRIPT",
    "cwd": "/tmp/project",
    "scratchpad_dir": "/tmp/scratch",
    "prompt_id": "prompt-4",
    "permission_mode": "auto",
    "hook_event_name": "UserPromptSubmit",
    "prompt": "<cross-session-message from=\"local_708eeb92\" name=\"Other session\">\nreply OK\n</cross-session-message>",
    "session_title": "Title"
  },
  "post_model_switch": {
    "session_id": "sess-1",
    "transcript_path": "TRANSCRIPT",
    "cwd": "/tmp/project",
    "scratchpad_dir": "/tmp/scratch",
    "prompt_id": "prompt-5",
    "hook_event_name": "PostModelSwitch",
    "from_model": "claude-opus-4-6",
    "to_model": "claude-opus-4-7",
    "requested_model": "claude-opus-4-7",
    "source": "sdk",
    "context_tokens": 86688,
    "prompt_cache_warm": true,
    "cache_ttl": "1h",
    "pricing": "catalog",
    "estimated_cache_write_usd": 0.8669
  }
}
```

- [ ] **Step 2: Write the failing tests**

`tests/test_source_session.py`:

```python
import json
import os
import stat
import threading
from pathlib import Path

import pytest

from laya_harness import session_state, source, transcript

PAYLOADS = json.loads((Path(__file__).parent / "fixtures" / "payloads.json").read_text())
DEFAULT = session_state.DEFAULT


# --- prompt source (spec §4.7) -------------------------------------------------------------

@pytest.mark.parametrize(
    "name, expected",
    [
        ("user_prompt_human", "human"),
        ("user_prompt_task_notification", "task-notification"),
        ("user_prompt_agent_message", "agent"),
        ("user_prompt_cross_session", "peer"),
    ],
)
def test_classify_captured_payloads(name, expected):
    assert source.classify(PAYLOADS[name]) == expected


def test_classify_subagent_guard():
    assert source.classify(dict(PAYLOADS["user_prompt_human"], agent_id="a1")) == "subagent"
    assert source.classify(dict(PAYLOADS["user_prompt_human"], transcript_path="/x/subagents/a.jsonl")) == "subagent"


def test_agent_type_alone_is_still_human():
    # a main session started with --agent carries agent_type on every prompt
    assert source.classify(dict(PAYLOADS["user_prompt_human"], agent_type="reviewer")) == "human"


def test_prefix_wins_over_agent_id():
    payload = dict(PAYLOADS["user_prompt_task_notification"], agent_id="a1")
    assert source.classify(payload) == "task-notification"


def test_non_string_prompt_and_path_are_human():
    assert source.classify({"prompt": 5, "transcript_path": 7}) == "human"


# --- transcript tail (spec §4.6) -----------------------------------------------------------

def _row(model, ts, effort="high", **extra):
    return json.dumps(
        {"type": "assistant", "timestamp": ts, "effort": effort, "message": {"model": model}, **extra}
    )


def test_last_assistant_returns_newest_main_thread_reply(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(
        "\n".join(
            [
                _row("claude-opus-4-6", "2026-10-08T04:18:27.000Z"),
                json.dumps({"type": "user", "message": {"content": "hi"}}),
                _row("claude-opus-4-7", "2026-10-08T04:28:11.000Z", effort="medium"),
                _row("claude-haiku-5-5", "2026-10-08T04:29:00.000Z", isSidechain=True),
                _row("<synthetic>", "2026-10-08T04:30:00.000Z"),
            ]
        )
        + "\n"
    )
    reply = transcript.last_assistant(str(t))
    assert reply == {"model": "claude-opus-4-7", "effort": "medium", "ts": 1791433691.0}


def test_last_assistant_never_blocks_on_a_fifo(tmp_path):
    """Spec §4.6: only a regular file is read. Opening a FIFO would block the hook until killed."""
    fifo = tmp_path / "transcript.fifo"
    os.mkfifo(fifo)
    results = []
    worker = threading.Thread(target=lambda: results.append(transcript.last_assistant(str(fifo))), daemon=True)
    worker.start()
    worker.join(2)
    blocked = worker.is_alive()
    if blocked:  # release a reader stuck in open() so the test can finish
        os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))
        worker.join(2)
    assert not blocked and results == [None]


def test_last_assistant_missing_empty_or_not_a_string(tmp_path):
    assert transcript.last_assistant(None) is None
    assert transcript.last_assistant(str(tmp_path / "nope.jsonl")) is None
    (tmp_path / "empty.jsonl").write_text("")
    assert transcript.last_assistant(str(tmp_path / "empty.jsonl")) is None
    assert transcript.last_assistant(1) is None  # never treated as a file descriptor
    os.fstat(1)  # stdout is still open


def test_reply_beyond_the_tail_is_not_returned(tmp_path, monkeypatch):
    monkeypatch.setattr(transcript, "TAIL_BYTES", 300)
    t = tmp_path / "t.jsonl"
    filler = json.dumps({"type": "user", "message": {"content": "x" * 400}})
    t.write_text(_row("claude-opus-4-7", "2026-10-08T04:28:11.000Z") + "\n" + filler + "\n")
    assert transcript.last_assistant(str(t)) is None


def test_cut_off_first_line_is_dropped(tmp_path, monkeypatch):
    t = tmp_path / "t.jsonl"
    row = _row("claude-opus-4-7", "2026-10-08T04:28:11.000Z")
    t.write_text("junk-before-the-seek-point" + row + "\n")
    monkeypatch.setattr(transcript, "TAIL_BYTES", len(row) + 1)  # the seek lands where the row starts
    assert transcript.last_assistant(str(t)) is None


def test_half_written_and_non_json_lines_are_skipped(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(
        _row("claude-opus-4-7", "2026-10-08T04:28:11.000Z") + "\n"
        + "not json at all\n"
        + "123\n"
        + json.dumps({"type": "assistant", "message": "oops"}) + "\n"
        + '{"type": "assistant", "message": {"mod'
    )
    assert transcript.last_assistant(str(t))["model"] == "claude-opus-4-7"


@pytest.mark.parametrize("bad", ["garbage", 17])
def test_bad_timestamp_gives_none(tmp_path, bad):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "assistant", "timestamp": bad, "message": {"model": "m"}}) + "\n")
    assert transcript.last_assistant(str(t)) == {"model": "m", "effort": None, "ts": None}


@pytest.mark.parametrize("bad_effort", [{"level": "high"}, 3])
def test_non_string_effort_counts_as_none(tmp_path, bad_effort):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "assistant", "effort": bad_effort, "message": {"model": "m"}}) + "\n")
    assert transcript.last_assistant(str(t))["effort"] is None


def test_last_assistant_reads_only_the_tail(tmp_path, monkeypatch):
    monkeypatch.setattr(transcript, "TAIL_BYTES", 300)
    t = tmp_path / "t.jsonl"
    t.write_text(
        _row("claude-opus-4-6", "2026-10-08T04:18:27.000Z") + "\n" + ("x" * 1000) + "\n"
        + _row("claude-opus-4-7", "2026-10-08T04:28:11.000Z") + "\n"
    )
    assert transcript.last_assistant(str(t))["model"] == "claude-opus-4-7"


# --- session files (spec §4.6) -------------------------------------------------------------

def test_session_file_round_trip_is_private(home):
    state = session_state.load("sess-1")
    assert state["model"] is None and state["prompt_count"] == 0
    state["prompt_count"] = 3
    session_state.save("sess-1", state)
    assert session_state.load("sess-1")["prompt_count"] == 3
    path = home / "sessions" / "sess-1.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_unsafe_session_id_is_hashed(home):
    session_state.save("../evil", dict(DEFAULT))
    files = [p.name for p in (home / "sessions").iterdir()]
    assert len(files) == 1 and len(files[0]) == 64 + len(".json")


@pytest.mark.parametrize("content", ["null", "[1, 2]", "not json", '{"prompt_count": null}',
                                     '{"switched_at": "x"}', '{"plan_shown": 1}', '{"prompt_count": true}',
                                     '{"prompt_count": -1}', '{"switched_at": true}'])
def test_corrupt_session_file_starts_from_defaults(home, content):
    (home / "sessions").mkdir(parents=True)
    (home / "sessions" / "sess-1.json").write_text(content)
    assert session_state.load("sess-1") == DEFAULT


def test_a_valid_non_default_state_round_trips(home):
    """An over-strict type check would silently reset every session (spec §4.6, §4.9)."""
    state = session_state.on_model_switch(dict(DEFAULT), "claude-opus-4-7", now=1000.0)
    state = session_state.on_human_prompt(state, 1010.0, None)
    state.update(prompt_count=5, effort="high", model_line_shown=True, plan_shown=True)
    session_state.save("sess-1", state)
    loaded = session_state.load("sess-1")
    assert loaded == state
    assert isinstance(loaded["updated"], float)
    assert (loaded["switched_at"], loaded["first_prompt_after_switch_at"]) == (1000.0, 1010.0)


# --- session start (spec §4.6) -------------------------------------------------------------

@pytest.mark.parametrize("payload", ["session_start_startup", "session_start_resume"])
def test_session_start_from_captured_sources(payload):
    state = dict(DEFAULT, prompt_count=4, model_line_shown=True, plan_shown=True)
    state = session_state.on_session_start(state, PAYLOADS[payload]["source"])
    reset = PAYLOADS[payload]["source"] == "startup"
    assert (state["prompt_count"], state["model_line_shown"], state["plan_shown"]) == (
        (0, False, False) if reset else (4, True, True))


@pytest.mark.parametrize("src, reset", [("startup", True), ("fork", True), ("resume", False),
                                        ("clear", False), ("compact", False)])
def test_which_sources_reset_the_counters(src, reset):
    state = session_state.on_session_start(dict(DEFAULT, prompt_count=4, model_line_shown=True, plan_shown=True), src)
    assert (state["prompt_count"], state["model_line_shown"], state["plan_shown"]) == (
        (0, False, False) if reset else (4, True, True))


# --- prompts, transcript and switches (spec §4.6) ------------------------------------------

def test_second_prompt_takes_model_and_effort_from_transcript():
    state = session_state.on_human_prompt(dict(DEFAULT), 100.0, None)
    assert state["prompt_count"] == 1 and state["model"] is None
    state = session_state.on_human_prompt(state, 200.0, {"model": "claude-opus-5-5", "effort": "xhigh", "ts": 150.0})
    assert (state["model"], state["effort"], state["model_source"]) == ("claude-opus-5-5", "xhigh", "transcript")


def test_first_prompt_ignores_transcript():
    state = session_state.on_human_prompt(dict(DEFAULT), 100.0, {"model": "m", "effort": "low", "ts": 50.0})
    assert state["model"] is None and state["effort"] is None


def test_missing_transcript_keeps_the_values():
    state = dict(DEFAULT, prompt_count=2, model="M", effort="high", model_source="transcript")
    state = session_state.on_human_prompt(state, 300.0, None)
    assert (state["prompt_count"], state["model"], state["effort"], state["model_source"]) == (
        3, "M", "high", "transcript")


def test_accepted_reply_without_effort_clears_it():
    state = dict(DEFAULT, prompt_count=2, model="claude-opus-5-5", effort="xhigh", model_source="transcript")
    state = session_state.on_human_prompt(state, 300.0, {"model": "claude-haiku-4-5", "effort": None, "ts": 250.0})
    assert (state["model"], state["effort"]) == ("claude-haiku-4-5", None)


def test_switch_precedence_regression():
    """Spec §4.6 + §6: switch to B; stale transcript still on A keeps B; a reply on B after the
    first post-switch prompt is accepted; a reply on A from the in-flight turn is ignored."""
    state = dict(DEFAULT, prompt_count=1, model="claude-opus-4-6", model_source="transcript")
    state = session_state.on_model_switch(state, PAYLOADS["post_model_switch"]["to_model"], now=1000.0)
    assert (state["model"], state["model_source"], state["switched_at"]) == ("claude-opus-4-7", "post_model_switch", 1000.0)
    state = session_state.on_human_prompt(state, 1010.0, {"model": "claude-opus-4-6", "effort": "high", "ts": 1005.0})
    assert (state["model"], state["model_source"], state["first_prompt_after_switch_at"]) == (
        "claude-opus-4-7", "post_model_switch", 1010.0)
    state = session_state.on_human_prompt(state, 1030.0, {"model": "claude-opus-4-7", "effort": "high", "ts": 1020.0})
    assert (state["model"], state["model_source"], state["switched_at"], state["first_prompt_after_switch_at"]) == (
        "claude-opus-4-7", "transcript", None, None)


def _pending(model="claude-opus-4-7"):
    state = dict(DEFAULT, prompt_count=1, model="claude-opus-4-6", model_source="transcript")
    state = session_state.on_model_switch(state, model, now=1000.0)
    return session_state.on_human_prompt(state, 1010.0, {"model": "claude-opus-4-6", "effort": "high", "ts": 1005.0})


def test_reply_at_exactly_the_first_prompt_time_keeps_the_switch():
    state = session_state.on_human_prompt(_pending(), 1030.0, {"model": "claude-opus-4-6", "effort": "high", "ts": 1010.0})
    assert (state["model"], state["model_source"]) == ("claude-opus-4-7", "post_model_switch")


def test_reply_without_timestamp_keeps_the_switch():
    state = session_state.on_human_prompt(_pending(), 1030.0, {"model": "claude-opus-4-6", "effort": "high", "ts": None})
    assert (state["model"], state["model_source"]) == ("claude-opus-4-7", "post_model_switch")


def test_effort_is_taken_while_a_switch_is_pending():
    state = session_state.on_human_prompt(_pending(), 1030.0, {"model": "claude-opus-4-6", "effort": "low", "ts": 1005.0})
    assert (state["model"], state["effort"]) == ("claude-opus-4-7", "low")


def test_a_new_switch_resets_the_first_prompt_time():
    state = dict(DEFAULT, prompt_count=1, model="A", model_source="transcript")
    state = session_state.on_model_switch(state, "B", now=1000.0)
    state = session_state.on_human_prompt(state, 1010.0, None)  # first prompt after A -> B
    state = session_state.on_model_switch(state, "C", now=1025.0)
    assert state["first_prompt_after_switch_at"] is None
    state = session_state.on_human_prompt(state, 1030.0, {"model": "B", "effort": "high", "ts": 1020.0})
    assert (state["model"], state["first_prompt_after_switch_at"]) == ("C", 1030.0)


def test_first_prompt_after_a_switch_is_recorded_even_without_a_reply():
    state = session_state.on_model_switch(dict(DEFAULT), "claude-opus-4-7", now=5.0)
    state = session_state.on_human_prompt(state, 9.0, None)
    assert (state["prompt_count"], state["first_prompt_after_switch_at"]) == (1, 9.0)


def test_switch_without_model_changes_nothing():
    state = session_state.on_model_switch(dict(DEFAULT), None, now=5.0)
    assert state["switched_at"] is None and state["model"] is None
```

- [ ] **Step 3: Create the modules as stubs**, so the tests fail on behaviour rather than on an import error (golden rule 4)

`laya_harness/source.py` (stub — bodies raise `NotImplementedError`):

```python
"""Where a UserPromptSubmit prompt came from (spec §4.7). Only `human` prompts are profiled.

The prefixes are checked first. A subagent is recognised by `agent_id` or a `/subagents/`
transcript path, never by `agent_type` alone: that is also set in a main session started with
`--agent`.
"""
PREFIXES = (('<task-notification', 'task-notification'), ('<agent-message', 'agent'), ('<cross-session-message', 'peer'))

def classify(payload: dict) -> str:
    raise NotImplementedError
```

`laya_harness/transcript.py` (stub — bodies raise `NotImplementedError`):

```python
"""The last assistant reply in a Claude Code transcript (spec §4.6). Reads only the tail."""
import json
import os
import stat
from datetime import datetime
TAIL_BYTES = 256 * 1024

def _timestamp(value):
    raise NotImplementedError

def last_assistant(path):
    """Return {"model", "effort", "ts"} for the newest main-thread assistant row in the tail, or None.

    Only the last TAIL_BYTES are read. A cut-off first line, lines that are not JSON objects,
    sidechain rows and synthetic models (names starting with "<") are skipped. A path that is not
    a string or not a regular file, or a missing or unreadable file, gives None. A lagging transcript still returns its
    newest row, which may be stale; session_state's pending-switch rule handles that.
    """
    raise NotImplementedError
```

`laya_harness/session_state.py` (stub — bodies raise `NotImplementedError`):

```python
"""Per-session state owned by the client (spec §4.6).

The model and effort start unknown: the desktop app gives hooks neither on a session's first
prompt. A PostModelSwitch stays authoritative until the transcript holds an assistant row
timestamped after the first prompt submitted after that switch.
"""
import hashlib
import json
import re
import time
from . import paths
DEFAULT = {'model': None, 'effort': None, 'model_source': None, 'switched_at': None, 'first_prompt_after_switch_at': None, 'prompt_count': 0, 'model_line_shown': False, 'plan_shown': False, 'updated': None}
_SAFE = re.compile('^[A-Za-z0-9_-]{1,128}$')
_NUMBER = (int, float)
_TYPES = {'model': (str, type(None)), 'effort': (str, type(None)), 'model_source': (str, type(None)), 'switched_at': _NUMBER + (type(None),), 'first_prompt_after_switch_at': _NUMBER + (type(None),), 'model_line_shown': (bool,), 'plan_shown': (bool,), 'updated': _NUMBER + (type(None),)}

def _valid(state: dict) -> bool:
    raise NotImplementedError

def _file(session_id: str):
    raise NotImplementedError

def load(session_id: str) -> dict:
    """The session's state, or the defaults if the file is missing, not a JSON object, or mistyped."""
    raise NotImplementedError

def save(session_id: str, state: dict) -> None:
    raise NotImplementedError

def on_session_start(state: dict, source) -> dict:
    raise NotImplementedError

def on_model_switch(state: dict, to_model, now: float) -> dict:
    raise NotImplementedError

def switch_pending(state: dict, reply) -> bool:
    raise NotImplementedError

def on_human_prompt(state: dict, now: float, reply) -> dict:
    """Count the prompt and fold in the transcript's last reply (from the 2nd prompt on)."""
    raise NotImplementedError
```

- [ ] **Step 4: Run the tests and confirm RED**

Run: `.venv/bin/python -m pytest -q tests/test_source_session.py`

Expected: `49 failed`; every failure is `NotImplementedError`. Record the output in the task report.

- [ ] **Step 5: Implement**, replacing the stubs with exactly this code

`laya_harness/source.py`:

```python
"""Where a UserPromptSubmit prompt came from (spec §4.7). Only `human` prompts are profiled.

The prefixes are checked first. A subagent is recognised by `agent_id` or a `/subagents/`
transcript path, never by `agent_type` alone: that is also set in a main session started with
`--agent`.
"""

PREFIXES = (
    ("<task-notification", "task-notification"),
    ("<agent-message", "agent"),
    ("<cross-session-message", "peer"),
)


def classify(payload: dict) -> str:
    prompt = payload.get("prompt")
    prompt = prompt if isinstance(prompt, str) else ""
    for prefix, name in PREFIXES:
        if prompt.startswith(prefix):
            return name
    transcript_path = payload.get("transcript_path")
    if payload.get("agent_id") or (isinstance(transcript_path, str) and "/subagents/" in transcript_path):
        return "subagent"
    return "human"
```

`laya_harness/transcript.py`:

```python
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
        except ValueError:
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
```

`laya_harness/session_state.py`:

```python
"""Per-session state owned by the client (spec §4.6).

The model and effort start unknown: the desktop app gives hooks neither on a session's first
prompt. A PostModelSwitch stays authoritative until the transcript holds an assistant row
timestamped after the first prompt submitted after that switch.
"""

import hashlib
import json
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
    except (OSError, ValueError):
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
```

- [ ] **Step 6: Run the tests and confirm GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_source_session.py`

Expected: `49 passed`.

Run: `.venv/bin/python -m pytest -q`

Expected: `83 passed, 1 deselected`.

- [ ] **Step 7: Self-review and report — no commit** (golden rule 2)

Run: `git diff --check` (expected: no output). Report to the controller: files changed, the exact RED and GREEN commands with their output, and anything skipped and why. The controller snapshots the task boundary on `refs/laywip/stage0/task-3` and dispatches the reviewers.

---

### Task 4: Catalog selection, copy deck, Claude Code adapter

**Files:**
- Create: `laya_harness/catalog.py`
- Create: `laya_harness/copytext.py`
- Create: `laya_harness/adapter_claude_code.py`
- Create: `tests/test_adapter.py`
- Test: `tests/test_adapter.py`

**Spec:** §4.9 (rules, gates, numbers shown), §4.12 (copy deck), §4.13 (cheapest that fits)

**Interfaces:**
- Consumes: `resources.questions()`, `resources.catalog()`, `resources.fit()` (Task 2).
- Produces:
- `catalog`: `NEVER = ("fable", "mythos")`, `canonical(model_id) -> str | None`, `never(model) -> bool`,
  `eligible(model) -> bool`,
  `select(cls, catalog, fit) -> {"model", "display", "effort", "class"} | None`, `known(catalog) -> set`.
- `copytext`: `MAX_LEN = 120`, `model_line(tier, tier_p, display, effort) -> str`, `plan_line(noul) -> str`.
- `adapter_claude_code`: `RULES_VERSION = "claude_code_v0"`,
  `tier_and_class(probabilities) -> (tier, tier_p, cls)`,
  `decide(answers, *, first_human, plan_shown, permission_mode, prompt, display, catalog, fit, session)
  -> {"lines", "line_for", "suppress_reason", "suggestion", "mismatches"}`.

> Revised after review round 1: equal-price versions go to the newest, compared number by number (5.5 over 5, 4.10 over 4.8); an option qualifies only if its model supports its effort, and an unresolvable option falls through to the next; Fable and Mythos are refused by family, id or display name in any case; and 38 more tests pin the gate edges, the literal copy-deck rows, the suppress-reason precedence, the `/plan` cases and all three `mismatches` entries (spec §4.9, §4.13 as of 03bab0d). Review round 2 added tests only: cheapest beats newest, each option keeps its own effort, each `never()` field on its own, `/planning` and a rounded-up tier value. Mockup: the §4.12 copy deck. There is no capturable surface until Task 8, so the visual review is recorded **N/A** here; the unit tests compare the exact strings.

- [ ] **Step 1: Write the failing tests**

`tests/test_adapter.py`:

```python
import copy

import pytest

from laya_harness import adapter_claude_code as adapter
from laya_harness import catalog, copytext, resources

DISPLAY = resources.questions()["display"]
CATALOG = resources.catalog()
FIT = resources.fit()


def answers(quick=0.4, routine=0.3, multi=0.2, arch=0.1, plan=0.2, parallel=0.1, plan_confidence=None):
    plan_answer = {"type": "noul", "noul": plan}
    if plan_confidence is not None:
        plan_answer["confidence"] = plan_confidence
    return {
        "difficulty": {"type": "choice", "probabilities": {
            "quick": quick, "routine": routine, "multi_file": multi, "architecture": arch}},
        "plan_first": plan_answer,
        "parallel": {"type": "noul", "noul": parallel},
    }


def run(a, *, first_human=True, plan_shown=False, permission_mode="auto", prompt="fix the typo",
        cat=CATALOG, fit=FIT, session=None):
    return adapter.decide(a, first_human=first_human, plan_shown=plan_shown,
                          permission_mode=permission_mode, prompt=prompt, display=DISPLAY,
                          catalog=cat, fit=fit, session=session or {"model": None, "effort": None})


def allow(*ids):
    cat = copy.deepcopy(CATALOG)
    for m in cat["models"]:
        if m["id"] in ids:
            m["allowed"] = True
    return cat


# --- catalog selection (spec §4.13) ---------------------------------------------------

def test_default_fit_picks_cheapest_allowed():
    assert catalog.select("quick", CATALOG, FIT) == {
        "model": "claude-haiku-5-5", "display": "Haiku 5.5", "effort": "low", "class": "quick"}
    assert catalog.select("routine", CATALOG, FIT) == {
        "model": "claude-sonnet-5-5", "display": "Sonnet 5.5", "effort": "medium", "class": "routine"}
    assert catalog.select("multi_file", CATALOG, FIT) == {
        "model": "claude-opus-5-5", "display": "Opus 5.5", "effort": "high", "class": "multi_file"}
    assert catalog.select("architecture", CATALOG, FIT) == {
        "model": "claude-opus-5-5", "display": "Opus 5.5", "effort": "xhigh", "class": "architecture"}


@pytest.mark.parametrize("options", [
    [{"model": "claude-sonnet-5", "effort": "medium"}, {"model": "claude-sonnet-5-5", "effort": "medium"}],
    [{"model": "claude-sonnet-5-5", "effort": "medium"}, {"model": "claude-sonnet-5", "effort": "medium"}],
    [{"family": "sonnet", "effort": "medium"}, {"model": "claude-sonnet-5", "effort": "medium"}],
])
def test_price_ties_go_to_the_newest_version(options):
    # Sonnet 5 and Sonnet 5.5 cost the same; "5" must not beat "5.5"
    choice = catalog.select("routine", allow("claude-sonnet-5"), {"classes": {"routine": options}})
    assert choice["model"] == "claude-sonnet-5-5"


def test_versions_compare_number_by_number():
    cat = {"models": [
        {"id": "x-4-8", "display": "X 4.8", "family": "x", "version": "4.8", "price": {"input": 1.0},
         "effort_levels": ["low"], "in_picker": True, "allowed": True},
        {"id": "x-4-10", "display": "X 4.10", "family": "x", "version": "4.10", "price": {"input": 1.0},
         "effort_levels": ["low"], "in_picker": True, "allowed": True},
    ]}
    fit = {"classes": {"quick": [{"model": "x-4-8", "effort": "low"}, {"model": "x-4-10", "effort": "low"}]}}
    assert catalog.select("quick", cat, fit)["model"] == "x-4-10"
    assert catalog.select("quick", cat, {"classes": {"quick": [{"family": "x", "effort": "low"}]}})["model"] == "x-4-10"


def test_base_price_decides_even_when_tiered():
    # Haiku 5.5's above-100k input price (0.5) would lose to a 0.2 model; its base price (0.1) wins
    cat = copy.deepcopy(CATALOG)
    cat["models"].append({"id": "y-1", "display": "Y 1", "family": "y", "version": "1", "price": {"input": 0.2},
                          "effort_levels": ["low"], "in_picker": True, "allowed": True})
    fit = {"classes": {"quick": [{"model": "y-1", "effort": "low"}, {"family": "haiku", "effort": "low"}]}}
    assert catalog.select("quick", cat, fit)["model"] == "claude-haiku-5-5"


def test_unresolvable_option_falls_through_to_the_next():
    cat = copy.deepcopy(CATALOG)
    for m in cat["models"]:
        if m["family"] == "haiku":
            m["allowed"] = False
    assert catalog.select("quick", cat, FIT) == {
        "model": "claude-sonnet-5-5", "display": "Sonnet 5.5", "effort": "low", "class": "quick"}
    fit = {"classes": {"quick": [{"model": "claude-unknown-9", "effort": "low"}, {"family": "sonnet", "effort": "low"}]}}
    assert catalog.select("quick", CATALOG, fit)["model"] == "claude-sonnet-5-5"


@pytest.mark.parametrize("family, model_id, display", [
    ("fable", "claude-fable-5-1", "Fable 5.1"),
    ("Fable", "claude-fable-5-1", "Fable 5.1"),
    (None, "claude-fable-5", "Fable 5"),
    ("opus", "claude-fable-5", "Fable 5"),
    ("opus", "claude-x", "Claude Mythos 5.1"),
    ("fable", "claude-x", "X"),
    ("opus", "claude-fable-9", "X 9"),
])
def test_fable_and_mythos_never_suggested_in_any_form(family, model_id, display):
    model = {"id": model_id, "display": display, "version": "9", "price": {"input": 0.01},
             "effort_levels": ["high"], "in_picker": True, "allowed": True}
    if family is not None:
        model["family"] = family
    cat = {"models": [model]}
    for fit in ({"classes": {"architecture": [{"model": model_id, "effort": "high"}]}},
                {"classes": {"architecture": [{"family": family or "opus", "effort": "high"}]}}):
        assert catalog.select("architecture", cat, fit) is None


def test_fable_never_suggested_even_if_the_catalog_allows_it():
    cat = copy.deepcopy(CATALOG)
    for m in cat["models"]:
        m["allowed"] = True
    fit = {"classes": {"architecture": [{"family": "fable", "effort": "high"},
                                        {"model": "claude-fable-5-1", "effort": "high"}]}}
    assert catalog.select("architecture", cat, fit) is None


def test_disallowed_or_not_in_picker_is_skipped():
    fit = {"classes": {"quick": [{"model": "claude-haiku-4-5", "effort": None}]}}
    assert catalog.select("quick", CATALOG, fit) is None  # Haiku 4.5 is opt-in
    cat = allow("claude-haiku-4-5")
    for m in cat["models"]:
        if m["id"] == "claude-haiku-4-5":
            m["in_picker"] = False
    assert catalog.select("quick", cat, fit) is None


def test_older_version_only_when_named_and_nothing_cheaper():
    cat = allow("claude-opus-4-8")
    named = {"classes": {"multi_file": [{"model": "claude-opus-4-8", "effort": "high"}]}}
    assert catalog.select("multi_file", cat, named)["model"] == "claude-opus-4-8"
    both = {"classes": {"multi_file": [{"model": "claude-opus-4-8", "effort": "high"},
                                       {"family": "opus", "effort": "high"}]}}
    assert catalog.select("multi_file", cat, both)["model"] == "claude-opus-5-5"
    assert catalog.select("multi_file", cat, FIT)["model"] == "claude-opus-5-5"


def test_model_without_effort_levels_is_named_without_one():
    cat = allow("claude-haiku-4-5")
    lone = {"classes": {"quick": [{"model": "claude-haiku-4-5", "effort": None}]}}
    assert catalog.select("quick", cat, lone) == {
        "model": "claude-haiku-4-5", "display": "Haiku 4.5", "effort": None, "class": "quick"}


def test_option_with_an_unsupported_effort_does_not_qualify():
    cat = allow("claude-haiku-4-5", "claude-opus-4-6")
    assert catalog.select("quick", cat, {"classes": {"quick": [{"model": "claude-haiku-4-5", "effort": "low"}]}}) is None
    fit = {"classes": {"architecture": [{"model": "claude-opus-4-6", "effort": "xhigh"},
                                        {"family": "opus", "effort": "xhigh"}]}}
    assert catalog.select("architecture", cat, fit)["model"] == "claude-opus-5-5"


def test_cheapest_beats_newest():
    # Haiku 4.5 (older, opted in, $1) beats Sonnet 5.5 ($2) whichever the fit table lists first
    cat = allow("claude-haiku-4-5")
    for order in ([{"model": "claude-sonnet-5-5", "effort": "low"}, {"model": "claude-haiku-4-5"}],
                  [{"model": "claude-haiku-4-5"}, {"model": "claude-sonnet-5-5", "effort": "low"}]):
        assert catalog.select("quick", cat, {"classes": {"quick": order}}) == {
            "model": "claude-haiku-4-5", "display": "Haiku 4.5", "effort": None, "class": "quick"}


def test_effort_stays_with_its_own_option():
    fit = {"classes": {"quick": [{"family": "sonnet", "effort": "medium"}, {"family": "haiku", "effort": "low"}]}}
    assert catalog.select("quick", CATALOG, fit)["effort"] == "low"


def test_canonical_names():
    assert catalog.canonical("claude-opus-5-5[1m]") == "claude-opus-5-5"
    assert catalog.canonical("Claude-Sonnet-4-5-20250929") == "claude-sonnet-4-5"
    assert catalog.canonical(None) is None


def test_known_lists_every_catalog_id_canonically():
    known = catalog.known(CATALOG)
    assert known == {catalog.canonical(m["id"]) for m in CATALOG["models"]}
    assert len(known) == 12 and {"claude-fable-5-1", "claude-fable-5"} <= known
    assert catalog.canonical("claude-opus-5-5[1m]") in known


# --- tier gate and model line (spec §4.9) ----------------------------------------------

def test_tier_sum_is_rounded_and_picks_more_likely_class():
    assert adapter.tier_and_class({"quick": 0.1, "routine": 0.7, "multi_file": 0.1, "architecture": 0.1}) == (
        "light", 0.8, "routine")
    assert adapter.tier_and_class({"quick": 0.05, "routine": 0.05, "multi_file": 0.3, "architecture": 0.6}) == (
        "heavy", 0.9, "architecture")
    assert adapter.tier_and_class({"quick": 0.05, "routine": 0.05, "multi_file": 0.6, "architecture": 0.3}) == (
        "heavy", 0.9, "multi_file")


def test_ties_go_lighter():
    assert adapter.tier_and_class({"quick": 0.25, "routine": 0.25, "multi_file": 0.25, "architecture": 0.25}) == (
        "light", 0.5, "quick")
    assert adapter.tier_and_class({"quick": 0.05, "routine": 0.05, "multi_file": 0.45, "architecture": 0.45}) == (
        "heavy", 0.9, "multi_file")


def test_model_line_on_first_prompt_above_gate():
    d = run(answers(quick=0.5, routine=0.36))
    assert d["lines"] == ["laya · light task (p=0.86) → Haiku 5.5 at low effort fits this task"]
    assert d["suggestion"]["model"] == "claude-haiku-5-5"
    assert d["suppress_reason"]["model"] is None


def test_tier_exactly_at_the_gate_shows():
    d = run(answers(quick=0.1, routine=0.7, multi=0.1, arch=0.1))  # 0.1 + 0.7 carries float noise
    assert d["lines"] == ["laya · light task (p=0.80) → Sonnet 5.5 at medium effort fits this task"]


@pytest.mark.parametrize("quick, routine", [(0.4, 0.3999), (0.4501, 0.3498)])
def test_tier_just_under_the_gate_is_silent(quick, routine):
    d = run(answers(quick=quick, routine=routine, multi=0.1, arch=1 - quick - routine - 0.1))
    assert d["lines"] == [] and d["suppress_reason"]["model"] == "below_threshold" and d["suggestion"] is None


def test_multi_file_line():
    d = run(answers(quick=0.03, routine=0.06, multi=0.61, arch=0.3))
    assert d["lines"] == ["laya · heavy task (p=0.91) → Opus 5.5 at high effort fits this task"]


def test_heavy_line_matches_copy_deck():
    d = run(answers(quick=0.03, routine=0.06, multi=0.3, arch=0.61))
    assert d["lines"][0] == "laya · heavy task (p=0.91) → Opus 5.5 at xhigh effort fits this task"


def test_model_line_only_on_first_human_prompt():
    d = run(answers(quick=0.5, routine=0.36), first_human=False)
    assert d["lines"] == [] and d["suppress_reason"]["model"] == "not_first_prompt" and d["suggestion"] is None


def test_no_fit_is_silent():
    d = run(answers(quick=0.5, routine=0.36), fit={"classes": {}})
    assert d["lines"] == [] and d["suppress_reason"]["model"] == "no_fit" and d["suggestion"] is None


def test_display_formats_gated_value_to_two_decimals():
    d = run(answers(quick=0.4401, routine=0.3401, multi=0.11, arch=0.1098))  # 0.7802
    assert d["lines"] == [] and d["suppress_reason"]["model"] == "below_threshold"
    d = run(answers(quick=0.4501, routine=0.3501, multi=0.1, arch=0.0998))  # 0.8002
    assert d["lines"][0].startswith("laya · light task (p=0.80) →")
    d = run(answers(quick=0.4501, routine=0.3551, multi=0.1, arch=0.0948))  # 0.8052 rounds up
    assert d["lines"] == ["laya · light task (p=0.81) → Haiku 5.5 at low effort fits this task"]


# --- copy deck (spec §4.12): the literal spec text --------------------------------------

@pytest.mark.parametrize("line, spec_text", [
    (lambda: copytext.model_line("light", 0.86, "Haiku 5.5", "low"),
     "laya · light task (p=0.86) → Haiku 5.5 at low effort fits this task"),
    (lambda: copytext.model_line("light", 0.86, "Sonnet 5.5", "medium"),
     "laya · light task (p=0.86) → Sonnet 5.5 at medium effort fits this task"),
    (lambda: copytext.model_line("light", 0.86, "Haiku 4.5", None),
     "laya · light task (p=0.86) → Haiku 4.5 fits this task"),
    (lambda: copytext.model_line("heavy", 0.91, "Opus 5.5", "xhigh"),
     "laya · heavy task (p=0.91) → Opus 5.5 at xhigh effort fits this task"),
    (lambda: copytext.plan_line(0.88),
     "laya · reads like a multi-step change (p=0.88) → Plan mode (mode menu, then 4), or tell Claude to plan first"),
])
def test_copy_deck_rows(line, spec_text):
    assert line() == spec_text


def test_display_rounds_to_two_decimals():
    assert "(p=0.86)" in copytext.plan_line(0.8567)
    assert "(p=0.81)" in copytext.model_line("light", 0.8051, "Haiku 5.5", "low")
    assert "(p=0.78)" in copytext.model_line("light", 0.7802, "Haiku 5.5", "low")


def test_every_copy_string_fits_120_chars():
    for m in CATALOG["models"]:
        for effort in m["effort_levels"] + [None]:
            for tier in ("light", "heavy"):
                assert len(copytext.model_line(tier, 0.99, m["display"], effort)) <= 120
    assert len(copytext.plan_line(0.99)) <= 120


# --- MODE line (spec §4.9) -------------------------------------------------------------

def test_plan_line_shown_on_first_prompt():
    d = run(answers(plan=0.88))
    assert d["lines"][-1] == ("laya · reads like a multi-step change (p=0.88) → Plan mode (mode menu, "
                              "then 4), or tell Claude to plan first")


def test_plan_exactly_at_the_threshold_shows():
    d = run(answers(plan=0.85))
    assert d["lines"] == [copytext.plan_line(0.85)] and "(p=0.85)" in d["lines"][0]


def test_plan_below_threshold_even_if_it_would_display_as_threshold():
    d = run(answers(plan=0.8496))
    assert d["lines"] == [] and d["suppress_reason"]["plan"] == "below_threshold"


@pytest.mark.parametrize("noul, confidence, shown", [(0.30, 0.70, False), (0.90, 0.10, True), (0.30, 0.99, False)])
def test_plan_uses_noul_never_confidence(noul, confidence, shown):
    d = run(answers(plan=noul, plan_confidence=confidence))
    assert d["lines"] == ([copytext.plan_line(noul)] if shown else [])


@pytest.mark.parametrize("mode, prompt", [("plan", "x" * 300), ("auto", "/plan " + "x" * 300),
                                         ("auto", "   /plan " + "x" * 300), ("auto", "/plan"),
                                         ("auto", "/planning-notes " + "x" * 300)])
def test_no_plan_line_in_plan_mode(mode, prompt):
    d = run(answers(plan=0.95), permission_mode=mode, prompt=prompt)
    assert d["lines"] == [] and d["suppress_reason"]["plan"] == "plan_mode"


def test_plan_mentioned_mid_prompt_does_not_suppress():
    d = run(answers(plan=0.95), prompt="see the /plan command docs " + "x" * 200)
    assert d["lines"] == [copytext.plan_line(0.95)]


def test_plan_needs_first_prompt_or_200_chars():
    assert run(answers(plan=0.9), first_human=False, prompt="x" * 199)["suppress_reason"]["plan"] == "too_short"
    assert len(run(answers(plan=0.9), first_human=False, prompt="x" * 200)["lines"]) == 1


def test_plan_line_once_per_session():
    d = run(answers(plan=0.9), plan_shown=True)
    assert d["lines"] == [] and d["suppress_reason"]["plan"] == "already_shown"


@pytest.mark.parametrize("kwargs, model_reason, plan_reason", [
    (dict(a=answers(quick=0.4, routine=0.3, plan=0.5), first_human=False), "not_first_prompt", "below_threshold"),
    (dict(a=answers(plan=0.5), permission_mode="plan"), "below_threshold", "below_threshold"),
    (dict(a=answers(plan=0.9), permission_mode="plan", first_human=False, prompt="x", plan_shown=True),
     "not_first_prompt", "plan_mode"),
    (dict(a=answers(plan=0.9), first_human=False, prompt="x", plan_shown=True), "not_first_prompt", "too_short"),
])
def test_suppress_reason_precedence(kwargs, model_reason, plan_reason):
    kwargs = dict(kwargs)
    d = run(kwargs.pop("a"), **kwargs)
    assert d["suppress_reason"] == {"model": model_reason, "plan": plan_reason}


def test_both_lines_model_first():
    d = run(answers(quick=0.03, routine=0.06, multi=0.3, arch=0.61, plan=0.91))
    assert len(d["lines"]) == 2 and d["lines"][0].startswith("laya · heavy task")
    assert d["lines"][1].startswith("laya · reads like")
    assert d["line_for"] == {"model": d["lines"][0], "plan": d["lines"][1]}


def test_mismatches_record_profile_state_and_channel():
    d = run(answers(quick=0.03, routine=0.06, multi=0.3, arch=0.61, plan=0.91, parallel=0.42),
            permission_mode="acceptEdits", session={"model": "claude-opus-4-7", "effort": "high"})
    assert d["mismatches"] == [
        {"type": "MODEL+REASONING", "profile": {"tier": "heavy", "tier_p": 0.91, "class": "architecture"},
         "state": {"model": "claude-opus-4-7", "effort": "high"}, "channel_later": "user"},
        {"type": "MODE", "profile": {"plan_first": 0.91}, "state": {"permission_mode": "acceptEdits"},
         "channel_later": "harness"},
        {"type": "PARALLELISM_OPPORTUNITY", "profile": {"parallel": 0.42}, "state": {}, "channel_later": "harness"},
    ]


def test_parallel_is_logged_never_shown():
    d = run(answers(parallel=0.99))
    assert d["lines"] == []
    assert {"type": "PARALLELISM_OPPORTUNITY", "profile": {"parallel": 0.99}, "state": {},
            "channel_later": "harness"} in d["mismatches"]


def test_never_a_decision_key():
    for a in (answers(quick=0.5, routine=0.36, plan=0.9), answers(quick=0.03, routine=0.06, multi=0.3, arch=0.61)):
        d = run(a)
        assert set(d) == {"lines", "line_for", "suppress_reason", "suggestion", "mismatches"}
```

- [ ] **Step 2: Create the modules as stubs**, so the tests fail on behaviour rather than on an import error (golden rule 4)

`laya_harness/catalog.py` (stub — bodies raise `NotImplementedError`):

```python
"""Cheapest model and effort that the fit table accepts (spec §4.13, D12, D13)."""
import re
NEVER = ('fable', 'mythos')
_DATE = re.compile('-\\d{8}$')

def canonical(model_id):
    """Lower-case, without a trailing "[1m]" or "-YYYYMMDD"; None stays None."""
    raise NotImplementedError

def _version_key(version: str):
    raise NotImplementedError

def never(model: dict) -> bool:
    """True for any Fable or Mythos model, judged by family, id or display name, in any case."""
    raise NotImplementedError

def eligible(model: dict) -> bool:
    raise NotImplementedError

def _resolve(option: dict, models: list):
    raise NotImplementedError

def select(cls: str, catalog: dict, fit: dict):
    """Return {"model", "display", "effort", "class"} for the cheapest qualifying option, or None."""
    raise NotImplementedError

def known(catalog: dict) -> set:
    raise NotImplementedError
```

`laya_harness/copytext.py` (stub — bodies raise `NotImplementedError`):

```python
"""The exact strings of the copy deck (spec §4.12). Numbers are formatted to two decimals."""
MAX_LEN = 120

def model_line(tier: str, tier_p: float, display: str, effort) -> str:
    raise NotImplementedError

def plan_line(noul: float) -> str:
    raise NotImplementedError
```

`laya_harness/adapter_claude_code.py` (stub — bodies raise `NotImplementedError`):

```python
"""Claude Code adapter rules for stage 0 (spec §4.9). Deterministic: profile × harness state.

Gating uses laya-mlx's values as returned (four decimals); the tier sum is rounded to four
decimals. Laya's `confidence` field is never used.
"""
from . import catalog as catalog_mod
from . import copytext
RULES_VERSION = 'claude_code_v0'

def tier_and_class(probabilities: dict):
    raise NotImplementedError

def decide(answers: dict, *, first_human: bool, plan_shown: bool, permission_mode, prompt: str, display: dict, catalog: dict, fit: dict, session: dict) -> dict:
    """Return {"lines", "line_for", "suppress_reason", "suggestion", "mismatches"}.

    `lines` holds at most two strings: the model line first, then the plan line.
    `line_for` names them: {"model": line or None, "plan": line or None}.
    `suppress_reason` is per line: {"model": reason or None, "plan": reason or None}.
    """
    raise NotImplementedError
```

- [ ] **Step 3: Run the tests and confirm RED**

Run: `.venv/bin/python -m pytest -q tests/test_adapter.py`

Expected: `63 failed`; every failure is `NotImplementedError`. Record the output in the task report.

- [ ] **Step 4: Implement**, replacing the stubs with exactly this code

`laya_harness/catalog.py`:

```python
"""Cheapest model and effort that the fit table accepts (spec §4.13, D12, D13)."""

import re

NEVER = ("fable", "mythos")  # the user's rule: never Fable (Mythos is its sibling line)
_DATE = re.compile(r"-\d{8}$")


def canonical(model_id):
    """Lower-case, without a trailing "[1m]" or "-YYYYMMDD"; None stays None."""
    if not model_id:
        return None
    name = model_id.strip().lower()
    if name.endswith("[1m]"):
        name = name[: -len("[1m]")]
    return _DATE.sub("", name)


def _version_key(version: str):
    return tuple(int(part) for part in version.split("."))


def never(model: dict) -> bool:
    """True for any Fable or Mythos model, judged by family, id or display name, in any case."""
    text = " ".join(str(model.get(key) or "") for key in ("family", "id", "display")).lower()
    return any(name in text for name in NEVER)


def eligible(model: dict) -> bool:
    return not never(model) and bool(model.get("allowed")) and bool(model.get("in_picker"))


def _resolve(option: dict, models: list):
    if "model" in option:
        wanted = canonical(option["model"])
        for m in models:
            if canonical(m["id"]) == wanted and eligible(m):
                return m
        return None
    family = [m for m in models if m.get("family") == option.get("family") and eligible(m)]
    return max(family, key=lambda m: _version_key(m["version"]), default=None)


def select(cls: str, catalog: dict, fit: dict):
    """Return {"model", "display", "effort", "class"} for the cheapest qualifying option, or None."""
    models = catalog["models"]
    candidates = []
    for option in fit["classes"].get(cls, []):
        model = _resolve(option, models)
        if model is None:
            continue
        effort = option.get("effort")
        if effort is not None and effort not in model["effort_levels"]:
            continue
        candidates.append((model["price"]["input"], _version_key(model["version"]), model, effort))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[1], reverse=True)  # newest first (5.5 > 5, 4.10 > 4.8)...
    candidates.sort(key=lambda c: c[0])  # ...then cheapest; the sort is stable, so ties keep newest first
    _, _, model, effort = candidates[0]
    return {"model": model["id"], "display": model["display"], "effort": effort, "class": cls}


def known(catalog: dict) -> set:
    return {canonical(m["id"]) for m in catalog["models"]}
```

`laya_harness/copytext.py`:

```python
"""The exact strings of the copy deck (spec §4.12). Numbers are formatted to two decimals."""

MAX_LEN = 120


def model_line(tier: str, tier_p: float, display: str, effort) -> str:
    fits = f"{display} at {effort} effort fits this task" if effort else f"{display} fits this task"
    return f"laya · {tier} task (p={tier_p:.2f}) → {fits}"


def plan_line(noul: float) -> str:
    return (
        f"laya · reads like a multi-step change (p={noul:.2f}) → "
        "Plan mode (mode menu, then 4), or tell Claude to plan first"
    )
```

`laya_harness/adapter_claude_code.py`:

```python
"""Claude Code adapter rules for stage 0 (spec §4.9). Deterministic: profile × harness state.

Gating uses laya-mlx's values as returned (four decimals); the tier sum is rounded to four
decimals. Laya's `confidence` field is never used.
"""

from . import catalog as catalog_mod
from . import copytext

RULES_VERSION = "claude_code_v0"


def tier_and_class(probabilities: dict):
    light = round(probabilities["quick"] + probabilities["routine"], 4)
    heavy = round(probabilities["multi_file"] + probabilities["architecture"], 4)
    if light >= heavy:
        cls = "quick" if probabilities["quick"] >= probabilities["routine"] else "routine"
        return "light", light, cls
    cls = "multi_file" if probabilities["multi_file"] >= probabilities["architecture"] else "architecture"
    return "heavy", heavy, cls


def decide(answers: dict, *, first_human: bool, plan_shown: bool, permission_mode, prompt: str,
           display: dict, catalog: dict, fit: dict, session: dict) -> dict:
    """Return {"lines", "line_for", "suppress_reason", "suggestion", "mismatches"}.

    `lines` holds at most two strings: the model line first, then the plan line.
    `line_for` names them: {"model": line or None, "plan": line or None}.
    `suppress_reason` is per line: {"model": reason or None, "plan": reason or None}.
    """
    line_for, reasons, suggestion = {"model": None, "plan": None}, {"model": None, "plan": None}, None

    tier, tier_p, cls = tier_and_class(answers["difficulty"]["probabilities"])
    if not first_human:
        reasons["model"] = "not_first_prompt"
    elif tier_p < display["difficulty"]["min_tier_p"]:
        reasons["model"] = "below_threshold"
    else:
        suggestion = catalog_mod.select(cls, catalog, fit)
        if suggestion is None:
            reasons["model"] = "no_fit"
        else:
            line_for["model"] = copytext.model_line(tier, tier_p, suggestion["display"], suggestion["effort"])

    plan = answers["plan_first"]["noul"]
    plan_rules = display["plan_first"]
    if plan < plan_rules["show_threshold"]:
        reasons["plan"] = "below_threshold"
    elif permission_mode == "plan" or prompt.lstrip().startswith("/plan"):
        reasons["plan"] = "plan_mode"
    elif not (first_human or len(prompt) >= plan_rules["min_chars"]):
        reasons["plan"] = "too_short"
    elif plan_shown:
        reasons["plan"] = "already_shown"
    else:
        line_for["plan"] = copytext.plan_line(plan)

    mismatches = [
        {"type": "MODEL+REASONING", "profile": {"tier": tier, "tier_p": tier_p, "class": cls},
         "state": {"model": session.get("model"), "effort": session.get("effort")},
         "channel_later": "user"},
        {"type": "MODE", "profile": {"plan_first": plan},
         "state": {"permission_mode": permission_mode}, "channel_later": "harness"},
        {"type": "PARALLELISM_OPPORTUNITY", "profile": {"parallel": answers["parallel"]["noul"]},
         "state": {}, "channel_later": "harness"},
    ]
    lines = [line for line in (line_for["model"], line_for["plan"]) if line]
    return {"lines": lines, "line_for": line_for, "suppress_reason": reasons, "suggestion": suggestion,
            "mismatches": mismatches}
```

- [ ] **Step 5: Run the tests and confirm GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_adapter.py`

Expected: `63 passed`.

Run: `.venv/bin/python -m pytest -q`

Expected: `146 passed, 1 deselected`.

- [ ] **Step 6: Self-review and report — no commit** (golden rule 2)

Run: `git diff --check` (expected: no output). Report to the controller: files changed, the exact RED and GREEN commands with their output, and anything skipped and why. The controller snapshots the task boundary on `refs/laywip/stage0/task-4` and dispatches the reviewers.

---

### Task 5: Local service and predictors

**Files:**
- Create: `laya_harness/predictor.py`
- Create: `laya_harness/service.py`
- Create: `tests/procs.py`
- Create: `tests/test_service.py`
- Test: `tests/test_service.py`

**Spec:** §4.4 (startup order, requests, idle exit, not_ready), §4.5 (offline local load), check 6 settings

**Interfaces:**
- Consumes: `config.load()`, `config.port()`, `paths.*` (Task 1); `resources.*` (Task 2).
- Produces:
- `predictor.FakePredictor(cfg)` and `predictor.RealPredictor(cfg)`, each with `load() -> None`,
  `predict(prompt) -> {"answers", "usage"}` and `laya_mlx_version`; `RealPredictor.missing() -> list`;
  `predictor.make(cfg)`; `predictor.PROMPT_CHAR_CAP = 65536` (the real predictor passes at most that
  many characters). `RealPredictor.load()` refuses a config `revision` that is not the pinned one
  (`ValueError`, "run laya-harness setup"). Fake-mode config knobs: `fake_answers`,
  `fake_load_seconds`, `fake_predict_seconds`, `fake_load_error`, `fake_predict_error`,
  `fake_print_stdout`.
- `service.main() -> int`, run as `python -I -m laya_harness.service`; a bad `idle_seconds` raises
  before the bind (exit 1). HTTP on 127.0.0.1:
  `GET /v1/health` → `{"app": "laya-harness", "version", "pid", "state", "reason", "checkpoint",
  "question_set"}`; `POST /v1/profile {"prompt": str}` → 200 `{"answers", "usage", "checkpoint",
  "question_set", "versions": {"laya_harness", "laya_mlx"}}`, 503 `{"state", "reason"}` while
  loading or not ready, 500 `{"error": <exception class>}` when inference raises, 400 bad body,
  403 foreign Host or any Origin, 404, 415 non-JSON. Health and profile requests count as activity
  for the idle exit. Internals the tests use: `_State(cfg, port)`, `_Server` (a
  `ThreadingHTTPServer` that joins accepted requests on close), `_Handler` (5 s socket timeout),
  `_watch_idle(st, server, stopped, idle_seconds)`.
- `tests/procs.py`: `env_for(home)`, `start_service(home, stdout=DEVNULL, stderr=DEVNULL)`,
  `request(port, method, path, body=None, headers=None, timeout=2.0) -> (status, body)`,
  `wait_health(port, want=("ready",), timeout=10.0)`, `stop(proc)`.

> Revised after review round 1 (spec §4.4–§6 as of f0b29ef): the idle exit never fires while loading, counts health requests, closes the listener first and finishes accepted requests (5 s handler timeout); a predict failure is a 500; a bad `idle_seconds` exits before the bind; the real predictor refuses an unpinned revision and caps the prompt at 65,536 characters; and 26 more tests pin every field, the request checks on GET and POST, the loopback bind, stdlib-only imports, the MLX lock, stdout, the idle rules and the real predictor's load with a stand-in laya_mlx. Review round 2 (spec 5e3aa5b): a client that gives up is not logged, and tests pin the idle-clock reset at the end of loading, the check before the bind, the 500 path off stdout and the beginning kept by the cap. The concurrency test proves the bind is the single-instance lock on macOS: of four services started at once, three exit 0 within 1 s and the fake model loads once.

- [ ] **Step 1: Write the supporting files**

`tests/procs.py`:

```python
"""Helpers for process-level tests: start the real service module and talk to it."""

import http.client
import json
import os
import subprocess
import sys
import time


def env_for(home) -> dict:
    env = dict(os.environ)
    env["LAYA_HARNESS_HOME"] = str(home)
    env["LAYA_HARNESS_TEST"] = "1"
    env["HF_HUB_OFFLINE"] = "1"
    return env


def start_service(home, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-I", "-m", "laya_harness.service"], env=env_for(home),
                            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)


def request(port, method, path, body=None, headers=None, timeout=2.0):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    payload = None if body is None else json.dumps(body).encode()
    hdrs = {"Content-Type": "application/json"} if body is not None else {}
    hdrs.update(headers or {})
    conn.request(method, path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    try:
        return resp.status, json.loads(data)
    except ValueError:
        return resp.status, data


def wait_health(port, want=("ready",), timeout=10.0) -> dict:
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            status, body = request(port, "GET", "/v1/health", timeout=0.5)
            last = body
            if status == 200 and body.get("state") in want:
                return body
        except OSError:
            pass
        time.sleep(0.05)
    raise AssertionError(f"service never reached {want}; last health: {last}")


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
```

- [ ] **Step 2: Write the failing tests**

`tests/test_service.py`:

```python
import http.client
import importlib.abc
import importlib.util
import json
import math
import os
import socket
import subprocess
import sys
import threading
import time

import pytest

from conftest import FAKE_ANSWERS, write_config
from laya_harness import config, predictor, resources
from laya_harness import service as service_module
from procs import env_for, request, start_service, stop, wait_health


@pytest.fixture
def service(configured, home):
    procs = []

    def launch(**changes):
        if changes:
            write_config(home, **changes)
        proc = start_service(home)
        procs.append(proc)
        return proc

    yield launch
    for proc in procs:
        stop(proc)


# --- endpoints and request checks ------------------------------------------------------

def test_health_and_profile_in_fake_mode(service, configured):
    service()
    health = wait_health(configured["port"])
    assert health["app"] == "laya-harness" and health["state"] == "ready"
    assert health["question_set"] == {"id": "profile_v0", "sha256": resources.questions_sha256()}
    status, body = request(configured["port"], "POST", "/v1/profile", {"prompt": "fix the typo"})
    assert status == 200
    assert body["answers"] == FAKE_ANSWERS
    assert body["checkpoint"]["revision"] == "047678560251f28113ee8f5df4be82102c7bf336"
    assert body["versions"]["laya_harness"] == "0.0.0"


def test_health_and_profile_carry_every_field(service, configured):
    proc = service()
    health = wait_health(configured["port"])
    ck = resources.checkpoint()
    assert health["pid"] == proc.pid  # `laya-harness stop` signals this pid
    assert health["version"] == "0.0.0" and health["reason"] is None
    assert health["checkpoint"] == {"repo": ck["repo"], "revision": ck["revision"], "model_mode": "fake"}
    status, body = request(configured["port"], "POST", "/v1/profile", {"prompt": "x"})
    assert status == 200
    assert body["usage"] == {"truncated": False, "state_tokens": 0, "state_tokens_dropped": 0}
    assert body["versions"] == {"laya_harness": "0.0.0", "laya_mlx": None}
    assert body["checkpoint"] == health["checkpoint"] and body["question_set"] == health["question_set"]


def test_profile_reports_the_predictors_laya_mlx_version():
    class Stub:
        laya_mlx_version = "9.9.9"

        def predict(self, prompt):
            return {"answers": {}, "usage": {"truncated": True}}

    server = service_module._Server(("127.0.0.1", 0), service_module._Handler)
    st = service_module._State({"model_mode": "fake"}, server.server_address[1])
    st.predictor, st.state = Stub(), "ready"
    server.st = st
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        status, body = request(st.port, "POST", "/v1/profile", {"prompt": "x"})
        assert status == 200
        assert body["versions"]["laya_mlx"] == "9.9.9" and body["usage"] == {"truncated": True}
    finally:
        server.shutdown()
        server.server_close()


def test_rejects_foreign_host_origin_and_content_type(service, configured):
    service()
    port = configured["port"]
    wait_health(port)
    assert request(port, "GET", "/v1/health", headers={"Host": f"evil.example:{port}"})[0] == 403
    assert request(port, "GET", "/v1/health", headers={"Origin": "http://evil.example"})[0] == 403
    assert request(port, "GET", "/v1/health", headers={"Host": f"localhost:{port}"})[0] == 200
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    conn.request("POST", "/v1/profile", body=b'{"prompt": "x"}', headers={"Content-Type": "text/plain"})
    assert conn.getresponse().status == 415
    assert request(port, "GET", "/nope")[0] == 404
    assert request(port, "POST", "/v1/profile", {"wrong": 1})[0] == 400


def test_profile_post_rejects_foreign_host_and_any_origin(service, configured):
    service()
    port = configured["port"]
    wait_health(port)
    prompt = {"prompt": "x"}
    assert request(port, "POST", "/v1/profile", prompt, headers={"Host": f"evil.example:{port}"})[0] == 403
    for origin in ("http://evil.example", f"http://127.0.0.1:{port}"):  # any Origin, even a local one
        assert request(port, "POST", "/v1/profile", prompt, headers={"Origin": origin})[0] == 403


def test_bad_bodies_and_paths(service, configured):
    service()
    port = configured["port"]
    wait_health(port)
    assert request(port, "POST", "/v1/profile", {"prompt": 5})[0] == 400
    assert request(port, "POST", "/v1/profile", ["x"])[0] == 400
    assert request(port, "POST", "/v1/elsewhere", {"prompt": "x"})[0] == 404
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    conn.request("POST", "/v1/profile", body=b"{not json", headers={"Content-Type": "application/json"})
    assert conn.getresponse().status == 400
    conn.close()


def test_binds_loopback_only(monkeypatch, configured):
    import http.server

    seen = []

    def refuse(self):
        seen.append(self.server_address)
        raise OSError(98 if sys.platform.startswith("linux") else 48, "taken")

    monkeypatch.setattr(http.server.HTTPServer, "server_bind", refuse)
    assert service_module.main() == 0
    assert seen == [("127.0.0.1", configured["port"])]


# --- loading, single instance, imports ------------------------------------------------

def test_profile_answers_503_while_loading(service, configured):
    service(fake_load_seconds=3)
    health = wait_health(configured["port"], want=("loading",))
    assert health["state"] == "loading"
    assert request(configured["port"], "POST", "/v1/profile", {"prompt": "x"}) == (503, {"state": "loading", "reason": None})


def test_failed_load_is_not_ready_and_stays_bound(service, configured):
    proc = service(fake_load_error="corrupt model.safetensors")
    health = wait_health(configured["port"], want=("not_ready",))
    assert health["reason"] == "RuntimeError: corrupt model.safetensors"
    time.sleep(1.0)
    assert proc.poll() is None
    assert request(configured["port"], "POST", "/v1/profile", {"prompt": "x"})[0] == 503


def test_failed_load_loads_once_then_idles_out(service, configured, home):
    proc = service(fake_load_error="corrupt model.safetensors", idle_seconds=2)
    port = configured["port"]
    pid = wait_health(port, want=("not_ready",))["pid"]
    for _ in range(3):  # spec §6: several prompts in a row, at most one load
        assert request(port, "POST", "/v1/profile", {"prompt": "x"}) == (
            503, {"state": "not_ready", "reason": "RuntimeError: corrupt model.safetensors"})
    assert wait_health(port, want=("not_ready",))["pid"] == pid
    proc.wait(timeout=2 + 3)  # §4.4 step 4: stays bound only until its idle timeout
    assert proc.returncode == 0
    # counted over the service's whole life, so a slow retry loop is caught too
    assert (home / "fake_loads.txt").read_text().split() == [str(pid)]


def test_concurrent_starts_load_once(configured, home):
    write_config(home, fake_load_seconds=3)
    procs = [start_service(home) for _ in range(4)]
    try:
        time.sleep(1.0)
        exited = [p for p in procs if p.poll() is not None]
        assert len(exited) == 3 and all(p.returncode == 0 for p in exited)
        wait_health(configured["port"])
        assert len((home / "fake_loads.txt").read_text().split()) == 1
    finally:
        for p in procs:
            stop(p)


IMPORT_PROBE = (  # runs the service as `-m` does (the __main__ guard included), then lists new imports
    "import runpy, sys\n"
    "before = set(sys.modules)\n"
    "try:\n"
    "    runpy.run_module('laya_harness.service', run_name='__main__')\n"
    "    rc = 0\n"
    "except SystemExit as exc:\n"
    "    rc = exc.code\n"
    "new = {m.partition('.')[0] for m in set(sys.modules) - before}\n"
    "sys.stderr.write(' '.join(sorted(new - set(sys.stdlib_module_names) - {'laya_harness'})) or 'stdlib only')\n"
    "sys.exit(rc)\n")


def test_service_imports_only_stdlib_when_port_taken_or_fake(configured, home):
    """§4.4 step 1 (standard library only before the bind) and fake mode (never laya_mlx or mlx)."""
    argv = [sys.executable, "-I", "-c", IMPORT_PROBE]
    with socket.socket() as holder:  # port taken: exit 0 at the bind
        holder.bind(("127.0.0.1", configured["port"]))
        holder.listen()
        taken = subprocess.run(argv, env=env_for(home), stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
    assert (taken.returncode, taken.stdout, taken.stderr) == (0, b"", b"stdlib only")
    assert not (home / "fake_loads.txt").exists()
    write_config(home, idle_seconds=1)  # port free: a fake load, then an idle exit
    served = subprocess.run(argv, env=env_for(home), stdin=subprocess.DEVNULL, capture_output=True, timeout=15)
    assert (served.returncode, served.stdout, served.stderr) == (0, b"", b"stdlib only")
    assert len((home / "fake_loads.txt").read_text().split()) == 1


# --- inference -------------------------------------------------------------------------

def test_inference_is_serialised_and_health_answers_during_it(service, configured):
    service(fake_predict_seconds=1.0)
    port = configured["port"]
    wait_health(port)
    statuses = []

    def call():
        statuses.append(request(port, "POST", "/v1/profile", {"prompt": "x"}, timeout=5)[0])

    threads = [threading.Thread(target=call, daemon=True) for _ in range(2)]
    started = time.monotonic()
    for t in threads:
        t.start()
    time.sleep(0.3)
    status, body = request(port, "GET", "/v1/health", timeout=0.5)  # answered while inference runs
    assert (status, body["state"]) == (200, "ready")
    for t in threads:
        t.join(timeout=5)
    assert statuses == [200, 200]
    assert time.monotonic() - started >= 1.9  # one MLX lock: the two predictions ran one after the other


@pytest.mark.parametrize("changes, state, status", [
    ({}, "ready", 200),
    ({"fake_load_error": "corrupt model.safetensors"}, "not_ready", 503),
    ({"fake_predict_error": "metal::malloc failed"}, "ready", 500),
])
def test_service_never_writes_to_stdout(configured, home, changes, state, status):
    write_config(home, idle_seconds=1, **changes)
    proc = start_service(home, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        wait_health(configured["port"], want=(state,))
        assert request(configured["port"], "POST", "/v1/profile", {"prompt": "x"})[0] == status
        out, err = proc.communicate(timeout=10)  # idle exit, so the interpreter flushes its buffers
    finally:
        stop(proc)
    assert proc.returncode == 0 and out == b""
    if state == "not_ready":
        assert b"load failed: RuntimeError: corrupt model.safetensors" in err
    if status == 500:  # §4.4: one line in service.log
        assert err.count(b"predict failed:") == 1 and b"RuntimeError: metal::malloc failed" in err


def test_a_client_that_gives_up_is_not_logged(capsys):
    server = service_module._Server(("127.0.0.1", 0), service_module._Handler)
    try:
        for exc in (BrokenPipeError(32, "Broken pipe"), ConnectionResetError(54, "Connection reset")):
            try:
                raise exc
            except OSError:
                server.handle_error(None, ("127.0.0.1", 1))
        assert capsys.readouterr().err == ""
        try:
            raise ValueError("a real problem")
        except ValueError:
            server.handle_error(None, ("127.0.0.1", 1))
        assert "ValueError: a real problem" in capsys.readouterr().err  # still logged with a traceback
    finally:
        server.server_close()


def test_predict_failure_is_a_500_and_the_service_stays_ready(service, configured):
    proc = service(fake_predict_error="metal::malloc failed")
    wait_health(configured["port"])
    assert request(configured["port"], "POST", "/v1/profile", {"prompt": "x"}) == (500, {"error": "RuntimeError"})
    assert proc.poll() is None
    assert wait_health(configured["port"])["state"] == "ready"


# --- idle exit -------------------------------------------------------------------------

def test_idle_exit_never_mid_request(service, configured):
    proc = service(idle_seconds=1, fake_predict_seconds=2.5)
    wait_health(configured["port"])
    result = {}

    def call():
        result["status"] = request(configured["port"], "POST", "/v1/profile", {"prompt": "x"}, timeout=5)[0]

    t = threading.Thread(target=call)
    t.start()
    time.sleep(1.5)
    assert proc.poll() is None  # idle time passed, but a request is in flight
    t.join()
    assert result["status"] == 200
    proc.wait(timeout=5)
    assert proc.returncode == 0


def test_idle_clock_waits_for_the_load(service, configured):
    proc = service(idle_seconds=1, fake_load_seconds=3)
    port = configured["port"]
    wait_health(port, want=("loading",))
    time.sleep(1.5)  # idle_seconds have passed, but the model is still loading
    assert request(port, "GET", "/v1/health", timeout=0.5)[1]["state"] in ("loading", "ready")
    wait_health(port)
    time.sleep(0.5)  # the idle clock restarted when the load ended
    assert request(port, "GET", "/v1/health", timeout=0.5)[1]["state"] == "ready"
    proc.wait(timeout=5)
    assert proc.returncode == 0  # and the service still exits once idle


@pytest.mark.parametrize("changes", [{}, {"fake_load_error": "corrupt model.safetensors"}])
def test_idle_clock_restarts_when_the_load_ends(service, configured, changes):
    """§4.4: idle time counts from the end of loading. No request is made while the 2.5 s load
    runs, so only the reset at the end of `_load` keeps the service up past that point."""
    proc = service(idle_seconds=2, fake_load_seconds=2.5, **changes)
    wait_health(configured["port"], want=("loading",))  # the only request, near the load's start
    time.sleep(2.5 + 1.0)  # the load has ended; an idle clock started at the poll would have fired
    assert proc.poll() is None
    proc.wait(timeout=5)
    assert proc.returncode == 0


def test_idle_timer_restarts_after_each_request(service, configured):
    proc = service(idle_seconds=1.5)
    port = configured["port"]
    wait_health(port)
    for _ in range(4):  # 2.8 s in all: well past one idle period counted from start-up
        time.sleep(0.7)
        assert request(port, "POST", "/v1/profile", {"prompt": "x"})[0] == 200
    assert proc.poll() is None
    proc.wait(timeout=1.5 + 2)
    assert proc.returncode == 0


def test_health_requests_extend_the_idle_deadline(service, configured):
    proc = service(idle_seconds=2)
    port = configured["port"]
    wait_health(port)
    for _ in range(4):  # 3.2 s of health checks, more than one idle period from start-up
        time.sleep(0.8)
        assert request(port, "GET", "/v1/health")[0] == 200
    assert proc.poll() is None
    proc.wait(timeout=5)
    assert proc.returncode == 0


def test_idle_exit_refuses_connections_before_it_stops(configured, home):
    """§4.3/§4.4: once the idle exit starts, a connect is refused (the client respawns), never
    accepted into the backlog and then reset when the listener closes."""
    cfg = config.load()
    port = config.port(cfg)
    server = service_module._Server(("127.0.0.1", port), service_module._Handler)
    st = service_module._State(cfg, port)
    st.state = "ready"
    seen = []

    def shutdown():  # stands in for server.shutdown(): probe the port at the moment the exit starts
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            seen.append("accepted")
        except ConnectionRefusedError:
            seen.append("refused")

    server.shutdown = shutdown
    try:
        watcher = threading.Thread(target=service_module._watch_idle,
                                   args=(st, server, threading.Event(), 0.1), daemon=True)
        watcher.start()
        watcher.join(timeout=5)
    finally:
        server.server_close()
    assert seen == ["refused"]


def test_idle_exit_finishes_a_request_already_accepted(service, configured):
    proc = service(idle_seconds=1)
    port = configured["port"]
    wait_health(port)
    body = b'{"prompt": "x"}'
    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall(f"POST /v1/profile HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\n"
                  f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n".encode())
        time.sleep(2.0)  # the idle exit starts while this request is still being read
        assert proc.poll() is None
        s.sendall(body)
        assert s.recv(65536).startswith(b"HTTP/1.0 200")
    proc.wait(timeout=5)
    assert proc.returncode == 0


def test_idle_exit_is_not_held_open_by_a_silent_client(service, configured):
    proc = service(idle_seconds=1)
    wait_health(configured["port"])
    with socket.create_connection(("127.0.0.1", configured["port"]), timeout=10):
        proc.wait(timeout=9)  # idle 1 s + the 5 s handler timeout + margin
    assert proc.returncode == 0


@pytest.mark.parametrize("value", ["15m", None, [], math.nan, 0, -5])
def test_bad_idle_seconds_exits_before_loading(configured, home, value):
    write_config(home, idle_seconds=value)
    proc = start_service(home, stderr=subprocess.PIPE)
    try:
        _, err = proc.communicate(timeout=5)
    finally:
        stop(proc)
    assert proc.returncode == 1 and b"idle_seconds must be a positive number" in err
    assert not (home / "fake_loads.txt").exists()


def test_bad_idle_seconds_is_refused_before_the_bind(configured, home):
    """§4.4 step 1: with the port taken, a service that checked after binding would exit 0."""
    write_config(home, idle_seconds=0)
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", configured["port"]))
        holder.listen()
        proc = start_service(home, stderr=subprocess.PIPE)
        try:
            _, err = proc.communicate(timeout=5)
        finally:
            stop(proc)
    assert proc.returncode == 1 and b"idle_seconds must be a positive number" in err


# --- the real predictor, without weights -------------------------------------------------

def test_real_predictor_rejects_missing_dir_without_download(monkeypatch, tmp_path):
    import laya_mlx.agent as agent_module

    def no_downloads(*args, **kwargs):
        raise AssertionError("snapshot_download must never be called")

    monkeypatch.setattr(agent_module, "snapshot_download", no_downloads)
    with pytest.raises(FileNotFoundError, match="missing model.safetensors"):
        predictor.RealPredictor({"model_dir": str(tmp_path / "absent")}).load()
    with pytest.raises(FileNotFoundError, match="absolute"):
        predictor.RealPredictor({"model_dir": "relative/dir"}).load()


def test_real_predictor_refuses_a_revision_that_is_not_pinned(tmp_path):
    pinned = resources.checkpoint()["revision"]
    with pytest.raises(ValueError, match=f"names revision 000000000000, not the pinned {pinned[:12]}: "
                                         "run laya-harness setup"):
        predictor.RealPredictor({"model_dir": str(tmp_path), "revision": "0" * 40}).load()
    with pytest.raises(FileNotFoundError, match="missing model.safetensors"):  # the pinned one goes on
        predictor.RealPredictor({"model_dir": str(tmp_path / "absent"), "revision": pinned}).load()


def test_real_predictor_loads_offline_with_check6_settings(monkeypatch, tmp_path, capsys):
    """§4.4 step 3 without weights: a stand-in laya_mlx records the offline flag at import and at
    load, the load arguments, max_len at every warm-up, the temperatures and the version."""
    ck = resources.checkpoint()
    model_dir = tmp_path / "model"
    for name in ck["required"]:
        (model_dir / name).parent.mkdir(parents=True, exist_ok=True)
        (model_dir / name).write_text("{}")
    seen = {}

    class Agent:
        temperature = (1.25, 1.5)
        temperature_by_options = {"4": 1.25}

        def __init__(self):
            self.cfg = {"max_len": 8192}
            self.predicted = []

        def predict(self, prompt, questions):
            self.predicted.append((prompt, self.cfg["max_len"], questions))
            return {"answers": {}, "usage": {"truncated": False}}

    def load(path, **kwargs):
        seen.update(path=path, kwargs=kwargs, offline_at_load=os.environ.get("HF_HUB_OFFLINE"), agent=Agent())
        return seen["agent"]

    class FakeLayaMlx(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        def find_spec(self, name, path, target=None):
            return importlib.util.spec_from_loader(name, self) if name == "laya_mlx" else None

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            seen["offline_at_import"] = os.environ.get("HF_HUB_OFFLINE")
            module.__version__ = "9.9.9"
            module.load = load

    monkeypatch.setitem(sys.modules, "laya_mlx", None)
    monkeypatch.delitem(sys.modules, "laya_mlx")  # teardown puts back the real module, if any
    monkeypatch.setattr(sys, "meta_path", [FakeLayaMlx(), *sys.meta_path])
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)

    assert isinstance(predictor.make({"model_mode": "real", "model_dir": str(model_dir)}), predictor.RealPredictor)
    p = predictor.RealPredictor({"model_dir": str(model_dir), "revision": ck["revision"]})
    p.load()

    assert seen["offline_at_import"] == "1" and seen["offline_at_load"] == "1"
    assert seen["path"] == str(model_dir)
    assert seen["kwargs"] == {"dtype": "float16", "batch_size": 1, "pad_to_multiple": 128}
    questions = resources.questions()["questions"]
    warmed = [(0 if pr == "warm-up" else len(pr.split()), max_len) for pr, max_len, _ in seen["agent"].predicted]
    assert warmed == [(w, 512) for w in ck["warmup_words"]]
    assert all(q == questions for *_, q in seen["agent"].predicted)
    assert p.laya_mlx_version == "9.9.9"
    assert p.predict("fix the typo") == {"answers": {}, "usage": {"truncated": False}}
    assert seen["agent"].predicted[-1] == ("fix the typo", 512, questions)
    out, err = capsys.readouterr()
    assert out == ""
    assert json.loads(err.strip().splitlines()[-1]) == {"temperature": [1.25, 1.5], "temperature_by_options": {"4": 1.25}}


def test_real_predictor_caps_the_prompt_before_tokenizing():
    seen = []

    class Agent:
        def predict(self, prompt, questions):
            seen.append(prompt)
            return {"answers": {}, "usage": {}}

    p = predictor.RealPredictor({"model_dir": "/unused"})
    p.agent = Agent()
    prompt = "head " + "x" * 5_000_000 + " tail"
    p.predict(prompt)
    assert predictor.PROMPT_CHAR_CAP == 65536
    assert seen == [prompt[:65536]] and seen[0].startswith("head ")  # the beginning is kept, as laya-mlx's own truncation does
```

- [ ] **Step 3: Create the modules as stubs**, so the tests fail on behaviour rather than on an import error (golden rule 4)

`laya_harness/predictor.py` (stub — bodies raise `NotImplementedError`):

```python
"""What answers the three questions (spec §4.4, §4.5).

`FakePredictor` never imports laya_mlx; tests and acceptance step 1 use it. `RealPredictor`
loads the pinned checkpoint from an absolute local directory, offline, with the check-6
settings, and warms every padded length before it is ready.
"""
import copy
import json
import os
import sys
import time
from pathlib import Path
from . import paths, resources
DEFAULT_FAKE_USAGE = {'truncated': False, 'state_tokens': 0, 'state_tokens_dropped': 0}
PROMPT_CHAR_CAP = 65536

class FakePredictor:
    laya_mlx_version = None

    def __init__(self, cfg: dict):
        raise NotImplementedError

    def load(self) -> None:
        raise NotImplementedError

    def predict(self, prompt: str) -> dict:
        raise NotImplementedError

class RealPredictor:

    def __init__(self, cfg: dict):
        raise NotImplementedError

    def missing(self) -> list:
        raise NotImplementedError

    def load(self) -> None:
        raise NotImplementedError

    def predict(self, prompt: str) -> dict:
        raise NotImplementedError

def make(cfg: dict):
    raise NotImplementedError
```

`laya_harness/service.py` (stub — bodies raise `NotImplementedError`):

```python
"""The local laya service (spec §4.4). Run as `python -I -m laya_harness.service`.

Startup order: check `idle_seconds`, then bind 127.0.0.1:<port> using the standard library only
(the bind is the single-instance lock), serve /v1/health from a thread, then load the predictor.
A failed load leaves the service bound and `not_ready` until its idle timeout. It never writes
to stdout.
"""
import errno
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from . import __version__, config, paths, resources

class _State:

    def __init__(self, cfg: dict, port: int):
        raise NotImplementedError

    def health(self) -> dict:
        raise NotImplementedError

    def touch(self) -> None:
        raise NotImplementedError

class _Server(ThreadingHTTPServer):
    daemon_threads = False

    def handle_error(self, request, client_address):
        raise NotImplementedError

class _Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'
    timeout = 5

    def log_message(self, *args):
        raise NotImplementedError

    def _send(self, code: int, body: dict) -> None:
        raise NotImplementedError

    def _forbidden(self) -> bool:
        raise NotImplementedError

    def do_GET(self):
        raise NotImplementedError

    def do_POST(self):
        raise NotImplementedError

def _watch_idle(st: _State, server, stopped: threading.Event, idle_seconds: float) -> None:
    raise NotImplementedError

def _load(st: _State) -> None:
    raise NotImplementedError

def _idle_seconds(cfg: dict) -> float:
    """`idle_seconds` as a positive number. Anything else, NaN included, is refused before the
    bind: a watcher that cannot count would keep the model resident for good."""
    raise NotImplementedError

def main() -> int:
    raise NotImplementedError
if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 4: Run the tests and confirm RED**

Run: `.venv/bin/python -m pytest -q tests/test_service.py`

Expected: `38 failed` (takes about 3 minutes: most tests wait for a service that never answers); every failure is `NotImplementedError`, an assertion that the service never came up, or an assertion that follows from it (`assert 4 == 3` in `test_concurrent_starts_load_once`, where all four stub processes exit; a `NotImplementedError` traceback where the import probe and the bad-`idle_seconds` tests expect their own output). Record the output in the task report.

- [ ] **Step 5: Implement**, replacing the stubs with exactly this code

`laya_harness/predictor.py`:

```python
"""What answers the three questions (spec §4.4, §4.5).

`FakePredictor` never imports laya_mlx; tests and acceptance step 1 use it. `RealPredictor`
loads the pinned checkpoint from an absolute local directory, offline, with the check-6
settings, and warms every padded length before it is ready.
"""

import copy
import json
import os
import sys
import time
from pathlib import Path

from . import paths, resources

DEFAULT_FAKE_USAGE = {"truncated": False, "state_tokens": 0, "state_tokens_dropped": 0}
PROMPT_CHAR_CAP = 65536  # far more than 512 tokens; tokenizing a huge paste would hold the GIL for seconds


class FakePredictor:
    laya_mlx_version = None

    def __init__(self, cfg: dict):
        self.answers = cfg.get("fake_answers") or {}
        self.load_seconds = float(cfg.get("fake_load_seconds", 0))
        self.predict_seconds = float(cfg.get("fake_predict_seconds", 0))
        self.load_error = cfg.get("fake_load_error")
        self.predict_error = cfg.get("fake_predict_error")
        self.print_stdout = bool(cfg.get("fake_print_stdout"))

    def load(self) -> None:
        if self.print_stdout:  # proves the spawn contract keeps this away from the hook
            print("fake service noise on stdout", flush=True)
            print("fake service noise on stderr", file=sys.stderr, flush=True)
        paths.append_private(paths.home() / "fake_loads.txt", str(os.getpid()))
        time.sleep(self.load_seconds)
        if self.load_error:
            raise RuntimeError(self.load_error)

    def predict(self, prompt: str) -> dict:
        time.sleep(self.predict_seconds)
        if self.predict_error:
            raise RuntimeError(self.predict_error)
        return {"answers": copy.deepcopy(self.answers), "usage": dict(DEFAULT_FAKE_USAGE)}


class RealPredictor:
    def __init__(self, cfg: dict):
        self.checkpoint = resources.checkpoint()
        self.questions = resources.questions()["questions"]
        self.model_dir = cfg.get("model_dir")
        self.revision = cfg.get("revision")
        self.agent = None
        self.laya_mlx_version = None

    def missing(self) -> list:
        root = Path(self.model_dir)
        return [name for name in self.checkpoint["required"] if not (root / name).is_file()]

    def load(self) -> None:
        if not self.model_dir or not os.path.isabs(self.model_dir):
            raise FileNotFoundError("model_dir must be an absolute local directory")
        pinned = self.checkpoint["revision"]
        if self.revision is not None and self.revision != pinned:
            raise ValueError(f"config.json names revision {str(self.revision)[:12]}, not the pinned "
                             f"{pinned[:12]}: run laya-harness setup")
        missing = self.missing()
        if missing:
            raise FileNotFoundError("missing " + ", ".join(missing))
        os.environ["HF_HUB_OFFLINE"] = "1"
        import laya_mlx

        s = self.checkpoint["settings"]
        self.agent = laya_mlx.load(self.model_dir, dtype=s["dtype"], batch_size=s["batch_size"],
                                   pad_to_multiple=s["pad_to_multiple"])
        self.agent.cfg["max_len"] = s["max_len"]
        print(json.dumps({"temperature": list(self.agent.temperature),
                          "temperature_by_options": dict(self.agent.temperature_by_options)}),
              file=sys.stderr, flush=True)
        for words in self.checkpoint["warmup_words"]:
            self.agent.predict(("word " * words) or "warm-up", self.questions)
        self.laya_mlx_version = laya_mlx.__version__

    def predict(self, prompt: str) -> dict:
        return self.agent.predict(prompt[:PROMPT_CHAR_CAP], self.questions)


def make(cfg: dict):
    return FakePredictor(cfg) if cfg.get("model_mode") == "fake" else RealPredictor(cfg)
```

`laya_harness/service.py`:

```python
"""The local laya service (spec §4.4). Run as `python -I -m laya_harness.service`.

Startup order: check `idle_seconds`, then bind 127.0.0.1:<port> using the standard library only
(the bind is the single-instance lock), serve /v1/health from a thread, then load the predictor.
A failed load leaves the service bound and `not_ready` until its idle timeout. It never writes
to stdout.
"""

import errno
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__, config, paths, resources


class _State:
    def __init__(self, cfg: dict, port: int):
        self.cfg = cfg
        self.port = port
        self.lock = threading.Lock()  # guards the state and counters below
        self.mlx = threading.Lock()  # all inference runs under this lock
        self.state = "loading"
        self.reason = None
        self.inflight = 0
        self.last_end = time.monotonic()
        self.predictor = None
        ck = resources.checkpoint()
        self.checkpoint = {"repo": ck["repo"], "revision": ck["revision"], "model_mode": cfg["model_mode"]}
        self.question_set = {"id": resources.questions()["id"], "sha256": resources.questions_sha256()}

    def health(self) -> dict:
        return {"app": "laya-harness", "version": __version__, "pid": os.getpid(), "state": self.state,
                "reason": self.reason, "checkpoint": self.checkpoint, "question_set": self.question_set}

    def touch(self) -> None:
        with self.lock:
            self.last_end = time.monotonic()


class _Server(ThreadingHTTPServer):
    daemon_threads = False  # server_close() then waits for every request already accepted

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
            return  # the client gave up (its 1.5 s deadline): routine, not a service problem
        super().handle_error(request, client_address)


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    timeout = 5  # a connection that sends nothing is dropped, so it cannot hold the service open

    def log_message(self, *args):  # keep service.log for real problems
        pass

    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _forbidden(self) -> bool:
        st = self.server.st
        allowed = {f"127.0.0.1:{st.port}", f"localhost:{st.port}"}
        if self.headers.get("Host") not in allowed or "Origin" in self.headers:
            self._send(403, {"error": "forbidden"})
            return True
        return False

    def do_GET(self):
        if self._forbidden():
            return
        if self.path == "/v1/health":
            st = self.server.st
            st.touch()  # a health check counts as activity (SessionStart before the first prompt)
            self._send(200, st.health())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self._forbidden():
            return
        if self.path != "/v1/profile":
            self._send(404, {"error": "not found"})
            return
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            self._send(415, {"error": "application/json required"})
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            prompt = body["prompt"]
            if not isinstance(prompt, str):
                raise ValueError("prompt must be a string")
        except (ValueError, KeyError, TypeError):
            self._send(400, {"error": "expected {\"prompt\": str}"})
            return
        st = self.server.st
        with st.lock:
            st.inflight += 1
        try:
            if st.state != "ready":
                self._send(503, {"state": st.state, "reason": st.reason})
                return
            try:
                with st.mlx:
                    result = st.predictor.predict(prompt)
            except Exception as exc:  # noqa: BLE001 — a predict failure is answered, never dropped
                print(f"predict failed: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
                self._send(500, {"error": type(exc).__name__})
                return
            self._send(200, {"answers": result["answers"], "usage": result["usage"],
                             "checkpoint": st.checkpoint, "question_set": st.question_set,
                             "versions": {"laya_harness": __version__,
                                          "laya_mlx": st.predictor.laya_mlx_version}})
        finally:
            with st.lock:
                st.inflight -= 1
                st.last_end = time.monotonic()


def _watch_idle(st: _State, server, stopped: threading.Event, idle_seconds: float) -> None:
    while not stopped.is_set():
        time.sleep(0.2)
        with st.lock:  # never idle while loading: a hung load keeps answering `loading`
            idle = (st.state != "loading" and st.inflight == 0
                    and time.monotonic() - st.last_end >= idle_seconds)
        if idle:
            server.socket.close()  # a later connect is refused, so the client starts a fresh service
            server.shutdown()
            stopped.set()


def _load(st: _State) -> None:
    from . import predictor

    try:
        p = predictor.make(st.cfg)
        p.load()
        with st.lock:  # the idle clock starts again when loading ends
            st.predictor = p
            st.state = "ready"
            st.last_end = time.monotonic()
    except BaseException as exc:  # noqa: BLE001 — any load failure means not_ready
        with st.lock:
            st.reason = f"{type(exc).__name__}: {exc}"
            st.state = "not_ready"
            st.last_end = time.monotonic()
        print(f"load failed: {st.reason}", file=sys.stderr, flush=True)


def _idle_seconds(cfg: dict) -> float:
    """`idle_seconds` as a positive number. Anything else, NaN included, is refused before the
    bind: a watcher that cannot count would keep the model resident for good."""
    try:
        seconds = float(cfg["idle_seconds"])
    except (TypeError, ValueError):
        seconds = 0.0
    if not seconds > 0:
        raise ValueError(f"idle_seconds must be a positive number, not {cfg['idle_seconds']!r}")
    return seconds


def main() -> int:
    cfg = config.load()
    port = config.port(cfg)
    idle_seconds = _idle_seconds(cfg)
    try:
        server = _Server(("127.0.0.1", port), _Handler)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            return 0
        raise
    paths.ensure_home()
    st = _State(cfg, port)
    server.st = st
    stopped = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=_watch_idle, args=(st, server, stopped, idle_seconds), daemon=True).start()
    _load(st)
    stopped.wait()
    server.server_close()  # joins the requests already accepted
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run the tests and confirm GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_service.py`

Expected: `38 passed`.

Run: `.venv/bin/python -m pytest -q`

Expected: `184 passed, 1 deselected`.

- [ ] **Step 7: Self-review and report — no commit** (golden rule 2)

Run: `git diff --check` (expected: no output). Report to the controller: files changed, the exact RED and GREEN commands with their output, and anything skipped and why. The controller snapshots the task boundary on `refs/laywip/stage0/task-5` and dispatches the reviewers.

---

### Task 6: Hook client and entry point

**Files:**
- Create: `laya_harness/hookargv.py`
- Create: `laya_harness/spawn.py`
- Create: `laya_harness/service_client.py`
- Create: `laya_harness/decision_log.py`
- Create: `laya_harness/client.py`
- Create: `laya_harness/__main__.py`
- Create: `tests/test_client_process.py`
- Test: `tests/test_client_process.py`

**Spec:** §4.1–§4.3 (flow, hook contract, spawn, warm-up wait), §4.6–§4.10 (state, source, rules, log), §5, §6

**Interfaces:**
- Consumes: Tasks 1–5: `config`, `paths`, `resources`, `source`, `transcript`, `session_state`, `adapter_claude_code`; the service from Task 5 (process tests start it in fake mode).
- Produces:
- `hookargv`: `EVENTS`, `TIMEOUTS = {"SessionStart": 8, "UserPromptSubmit": 3, "PostModelSwitch": 3}`,
  `hook_argv(interpreter, harness, event) -> list`, `hook_entry(interpreter, event) -> dict`,
  `settings_snippet(interpreter) -> dict` — the one function that builds the registered command.
- `spawn.service_argv(interpreter) -> list`, `spawn.spawn_service(cfg) -> None`.
- `service_client.health(port, timeout) -> (outcome, body)`,
  `service_client.profile(port, prompt, deadline) -> (outcome, body)`; outcomes `ok`, `refused`,
  `loading`, `not_ready`, `timeout`, `foreign`, `error`. Each call has a wall-clock limit (the
  request runs in a daemon thread), so a trickling listener cannot stretch it.
- `decision_log`: `SCHEMA_VERSION = 1`, `iso(ts) -> str`, `append(row) -> None`, `problem(message) -> None`.
- `client.run(harness, event, raw: bytes, started: float) -> str | None`; `PROFILE_DEADLINE = 1.5`,
  `WAIT_BUDGET = 4.0`, `HEALTH_TIMEOUT = 0.5`; `_wait_until_ready(port, spawned)` (the tests drive
  it with a fake clock). A UserPromptSubmit that raises still appends a row with status `error`;
  the row is written before the session's shown flags are saved; a decided row records the
  service's `question_set` and `versions.service_laya_harness`.
- `__main__.main(argv=None) -> int`; `python -I -m laya_harness hook claude-code <Event>` never
  raises and always exits 0.

> Revised after review round 1 (spec 516719a): wall-clock deadlines; an `error` row on any client failure; rows escape non-ASCII and are written before the shown flags are saved; rows record the service's question set and version; `service.log` is 0600; timeouts and foreign listeners get a `client.log` line; stdout is redirected at the descriptor level during a hook; and 22 more tests pin the exec-form argv, spawn only on refused, the detached session and its log, the wait's stop conditions and poll cap, file modes and skipped-row reasons. Contract files (hook contract §4.2, decision log §4.10): route the code review to `opus` per the gate profile. `__main__.py` here ends with a usage message for non-hook arguments; Task 7 replaces those three lines with the commands dispatch.

- [ ] **Step 1: Write the failing tests**

`tests/test_client_process.py`:

```python
"""Process-level tests of the hook client (spec §6): they run the exact registered argv."""

import json
import os
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import types
from pathlib import Path

import pytest

from conftest import write_config
from laya_harness import client, hookargv
from procs import env_for, request, start_service, stop, wait_health

PAYLOADS = json.loads((Path(__file__).parent / "fixtures" / "payloads.json").read_text())
ABOVE_GATE = {
    "difficulty": {"type": "choice", "choice": "architecture",
                   "probabilities": {"quick": 0.03, "routine": 0.06, "multi_file": 0.3, "architecture": 0.61}},
    "plan_first": {"type": "noul", "noul": 0.91},
    "parallel": {"type": "noul", "noul": 0.2},
}


def run_hook(home, event, payload, harness="claude-code", timeout=15):
    argv = hookargv.hook_argv(sys.executable, harness, event)
    data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    started = time.monotonic()
    result = subprocess.run(argv, input=data, capture_output=True, env=env_for(home), timeout=timeout)
    result.elapsed = time.monotonic() - started
    assert result.returncode == 0, result
    out = result.stdout.decode()
    assert out == "" or set(json.loads(out)) == {"systemMessage"}
    return result


def rows(home):
    path = home / "decisions.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def loads(home):
    path = home / "fake_loads.txt"
    return len(path.read_text().split()) if path.exists() else 0


@pytest.fixture
def cleanup(configured):
    """Stop any service a hook spawned on the test port."""
    procs = []
    yield procs
    for proc in procs:
        stop(proc)
    try:
        status, body = request(configured["port"], "GET", "/v1/health", timeout=0.5)
        if status == 200 and body.get("app") == "laya-harness":
            os.kill(body["pid"], signal.SIGTERM)
    except OSError:
        pass


class Listener(threading.Thread):
    """A foreign listener on the test port: "junk" answers with garbage, "hang" never replies."""

    def __init__(self, port, mode):
        super().__init__(daemon=True)
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", port))
        self.sock.listen(8)
        self.mode, self.held = mode, []

    def run(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            if self.mode == "junk":
                conn.recv(65536)
                conn.sendall(b"HTTP/1.0 200 OK\r\n\r\nnot laya at all")
                conn.close()
            else:
                self.held.append(conn)

    def close(self):
        self.sock.close()
        for conn in self.held:
            conn.close()


class Trickle(Listener):
    """A foreign listener that answers one byte every 0.2 s: each read is quick, the whole is not."""

    def run(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            self.held.append(conn)
            threading.Thread(target=self._drip, args=(conn,), daemon=True).start()

    def _drip(self, conn):
        try:
            conn.recv(65536)
            for byte in b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}":
                conn.sendall(bytes([byte]))
                time.sleep(0.2)
        except OSError:
            pass


def human(prompt="fix the typo in README", session="sess-1"):
    return dict(PAYLOADS["user_prompt_human"], prompt=prompt, session_id=session, transcript_path="")


def served_reply(**changes):
    reply = {"answers": ABOVE_GATE, "usage": {"truncated": False},
             "checkpoint": {"repo": "aac6fef/laya-mlx", "revision": "r", "model_mode": "fake"},
             "question_set": {"id": "profile_v0", "sha256": "0" * 64},
             "versions": {"laya_harness": "9.9.9", "laya_mlx": "0.3.0"}}
    reply.update(changes)
    return reply


# --- fail-open --------------------------------------------------------------------------

def test_bad_event_and_harness_print_nothing(configured, home):
    assert run_hook(home, "NoSuchEvent", human()).stdout == b""
    assert run_hook(home, "UserPromptSubmit", human(), harness="nope").stdout == b""
    assert "unknown" in (home / "client.log").read_text()


def test_garbage_stdin_prints_nothing(configured, home):
    assert run_hook(home, "UserPromptSubmit", b"\x00not json").stdout == b""
    assert "hook failed" in (home / "client.log").read_text()


@pytest.mark.parametrize("payload", [b"\x00not json", b"[1, 2]", b"", json.dumps(dict(PAYLOADS["user_prompt_human"],
                                     session_id=5, transcript_path="")).encode()])
def test_client_error_still_logs_an_error_row(configured, home, payload):
    assert run_hook(home, "UserPromptSubmit", payload).stdout == b""
    assert [r["status"] for r in rows(home)] == ["error"]  # spec §5: one row, status error
    assert "hook failed" in (home / "client.log").read_text()


def test_hook_argv_is_the_registered_exec_form():
    assert hookargv.hook_argv("/x/py", "claude-code", "UserPromptSubmit") == [
        "/x/py", "-I", "-m", "laya_harness", "hook", "claude-code", "UserPromptSubmit"]


def test_state_files_are_private(configured, home, cleanup):
    run_hook(home, "UserPromptSubmit", human())  # nothing bound: spawns, so service.log exists too
    wait_health(configured["port"])
    run_hook(home, "NoSuchEvent", human())
    assert stat.S_IMODE(home.stat().st_mode) == 0o700
    for name in ("decisions.jsonl", "client.log", "service.log"):
        assert stat.S_IMODE((home / name).stat().st_mode) == 0o600, name


def test_mode_off_does_nothing(configured, home):
    write_config(home, mode="off")
    result = run_hook(home, "UserPromptSubmit", human())
    assert result.stdout == b"" and rows(home) == [] and loads(home) == 0


# --- UserPromptSubmit ---------------------------------------------------------------------

def test_service_down_spawns_once_and_shows_nothing(configured, home, cleanup):
    write_config(home, fake_load_seconds=1)
    first = run_hook(home, "UserPromptSubmit", human())
    second = run_hook(home, "UserPromptSubmit", human(session="sess-2"))
    assert first.stdout == b"" and second.stdout == b""
    assert rows(home)[0]["status"] == "started_service" and rows(home)[0]["cold"] is True
    wait_health(configured["port"])
    assert loads(home) == 1


def test_first_prompt_shows_both_lines_and_logs_the_row(configured, home, cleanup):
    write_config(home, fake_answers=ABOVE_GATE)
    cleanup.append(start_service(home))
    wait_health(configured["port"])
    result = run_hook(home, "UserPromptSubmit", human("redesign the auth layer and migrate JWT handling"))
    assert json.loads(result.stdout) == {"systemMessage": (
        "laya · heavy task (p=0.91) → Opus 5.5 at xhigh effort fits this task\n"
        "laya · reads like a multi-step change (p=0.91) → Plan mode (mode menu, then 4), or tell Claude to plan first")}
    row = rows(home)[-1]
    assert row["status"] == "decided" and row["source"] == "human"
    assert row["suggestion"] == {"model": "claude-opus-5-5", "display": "Opus 5.5", "effort": "xhigh",
                                 "class": "architecture"}
    assert row["question_set"]["id"] == "profile_v0" and row["prompt_id"] == "prompt-1"
    assert row["versions"]["adapter_rules"] == "claude_code_v0"
    assert row["latency_ms"] > 0
    second = run_hook(home, "UserPromptSubmit", human("x" * 300))
    assert second.stdout == b""
    assert rows(home)[-1]["suppress_reason"] == {"model": "not_first_prompt", "plan": "already_shown"}


def test_machine_turns_record_source_and_reason(configured, home):
    for name in ("user_prompt_task_notification", "user_prompt_agent_message", "user_prompt_cross_session"):
        run_hook(home, "UserPromptSubmit", dict(PAYLOADS[name], transcript_path=""))
    assert [r["source"] for r in rows(home)] == ["task-notification", "agent", "peer"]
    assert all(r["suppress_reason"] == {"model": "not_human", "plan": "not_human"} for r in rows(home))


def test_row_records_what_the_service_ran(configured, home, monkeypatch):
    reply = served_reply()
    monkeypatch.setattr(client.service_client, "profile", lambda port, prompt, deadline: ("ok", reply))
    out = client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic())
    row = rows(home)[-1]
    assert out and row["status"] == "decided"
    assert row["question_set"] == reply["question_set"]  # what produced the answers, not the client's file
    assert row["versions"]["service_laya_harness"] == "9.9.9" and row["versions"]["laya_harness"] == "0.0.0"
    assert "run laya-harness stop" in (home / "client.log").read_text()


def test_a_failed_row_write_never_marks_a_line_as_shown(configured, home, monkeypatch):
    monkeypatch.setattr(client.service_client, "profile", lambda port, prompt, deadline: ("ok", served_reply()))

    def full_disk(row):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(client.decision_log, "append", full_disk)
    with pytest.raises(OSError):
        client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic())
    state = json.loads((home / "sessions" / "sess-1.json").read_text())
    assert state["model_line_shown"] is False and state["plan_shown"] is False


def test_lone_surrogate_prompt_still_shows_and_logs(configured, home, cleanup):
    write_config(home, fake_answers=ABOVE_GATE)
    cleanup.append(start_service(home))
    wait_health(configured["port"])
    result = run_hook(home, "UserPromptSubmit", human("redesign the auth layer \ud83d and migrate JWT handling"))
    assert result.stdout != b"" and rows(home)[-1]["status"] == "decided"


def test_machine_turns_are_skipped_without_calling_the_service(configured, home):
    for name in ("user_prompt_task_notification", "user_prompt_agent_message", "user_prompt_cross_session"):
        payload = dict(PAYLOADS[name], transcript_path="")
        assert run_hook(home, "UserPromptSubmit", payload).stdout == b""
    assert [r["status"] for r in rows(home)] == ["skipped"] * 3
    assert loads(home) == 0  # nothing was spawned
    assert not (home / "sessions" / "sess-1.json").exists()  # session state untouched


def test_log_only_shows_nothing_but_records_why(configured, home, cleanup):
    write_config(home, fake_answers=ABOVE_GATE, mode="log-only")
    cleanup.append(start_service(home))
    wait_health(configured["port"])
    assert run_hook(home, "UserPromptSubmit", human()).stdout == b""
    assert rows(home)[-1]["suppress_reason"] == {"model": "log_only", "plan": "log_only"}


def test_slow_reply_times_out_quickly(configured, home, cleanup):
    write_config(home, fake_predict_seconds=3)
    cleanup.append(start_service(home))
    wait_health(configured["port"])
    result = run_hook(home, "UserPromptSubmit", human())
    assert result.stdout == b"" and result.elapsed < 2.0
    assert rows(home)[-1]["status"] == "timeout"
    assert not (home / "service.log").exists()  # a timeout never spawns (spec §4.3)


@pytest.mark.parametrize("mode, status", [("junk", "error"), ("hang", "timeout")])
def test_foreign_listener_is_left_alone(configured, home, mode, status):
    listener = Listener(configured["port"], mode)
    listener.start()
    try:
        result = run_hook(home, "UserPromptSubmit", human())
    finally:
        listener.close()
    assert result.stdout == b"" and result.elapsed < 2.5
    assert rows(home)[-1]["status"] == status and loads(home) == 0
    assert not (home / "service.log").exists()  # spawn_service opens it: nothing was spawned
    assert f"port {configured['port']}" in (home / "client.log").read_text()  # spec §5: one line


@pytest.mark.parametrize("event, limit", [("UserPromptSubmit", 2.0), ("SessionStart", 1.5)])
def test_trickling_listener_cannot_stretch_the_deadline(configured, home, event, limit):
    listener = Trickle(configured["port"], "trickle")
    listener.start()
    try:
        result = run_hook(home, event, human() if event == "UserPromptSubmit" else start_payload(), timeout=30)
    finally:
        listener.close()
    assert result.elapsed < limit and not (home / "service.log").exists()


def test_spawned_service_is_detached_and_logs_stderr(configured, home, cleanup):
    write_config(home, fake_load_error="broken")  # the service prints "load failed" to stderr
    run_hook(home, "UserPromptSubmit", human())
    body = wait_health(configured["port"], want=("not_ready",))
    assert os.getsid(body["pid"]) == body["pid"]  # its own session: the hook runner cannot reap it
    deadline = time.monotonic() + 2
    while "load failed" not in (home / "service.log").read_text() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert "load failed" in (home / "service.log").read_text()


def test_spawn_does_not_hold_the_hook_pipes(configured, home, cleanup):
    write_config(home, fake_print_stdout=True)
    argv = hookargv.hook_argv(sys.executable, "claude-code", "UserPromptSubmit")
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env_for(home))
    proc.stdin.write(json.dumps(human()).encode())
    proc.stdin.close()
    proc.wait(timeout=10)
    exited = time.monotonic()
    out, err = proc.stdout.read(), proc.stderr.read()  # returns at EOF on both pipes
    assert time.monotonic() - exited < 0.5
    assert proc.returncode == 0 and out == b""
    assert wait_health(configured["port"])["state"] == "ready"  # the child outlived the hook


# --- SessionStart and PostModelSwitch -----------------------------------------------------

def start_payload(source="startup"):
    return dict(PAYLOADS["session_start_startup"], source=source, transcript_path="")


def test_startup_waits_while_loading_then_returns(configured, home, cleanup):
    write_config(home, fake_load_seconds=1.5)
    result = run_hook(home, "SessionStart", start_payload())
    assert result.stdout == b""
    assert 1.0 < result.elapsed < 3.5
    assert wait_health(configured["port"], timeout=0.5)["state"] == "ready"


def test_startup_gives_up_after_four_seconds(configured, home, cleanup):
    write_config(home, fake_load_seconds=8)
    result = run_hook(home, "SessionStart", start_payload())
    assert 3.8 < result.elapsed < 5.5 and result.stdout == b""


def test_startup_returns_at_once_when_not_ready(configured, home, cleanup):
    write_config(home, fake_load_error="broken")
    cleanup.append(start_service(home))
    wait_health(configured["port"], want=("not_ready",))
    assert run_hook(home, "SessionStart", start_payload()).elapsed < 1.0


@pytest.mark.parametrize("mode", ["junk", "hang"])
def test_startup_returns_at_once_on_foreign_listener(configured, home, mode):
    listener = Listener(configured["port"], mode)
    listener.start()
    try:
        result = run_hook(home, "SessionStart", start_payload())
    finally:
        listener.close()
    assert result.elapsed < 1.5 and loads(home) == 0
    assert not (home / "service.log").exists()
    assert "no service started" in (home / "client.log").read_text()


@pytest.mark.parametrize("source", ["resume", "clear", "compact", "fork"])
def test_other_sources_start_the_service_without_waiting(configured, home, cleanup, source):
    write_config(home, fake_load_seconds=8)
    assert run_hook(home, "SessionStart", start_payload(source)).elapsed < 1.0
    wait_health(configured["port"], want=("loading",))  # started; this also lets cleanup stop it


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


@pytest.mark.parametrize("replies, spawned, polls", [
    ([("ok", {"state": "ready"})], False, 1),
    ([("ok", {"state": "not_ready"})], False, 1),
    ([("foreign", None)], False, 1),
    ([("error", None)], False, 1),
    ([("timeout", None)], True, 1),
    ([("refused", None)], False, 1),
    ([("refused", None)] * 3 + [("ok", {"state": "ready"})], True, 4),
    ([("ok", {"state": "loading"}), ("timeout", None), ("ok", {"state": "ready"})], False, 3),
])
def test_wait_stop_conditions(monkeypatch, replies, spawned, polls):
    clock, seen = FakeClock(), []
    monkeypatch.setattr(client, "time", types.SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep))

    def health(port, timeout):
        seen.append(timeout)
        return replies[min(len(seen), len(replies)) - 1]

    monkeypatch.setattr(client.service_client, "health", health)
    client._wait_until_ready(1, spawned)
    assert len(seen) == polls


def test_wait_caps_each_poll_at_the_time_left(monkeypatch):
    clock, seen = FakeClock(), []
    monkeypatch.setattr(client, "time", types.SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep))

    def health(port, timeout):
        seen.append(timeout)
        clock.now += timeout
        return "ok", {"state": "loading"}

    monkeypatch.setattr(client.service_client, "health", health)
    client._wait_until_ready(1, spawned=True)
    assert clock.now <= client.WAIT_BUDGET + 1e-6 and seen[-1] < client.HEALTH_TIMEOUT


def test_startup_in_mode_off_starts_nothing(configured, home):
    write_config(home, mode="off")
    assert run_hook(home, "SessionStart", start_payload()).elapsed < 1.0
    assert loads(home) == 0


def test_model_switch_records_model_and_prints_nothing(configured, home):
    payload = dict(PAYLOADS["post_model_switch"], transcript_path="")
    assert run_hook(home, "PostModelSwitch", payload).stdout == b""
    state = json.loads((home / "sessions" / "sess-1.json").read_text())
    assert state["model"] == "claude-opus-4-7" and state["model_source"] == "post_model_switch"


def test_settings_snippet_uses_the_same_argv():
    snippet = hookargv.settings_snippet("/x/py")
    entry = snippet["hooks"]["UserPromptSubmit"][0]["hooks"][0]
    assert [entry["command"], *entry["args"]] == hookargv.hook_argv("/x/py", "claude-code", "UserPromptSubmit")
    assert {e: snippet["hooks"][e][0]["hooks"][0]["timeout"] for e in hookargv.EVENTS} == {
        "SessionStart": 8, "UserPromptSubmit": 3, "PostModelSwitch": 3}
```

- [ ] **Step 2: Create the modules as stubs**, so the tests fail on behaviour rather than on an import error (golden rule 4)

`laya_harness/hookargv.py` (stub — bodies raise `NotImplementedError`):

```python
"""The one place that builds the hook command (spec §4.2, §10). setup, the tests and the
install snippet all use it, so what is tested is exactly what is registered."""
EVENTS = ('SessionStart', 'UserPromptSubmit', 'PostModelSwitch')
TIMEOUTS = {'SessionStart': 8, 'UserPromptSubmit': 3, 'PostModelSwitch': 3}

def hook_argv(interpreter: str, harness: str, event: str) -> list:
    raise NotImplementedError

def hook_entry(interpreter: str, event: str) -> dict:
    raise NotImplementedError

def settings_snippet(interpreter: str) -> dict:
    raise NotImplementedError
```

`laya_harness/spawn.py` (stub — bodies raise `NotImplementedError`):

```python
"""Start the service fully detached (spec §4.3): no inherited stdin or stdout, stderr to
service.log, its own session. The caller never waits for it."""
import os
import subprocess
from . import config, paths

def service_argv(interpreter: str) -> list:
    raise NotImplementedError

def spawn_service(cfg: dict) -> None:
    raise NotImplementedError
```

`laya_harness/service_client.py` (stub — bodies raise `NotImplementedError`):

```python
"""Calls from the hook client to the local service (spec §4.2, §4.3). Standard library only.

Outcomes: "ok", "refused" (nothing bound to the port), "loading", "not_ready", "timeout",
"foreign" (a listener that is not laya-harness) and "error".
"""
import http.client
import json
import threading
import time

def _call(port: int, method: str, path: str, body, timeout: float):
    """One request with a wall-clock limit. The socket timeout applies to each read, so a
    listener that trickles bytes could otherwise stretch it without end (spec §4.2)."""
    raise NotImplementedError

def _request(port: int, method: str, path: str, body, timeout: float):
    raise NotImplementedError

def _json(raw):
    raise NotImplementedError

def health(port: int, timeout: float):
    raise NotImplementedError

def profile(port: int, prompt: str, deadline: float):
    raise NotImplementedError
```

`laya_harness/decision_log.py` (stub — bodies raise `NotImplementedError`):

```python
"""The decision log and the client's diagnostics (spec §4.10). Both stay on this Mac, 0600."""
import json
from datetime import datetime, timezone
from . import paths
SCHEMA_VERSION = 1

def iso(ts: float) -> str:
    raise NotImplementedError

def append(row: dict) -> None:
    raise NotImplementedError

def problem(message: str) -> None:
    raise NotImplementedError
```

`laya_harness/client.py` (stub — bodies raise `NotImplementedError`):

```python
"""The hook client (spec §4.1–§4.3, §4.6–§4.10). Standard library only: never imports laya_mlx.

`run` returns the text for stdout (one JSON object) or None. It may raise; the entry point in
`__main__` turns every failure into "print nothing, exit 0".
"""
import json
import time
from . import __version__, adapter_claude_code, config, decision_log, resources, service_client, session_state, source, spawn, transcript
PROFILE_DEADLINE = 1.5
WAIT_BUDGET = 4.0
HEALTH_TIMEOUT = 0.5

def run(harness, event, raw: bytes, started: float):
    raise NotImplementedError

def _error_row(cfg: dict, payload: dict, started: float) -> None:
    """Spec §5, §4.10: a client error still leaves one row, with status `error`."""
    raise NotImplementedError

def _ensure_service(cfg: dict, port: int) -> bool:
    """Start the service if nothing is bound to the port. Return True if this call spawned it."""
    raise NotImplementedError

def _wait_until_ready(port: int, spawned: bool) -> None:
    """Spec §4.3: poll for at most 4 s, and only while the service is starting."""
    raise NotImplementedError

def _session_start(cfg: dict, payload: dict) -> None:
    raise NotImplementedError

def _model_switch(payload: dict) -> None:
    raise NotImplementedError

def _base_row(cfg: dict, payload: dict, src: str, now: float) -> dict:
    raise NotImplementedError

def _finish(row: dict, state: dict, started: float, out, logged: list):
    raise NotImplementedError

def _prompt(cfg: dict, payload: dict, started: float, logged: list):
    raise NotImplementedError
```

`laya_harness/__main__.py` (stub — bodies raise `NotImplementedError`):

```python
"""Entry point: `python -I -m laya_harness hook claude-code <Event>` (hooks) and the
`laya-harness` console script (commands)."""
import time
_STARTED = time.monotonic()
import os
import sys

def _hook(args: list) -> None:
    """Never raises, always exits 0, and writes at most one JSON object to stdout (spec §4.2).

    Exit code 2 would block the prompt in every project, so argument errors, bad input and
    crashes all end the same way: nothing on stdout, exit 0, a line in client.log.
    """
    raise NotImplementedError

def main(argv=None) -> int:
    raise NotImplementedError
if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 3: Run the tests and confirm RED**

Run: `.venv/bin/python -m pytest -q tests/test_client_process.py`

Expected: `45 failed`; every failure is `NotImplementedError`. Record the output in the task report.

- [ ] **Step 4: Implement**, replacing the stubs with exactly this code

`laya_harness/hookargv.py`:

```python
"""The one place that builds the hook command (spec §4.2, §10). setup, the tests and the
install snippet all use it, so what is tested is exactly what is registered."""

EVENTS = ("SessionStart", "UserPromptSubmit", "PostModelSwitch")
TIMEOUTS = {"SessionStart": 8, "UserPromptSubmit": 3, "PostModelSwitch": 3}


def hook_argv(interpreter: str, harness: str, event: str) -> list:
    return [interpreter, "-I", "-m", "laya_harness", "hook", harness, event]


def hook_entry(interpreter: str, event: str) -> dict:
    argv = hook_argv(interpreter, "claude-code", event)
    return {"type": "command", "command": argv[0], "args": argv[1:], "timeout": TIMEOUTS[event]}


def settings_snippet(interpreter: str) -> dict:
    return {"hooks": {event: [{"hooks": [hook_entry(interpreter, event)]}] for event in EVENTS}}
```

`laya_harness/spawn.py`:

```python
"""Start the service fully detached (spec §4.3): no inherited stdin or stdout, stderr to
service.log, its own session. The caller never waits for it."""

import os
import subprocess

from . import config, paths


def service_argv(interpreter: str) -> list:
    return [interpreter, "-I", "-m", "laya_harness.service"]


def spawn_service(cfg: dict) -> None:
    home = paths.ensure_home()
    fd = os.open(paths.service_log(), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "ab") as log:
        subprocess.Popen(
            service_argv(config.interpreter(cfg)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=log,
            start_new_session=True,
            close_fds=True,
            cwd=str(home),
        )
```

`laya_harness/service_client.py`:

```python
"""Calls from the hook client to the local service (spec §4.2, §4.3). Standard library only.

Outcomes: "ok", "refused" (nothing bound to the port), "loading", "not_ready", "timeout",
"foreign" (a listener that is not laya-harness) and "error".
"""

import http.client
import json
import threading
import time


def _call(port: int, method: str, path: str, body, timeout: float):
    """One request with a wall-clock limit. The socket timeout applies to each read, so a
    listener that trickles bytes could otherwise stretch it without end (spec §4.2)."""
    result = {}

    def work():
        try:
            result["value"] = _request(port, method, path, body, timeout)
        except BaseException as exc:  # noqa: BLE001 — handed back to the caller below
            result["error"] = exc

    worker = threading.Thread(target=work, daemon=True)  # abandoned on timeout; the hook exits soon
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        raise TimeoutError(f"no complete reply within {timeout} s")
    if "error" in result:
        raise result["error"]
    return result["value"]


def _request(port: int, method: str, path: str, body, timeout: float):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"} if body is not None else {}
        conn.request(method, path, body=data, headers=headers)
        resp = conn.getresponse()
        return resp.status, resp.read()
    finally:
        conn.close()


def _json(raw):
    try:
        value = json.loads(raw)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def health(port: int, timeout: float):
    try:
        status, raw = _call(port, "GET", "/v1/health", None, timeout)
    except ConnectionRefusedError:
        return "refused", None
    except TimeoutError:
        return "timeout", None
    except (OSError, http.client.HTTPException):
        return "error", None
    body = _json(raw)
    if status == 200 and body is not None and body.get("app") == "laya-harness":
        return "ok", body
    return "foreign", None


def profile(port: int, prompt: str, deadline: float):
    started = time.monotonic()
    try:
        status, raw = _call(port, "POST", "/v1/profile", {"prompt": prompt}, deadline)
    except ConnectionRefusedError:
        return "refused", None
    except TimeoutError:
        return "timeout", None
    except (OSError, http.client.HTTPException):
        return "error", None
    if time.monotonic() - started > deadline:
        return "timeout", None
    body = _json(raw)
    if status == 200 and body is not None and isinstance(body.get("answers"), dict):
        return "ok", body
    if status == 503 and body is not None and body.get("state") in ("loading", "not_ready"):
        return body["state"], body
    return "error", body
```

`laya_harness/decision_log.py`:

```python
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
```

`laya_harness/client.py`:

```python
"""The hook client (spec §4.1–§4.3, §4.6–§4.10). Standard library only: never imports laya_mlx.

`run` returns the text for stdout (one JSON object) or None. It may raise; the entry point in
`__main__` turns every failure into "print nothing, exit 0".
"""

import json
import time

from . import (__version__, adapter_claude_code, config, decision_log, resources, service_client,
               session_state, source, spawn, transcript)

PROFILE_DEADLINE = 1.5
WAIT_BUDGET = 4.0
HEALTH_TIMEOUT = 0.5


def run(harness, event, raw: bytes, started: float):
    if harness != "claude-code":
        decision_log.problem(f"unknown harness {harness!r}")
        return None
    cfg = config.load()
    if cfg["mode"] == "off":
        return None
    payload, logged = None, []
    try:
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("hook input is not a JSON object")
        if event == "SessionStart":
            _session_start(cfg, payload)
            return None
        if event == "PostModelSwitch":
            _model_switch(payload)
            return None
        if event == "UserPromptSubmit":
            return _prompt(cfg, payload, started, logged)
    except BaseException:
        if event == "UserPromptSubmit" and not logged:
            _error_row(cfg, payload if isinstance(payload, dict) else {}, started)
        raise  # `__main__` writes the client.log line and still exits 0
    decision_log.problem(f"unknown event {event!r}")
    return None


def _error_row(cfg: dict, payload: dict, started: float) -> None:
    """Spec §5, §4.10: a client error still leaves one row, with status `error`."""
    try:
        row = _base_row(cfg, payload, None, time.time())
        row.update(status="error", latency_ms=round((time.monotonic() - started) * 1000, 1))
        decision_log.append(row)
    except BaseException:  # noqa: BLE001 — the log itself may be what failed
        pass


def _ensure_service(cfg: dict, port: int) -> bool:
    """Start the service if nothing is bound to the port. Return True if this call spawned it."""
    outcome, _ = service_client.health(port, timeout=0.3)
    if outcome == "refused":
        spawn.spawn_service(cfg)
        return True
    if outcome in ("foreign", "timeout"):
        decision_log.problem(f"port {port}: {outcome} on the health check; no service started")
    return False


def _wait_until_ready(port: int, spawned: bool) -> None:
    """Spec §4.3: poll for at most 4 s, and only while the service is starting."""
    deadline = time.monotonic() + WAIT_BUDGET
    first = True
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        outcome, body = service_client.health(port, timeout=min(HEALTH_TIMEOUT, remaining))
        if outcome == "ok":
            if body.get("state") != "loading":
                return
        elif outcome == "refused":
            if not spawned:
                return
        elif outcome == "timeout":
            if first:
                return
        else:
            return
        first = False
        time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))


def _session_start(cfg: dict, payload: dict) -> None:
    sid = payload.get("session_id") or ""
    state = session_state.on_session_start(session_state.load(sid), payload.get("source"))
    session_state.save(sid, state)
    port = config.port(cfg)
    spawned = _ensure_service(cfg, port)
    if payload.get("source") == "startup":
        _wait_until_ready(port, spawned)


def _model_switch(payload: dict) -> None:
    sid = payload.get("session_id") or ""
    state = session_state.on_model_switch(session_state.load(sid), payload.get("to_model"), time.time())
    session_state.save(sid, state)


def _base_row(cfg: dict, payload: dict, src: str, now: float) -> dict:
    questions = resources.questions()
    return {
        "schema_version": decision_log.SCHEMA_VERSION,
        "ts": decision_log.iso(now),
        "session_id": payload.get("session_id"),
        "prompt_id": payload.get("prompt_id"),
        "transcript_path": payload.get("transcript_path"),
        "cwd": payload.get("cwd"),
        "event": "UserPromptSubmit",
        "source": src,
        "mode": cfg["mode"],
        "status": None,
        "shown_text": None,
        "suppress_reason": None,
        "suggestion": None,
        "prompt": payload.get("prompt") or "",
        "truncated": None,
        "answers": None,
        "usage": None,
        "mismatches": None,
        "checkpoint": None,
        "question_set": {"id": questions["id"], "sha256": resources.questions_sha256()},
        "versions": {"laya_harness": __version__, "laya_mlx": None,
                     "adapter_rules": adapter_claude_code.RULES_VERSION,
                     "catalog": resources.catalog_sha256()},
        "session": None,
        "permission_mode": payload.get("permission_mode"),
        "latency_ms": None,
        "cold": False,
    }


def _finish(row: dict, state: dict, started: float, out, logged: list):
    row["session"] = {"model": state["model"], "effort": state["effort"], "model_source": state["model_source"]}
    row["latency_ms"] = round((time.monotonic() - started) * 1000, 1)
    decision_log.append(row)
    logged.append(True)
    return out


def _prompt(cfg: dict, payload: dict, started: float, logged: list):
    now = time.time()
    prompt = payload.get("prompt") or ""
    src = source.classify(payload)
    sid = payload.get("session_id") or ""
    state = session_state.load(sid)
    row = _base_row(cfg, payload, src, now)
    if src != "human":
        row.update(status="skipped", suppress_reason={"model": "not_human", "plan": "not_human"})
        return _finish(row, state, started, None, logged)

    first_human = state["prompt_count"] == 0
    reply = transcript.last_assistant(payload.get("transcript_path")) if state["prompt_count"] >= 1 else None
    state = session_state.on_human_prompt(state, now, reply)
    session_state.save(sid, state)

    port = config.port(cfg)
    outcome, body = service_client.profile(port, prompt, PROFILE_DEADLINE)
    if outcome == "refused":
        spawn.spawn_service(cfg)
        status = "started_service"
    elif outcome == "ok":
        status = "decided"
    elif outcome in ("loading", "not_ready", "timeout"):
        status = outcome
        if outcome == "timeout":
            decision_log.problem(f"port {port}: no complete reply within {PROFILE_DEADLINE} s")
    else:
        status = "error"
        decision_log.problem(f"unexpected reply from the service on port {port}")
    row["status"] = status
    row["cold"] = status in ("started_service", "loading")
    if status != "decided":
        return _finish(row, state, started, None, logged)

    questions = resources.questions()
    decision = adapter_claude_code.decide(
        body["answers"], first_human=first_human, plan_shown=state["plan_shown"],
        permission_mode=payload.get("permission_mode"), prompt=prompt, display=questions["display"],
        catalog=resources.catalog(), fit=resources.fit(), session=state)
    reasons = dict(decision["suppress_reason"])
    if cfg["mode"] == "log-only":
        for key, line in decision["line_for"].items():
            if line:
                reasons[key] = "log_only"
        shown = []
    else:
        shown = decision["lines"]
        if decision["line_for"]["model"]:
            state["model_line_shown"] = True
        if decision["line_for"]["plan"]:
            state["plan_shown"] = True

    usage = body.get("usage") or {}
    row.update(shown_text="\n".join(shown) or None, suppress_reason=reasons,
               suggestion=decision["suggestion"], mismatches=decision["mismatches"],
               answers=body["answers"], usage=usage, truncated=usage.get("truncated"),
               checkpoint=body.get("checkpoint"))
    versions = body.get("versions") or {}
    row["versions"].update(laya_mlx=versions.get("laya_mlx"), service_laya_harness=versions.get("laya_harness"))
    served = body.get("question_set")
    if isinstance(served, dict):  # the row records what produced the answers (spec §4.10, §5)
        if served != row["question_set"]:
            decision_log.problem(f"the service runs question set {served} but the client has "
                                 f"{row['question_set']}: run laya-harness stop")
        row["question_set"] = served
    out = json.dumps({"systemMessage": "\n".join(shown)}, ensure_ascii=False) if shown else None
    out = _finish(row, state, started, out, logged)
    if shown:
        session_state.save(sid, state)  # after the row: a failed write never marks a line as shown
    return out
```

`laya_harness/__main__.py`:

```python
"""Entry point: `python -I -m laya_harness hook claude-code <Event>` (hooks) and the
`laya-harness` console script (commands)."""

import time

_STARTED = time.monotonic()  # the hook's duration is measured from process start (spec §8)

import os  # noqa: E402
import sys  # noqa: E402


def _hook(args: list) -> None:
    """Never raises, always exits 0, and writes at most one JSON object to stdout (spec §4.2).

    Exit code 2 would block the prompt in every project, so argument errors, bad input and
    crashes all end the same way: nothing on stdout, exit 0, a line in client.log.
    """
    out = None
    real_stdout = None
    try:
        real_stdout = os.dup(1)
        os.dup2(os.open(os.devnull, os.O_WRONLY), 1)  # nothing a library or child writes reaches Claude
        sys.stdout = sys.stderr  # stray prints must never reach Claude's context
        from . import paths

        try:
            paths.ensure_home()
            log_fd = os.open(paths.client_log(), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            os.dup2(log_fd, 2)
        except BaseException:  # noqa: BLE001
            pass
        harness, event = (list(args) + [None, None])[:2]
        raw = sys.stdin.buffer.read()  # read stdin to the end before anything is spawned
        from . import client

        out = client.run(harness, event, raw, _STARTED)
    except BaseException as exc:  # noqa: BLE001
        try:
            from . import decision_log

            decision_log.problem(f"hook failed: {type(exc).__name__}: {exc}")
        except BaseException:  # noqa: BLE001
            pass
    try:
        if out and real_stdout is not None:
            os.write(real_stdout, out.encode("utf-8"))
    finally:
        os._exit(0)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["hook"]:
        _hook(argv[1:])
    print("usage: laya-harness hook claude-code <SessionStart|UserPromptSubmit|PostModelSwitch>",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the tests and confirm GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_client_process.py`

Expected: `45 passed`.

Run: `.venv/bin/python -m pytest -q`

Expected: `229 passed, 1 deselected`.

- [ ] **Step 6: Self-review and report — no commit** (golden rule 2)

Run: `git diff --check` (expected: no output). Report to the controller: files changed, the exact RED and GREEN commands with their output, and anything skipped and why. The controller snapshots the task boundary on `refs/laywip/stage0/task-6` and dispatches the reviewers.

---

### Task 7: Commands: setup, status, stop, mode

**Files:**
- Create: `laya_harness/commands.py`
- Create: `tests/test_commands.py`
- Modify: `laya_harness/__main__.py`
- Test: `tests/test_commands.py`

**Spec:** §4.5 (setup), §4.11 (commands), §4.13 (unknown models in status), §10

**Interfaces:**
- Consumes: `config`, `paths`, `resources`, `catalog`, `hookargv`, `service_client` (Tasks 1–6).
- Produces:
- `commands`: `SETUP_SESSION = "laya-setup-check"`, `setup(download=None, out=None) -> int`,
  `unknown_models() -> set`, `status(out=None) -> int`, `stop(out=None) -> int`,
  `set_mode(value, out=None) -> int`, `main(argv) -> int`.

> Revised after review round 1 (spec 83e1126): `stop` exits 1 and stops nothing when the port does not answer as laya-harness, and never signals an invalid pid; `status` reads the log line by line and skips rows it cannot read; `mode` refuses other values; `setup` prints the download size and source first; and 16 more tests pin every status outcome, the reuse sha check, the download arguments and the hook self-check (the two stop tests now stop their service in a `finally`). `setup` is the only network path, and the tests inject the downloader, so no test touches the network. From the Task 2 review: `setup` reuses a checkpoint only when every required file is present and the weights match, and fails if a download stays incomplete (spec §4.5). Known limitation, deferred from review of Task 1 (P3-9): a hand-edited invalid `mode` in config.json makes `laya-harness mode` and `status` raise; the hooks still fail silent, and the fix is to edit the file by hand.

- [ ] **Step 1: Write the failing tests**

`tests/test_commands.py`:

```python
import hashlib
import io
import json
import sys

import pytest

from conftest import write_config
from laya_harness import commands, config, hookargv, resources
from procs import start_service, stop, wait_health

FAKE_WEIGHTS = b"not really weights"


@pytest.fixture
def fake_checkpoint(monkeypatch):
    ck = dict(resources.checkpoint(), weights_sha256=hashlib.sha256(FAKE_WEIGHTS).hexdigest())
    monkeypatch.setattr(commands.resources, "checkpoint", lambda: ck)
    return ck


def place(model_dir, content, skip=()):
    """Write every required checkpoint file, with `content` as the weights."""
    for name in resources.checkpoint()["required"]:
        if name in skip:
            continue
        path = model_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if name == "model.safetensors" else b"{}")


def writer(content, skip=()):
    calls = []

    def download(ck, model_dir):
        calls.append(model_dir)
        place(model_dir, content, skip)

    download.calls = calls
    return download


def test_setup_downloads_writes_config_and_prints_snippet(home, fake_checkpoint):
    out = io.StringIO()
    download = writer(FAKE_WEIGHTS)
    assert commands.setup(download=download, out=out) == 0
    model_dir = home / "models" / f"laya-mlx@{fake_checkpoint['revision']}"
    assert download.calls == [model_dir]
    cfg = config.load()
    assert cfg["model_dir"] == str(model_dir) and cfg["interpreter"] == sys.executable
    assert cfg["revision"] == "047678560251f28113ee8f5df4be82102c7bf336"
    assert out.getvalue().startswith("downloading the pinned checkpoint (about 807 MB) from aac6fef/laya-mlx@047678560251")
    snippet = json.loads(out.getvalue().split("(spec §10):\n", 1)[1])
    assert snippet == hookargv.settings_snippet(sys.executable)
    assert not (home / "sessions" / f"{commands.SETUP_SESSION}.json").exists()


def test_setup_reuses_a_complete_matching_checkpoint(home, fake_checkpoint):
    model_dir = home / "models" / f"laya-mlx@{fake_checkpoint['revision']}"
    place(model_dir, FAKE_WEIGHTS)
    download = writer(FAKE_WEIGHTS)
    out = io.StringIO()
    assert commands.setup(download=download, out=out) == 0
    assert download.calls == [] and "already in place" in out.getvalue()


def test_setup_repairs_a_checkpoint_missing_its_tokenizer(home, fake_checkpoint):
    model_dir = home / "models" / f"laya-mlx@{fake_checkpoint['revision']}"
    place(model_dir, FAKE_WEIGHTS, skip=("tokenizer/tokenizer.json",))
    download = writer(FAKE_WEIGHTS)
    assert commands.setup(download=download, out=io.StringIO()) == 0
    assert download.calls == [model_dir]
    assert (model_dir / "tokenizer" / "tokenizer.json").is_file()


def test_setup_replaces_a_complete_checkpoint_whose_weights_do_not_match(home, fake_checkpoint):
    model_dir = home / "models" / f"laya-mlx@{fake_checkpoint['revision']}"
    place(model_dir, b"tampered")
    download = writer(FAKE_WEIGHTS)
    out = io.StringIO()
    assert commands.setup(download=download, out=out) == 0
    assert download.calls == [model_dir] and "already in place" not in out.getvalue()


def test_download_fetches_only_the_pinned_revision_and_listed_files(tmp_path, monkeypatch):
    import huggingface_hub

    calls = []
    monkeypatch.setattr(huggingface_hub, "snapshot_download", lambda *a, **k: calls.append((a, k)))
    ck = resources.checkpoint()
    commands._download(ck, tmp_path / "m")
    assert calls == [(("aac6fef/laya-mlx",), {"revision": "047678560251f28113ee8f5df4be82102c7bf336",
                                              "local_dir": str(tmp_path / "m"), "allow_patterns": ck["files"]})]


def test_setup_fails_when_the_hook_command_fails(home, fake_checkpoint, monkeypatch):
    monkeypatch.setattr(commands.hookargv, "hook_argv", lambda *a: [sys.executable, "-c", "import sys; sys.exit(3)"])
    out = io.StringIO()
    assert commands.setup(download=writer(FAKE_WEIGHTS), out=out) == 1
    assert "failed its check (exit 3)" in out.getvalue() and '"hooks"' not in out.getvalue()


def test_setup_rejects_a_checksum_mismatch(home, fake_checkpoint):
    out = io.StringIO()
    assert commands.setup(download=writer(b"tampered"), out=out) == 1
    assert "does not match" in out.getvalue()
    assert not (home / "config.json").exists()


def test_setup_rejects_an_incomplete_download(home, fake_checkpoint):
    out = io.StringIO()
    assert commands.setup(download=writer(FAKE_WEIGHTS, skip=("encoder/config.json",)), out=out) == 1
    assert "incomplete" in out.getvalue()
    assert not (home / "config.json").exists()


def test_mode_sets_config_and_rejects_unknown(home):
    assert commands.main(["mode", "log-only"]) == 0
    assert config.load()["mode"] == "log-only"
    with pytest.raises(SystemExit):
        commands.main(["mode", "loud"])
    with pytest.raises(ValueError):
        commands.set_mode("loud")
    assert config.load()["mode"] == "log-only"


def test_status_down_and_ready(configured, home):
    out = io.StringIO()
    commands.status(out=out)
    assert out.getvalue().startswith("laya-harness: down · mode show · checkpoint not set up ·")
    proc = start_service(home)
    try:
        wait_health(configured["port"])
        out = io.StringIO()
        commands.status(out=out)
        assert out.getvalue().startswith("laya-harness: ready · mode show")
    finally:
        stop(proc)


@pytest.mark.parametrize("outcome, body, shown", [
    ("ok", {"app": "laya-harness", "state": "not_ready", "reason": "FileNotFoundError: missing x"},
     "not_ready (FileNotFoundError: missing x)"),
    ("ok", {"app": "laya-harness", "state": "loading"}, "loading"),
    ("timeout", None, "unreachable (timeout)"),
    ("foreign", None, "unreachable (foreign)"),
])
def test_status_line_for_each_health_outcome(configured, home, monkeypatch, outcome, body, shown):
    write_config(home, revision="047678560251f28113ee8f5df4be82102c7bf336")
    monkeypatch.setattr(commands.service_client, "health", lambda port, timeout: (outcome, body))
    out = io.StringIO()
    assert commands.status(out=out) == 0
    assert out.getvalue() == f"laya-harness: {shown} · mode show · checkpoint 047678560251 · logs {home}\n"


def test_status_skips_rows_it_cannot_read(configured, home):
    lines = ['{"trunc', "123", "null", "[1]", '{"session": "x"}', '{"session": {"model": 5}}',
             json.dumps({"session": {"model": "claude-opus-6"}})]
    (home / "decisions.jsonl").write_bytes(("\n".join(lines) + "\n").encode() + b"\xff\n")
    out = io.StringIO()
    assert commands.status(out=out) == 0
    assert out.getvalue().splitlines()[1] == "models in the log that the catalog does not list: claude-opus-6"


def test_status_lists_models_the_catalog_does_not_know(configured, home):
    rows = [{"session": {"model": "claude-opus-5-5[1m]"}}, {"session": {"model": "claude-opus-6"}},
            {"session": {"model": None}}]
    (home / "decisions.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    out = io.StringIO()
    commands.status(out=out)
    assert "models in the log that the catalog does not list: claude-opus-6" in out.getvalue()


def test_stop_kills_the_service_and_warns(configured, home):
    proc = start_service(home)
    try:
        wait_health(configured["port"])
        out = io.StringIO()
        assert commands.stop(out=out) == 0
        proc.wait(timeout=5)
        assert "stopped the service" in out.getvalue() and "mode off" in out.getvalue()
        out = io.StringIO()
        assert commands.stop(out=out) == 0
        assert out.getvalue().strip() == "laya-harness: not running"
    finally:
        stop(proc)


def test_stop_in_mode_off_does_not_warn(configured, home):
    write_config(home, mode="off")
    proc = start_service(home)
    try:
        wait_health(configured["port"])
        out = io.StringIO()
        commands.stop(out=out)
        proc.wait(timeout=5)
        assert "mode off" not in out.getvalue()
    finally:
        stop(proc)


@pytest.mark.parametrize("outcome", ["timeout", "foreign", "error"])
def test_stop_reports_a_port_it_cannot_identify(configured, monkeypatch, outcome):
    monkeypatch.setattr(commands.service_client, "health", lambda port, timeout: (outcome, None))
    monkeypatch.setattr(commands.os, "kill", lambda *a: pytest.fail("os.kill called"))
    out = io.StringIO()
    assert commands.stop(out=out) == 1
    assert "not running" not in out.getvalue() and f"({outcome})" in out.getvalue()


@pytest.mark.parametrize("pid", [0, -1, None, "123", True])
def test_stop_never_signals_an_invalid_pid(configured, monkeypatch, pid):
    monkeypatch.setattr(commands.service_client, "health",
                        lambda port, timeout: ("ok", {"app": "laya-harness", "pid": pid, "state": "ready"}))
    monkeypatch.setattr(commands.os, "kill", lambda *a: pytest.fail("os.kill called"))
    assert commands.stop(out=io.StringIO()) == 1
```

- [ ] **Step 2: Create the modules as stubs**, so the tests fail on behaviour rather than on an import error (golden rule 4)

`laya_harness/commands.py` (stub — bodies raise `NotImplementedError`):

```python
"""`laya-harness setup | status | stop | mode` (spec §4.5, §4.11). Only `setup` touches the
network, and only to download the pinned checkpoint."""
import argparse
import json
import os
import signal
import subprocess
import sys
from . import catalog, config, hookargv, paths, resources, service_client
SETUP_SESSION = 'laya-setup-check'

def _download(checkpoint: dict, model_dir) -> None:
    raise NotImplementedError

def _complete(model_dir, checkpoint: dict) -> bool:
    raise NotImplementedError

def setup(download=None, out=None) -> int:
    raise NotImplementedError

def unknown_models() -> set:
    raise NotImplementedError

def status(out=None) -> int:
    raise NotImplementedError

def stop(out=None) -> int:
    raise NotImplementedError

def set_mode(value: str, out=None) -> int:
    raise NotImplementedError

def main(argv) -> int:
    raise NotImplementedError
```

- [ ] **Step 3: Run the tests and confirm RED**

Run: `.venv/bin/python -m pytest -q tests/test_commands.py`

Expected: `26 failed`; every failure is `NotImplementedError`. Record the output in the task report.

- [ ] **Step 4: Implement**, replacing the stubs with exactly this code

`laya_harness/commands.py`:

```python
"""`laya-harness setup | status | stop | mode` (spec §4.5, §4.11). Only `setup` touches the
network, and only to download the pinned checkpoint."""

import argparse
import json
import os
import signal
import subprocess
import sys

from . import catalog, config, hookargv, paths, resources, service_client

SETUP_SESSION = "laya-setup-check"


def _download(checkpoint: dict, model_dir) -> None:
    from huggingface_hub import snapshot_download

    model_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(checkpoint["repo"], revision=checkpoint["revision"], local_dir=str(model_dir),
                      allow_patterns=checkpoint["files"])


def _complete(model_dir, checkpoint: dict) -> bool:
    return all((model_dir / name).is_file() for name in checkpoint["required"])


def setup(download=None, out=None) -> int:
    out = out or sys.stdout
    paths.ensure_home()
    ck = resources.checkpoint()
    model_dir = paths.models_dir() / f"laya-mlx@{ck['revision']}"
    weights = model_dir / "model.safetensors"
    if _complete(model_dir, ck) and resources.sha256_file(weights) == ck["weights_sha256"]:
        print(f"checkpoint already in place: {model_dir}", file=out)
    else:
        print(f"downloading the pinned checkpoint (about 807 MB) from {ck['repo']}@{ck['revision'][:12]} "
              f"into {model_dir}", file=out)
        (download or _download)(ck, model_dir)
        if not _complete(model_dir, ck) or resources.sha256_file(weights) != ck["weights_sha256"]:
            print("the download is incomplete or does not match the pinned sha256", file=out)
            return 1
    cfg = config.load()
    cfg.update(interpreter=sys.executable, model_dir=str(model_dir), repo=ck["repo"], revision=ck["revision"])
    config.save(cfg)

    argv = hookargv.hook_argv(sys.executable, "claude-code", "PostModelSwitch")
    probe = {"session_id": SETUP_SESSION, "hook_event_name": "PostModelSwitch"}
    result = subprocess.run(argv, input=json.dumps(probe).encode(), capture_output=True, timeout=30)
    (paths.sessions_dir() / f"{SETUP_SESSION}.json").unlink(missing_ok=True)
    if result.returncode != 0 or result.stdout:
        print(f"the hook command failed its check (exit {result.returncode})", file=out)
        return 1
    print("Add these hooks to ~/.claude/settings.json (spec §10):", file=out)
    print(json.dumps(hookargv.settings_snippet(sys.executable), indent=2), file=out)
    return 0


def unknown_models() -> set:
    known = catalog.known(resources.catalog())
    seen = set()
    path = paths.decisions_path()
    if not path.is_file():
        return seen
    with open(path, encoding="utf-8", errors="replace") as f:  # line by line: the log can be large
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            session = row.get("session") if isinstance(row, dict) else None
            model = session.get("model") if isinstance(session, dict) else None
            name = catalog.canonical(model) if isinstance(model, str) else None
            if name and name not in known:
                seen.add(name)
    return seen


def status(out=None) -> int:
    out = out or sys.stdout
    cfg = config.load()
    outcome, body = service_client.health(config.port(cfg), timeout=0.5)
    if outcome == "refused":
        state = "down"
    elif outcome == "ok":
        state = body["state"] + (f" ({body['reason']})" if body.get("reason") else "")
    else:
        state = f"unreachable ({outcome})"
    revision = (cfg.get("revision") or "")[:12] or "not set up"
    print(f"laya-harness: {state} · mode {cfg['mode']} · checkpoint {revision} · logs {paths.home()}", file=out)
    unknown = unknown_models()
    if unknown:
        print("models in the log that the catalog does not list: " + ", ".join(sorted(unknown)), file=out)
    return 0


def stop(out=None) -> int:
    out = out or sys.stdout
    cfg = config.load()
    outcome, body = service_client.health(config.port(cfg), timeout=0.5)
    if outcome == "refused":
        print("laya-harness: not running", file=out)
        return 0
    if outcome != "ok":
        print(f"laya-harness: port {config.port(cfg)} did not answer as laya-harness ({outcome}); "
              "nothing stopped", file=out)
        return 1
    pid = body.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 1 or pid == os.getpid():
        print(f"laya-harness: the service reported an invalid pid {pid!r}; nothing stopped", file=out)
        return 1
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:  # it exited between the health check and the signal
        print("laya-harness: not running", file=out)
        return 0
    print(f"stopped the service (pid {body['pid']})", file=out)
    if cfg["mode"] != "off":
        print("note: the next prompt starts it again; `laya-harness mode off` keeps it down", file=out)
    return 0


def set_mode(value: str, out=None) -> int:
    out = out or sys.stdout
    if value not in config.MODES:
        raise ValueError(f"mode must be one of {', '.join(config.MODES)}, not {value!r}")
    cfg = config.load()
    cfg["mode"] = value
    config.save(cfg)
    print(f"mode: {value}", file=out)
    return 0


def main(argv) -> int:
    parser = argparse.ArgumentParser(prog="laya-harness")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="download the pinned checkpoint and print the hooks snippet")
    sub.add_parser("status", help="one line: service state, mode, checkpoint, logs")
    sub.add_parser("stop", help="stop the running service")
    mode = sub.add_parser("mode", help="show, log-only or off")
    mode.add_argument("value", choices=config.MODES)
    args = parser.parse_args(argv)
    if args.command == "setup":
        return setup()
    if args.command == "status":
        return status()
    if args.command == "stop":
        return stop()
    return set_mode(args.value)
```

- [ ] **Step 5: Route commands from the entry point** — in `laya_harness/__main__.py`, replace the usage lines at the end of `main()`:

```python
    print("usage: laya-harness hook claude-code <SessionStart|UserPromptSubmit|PostModelSwitch>",
          file=sys.stderr)
    return 2
```

with:

```python
    from . import commands

    return commands.main(argv)
```

- [ ] **Step 6: Run the tests and confirm GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_commands.py`

Expected: `26 passed`.

Run: `.venv/bin/python -m pytest -q`

Expected: `255 passed, 1 deselected`.

- [ ] **Step 7: Self-review and report — no commit** (golden rule 2)

Run: `git diff --check` (expected: no output). Report to the controller: files changed, the exact RED and GREEN commands with their output, and anything skipped and why. The controller snapshots the task boundary on `refs/laywip/stage0/task-7` and dispatches the reviewers.

---

### Task 8: Real-model gate, acceptance and install (controller, with the user)

**Files:**
- Modify: `tests/test_checkpoint_smoke.py` (replace the scaffold's version)
- Create: `docs/qa/design-qa.md`
- Modify: `docs/workflows/two-agent-swe-workflow.md` (record the newly executed commands)

**Spec:** §4.4, §4.5, §7 check 6, §8 (acceptance), §10 (install).

- [ ] **Step 1 (subagent): Replace the real-model smoke test** with exactly this file. It is a
  controller-only gate (`-m real_model`); the subagent writes it but does not run it.

`tests/test_checkpoint_smoke.py`:

```python
"""Controller-only gate (`pytest -m real_model`): the pinned checkpoint, the packaged question
set and the check-6 settings, end to end through the real service (spec §4.4, §4.5, check 6).
The weights are read from ~/.laya-harness/models; all other state uses a temporary directory."""

import time
from pathlib import Path

import pytest

from conftest import write_config
from laya_harness import resources
from procs import request, start_service, stop, wait_health

pytestmark = pytest.mark.real_model

MODEL_DIR = Path.home() / ".laya-harness" / "models" / f"laya-mlx@{resources.checkpoint()['revision']}"


def test_real_service_answers_the_stage0_questions(configured, home):
    if not MODEL_DIR.is_dir():
        pytest.fail(f"pinned checkpoint missing: {MODEL_DIR} (run `laya-harness setup`)")
    write_config(home, model_mode="real", model_dir=str(MODEL_DIR))
    started = time.monotonic()
    proc = start_service(home)
    try:
        health = wait_health(configured["port"], want=("ready", "not_ready"), timeout=30)
        assert health["state"] == "ready", health
        cold = time.monotonic() - started
        assert cold < 6.0, f"cold start {cold:.2f}s"

        t = time.monotonic()
        status, body = request(configured["port"], "POST", "/v1/profile",
                               {"prompt": "rename the variable foo to bar in utils.py"}, timeout=5)
        warm = time.monotonic() - t
        assert status == 200 and warm < 1.0, (status, warm)

        answers = body["answers"]
        assert sorted(answers) == ["difficulty", "parallel", "plan_first"]
        probabilities = answers["difficulty"]["probabilities"]
        assert set(probabilities) == {"quick", "routine", "multi_file", "architecture"}
        assert abs(sum(probabilities.values()) - 1) <= 0.0002
        for field in ("plan_first", "parallel"):
            assert 0 <= answers[field]["noul"] <= 1
        assert body["usage"]["truncated"] is False
        assert body["versions"]["laya_mlx"] == "0.3.0"

        status, body = request(configured["port"], "POST", "/v1/profile", {"prompt": "word " * 900}, timeout=5)
        assert status == 200 and body["usage"]["truncated"] is True

        log = (home / "service.log").read_text() if (home / "service.log").exists() else ""
        assert log == ""  # started directly by the test, so stderr went to DEVNULL, not the log
    finally:
        stop(proc)
```

- [ ] **Step 2 (controller): Register the console script and record the new gates.**
  Run `.venv/bin/python -m pip install -e ".[dev]"`, then `.venv/bin/laya-harness status`
  (expected: `laya-harness: down · mode show · checkpoint not set up · logs /Users/thunderstruck/.laya-harness`).
  Add `laya-harness setup | status | stop | mode` to the gate profile with the results you observed.

- [ ] **Step 3 (controller): Final gates.** Run `.venv/bin/python -m pytest -q` (expected
  `255 passed, 1 deselected`) and `.venv/bin/python -m pytest -q -m real_model` (expected `1 passed`).
  Contract-drift check: `git status --porcelain -- docs/` must be empty. The controller commits every
  doc change on its own before code, so an uncommitted doc edit can only have come from a subagent.

- [ ] **Step 4 (controller): Setup and acceptance hooks.** Run `.venv/bin/laya-harness setup`
  (expected: `checkpoint already in place`, then the snippet). Write the snippet's `hooks` object
  into this repo's `.claude/settings.local.json` (git-ignored); this is the acceptance-only
  registration. `~/.claude/settings.json` is not touched yet.

- [ ] **Step 5 (controller + user): Acceptance, spec §8.** Before every step that changes config,
  mode or code, run `.venv/bin/laya-harness stop`. UI steps are done by the user from the written
  instructions; the controller reads `~/.laya-harness/decisions.jsonl`, `client.log` and `service.log`.
  1. **Fake model, then real.** Set `"model_mode": "fake"` and a `fake_answers` profile for each copy
     state in §4.12 (light at 0.86, heavy at 0.91, plan at 0.88, both). The user opens a new Code
     session in this folder, sends a prompt, and screenshots each state (Cmd+Shift+4). The lines must
     match §4.12 exactly. Then set `"model_mode": "real"`, stop the service, and record whatever
     appears for a few real prompts.
  2. **No harm.** Over at least 20 prompts: zero blocked prompts, zero hook-timeout notices, and the
     logged `latency_ms` worst case at most about 1600.
  3. **Down paths.** (a) Service stopped, one prompt: nothing shown, Claude responds, the service is
     started exactly once, reaches `ready` after the hook exits (`laya-harness status`), and is still
     running after that session is closed. (b) `model_dir` pointing at an empty directory: several
     prompts show nothing, `status` shows `not_ready (FileNotFoundError: missing …)`, and nothing
     restarts in a loop (one service pid throughout). (c) A listener that never replies on the port
     (`python3 -c "import socket,time;s=socket.socket();s.bind(('127.0.0.1',47913));s.listen();time.sleep(60)"`):
     the prompt goes through within about 1.6 s with nothing shown.
  4. **Cold start.** With the service stopped, open a new session: the first prompt gets a profile and
     the first reply is delayed by at most about 4 s. Record the share of sessions whose first human
     prompt got no profile.
  5. **Off switch.** `laya-harness mode off`: no row is written and nothing is started; then
     `laya-harness mode show`.

- [ ] **Step 6 (visual reviewer): Compare the screenshots with §4.12** and the check-1 screenshots,
  surface by surface, per the gate profile; record the verdict.

- [ ] **Step 7 (controller): QA record.** Write `docs/qa/design-qa.md` with the result the comparison
  actually produced, per surface: `passed` only when every §4.12 state was compared with no P0–P2 left.

- [ ] **Step 8 (controller): One commit.** `git add` the explicit paths of Tasks 1–8 and commit
  (message ends with the Co-Authored-By trailer), then delete the `refs/laywip/stage0/*` refs.

- [ ] **Step 9 (controller + user): Install.** Show the user the exact diff that adds the snippet's
  three hooks to `~/.claude/settings.json`; apply it only with their approval. Remove the
  acceptance hooks from `.claude/settings.local.json`. `laya-harness mode off` remains the soft off
  switch; removing the three entries uninstalls.

---

## Spec coverage

| Spec | Task |
|---|---|
| §1.1 principles (instant, silent when unsure, System 2 decides) | 4 (gates), 6 (fail-open, deadlines) |
| §4.1 flow, three hooks | 6 |
| §4.2 hook contract (exec form, stdlib, exit 0, one JSON object, synchronous) | 6 |
| §4.3 spawn contract and warm-up wait | 6 |
| §4.4 service (bind first, health, checks, MLX lock, not_ready, idle, fake mode) | 5 |
| §4.5 checkpoint pin, offline local load, setup | 2, 5, 7 |
| §4.6 session state and switch precedence | 3 |
| §4.7 prompt source | 3 |
| §4.8 questions and thresholds | 2 |
| §4.9 adapter rules and numbers shown | 4 |
| §4.10 decision log | 6 |
| §4.11 commands and the test guard | 1, 7 |
| §4.12 copy deck | 4, 8 |
| §4.13 catalog and fit table | 2, 4, 7 (`status` lists unknown models) |
| §5 failure handling | 5, 6 |
| §6 testing | 1–8 |
| §8 acceptance, §10 install | 8 |
