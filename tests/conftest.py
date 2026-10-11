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
